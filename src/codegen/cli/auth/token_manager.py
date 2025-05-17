import json
import logging
import os
import stat
from pathlib import Path

from codegen.cli.api.client import RestAPI
from codegen.cli.auth.constants import AUTH_FILE, CONFIG_DIR
from codegen.cli.errors import AuthError

logger = logging.getLogger(__name__)


class TokenManager:
    """Manages authentication tokens for the Codegen CLI.

    This class handles storing, retrieving, validating, and clearing
    authentication tokens. It ensures tokens are stored securely and
    validates them before use.
    """

    def __init__(self):
        self.config_dir = CONFIG_DIR
        self.token_file = AUTH_FILE
        self._ensure_config_dir()

    def _ensure_config_dir(self):
        """Create config directory if it doesn't exist."""
        if not os.path.exists(self.config_dir):
            Path(self.config_dir).mkdir(parents=True, exist_ok=True)
            # Set directory permissions to be accessible only by the owner
            os.chmod(self.config_dir, stat.S_IRWXU)

    def authenticate_token(self, token: str) -> None:
        """Authenticate the token with the API.

        Args:
            token: The token to authenticate.

        Raises:
            AuthError: If the token is invalid or the session is not active.
        """
        try:
            identity = RestAPI(token).identify()
            if not identity:
                msg = "No identity found for session"
                raise AuthError(msg)
            if identity.auth_context.status != "active":
                msg = "Current session is not active. API Token may be invalid or may have expired."
                raise AuthError(msg)
            self.save_token(token)
        except Exception as e:
            if not isinstance(e, AuthError):
                logger.exception(f"Error authenticating token: {e}")
                msg = f"Failed to authenticate token: {e}"
                raise AuthError(msg) from e
            raise

    def save_token(self, token: str) -> None:
        """Save API token to disk securely.

        Args:
            token: The token to save.

        Raises:
            OSError: If there's an error saving the token.
        """
        try:
            # Create the parent directory if it doesn't exist
            self._ensure_config_dir()

            # Write the token to a temporary file first
            temp_file = f"{self.token_file}.tmp"
            with open(temp_file, "w") as f:
                json.dump({"token": token}, f)

            # Secure the temporary file permissions (read/write for owner only)
            os.chmod(temp_file, stat.S_IRUSR | stat.S_IWUSR)  # 0o600

            # Atomically replace the old file with the new one
            os.replace(temp_file, self.token_file)

        except Exception as e:
            logger.exception(f"Error saving token: {e}")
            msg = f"Error saving token: {e}"
            raise OSError(msg) from e

    def get_token(self) -> str | None:
        """Retrieve token from disk if it exists and is valid.

        Returns:
            The token if it exists and is valid, None otherwise.
        """
        try:
            if not os.access(self.config_dir, os.R_OK):
                logger.warning("Config directory is not readable")
                return None

            if not os.path.exists(self.token_file):
                return None

            # Check file permissions
            file_mode = os.stat(self.token_file).st_mode
            if file_mode & (stat.S_IRWXG | stat.S_IRWXO):  # Group or other has any permissions
                logger.warning("Token file has insecure permissions, fixing...")
                os.chmod(self.token_file, stat.S_IRUSR | stat.S_IWUSR)  # 0o600

            with open(self.token_file) as f:
                data = json.load(f)
                token = data.get("token")
                if not token:
                    logger.warning("Token file exists but contains no token")
                    return None

                return token

        except json.JSONDecodeError as e:
            logger.exception(f"Invalid JSON in token file: {e}")
            return None
        except (KeyError, OSError) as e:
            logger.exception(f"Error reading token: {e}")
            return None

    def clear_token(self) -> None:
        """Remove stored token securely."""
        try:
            if os.path.exists(self.token_file):
                # Overwrite the file with zeros before deleting
                with open(self.token_file, "wb") as f:
                    f.write(b"\0" * 100)  # Overwrite with null bytes
                os.remove(self.token_file)
        except OSError as e:
            logger.exception(f"Error clearing token: {e}")


def get_current_token() -> str | None:
    """Get the current authentication token if one exists.

    This is a helper function that creates a TokenManager instance and retrieves
    the stored token.

    Returns:
        Optional[str]: The current valid API token if one exists.
                      Returns None if no token exists.

    """
    token_manager = TokenManager()
    return token_manager.get_token()
