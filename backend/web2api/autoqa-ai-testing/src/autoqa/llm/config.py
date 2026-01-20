"""
LLM configuration models for AutoQA.

Provides Pydantic-validated configuration for OpenAI-compatible LLM endpoints
with per-tool enable/disable capability.
"""

from __future__ import annotations

import os
from enum import StrEnum
from functools import cached_property
from pathlib import Path
from typing import Any, Self

import yaml
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SecretStr,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProvider(StrEnum):
    """Supported LLM provider types."""

    OPENAI = "openai"
    AZURE = "azure"
    ANTHROPIC = "anthropic"
    LOCAL = "local"  # For local/self-hosted models
    CUSTOM = "custom"  # For any OpenAI-compatible endpoint


class ToolName(StrEnum):
    """AutoQA tools that can use LLM enhancement."""

    TEST_BUILDER = "test_builder"
    STEP_TRANSFORMER = "step_transformer"
    ASSERTIONS = "assertions"
    SELF_HEALING = "self_healing"
    CHAOS_AGENTS = "chaos_agents"


class RetryConfig(BaseModel):
    """Configuration for retry behavior on LLM API calls."""

    model_config = ConfigDict(frozen=True)

    max_retries: int = Field(default=3, ge=0, le=10)
    initial_delay_ms: int = Field(default=1000, ge=100, le=30000)
    max_delay_ms: int = Field(default=30000, ge=1000, le=120000)
    exponential_base: float = Field(default=2.0, ge=1.0, le=4.0)
    jitter: bool = True


class RateLimitConfig(BaseModel):
    """Configuration for rate limiting LLM API calls."""

    model_config = ConfigDict(frozen=True)

    requests_per_minute: int = Field(default=60, ge=1, le=10000)
    tokens_per_minute: int = Field(default=90000, ge=1000, le=10000000)
    concurrent_requests: int = Field(default=5, ge=1, le=100)


class LLMEndpointConfig(BaseModel):
    """Configuration for an LLM API endpoint."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    base_url: str = Field(
        default="https://api.openai.com/v1",
        description="Base URL for the OpenAI-compatible API endpoint",
    )
    api_key: SecretStr = Field(
        default=SecretStr(""),
        description="API key for authentication",
    )
    model: str = Field(
        default="gpt-4o-mini",
        description="Model identifier to use for completions",
    )
    provider: LLMProvider = Field(
        default=LLMProvider.OPENAI,
        description="LLM provider type",
    )

    # Request parameters
    temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, ge=1, le=128000)
    timeout_ms: int = Field(default=30000, ge=1000, le=300000)

    # Azure-specific fields
    azure_deployment: str | None = Field(
        default=None,
        description="Azure OpenAI deployment name (required for Azure provider)",
    )
    azure_api_version: str = Field(
        default="2024-02-15-preview",
        description="Azure OpenAI API version",
    )

    # Retry and rate limiting
    retry: RetryConfig = Field(default_factory=RetryConfig)
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, v: str) -> str:
        """Ensure base_url is valid and strip trailing slashes."""
        v = v.rstrip("/")
        if not v.startswith(("http://", "https://")):
            raise ValueError("base_url must start with http:// or https://")
        return v

    @model_validator(mode="after")
    def validate_azure_config(self) -> Self:
        """Validate Azure-specific configuration."""
        if self.provider == LLMProvider.AZURE and not self.azure_deployment:
            raise ValueError("azure_deployment is required for Azure provider")
        return self

    @property
    def has_api_key(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key.get_secret_value())


class ToolLLMConfig(BaseModel):
    """Per-tool LLM configuration."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    enabled: bool = Field(
        default=False,
        description="Whether LLM is enabled for this tool",
    )
    endpoint_override: LLMEndpointConfig | None = Field(
        default=None,
        description="Optional endpoint override for this specific tool",
    )
    temperature_override: float | None = Field(
        default=None,
        ge=0.0,
        le=2.0,
        description="Optional temperature override for this tool",
    )
    max_tokens_override: int | None = Field(
        default=None,
        ge=1,
        le=128000,
        description="Optional max_tokens override for this tool",
    )
    custom_system_prompt: str | None = Field(
        default=None,
        description="Optional custom system prompt for this tool",
    )


