"""
Eversale Local Proxy — Configuration Module

Centralized configuration for the local API gateway that routes
eversale LLM requests to configured backends.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class ProxyConfig:
    """Configuration for the eversale local proxy server."""

    # Server settings
    host: str = "127.0.0.1"
    port: int = 8765

    # Backend selection: "anthropic", "openai", "ollama", "custom"
    backend: str = "anthropic"

    # Backend URLs (resolved per backend type)
    anthropic_base_url: str = "https://api.anthropic.com"
    openai_base_url: str = "https://api.openai.com/v1"
    ollama_base_url: str = "http://127.0.0.1:11434"
    custom_base_url: str = ""

    # API Keys
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    # Default model mappings: eversale name → actual model name per backend
    model_map_anthropic: Dict[str, str] = field(default_factory=lambda: {
        "glm-5": "claude-sonnet-4-20250514",
        "glm-4.5v": "claude-sonnet-4-20250514",
        "gpt-4o": "claude-sonnet-4-20250514",
        "gpt-4o-mini": "claude-sonnet-4-20250514",
        "qwen3:8b": "claude-sonnet-4-20250514",
    })

    model_map_openai: Dict[str, str] = field(default_factory=lambda: {
        "glm-5": "gpt-4o",
        "glm-4.5v": "gpt-4o",
        "gpt-4o": "gpt-4o",
        "gpt-4o-mini": "gpt-4o-mini",
        "qwen3:8b": "gpt-4o-mini",
    })

    model_map_ollama: Dict[str, str] = field(default_factory=lambda: {
        "glm-5": "qwen2.5:7b",
        "glm-4.5v": "llava:7b",
        "gpt-4o": "qwen2.5:7b",
        "gpt-4o-mini": "qwen2.5:7b",
        "qwen3:8b": "qwen2.5:7b",
    })

    # Timeouts
    request_timeout: float = 120.0
    connect_timeout: float = 10.0

    # Logging
    log_requests: bool = True
    log_file: str = ""

    # Anthropic API version
    anthropic_api_version: str = "2023-06-01"

    @classmethod
    def from_env(cls) -> "ProxyConfig":
        """Load configuration from environment variables."""
        config = cls()

        # Server
        config.host = os.environ.get("EVERSALE_PROXY_HOST", config.host)
        config.port = int(os.environ.get("EVERSALE_PROXY_PORT", str(config.port)))

        # Backend selection
        config.backend = os.environ.get("LLM_BACKEND", "").lower().strip()
        if not config.backend:
            # Auto-detect from available keys
            if os.environ.get("ANTHROPIC_API_KEY"):
                config.backend = "anthropic"
            elif os.environ.get("OPENAI_API_KEY"):
                config.backend = "openai"
            elif os.environ.get("OLLAMA_HOST"):
                config.backend = "ollama"
            else:
                # Check if ANTHROPIC_BASE_URL points to z.ai (default from PR #213)
                base = os.environ.get("ANTHROPIC_BASE_URL", "")
                if "z.ai" in base:
                    config.backend = "custom"
                    config.custom_base_url = base
                else:
                    config.backend = "anthropic"

        # Backend URLs
        config.anthropic_base_url = os.environ.get(
            "ANTHROPIC_BASE_URL",
            os.environ.get("LLM_BACKEND_URL", config.anthropic_base_url),
        )
        config.openai_base_url = os.environ.get(
            "OPENAI_BASE_URL",
            os.environ.get("LLM_BACKEND_URL", config.openai_base_url),
        )
        config.ollama_base_url = os.environ.get(
            "OLLAMA_HOST",
            os.environ.get("LLM_BACKEND_URL", config.ollama_base_url),
        )
        config.custom_base_url = os.environ.get(
            "LLM_BACKEND_URL",
            os.environ.get("ANTHROPIC_BASE_URL", config.custom_base_url),
        )

        # API Keys
        config.anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        config.openai_api_key = os.environ.get("OPENAI_API_KEY", "")

        # Timeouts
        config.request_timeout = float(
            os.environ.get("LLM_TIMEOUT", str(config.request_timeout))
        )

        # Logging
        config.log_requests = os.environ.get(
            "EVERSALE_PROXY_LOG", "1"
        ).lower() in ("1", "true", "yes")

        eversale_home = os.environ.get(
            "EVERSALE_HOME", os.path.join(os.path.expanduser("~"), ".eversale")
        )
        config.log_file = os.environ.get(
            "EVERSALE_PROXY_LOG_FILE",
            os.path.join(eversale_home, "logs", "proxy.log"),
        )

        return config

    def get_backend_url(self) -> str:
        """Get the active backend URL."""
        if self.backend == "anthropic":
            return self.anthropic_base_url.rstrip("/")
        elif self.backend == "openai":
            return self.openai_base_url.rstrip("/")
        elif self.backend == "ollama":
            return self.ollama_base_url.rstrip("/")
        elif self.backend == "custom":
            return self.custom_base_url.rstrip("/")
        return self.anthropic_base_url.rstrip("/")

    def get_api_key(self) -> str:
        """Get the active API key for the backend."""
        if self.backend == "anthropic":
            return self.anthropic_api_key
        elif self.backend == "openai":
            return self.openai_api_key
        elif self.backend == "custom":
            # Custom backends may use either key
            return self.anthropic_api_key or self.openai_api_key
        return ""

    def map_model(self, eversale_model: str) -> str:
        """Map an eversale model name to the actual backend model name."""
        if self.backend == "anthropic":
            return self.model_map_anthropic.get(eversale_model, eversale_model)
        elif self.backend == "openai":
            return self.model_map_openai.get(eversale_model, eversale_model)
        elif self.backend == "ollama":
            return self.model_map_ollama.get(eversale_model, eversale_model)
        # Custom backend: pass through model name as-is
        return eversale_model

