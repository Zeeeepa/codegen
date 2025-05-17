from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from codegen.cli.commands.expert.main import expert_command
from codegen.cli.api.schemas import AskExpertResponse


@pytest.fixture
def mock_rest_api_client():
    """Mocks the RestAPI client."""
    with patch("codegen.cli.commands.expert.main.RestAPI") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_get_current_token():
    """Mocks the get_current_token function."""
    with patch("codegen.cli.commands.expert.main.get_current_token", return_value="mock-token"):
        yield


@pytest.fixture
def mock_expert_response():
    """Creates a mock expert response."""
    response = MagicMock(spec=AskExpertResponse)
    response.answer = "This is the expert's answer."
    return response


def test_expert_command(runner, mock_rest_api_client, mock_get_current_token, mock_expert_response):
    """Test expert command."""
    # Set up the mock API client to return a mock response
    mock_rest_api_client.ask_expert.return_value = mock_expert_response
    
    result = runner.invoke(expert_command, ["How do I use codegen?"])
    
    # Check that the command executed successfully
    assert result.exit_code == 0
    
    # Check that the API client was created with the correct token
    mock_rest_api_client.ask_expert.assert_called_once_with(query="How do I use codegen?")
    
    # Check that the expert's answer is in the output
    assert "This is the expert's answer." in result.output


def test_expert_command_no_token(runner):
    """Test expert command when no token is available."""
    # Mock get_current_token to return None
    with patch("codegen.cli.commands.expert.main.get_current_token", return_value=None):
        result = runner.invoke(expert_command, ["How do I use codegen?"])
        
        # Check that the command failed
        assert result.exit_code != 0
        
        # Check that the error message is in the output
        assert "Authentication required" in result.output


def test_expert_command_no_query(runner, mock_get_current_token):
    """Test expert command when no query is provided."""
    result = runner.invoke(expert_command, [])
    
    # Check that the command failed
    assert result.exit_code != 0
    
    # Check that the error message is in the output
    assert "Missing argument" in result.output

