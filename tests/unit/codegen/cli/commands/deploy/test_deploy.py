from unittest.mock import patch, MagicMock, mock_open

import pytest
from click.testing import CliRunner

from codegen.cli.commands.deploy.main import deploy_command
from codegen.cli.api.schemas import DeployResponse
from codegen.cli.utils.codemods import Codemod


@pytest.fixture
def mock_rest_api_client():
    """Mocks the RestAPI client."""
    with patch("codegen.cli.commands.deploy.main.RestAPI") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_get_current_token():
    """Mocks the get_current_token function."""
    with patch("codegen.cli.commands.deploy.main.get_current_token", return_value="mock-token"):
        yield


@pytest.fixture
def mock_codemod():
    """Creates a mock Codemod."""
    with patch("codegen.cli.commands.deploy.main.Codemod") as mock_class:
        mock_instance = MagicMock(spec=Codemod)
        mock_instance.name = "test_codemod"
        mock_instance.get_current_source.return_value = "def test_codemod():\n    pass"
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_deploy_response():
    """Creates a mock deploy response."""
    response = MagicMock(spec=DeployResponse)
    response.success = True
    response.message = "Deployment successful"
    return response


def test_deploy_command(runner, mock_rest_api_client, mock_get_current_token, mock_codemod, mock_deploy_response, mock_session):
    """Test deploy command."""
    # Set up the mock API client to return a mock response
    mock_rest_api_client.deploy.return_value = mock_deploy_response
    
    # Mock file operations
    with patch("os.path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data="def test_codemod():\n    pass")):
        
        result = runner.invoke(deploy_command, ["test_codemod"])
        
        # Check that the command executed successfully
        assert result.exit_code == 0
        
        # Check that the API client was created with the correct token
        mock_rest_api_client.deploy.assert_called_once()
        args, kwargs = mock_rest_api_client.deploy.call_args
        assert kwargs["codemod_name"] == "test_codemod"
        assert kwargs["codemod_source"] == "def test_codemod():\n    pass"
        
        # Check that the success message is in the output
        assert "Deployment successful" in result.output


def test_deploy_command_file_not_exists(runner, mock_rest_api_client, mock_get_current_token, mock_session):
    """Test deploy command when the file does not exist."""
    # Mock file operations to indicate the file does not exist
    with patch("os.path.exists", return_value=False):
        result = runner.invoke(deploy_command, ["test_codemod"])
        
        # Check that the command failed
        assert result.exit_code != 0
        
        # Check that the API client was not called
        mock_rest_api_client.deploy.assert_not_called()
        
        # Check that the error message is in the output
        assert "Codemod file not found" in result.output


def test_deploy_command_no_token(runner, mock_session):
    """Test deploy command when no token is available."""
    # Mock get_current_token to return None
    with patch("codegen.cli.commands.deploy.main.get_current_token", return_value=None):
        result = runner.invoke(deploy_command, ["test_codemod"])
        
        # Check that the command failed
        assert result.exit_code != 0
        
        # Check that the error message is in the output
        assert "Authentication required" in result.output


def test_deploy_command_with_message(runner, mock_rest_api_client, mock_get_current_token, mock_codemod, mock_deploy_response, mock_session):
    """Test deploy command with a custom message."""
    # Set up the mock API client to return a mock response
    mock_rest_api_client.deploy.return_value = mock_deploy_response
    
    # Mock file operations
    with patch("os.path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data="def test_codemod():\n    pass")):
        
        result = runner.invoke(deploy_command, ["test_codemod", "--message", "Custom deployment message"])
        
        # Check that the command executed successfully
        assert result.exit_code == 0
        
        # Check that the API client was created with the correct token and message
        mock_rest_api_client.deploy.assert_called_once()
        args, kwargs = mock_rest_api_client.deploy.call_args
        assert kwargs["codemod_name"] == "test_codemod"
        assert kwargs["message"] == "Custom deployment message"
        
        # Check that the success message is in the output
        assert "Deployment successful" in result.output


def test_deploy_command_with_lint_mode(runner, mock_rest_api_client, mock_get_current_token, mock_codemod, mock_deploy_response, mock_session):
    """Test deploy command with lint mode enabled."""
    # Set up the mock API client to return a mock response
    mock_rest_api_client.deploy.return_value = mock_deploy_response
    
    # Mock file operations
    with patch("os.path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data="def test_codemod():\n    pass")):
        
        result = runner.invoke(deploy_command, ["test_codemod", "--lint"])
        
        # Check that the command executed successfully
        assert result.exit_code == 0
        
        # Check that the API client was created with the correct token and lint_mode
        mock_rest_api_client.deploy.assert_called_once()
        args, kwargs = mock_rest_api_client.deploy.call_args
        assert kwargs["codemod_name"] == "test_codemod"
        assert kwargs["lint_mode"] is True
        
        # Check that the success message is in the output
        assert "Deployment successful" in result.output

