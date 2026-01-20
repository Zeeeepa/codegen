"""Tests for LLM configuration module."""

from __future__ import annotations

import os
from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest
import yaml
from pydantic import SecretStr

from autoqa.llm.config import (
    LLMConfig,
    LLMEndpointConfig,
    LLMProvider,
    LLMSettings,
    RateLimitConfig,
    RetryConfig,
    ToolLLMConfig,
    ToolName,
    load_llm_config,
)


class TestLLMEndpointConfig:
    """Tests for LLMEndpointConfig."""

    def test_default_config(self) -> None:
        """Test default endpoint configuration."""
        config = LLMEndpointConfig()

        assert config.base_url == "https://api.openai.com/v1"
        assert config.model == "gpt-4o-mini"
        assert config.provider == LLMProvider.OPENAI
        assert config.temperature == 0.3
        assert config.max_tokens == 2048
        assert not config.has_api_key

    def test_custom_config(self) -> None:
        """Test custom endpoint configuration."""
        config = LLMEndpointConfig(
            base_url="https://custom.api.com/v1",
            api_key=SecretStr("test-key"),
            model="gpt-4",
            temperature=0.7,
            max_tokens=4096,
        )

        assert config.base_url == "https://custom.api.com/v1"
        assert config.has_api_key
        assert config.api_key.get_secret_value() == "test-key"
        assert config.model == "gpt-4"

    def test_base_url_trailing_slash_stripped(self) -> None:
        """Test that trailing slashes are stripped from base_url."""
        config = LLMEndpointConfig(base_url="https://api.example.com/v1/")
        assert config.base_url == "https://api.example.com/v1"

    def test_invalid_base_url(self) -> None:
        """Test that invalid base_url raises error."""
        with pytest.raises(ValueError, match="http"):
            LLMEndpointConfig(base_url="invalid-url")

    def test_azure_config_requires_deployment(self) -> None:
        """Test that Azure provider requires deployment name."""
        with pytest.raises(ValueError, match="azure_deployment"):
            LLMEndpointConfig(
                provider=LLMProvider.AZURE,
                base_url="https://myresource.openai.azure.com",
            )

    def test_azure_config_valid(self) -> None:
        """Test valid Azure configuration."""
        config = LLMEndpointConfig(
            provider=LLMProvider.AZURE,
            base_url="https://myresource.openai.azure.com",
            azure_deployment="my-deployment",
        )
        assert config.azure_deployment == "my-deployment"


class TestToolLLMConfig:
    """Tests for ToolLLMConfig."""

    def test_default_disabled(self) -> None:
        """Test that tools are disabled by default."""
        config = ToolLLMConfig()
        assert not config.enabled

    def test_enabled_with_override(self) -> None:
        """Test enabled config with temperature override."""
        config = ToolLLMConfig(
            enabled=True,
            temperature_override=0.5,
        )
        assert config.enabled
        assert config.temperature_override == 0.5


class TestLLMConfig:
    """Tests for LLMConfig."""

    def test_default_config_disabled(self) -> None:
        """Test that LLM is disabled by default."""
        config = LLMConfig()

        assert not config.enabled
        for tool in ToolName:
            assert not config.is_tool_enabled(tool)

    def test_tool_not_enabled_when_global_disabled(self) -> None:
        """Test that tools are not enabled when global is disabled."""
        config = LLMConfig(
            enabled=False,
            test_builder=ToolLLMConfig(enabled=True),
        )
        assert not config.is_tool_enabled(ToolName.TEST_BUILDER)

    def test_tool_enabled_when_both_enabled(self) -> None:
        """Test that tool is enabled when both global and tool are enabled."""
        config = LLMConfig(
            enabled=True,
            test_builder=ToolLLMConfig(enabled=True),
        )
        assert config.is_tool_enabled(ToolName.TEST_BUILDER)

    def test_get_effective_endpoint_default(self) -> None:
        """Test getting effective endpoint uses default."""
        config = LLMConfig(
            default_endpoint=LLMEndpointConfig(model="gpt-4"),
        )
        endpoint = config.get_effective_endpoint(ToolName.TEST_BUILDER)
        assert endpoint.model == "gpt-4"

    def test_get_effective_endpoint_override(self) -> None:
        """Test getting effective endpoint with tool override."""
        custom_endpoint = LLMEndpointConfig(model="custom-model")
        config = LLMConfig(
            default_endpoint=LLMEndpointConfig(model="default-model"),
            test_builder=ToolLLMConfig(
                enabled=True,
                endpoint_override=custom_endpoint,
            ),
        )
        endpoint = config.get_effective_endpoint(ToolName.TEST_BUILDER)
        assert endpoint.model == "custom-model"

    def test_get_effective_temperature(self) -> None:
        """Test getting effective temperature with override."""
        config = LLMConfig(
            default_endpoint=LLMEndpointConfig(temperature=0.3),
            test_builder=ToolLLMConfig(
                enabled=True,
                temperature_override=0.7,
            ),
        )
        assert config.get_effective_temperature(ToolName.TEST_BUILDER) == 0.7
        assert config.get_effective_temperature(ToolName.ASSERTIONS) == 0.3


class TestLoadLLMConfig:
    """Tests for load_llm_config function."""

    def test_load_default_config(self) -> None:
        """Test loading default config when no file exists."""
        config = load_llm_config()
        assert isinstance(config, LLMConfig)

    def test_load_from_yaml_file(self, tmp_path: Path) -> None:
        """Test loading config from YAML file."""
        config_file = tmp_path / "llm.yaml"
        config_data = {
            "enabled": True,
            "default_endpoint": {
                "base_url": "https://custom.api.com/v1",
                "model": "custom-model",
            },
            "test_builder": {
                "enabled": True,
            },
        }
        with config_file.open("w") as f:
            yaml.dump(config_data, f)

        config = load_llm_config(config_file=config_file, env_override=False)

        assert config.enabled
        assert config.default_endpoint.model == "custom-model"
        assert config.is_tool_enabled(ToolName.TEST_BUILDER)

    def test_env_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that environment variables can override config."""
        monkeypatch.setenv("AUTOQA_LLM_ENABLED", "true")
        monkeypatch.setenv("AUTOQA_LLM_MODEL", "env-model")
        monkeypatch.setenv("AUTOQA_LLM_TEST_BUILDER_ENABLED", "true")

        config = load_llm_config()

        assert config.enabled
        assert config.default_endpoint.model == "env-model"


class TestRetryConfig:
    """Tests for RetryConfig."""

    def test_default_values(self) -> None:
        """Test default retry configuration."""
        config = RetryConfig()
        assert config.max_retries == 3
        assert config.initial_delay_ms == 1000
        assert config.exponential_base == 2.0
        assert config.jitter


class TestRateLimitConfig:
    """Tests for RateLimitConfig."""

    def test_default_values(self) -> None:
        """Test default rate limit configuration."""
        config = RateLimitConfig()
        assert config.requests_per_minute == 60
        assert config.tokens_per_minute == 90000
        assert config.concurrent_requests == 5
