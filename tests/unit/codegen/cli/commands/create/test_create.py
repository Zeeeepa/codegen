from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from codegen.cli.commands.create.main import create_command
from codegen.cli.api.schemas import CreateResponse


@pytest.fixture
def mock_rest_api_client():
    """Mocks the RestAPI client."""
    with patch("codegen.cli.commands.create.main.RestAPI") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_get_current_token():
    """Mocks the get_current_token function."""
    with patch("codegen.cli.commands.create.main.get_current_token", return_value="mock-token"):
        yield


@pytest.fixture
def mock_create_response():
    """Creates a mock create response."""
    response = MagicMock(spec=CreateResponse)
    response.codemod = "def test_codemod():\n    pass"
    return response


def test_create_command(runner, mock_rest_api_client, mock_get_current_token, mock_create_response, mock_session):
    """Test create command."""
    # Set up the mock API client to return a mock response
    mock_rest_api_client.create.return_value = mock_create_response
    
    # Mock file operations
    with patch("builtins.open", mock_open()) as mock_file, \
         patch("os.path.exists", return_value=False):
        
        result = runner.invoke(create_command, ["test_codemod", "Test description"])
        
        # Check that the command executed successfully
        assert result.exit_code == 0
        
        # Check that the API client was created with the correct token
        mock_rest_api_client.create.assert_called_once_with(name="test_codemod", query="Test description")
        
        # Check that the file was written with the correct content
        mock_file.assert_called_once()
        mock_file().write.assert_called_once_with(mock_create_response.codemod)


def test_create_command_file_exists(runner, mock_rest_api_client, mock_get_current_token, mock_create_response, mock_session):
    """Test create command when the file already exists."""
    # Set up the mock API client to return a mock response
    mock_rest_api_client.create.return_value = mock_create_response
    
    # Mock file operations to indicate the file already exists
    with patch("os.path.exists", return_value=True), \
         patch("builtins.open", mock_open()) as mock_file:
        
        result = runner.invoke(create_command, ["test_codemod", "Test description"])
        
        # Check that the command failed
        assert result.exit_code != 0
        
        # Check that the API client was not called
        mock_rest_api_client.create.assert_not_called()
        
        # Check that the file was not written
        mock_file.assert_not_called()


def test_create_command_no_token(runner, mock_session):
    """Test create command when no token is available."""
    # Mock get_current_token to return None
    with patch("codegen.cli.commands.create.main.get_current_token", return_value=None):
        result = runner.invoke(create_command, ["test_codemod", "Test description"])
        
        # Check that the command failed
        assert result.exit_code != 0
        
        # Check that the error message is in the output
        assert "Authentication required" in result.output

