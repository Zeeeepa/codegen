import pytest
from click.testing import CliRunner
from unittest.mock import patch

from codegen.cli.commands.login.main import login_command


@pytest.fixture
def mock_login_routine():
    """Mocks the login_routine function."""
    with patch("codegen.cli.commands.login.main.login_routine") as mock:
        yield mock


def test_login_command_with_token(runner, mock_login_routine, mock_get_current_token):
    """Test login command with a token."""
    # Mock get_current_token to return None (not authenticated)
    with patch("codegen.cli.commands.login.main.get_current_token", return_value=None):
        result = runner.invoke(login_command, ["--token", "test-token"])
        
        # Check that the command executed successfully
        assert result.exit_code == 0
        
        # Check that login_routine was called with the correct token
        mock_login_routine.assert_called_once_with("test-token")


def test_login_command_without_token(runner, mock_login_routine, mock_get_current_token):
    """Test login command without a token."""
    # Mock get_current_token to return None (not authenticated)
    with patch("codegen.cli.commands.login.main.get_current_token", return_value=None):
        result = runner.invoke(login_command)
        
        # Check that the command executed successfully
        assert result.exit_code == 0
        
        # Check that login_routine was called with None
        mock_login_routine.assert_called_once_with(None)


def test_login_command_already_authenticated(runner, mock_login_routine):
    """Test login command when already authenticated."""
    # Mock get_current_token to return a token (already authenticated)
    with patch("codegen.cli.commands.login.main.get_current_token", return_value="existing-token"):
        result = runner.invoke(login_command)
        
        # Check that the command failed with the expected error
        assert result.exit_code != 0
        assert "Already authenticated" in result.output
        
        # Check that login_routine was not called
        mock_login_routine.assert_not_called()

