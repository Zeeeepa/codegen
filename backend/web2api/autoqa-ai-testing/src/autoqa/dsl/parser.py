"""
DSL Parser for YAML test definitions.

Handles parsing, variable interpolation, and secret resolution.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import structlog
import yaml
from pydantic import ValidationError

from autoqa.dsl.models import (
    SecretReference,
    SecretSource,
    TestSpec,
    TestSuite,
)
from autoqa.dsl.validator import DSLValidator

logger = structlog.get_logger(__name__)


class SecretResolutionError(Exception):
    """Raised when a secret cannot be resolved."""

    def __init__(self, source: SecretSource, key: str, reason: str) -> None:
        self.source = source
        self.key = key
        self.reason = reason
        super().__init__(f"Failed to resolve secret {source}:{key}: {reason}")


class DSLParseError(Exception):
    """Raised when YAML parsing fails."""

    def __init__(self, message: str, line: int | None = None, column: int | None = None) -> None:
        self.line = line
        self.column = column
        location = ""
        if line is not None:
            location = f" at line {line}"
            if column is not None:
                location += f", column {column}"
        super().__init__(f"{message}{location}")


class SecretResolver:
    """Resolves secret references from various backends."""

    def __init__(
        self,
        vault_client: Any | None = None,
        aws_client: Any | None = None,
        k8s_client: Any | None = None,
    ) -> None:
        self._vault_client = vault_client
        self._aws_client = aws_client
        self._k8s_client = k8s_client
        self._cache: dict[str, str] = {}

    def resolve(self, ref: SecretReference) -> str:
        """Resolve a secret reference to its actual value."""
        cache_key = f"{ref.source}:{ref.key}:{ref.path}:{ref.version}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        match ref.source:
            case SecretSource.ENV:
                value = self._resolve_env(ref)
            case SecretSource.VAULT:
                value = self._resolve_vault(ref)
            case SecretSource.AWS_SECRETS:
                value = self._resolve_aws_secrets(ref)
            case SecretSource.K8S_SECRET:
                value = self._resolve_k8s_secret(ref)
            case _:
                raise SecretResolutionError(ref.source, ref.key, f"Unknown source: {ref.source}")

        self._cache[cache_key] = value
        return value

    def _resolve_env(self, ref: SecretReference) -> str:
        """Resolve environment variable."""
        value = os.environ.get(ref.key)
        if value is None:
            raise SecretResolutionError(
                ref.source, ref.key, f"Environment variable '{ref.key}' not set"
            )
        return value

    def _resolve_vault(self, ref: SecretReference) -> str:
        """Resolve HashiCorp Vault secret."""
        if self._vault_client is None:
            vault_addr = os.environ.get("VAULT_ADDR")
            vault_token = os.environ.get("VAULT_TOKEN")
            if not vault_addr or not vault_token:
                raise SecretResolutionError(
                    ref.source,
                    ref.key,
                    "Vault client not configured and VAULT_ADDR/VAULT_TOKEN not set",
                )
            try:
                import hvac

                self._vault_client = hvac.Client(url=vault_addr, token=vault_token)
            except ImportError as e:
                raise SecretResolutionError(
                    ref.source, ref.key, "hvac package not installed for Vault support"
                ) from e

        path = ref.path or "secret/data"
        try:
            response = self._vault_client.secrets.kv.v2.read_secret_version(
                path=f"{path}/{ref.key}",
                version=int(ref.version) if ref.version else None,
            )
            data = response.get("data", {}).get("data", {})
            if not data:
                raise SecretResolutionError(ref.source, ref.key, "Secret not found in Vault")
            return data.get("value", str(data))
        except Exception as e:
            raise SecretResolutionError(ref.source, ref.key, str(e)) from e

    def _resolve_aws_secrets(self, ref: SecretReference) -> str:
        """Resolve AWS Secrets Manager secret."""
        if self._aws_client is None:
            try:
                import boto3

                self._aws_client = boto3.client("secretsmanager")
            except ImportError as e:
                raise SecretResolutionError(
                    ref.source, ref.key, "boto3 package not installed for AWS Secrets support"
                ) from e

        try:
            kwargs: dict[str, Any] = {"SecretId": ref.key}
            if ref.version:
                kwargs["VersionId"] = ref.version
            response = self._aws_client.get_secret_value(**kwargs)
            return response.get("SecretString", "")
        except Exception as e:
            raise SecretResolutionError(ref.source, ref.key, str(e)) from e

    def _resolve_k8s_secret(self, ref: SecretReference) -> str:
        """Resolve Kubernetes secret."""
        if self._k8s_client is None:
            try:
                from kubernetes import client, config

                config.load_incluster_config()
                self._k8s_client = client.CoreV1Api()
            except ImportError as e:
                raise SecretResolutionError(
                    ref.source, ref.key, "kubernetes package not installed"
                ) from e
            except Exception:
                try:
                    from kubernetes import config

                    config.load_kube_config()
                except Exception as e:
                    raise SecretResolutionError(
                        ref.source, ref.key, f"Failed to configure Kubernetes client: {e}"
                    ) from e

        namespace = ref.path or "default"
        try:
            import base64

            secret = self._k8s_client.read_namespaced_secret(name=ref.key, namespace=namespace)
            if secret.data is None:
                raise SecretResolutionError(ref.source, ref.key, "Secret has no data")
            key_name = ref.version or "value"
            if key_name not in secret.data:
                raise SecretResolutionError(
                    ref.source, ref.key, f"Key '{key_name}' not found in secret"
                )
            return base64.b64decode(secret.data[key_name]).decode("utf-8")
        except Exception as e:
            if isinstance(e, SecretResolutionError):
                raise
            raise SecretResolutionError(ref.source, ref.key, str(e)) from e

    def clear_cache(self) -> None:
        """Clear the secret cache."""
        self._cache.clear()


class DSLParser:
    """Parser for YAML test DSL files."""

    SECRET_PATTERN = re.compile(r"\$\{(env|vault|aws_secrets|k8s_secret):([^}]+)\}")
    VARIABLE_PATTERN = re.compile(r"\$\{([a-zA-Z_][a-zA-Z0-9_]*)\}")

    def __init__(
        self,
        secret_resolver: SecretResolver | None = None,
        validator: DSLValidator | None = None,
    ) -> None:
        self._secret_resolver = secret_resolver or SecretResolver()
        self._validator = validator or DSLValidator()
        self._log = logger.bind(component="dsl_parser")

    def parse_file(self, path: str | Path) -> TestSpec | TestSuite:
        """Parse a YAML test file."""
        file_path = Path(path)
        if not file_path.exists():
            raise DSLParseError(f"File not found: {file_path}")
        if not file_path.is_file():
            raise DSLParseError(f"Path is not a file: {file_path}")

        self._log.info("Parsing test file", path=str(file_path))
        content = file_path.read_text(encoding="utf-8")
        return self.parse_string(content, source_file=str(file_path))

    def parse_string(
        self,
        content: str,
        source_file: str | None = None,
        variables: dict[str, str] | None = None,
    ) -> TestSpec | TestSuite:
        """Parse YAML content string."""
        try:
            raw_data = yaml.safe_load(content)
        except yaml.YAMLError as e:
            line = getattr(e, "problem_mark", None)
            if line:
                raise DSLParseError(str(e), line=line.line + 1, column=line.column + 1) from e
            raise DSLParseError(f"Invalid YAML: {e}") from e

        if not isinstance(raw_data, dict):
            raise DSLParseError("YAML root must be a mapping/dictionary")

        combined_vars = {**(variables or {})}
        if "variables" in raw_data and isinstance(raw_data["variables"], dict):
            combined_vars.update(raw_data["variables"])

        resolved_data = self._resolve_variables(raw_data, combined_vars)
        resolved_data = self._resolve_secrets(resolved_data)

        try:
            if "tests" in resolved_data:
                result = TestSuite.model_validate(resolved_data)
                self._log.info("Parsed test suite", name=result.name, test_count=len(result.tests))
            else:
                result = TestSpec.model_validate(resolved_data)
                self._log.info("Parsed test spec", name=result.name, step_count=len(result.steps))
        except ValidationError as e:
            error_messages = []
            for error in e.errors():
                loc = ".".join(str(x) for x in error["loc"])
                error_messages.append(f"  {loc}: {error['msg']}")
            raise DSLParseError(
                "Validation failed:\n" + "\n".join(error_messages)
            ) from e

        validation_errors = self._validator.validate(result)
        if validation_errors:
            raise DSLParseError(
                "Semantic validation failed:\n" + "\n".join(f"  - {e}" for e in validation_errors)
            )

        return result

    def _resolve_variables(
        self, data: Any, variables: dict[str, str], depth: int = 0
    ) -> Any:
        """Recursively resolve variable references in data."""
        if depth > 50:
            raise DSLParseError("Maximum variable resolution depth exceeded (circular reference?)")

        if isinstance(data, str):
            return self._interpolate_string(data, variables)
        elif isinstance(data, dict):
            return {k: self._resolve_variables(v, variables, depth + 1) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._resolve_variables(item, variables, depth + 1) for item in data]
        return data

    def _interpolate_string(self, value: str, variables: dict[str, str]) -> str:
        """Interpolate variable references in a string."""

        def replace_var(match: re.Match[str]) -> str:
            var_name = match.group(1)
            if var_name in variables:
                resolved = variables[var_name]
                if isinstance(resolved, SecretReference):
                    return str(resolved)
                return str(resolved)
            return match.group(0)

        return self.VARIABLE_PATTERN.sub(replace_var, value)

    def _resolve_secrets(self, data: Any, depth: int = 0) -> Any:
        """Recursively resolve secret references in data."""
        if depth > 50:
            raise DSLParseError("Maximum secret resolution depth exceeded")

        if isinstance(data, str):
            return self._resolve_secret_string(data)
        elif isinstance(data, dict):
            return {k: self._resolve_secrets(v, depth + 1) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._resolve_secrets(item, depth + 1) for item in data]
        return data

    def _resolve_secret_string(self, value: str) -> str:
        """Resolve secret references in a string."""

        def replace_secret(match: re.Match[str]) -> str:
            source_str = match.group(1)
            key = match.group(2)

            parts = key.split(":", 2)
            main_key = parts[0]
            path = parts[1] if len(parts) > 1 else None
            version = parts[2] if len(parts) > 2 else None

            try:
                source = SecretSource(source_str)
            except ValueError as e:
                raise DSLParseError(f"Unknown secret source: {source_str}") from e

            ref = SecretReference(source=source, key=main_key, path=path, version=version)
            return self._secret_resolver.resolve(ref)

        return self.SECRET_PATTERN.sub(replace_secret, value)

    def parse_directory(
        self,
        directory: str | Path,
        pattern: str = "**/*.yaml",
        recursive: bool = True,
    ) -> list[TestSpec | TestSuite]:
        """Parse all YAML files in a directory."""
        dir_path = Path(directory)
        if not dir_path.exists():
            raise DSLParseError(f"Directory not found: {dir_path}")
        if not dir_path.is_dir():
            raise DSLParseError(f"Path is not a directory: {dir_path}")

        results: list[TestSpec | TestSuite] = []
        glob_method = dir_path.rglob if recursive else dir_path.glob

        for file_path in sorted(glob_method(pattern)):
            if file_path.name.startswith("."):
                continue
            try:
                result = self.parse_file(file_path)
                results.append(result)
            except DSLParseError as e:
                self._log.error("Failed to parse file", path=str(file_path), error=str(e))
                raise

        self._log.info("Parsed directory", path=str(dir_path), file_count=len(results))
        return results
