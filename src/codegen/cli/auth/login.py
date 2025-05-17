import logging
import webbrowser

import rich
import rich_click as click

from codegen.cli.api.webapp_routes import USER_SECRETS_ROUTE
from codegen.cli.auth.token_manager import TokenManager
from codegen.cli.env.global_env import global_env
from codegen.cli.errors import AuthError

logger = logging.getLogger(__name__)


def login_routine(token: str | None = None) -> str:
    """Guide user through login flow and return authenticated session.

    This function handles the authentication flow for the Codegen CLI.
    It tries to authenticate using a token provided in the following order:
    1. Token provided as an argument
    2. Token from environment variable
    3. Token from browser flow

    Args:
        token: Codegen user access token associated with github account

    Returns:
        str: The authenticated token

    Raises:
        click.ClickException: If login fails
    """
    # Try environment variable first
    token = token or global_env.CODEGEN_USER_ACCESS_TOKEN

    # If no token provided, guide user through browser flow
    if not token:
        rich.print(f"Opening {USER_SECRETS_ROUTE} to get your authentication token...")
        try:
            webbrowser.open_new(USER_SECRETS_ROUTE)
        except Exception as e:
            logger.warning(f"Failed to open browser: {e}")
            rich.print("[yellow]Could not open browser automatically. Please visit:[/yellow]")
            rich.print(f"[blue]{USER_SECRETS_ROUTE}[/blue]")

        token = click.prompt("Please enter your authentication token from the browser", hide_input=False)

    if not token:
        msg = "Token must be provided via CODEGEN_USER_ACCESS_TOKEN environment variable or manual input"
        raise click.ClickException(msg)

    # Validate and store token
    try:
        token_manager = TokenManager()
        token_manager.authenticate_token(token)
        rich.print(f"[green]✓ Stored token to:[/green] {token_manager.token_file}")
        rich.print("[cyan]📊 Hey![/cyan] We collect anonymous usage data to improve your experience 🔒")
        rich.print("To opt out, set [green]telemetry_enabled = false[/green] in [cyan]~/.config/codegen-sh/analytics.json[/cyan] ✨")
        return token
    except AuthError as e:
        logger.exception(f"Authentication failed: {e}")
        msg = f"Error: {e!s}"
        raise click.ClickException(msg)
    except Exception as e:
        logger.exception(f"Unexpected error during login: {e}")
        msg = f"Unexpected error: {e!s}"
        raise click.ClickException(msg)
