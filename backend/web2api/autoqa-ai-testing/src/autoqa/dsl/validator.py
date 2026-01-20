"""
Semantic validator for DSL test specifications.

Performs deeper validation beyond Pydantic schema validation.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from autoqa.dsl.models import TestSpec, TestStep, TestSuite

logger = structlog.get_logger(__name__)


class DSLValidator:
    """Validates test specifications for semantic correctness."""

    URL_PATTERN = re.compile(
        r"^(https?://|owl://|about:|data:|file://)"
        r"|([\w.-]+\.[a-zA-Z]{2,})"
        r"|localhost(:\d+)?"
    )

    def __init__(self) -> None:
        self._log = logger.bind(component="dsl_validator")

    def validate(self, spec: TestSpec | TestSuite) -> list[str]:
        """Validate a test specification or suite."""
        errors: list[str] = []

        if hasattr(spec, "tests"):
            errors.extend(self._validate_suite(spec))  # type: ignore[arg-type]
        else:
            errors.extend(self._validate_spec(spec))  # type: ignore[arg-type]

        return errors

    def _validate_suite(self, suite: TestSuite) -> list[str]:
        """Validate a test suite."""
        errors: list[str] = []

        test_names = set()
        for i, test in enumerate(suite.tests):
            if test.name in test_names:
                errors.append(f"Duplicate test name in suite: '{test.name}'")
            test_names.add(test.name)

            test_errors = self._validate_spec(test)
            for error in test_errors:
                errors.append(f"Test '{test.name}': {error}")

        if suite.before_suite:
            hook_errors = self._validate_steps(suite.before_suite.steps, "before_suite")
            errors.extend(hook_errors)

        if suite.after_suite:
            hook_errors = self._validate_steps(suite.after_suite.steps, "after_suite")
            errors.extend(hook_errors)

        return errors

    def _validate_spec(self, spec: TestSpec) -> list[str]:
        """Validate a single test specification."""
        errors: list[str] = []

        errors.extend(self._validate_steps(spec.steps, "steps"))

        if spec.before_all:
            errors.extend(self._validate_steps(spec.before_all.steps, "before_all"))
        if spec.before_each:
            errors.extend(self._validate_steps(spec.before_each.steps, "before_each"))
        if spec.after_each:
            errors.extend(self._validate_steps(spec.after_each.steps, "after_each"))
        if spec.after_all:
            errors.extend(self._validate_steps(spec.after_all.steps, "after_all"))

        errors.extend(self._validate_variable_references(spec))
        errors.extend(self._validate_capture_references(spec.steps))

        return errors

    def _validate_steps(self, steps: list[TestStep], context: str) -> list[str]:
        """Validate a list of test steps."""
        errors: list[str] = []

        for i, step in enumerate(steps):
            step_id = step.name or f"step {i + 1}"
            prefix = f"{context}.{step_id}"

            if step.url:
                if not self._is_valid_url(step.url) and not step.url.startswith("${"):
                    errors.append(f"{prefix}: Invalid URL format '{step.url}'")

            if step.timeout is not None and step.timeout < 0:
                errors.append(f"{prefix}: Timeout cannot be negative")

            if step.retry_count > 0 and step.retry_delay_ms < 100:
                errors.append(
                    f"{prefix}: retry_delay_ms should be at least 100ms "
                    "when retry_count > 0"
                )

            if step.visual_assertion:
                va = step.visual_assertion
                if va.threshold < 0.01 and va.mode != "pixel":
                    errors.append(
                        f"{prefix}: Threshold below 0.01 is only recommended "
                        "for pixel-perfect comparison"
                    )

            if step.network_assertion:
                na = step.network_assertion
                if na.is_regex:
                    try:
                        re.compile(na.url_pattern)
                    except re.error as e:
                        errors.append(f"{prefix}: Invalid regex pattern: {e}")

            if step.custom_assertion:
                ca = step.custom_assertion
                dangerous_patterns = [
                    "eval(",
                    "Function(",
                    "setTimeout(",
                    "setInterval(",
                    "fetch(",
                    "XMLHttpRequest",
                ]
                for pattern in dangerous_patterns:
                    if pattern in ca.script:
                        self._log.warning(
                            "Potentially dangerous script pattern detected",
                            step=step_id,
                            pattern=pattern,
                        )

            if step.file_paths:
                for path in step.file_paths:
                    if path.startswith("${"):
                        continue
                    if ".." in path:
                        errors.append(
                            f"{prefix}: File path cannot contain '..': {path}"
                        )

        return errors

    def _validate_variable_references(self, spec: TestSpec) -> list[str]:
        """Validate that variable references are defined."""
        errors: list[str] = []
        defined_vars = set(spec.variables.keys())
        if spec.environment.variables:
            defined_vars.update(spec.environment.variables.keys())

        var_pattern = re.compile(r"\$\{([a-zA-Z_][a-zA-Z0-9_]*)\}")

        def check_string(value: str, context: str) -> None:
            for match in var_pattern.finditer(value):
                var_name = match.group(1)
                if var_name not in defined_vars:
                    if not var_name.startswith(("env:", "vault:", "aws_secrets:", "k8s_secret:")):
                        errors.append(
                            f"{context}: Undefined variable '${{{var_name}}}'"
                        )

        def check_step(step: TestStep, idx: int) -> None:
            step_name = step.name or f"step {idx + 1}"
            for field in ["selector", "text", "value", "url", "script"]:
                val = getattr(step, field)
                if isinstance(val, str):
                    check_string(val, f"steps.{step_name}.{field}")

        for i, step in enumerate(spec.steps):
            check_step(step, i)

        return errors

    def _validate_capture_references(self, steps: list[TestStep]) -> list[str]:
        """Validate that captured variables are used after being defined."""
        errors: list[str] = []
        captured_vars: set[str] = set()

        for i, step in enumerate(steps):
            step_name = step.name or f"step {i + 1}"

            if step.skip_if:
                var_pattern = re.compile(r"\$\{([a-zA-Z_][a-zA-Z0-9_]*)\}")
                for match in var_pattern.finditer(step.skip_if):
                    var_name = match.group(1)
                    if var_name not in captured_vars:
                        errors.append(
                            f"steps.{step_name}: skip_if references "
                            f"'${{{var_name}}}' before it is captured"
                        )

            if step.capture_as:
                if step.capture_as in captured_vars:
                    self._log.warning(
                        "Overwriting previously captured variable",
                        step=step_name,
                        variable=step.capture_as,
                    )
                captured_vars.add(step.capture_as)

        return errors

    def _is_valid_url(self, url: str) -> bool:
        """Check if URL has a valid format."""
        if self.URL_PATTERN.match(url):
            return True
        return "/" in url or url.startswith("${")
