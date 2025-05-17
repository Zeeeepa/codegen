import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from codegen.cli.auth.token_manager import TokenManager, get_current_token
from codegen.cli.errors import AuthError


@pytest.fixture
def token_manager():
    """Create a token manager with a temporary token file."""
    with patch.object(TokenManager, "token_file", Path("/tmp/test_auth.json")):
        with patch.object(TokenManager, "config_dir", Path("/tmp")):
            manager = TokenManager()
            # Ensure the file doesn't exist at the start of each test
            if os.path.exists(manager.token_file):
                os.remove(manager.token_file)
            yield manager
            # Clean up after the test
            if os.path.exists(manager.token_file):
                os.remove(manager.token_file)


class TestTokenManager:
    def test_init_creates_config_dir(self, token_manager):
        """Test that the config directory is created if it doesn't exist."""
        with patch("os.path.exists", return_value=False):
            with patch("pathlib.Path.mkdir") as mock_mkdir:
                TokenManager()
                mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_save_token(self, token_manager):
        """Test that save_token writes the token to the token file."""
        test_token = "test_token_123"
        token_manager.save_token(test_token)

        # Verify the token was saved correctly
        assert os.path.exists(token_manager.token_file)
        with open(token_manager.token_file) as f:
            data = json.load(f)
            assert data["token"] == test_token

        # Verify file permissions (read/write for owner only)
        file_mode = os.stat(token_manager.token_file).st_mode & 0o777
        assert file_mode == 0o600

    def test_get_token_returns_none_if_no_file(self, token_manager):
        """Test that get_token returns None if the token file doesn't exist."""
        assert not os.path.exists(token_manager.token_file)
        assert token_manager.get_token() is None

    def test_get_token_returns_none_if_no_read_access(self, token_manager):
        """Test that get_token returns None if the config dir isn't readable."""
        with patch("os.access", return_value=False):
            assert token_manager.get_token() is None

    def test_get_token_returns_token(self, token_manager):
        """Test that get_token returns the token from the token file."""
        test_token = "test_token_456"
        token_manager.save_token(test_token)
        assert token_manager.get_token() == test_token

    def test_get_token_handles_json_error(self, token_manager):
        """Test that get_token handles JSON errors gracefully."""
        # Write invalid JSON to the token file
        with open(token_manager.token_file, "w") as f:
            f.write("not valid json")

        # Should return None and not raise an exception
        assert token_manager.get_token() is None

    def test_get_token_handles_missing_token_key(self, token_manager):
        """Test that get_token handles missing token key in the JSON."""
        # Write JSON without a token key
        with open(token_manager.token_file, "w") as f:
            json.dump({"not_token": "value"}, f)

        # Should return None
        assert token_manager.get_token() is None

    def test_clear_token(self, token_manager):
        """Test that clear_token removes the token file."""
        test_token = "test_token_789"
        token_manager.save_token(test_token)
        assert os.path.exists(token_manager.token_file)

        token_manager.clear_token()
        assert not os.path.exists(token_manager.token_file)

    def test_clear_token_no_file(self, token_manager):
        """Test that clear_token doesn't raise an error if the file doesn't exist."""
        assert not os.path.exists(token_manager.token_file)
        token_manager.clear_token()  # Should not raise an exception

    def test_authenticate_token_success(self, token_manager):
        """Test successful token authentication."""
        test_token = "valid_token"

        # Mock the RestAPI.identify method to return a valid identity
        mock_identity = MagicMock()
        mock_identity.auth_context.status = "active"

        with patch("codegen.cli.api.client.RestAPI") as mock_rest_api:
            mock_rest_api_instance = mock_rest_api.return_value
            mock_rest_api_instance.identify.return_value = mock_identity

            # Should not raise an exception
            token_manager.authenticate_token(test_token)

            # Verify the token was saved
            assert os.path.exists(token_manager.token_file)
            with open(token_manager.token_file) as f:
                data = json.load(f)
                assert data["token"] == test_token

    def test_authenticate_token_no_identity(self, token_manager):
        """Test token authentication with no identity returned."""
        test_token = "invalid_token"

        with patch("codegen.cli.api.client.RestAPI") as mock_rest_api:
            mock_rest_api_instance = mock_rest_api.return_value
            mock_rest_api_instance.identify.return_value = None

            # Should raise an AuthError
            with pytest.raises(AuthError, match="No identity found for session"):
                token_manager.authenticate_token(test_token)

    def test_authenticate_token_inactive(self, token_manager):
        """Test token authentication with inactive status."""
        test_token = "expired_token"

        # Mock the RestAPI.identify method to return an inactive identity
        mock_identity = MagicMock()
        mock_identity.auth_context.status = "inactive"

        with patch("codegen.cli.api.client.RestAPI") as mock_rest_api:
            mock_rest_api_instance = mock_rest_api.return_value
            mock_rest_api_instance.identify.return_value = mock_identity

            # Should raise an AuthError
            with pytest.raises(AuthError, match="Current session is not active"):
                token_manager.authenticate_token(test_token)


def test_get_current_token():
    """Test the get_current_token helper function."""
    test_token = "helper_test_token"

    with patch.object(TokenManager, "get_token", return_value=test_token):
        assert get_current_token() == test_token