class LLMConfig(BaseModel):
    """Complete LLM configuration for AutoQA."""

    model_config = ConfigDict(extra="forbid")

    # Global enable/disable
    enabled: bool = Field(
        default=False,
        description="Global LLM enable flag. When False, all LLM features are disabled.",
    )

    # Default endpoint configuration
    default_endpoint: LLMEndpointConfig = Field(
        default_factory=LLMEndpointConfig,
        description="Default LLM endpoint configuration used when tool-specific not set",
    )

    # Per-tool configurations
    test_builder: ToolLLMConfig = Field(
        default_factory=ToolLLMConfig,
        description="LLM configuration for Auto Test Builder",
    )
    step_transformer: ToolLLMConfig = Field(
        default_factory=ToolLLMConfig,
        description="LLM configuration for Step Transformer (natural language to action)",
    )
    assertions: ToolLLMConfig = Field(
        default_factory=ToolLLMConfig,
        description="LLM configuration for semantic assertions",
    )
    self_healing: ToolLLMConfig = Field(
        default_factory=ToolLLMConfig,
        description="LLM configuration for self-healing selector enhancement",
    )
    chaos_agents: ToolLLMConfig = Field(
        default_factory=ToolLLMConfig,
        description="LLM configuration for chaos/generative testing",
    )

    def is_tool_enabled(self, tool: ToolName) -> bool:
        """Check if LLM is enabled for a specific tool."""
        if not self.enabled:
            return False
        tool_config = self.get_tool_config(tool)
        return tool_config.enabled

    def get_tool_config(self, tool: ToolName) -> ToolLLMConfig:
        """Get configuration for a specific tool."""
        match tool:
            case ToolName.TEST_BUILDER:
                return self.test_builder
            case ToolName.STEP_TRANSFORMER:
                return self.step_transformer
            case ToolName.ASSERTIONS:
                return self.assertions
            case ToolName.SELF_HEALING:
                return self.self_healing
            case ToolName.CHAOS_AGENTS:
                return self.chaos_agents
            case _:
                raise ValueError(f"Unknown tool: {tool}")

    def get_effective_endpoint(self, tool: ToolName) -> LLMEndpointConfig:
        """Get the effective endpoint configuration for a tool."""
        tool_config = self.get_tool_config(tool)
        if tool_config.endpoint_override:
            return tool_config.endpoint_override
        return self.default_endpoint

    def get_effective_temperature(self, tool: ToolName) -> float:
        """Get the effective temperature for a tool."""
        tool_config = self.get_tool_config(tool)
        if tool_config.temperature_override is not None:
            return tool_config.temperature_override
        return self.get_effective_endpoint(tool).temperature

    def get_effective_max_tokens(self, tool: ToolName) -> int:
        """Get the effective max_tokens for a tool."""
        tool_config = self.get_tool_config(tool)
        if tool_config.max_tokens_override is not None:
            return tool_config.max_tokens_override
        return self.get_effective_endpoint(tool).max_tokens


