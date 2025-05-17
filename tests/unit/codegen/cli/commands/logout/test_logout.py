import pytest
from click.testing import CliRunner
from unittest.mock import patch

from codegen.cli.commands.logout.main import logout_command


@pytest.fixture
def mock_clear_token():
    """Mocks the clear_token function."""
    with patch("codegen.cli.commands.logout.main.clear_token") as mock:
        yield mock


def test_logout_command(runner, mock_clear_token):
    """Test logout command."""
    result = runner.invoke(logout_command)
    
    # Check that the command executed successfully
    assert result.exit_code == 0
    
    # Check that clear_token was called
    mock_clear_token.assert_called_once()
    
    # Check that the success message is in the output
    assert "Logged out successfully" in result.output

