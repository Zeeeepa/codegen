from codegen.configs.models.base_config import BaseConfig


class SecretsConfig(BaseConfig):
    """Configuration for various API secrets and tokens.

    Loads from environment variables.
    Falls back to .env file for missing values.
    """

    def __init__(self, prefix: str = "", *args, **kwargs) -> None:
        super().__init__(prefix=prefix, *args, **kwargs)

    github_token: str | None = None
    openai_api_key: str | None = None
    linear_api_key: str | None = None
    
    # Anthropic configuration for custom endpoints (e.g., GLM models)
    anthropic_api_key: str | None = None
    anthropic_base_url: str | None = None
    anthropic_model: str | None = None