class LLMSettings(BaseSettings):
    """
    Environment-based LLM settings.

    Loads configuration from environment variables with AUTOQA_LLM_ prefix.
    """

    model_config = SettingsConfigDict(
        env_prefix="AUTOQA_LLM_",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    # Global settings from environment
    enabled: bool = False
    base_url: str = "https://api.openai.com/v1"
    api_key: SecretStr = SecretStr("")
    model: str = "gpt-4o-mini"
    provider: LLMProvider = LLMProvider.OPENAI
    temperature: float = 0.3
    max_tokens: int = 2048
    timeout_ms: int = 30000

    # Azure-specific
    azure_deployment: str | None = None
    azure_api_version: str = "2024-02-15-preview"

    # Per-tool enable flags from environment
    test_builder_enabled: bool = False
    step_transformer_enabled: bool = False
    assertions_enabled: bool = False
    self_healing_enabled: bool = False
    chaos_agents_enabled: bool = False

    # Config file path
    config_file: Path | None = None

    @cached_property
    def config(self) -> LLMConfig:
        """Build complete LLMConfig from environment and optional file."""
        # Load from config file if specified
        file_config: dict[str, Any] = {}
        if self.config_file and self.config_file.exists():
            with self.config_file.open() as f:
                file_config = yaml.safe_load(f) or {}

        # Build endpoint config
        endpoint = LLMEndpointConfig(
            base_url=file_config.get("base_url", self.base_url),
            api_key=SecretStr(
                file_config.get("api_key", self.api_key.get_secret_value())
            ),
            model=file_config.get("model", self.model),
            provider=LLMProvider(file_config.get("provider", self.provider)),
            temperature=file_config.get("temperature", self.temperature),
            max_tokens=file_config.get("max_tokens", self.max_tokens),
            timeout_ms=file_config.get("timeout_ms", self.timeout_ms),
            azure_deployment=file_config.get("azure_deployment", self.azure_deployment),
            azure_api_version=file_config.get(
                "azure_api_version", self.azure_api_version
            ),
        )

        # Build tool configs
        def build_tool_config(
            tool_name: str, env_enabled: bool
        ) -> ToolLLMConfig:
            tool_file_config = file_config.get(tool_name, {})
            return ToolLLMConfig(
                enabled=tool_file_config.get("enabled", env_enabled),
                temperature_override=tool_file_config.get("temperature"),
                max_tokens_override=tool_file_config.get("max_tokens"),
                custom_system_prompt=tool_file_config.get("system_prompt"),
            )

        return LLMConfig(
            enabled=file_config.get("enabled", self.enabled),
            default_endpoint=endpoint,
            test_builder=build_tool_config(
                "test_builder", self.test_builder_enabled
            ),
            step_transformer=build_tool_config(
                "step_transformer", self.step_transformer_enabled
            ),
            assertions=build_tool_config("assertions", self.assertions_enabled),
            self_healing=build_tool_config(
                "self_healing", self.self_healing_enabled
            ),
            chaos_agents=build_tool_config(
                "chaos_agents", self.chaos_agents_enabled
            ),
        )


def load_llm_config(
    config_file: Path | str | None = None,
    env_override: bool = True,
) -> LLMConfig:
    """
    Load LLM configuration from file and/or environment.

    Priority (highest to lowest):
    1. Environment variables (if env_override=True)
    2. Config file
    3. Defaults

    Args:
        config_file: Optional path to YAML config file
        env_override: Whether environment variables override file config

    Returns:
        Complete LLMConfig instance
    """
    # First, try to load from file
    file_config: dict[str, Any] = {}
    if config_file:
        config_path = Path(config_file)
        if config_path.exists():
            with config_path.open() as f:
                file_config = yaml.safe_load(f) or {}

    # Check for standard config locations
    standard_paths = [
        Path(".autoqa/llm.yaml"),
        Path(".autoqa/llm.yml"),
        Path("autoqa-llm.yaml"),
        Path("autoqa-llm.yml"),
    ]
    if not file_config:
        for path in standard_paths:
            if path.exists():
                with path.open() as f:
                    file_config = yaml.safe_load(f) or {}
                break

    # Build settings from environment
    settings = LLMSettings(config_file=Path(config_file) if config_file else None)

    if env_override:
        # Environment takes precedence
        return settings.config

    # File config takes precedence over defaults
    if file_config:
        return _build_config_from_dict(file_config)

    return settings.config


def _build_config_from_dict(data: dict[str, Any]) -> LLMConfig:
    """Build LLMConfig from a dictionary (e.g., loaded from YAML)."""
    # Build endpoint
    endpoint_data = data.get("default_endpoint", {})
    if "api_key" in endpoint_data:
        endpoint_data["api_key"] = SecretStr(endpoint_data["api_key"])
    else:
        # Try to get from environment as fallback
        env_key = os.getenv("AUTOQA_LLM_API_KEY", "")
        endpoint_data["api_key"] = SecretStr(env_key)

    endpoint = LLMEndpointConfig(**endpoint_data)

    # Build tool configs
    def parse_tool_config(tool_data: dict[str, Any] | None) -> ToolLLMConfig:
        if not tool_data:
            return ToolLLMConfig()
        return ToolLLMConfig(**tool_data)

    return LLMConfig(
        enabled=data.get("enabled", False),
        default_endpoint=endpoint,
        test_builder=parse_tool_config(data.get("test_builder")),
        step_transformer=parse_tool_config(data.get("step_transformer")),
        assertions=parse_tool_config(data.get("assertions")),
        self_healing=parse_tool_config(data.get("self_healing")),
        chaos_agents=parse_tool_config(data.get("chaos_agents")),
    )
