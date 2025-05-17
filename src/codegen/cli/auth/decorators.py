import functools
import logging
from collections.abc import Callable

import click
import rich

from codegen.cli.auth.login import login_routine
from codegen.cli.auth.session import CodegenSession
from codegen.cli.auth.token_manager import TokenManager, get_current_token
from codegen.cli.errors import AuthError
from codegen.cli.rich.pretty_print import pretty_print_error

logger = logging.getLogger(__name__)


def requires_auth(f: Callable) -> Callable:
    """Decorator that ensures a user is authenticated and injects a CodegenSession.
    
    This decorator performs the following checks:
    1. Verifies that there is an active session
    2. Checks for a valid authentication token
    3. If no token exists, initiates the login flow
    4. If the token is invalid, initiates the login flow
    
    Args:
        f: The function to decorate
        
    Returns:
        The decorated function
    """

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        session = CodegenSession.from_active_session()

        # Check for valid session
        if session is None:
            logger.error("No active session found")
            pretty_print_error("There is currently no active session.\nPlease run 'codegen init' to initialize the project.")
            raise click.Abort()

        # Check for valid token
        token = get_current_token()
        if token is None:
            logger.info("No authentication token found, initiating login flow")
            rich.print("[yellow]Not authenticated. Let's get you logged in first![/yellow]\n")
            try:
                login_routine()
            except Exception as e:
                logger.error(f"Login failed: {e}")
                pretty_print_error(f"Authentication failed: {e}")
                raise click.Abort()
        else:
            try:
                logger.debug("Validating existing authentication token")
                token_manager = TokenManager()
                token_manager.authenticate_token(token)
            except AuthError as e:
                logger.warning(f"Authentication token is invalid or expired: {e}")
                rich.print("[yellow]Authentication token is invalid or expired. Let's get you logged in again![/yellow]\n")
                try:
                    login_routine()
                except Exception as login_error:
                    logger.error(f"Login failed: {login_error}")
                    pretty_print_error(f"Authentication failed: {login_error}")
                    raise click.Abort()

        return f(*args, session=session, **kwargs)

    return wrapper
