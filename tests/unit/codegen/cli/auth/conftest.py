from unittest.mock import MagicMock, patch

import pytest

from codegen.cli.auth.token_manager import TokenManager


@pytest.fixture
def temp_token_file(tmp_path):
    """Create a temporary token file for testing."""
    token_file = tmp_path / "auth.json"
    return token_file


@pytest.fixture
def mock_token_manager(temp_token_file):
    """Create a token manager with a temporary token file."""
    with patch.object(TokenManager, "token_file", temp_token_file):
        with patch.object(TokenManager, "config_dir", temp_token_file.parent):
            manager = TokenManager()
            yield manager


@pytest.fixture
def valid_token():
    """Return a valid token for testing."""
    return "valid_test_token_123"


@pytest.fixture
def mock_rest_api():
    """Mock the RestAPI class."""
    with patch("codegen.cli.api.client.RestAPI") as mock_rest_api_class:
        mock_instance = mock_rest_api_class.return_value

        # Create a mock identity with active status
        mock_identity = MagicMock()
        mock_identity.auth_context.status = "active"
        mock_instance.identify.return_value = mock_identity

        yield mock_instance
