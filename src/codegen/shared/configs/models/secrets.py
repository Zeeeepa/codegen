from codegen.shared.configs.models.base_config import BaseConfig


class SecretsConfig(BaseConfig):
    """Configuration for various API secrets and tokens.

    Loads from environment variables with the SECRETS_ prefix.
    Falls back to .env file for missing values.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(prefix="", *args, **kwargs)

    # Model providers
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    langsmith_api_key: str | None = None

    # Github
    github_token: str | None = None

    # Slack
    slack_bot_token: str | None = None
    slack_signing_secret: str | None = None

    # Linear
    linear_api_key: str | None = None


DefaultSecrets = SecretsConfig()
