from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from codegen.cli.commands.config.main import config_command


@pytest.fixture
def mock_session():
    """Mocks the CodegenSession."""
    with patch("codegen.cli.commands.config.main.CodegenSession") as mock_class:
        mock_instance = MagicMock()
        mock_instance.config.repository.language = "PYTHON"
        mock_instance.config.repository.owner = "test-owner"
        mock_instance.config.repository.repo_name = "test-repo"
        mock_instance.config.repository.full_name = "test-owner/test-repo"
        mock_instance.config.repository.path = "/mock/repo"
        mock_instance.config.repository.user_name = "Test User"
        mock_instance.config.repository.user_email = "test@example.com"
        mock_class.from_active_session.return_value = mock_instance
        yield mock_instance


def test_config_command_get(runner, mock_session):
    """Test config command with get operation."""
    result = runner.invoke(config_command, ["get", "repository.language"])
    
    # Check that the command executed successfully
    assert result.exit_code == 0
    
    # Check that the config value is in the output
    assert "PYTHON" in result.output


def test_config_command_set(runner, mock_session):
    """Test config command with set operation."""
    result = runner.invoke(config_command, ["set", "repository.language", "JAVASCRIPT"])
    
    # Check that the command executed successfully
    assert result.exit_code == 0
    
    # Check that the config was updated
    assert mock_session.config.repository.language == "JAVASCRIPT"
    
    # Check that the config was saved
    mock_session.config.save.assert_called_once()
    
    # Check that the success message is in the output
    assert "Config updated" in result.output


def test_config_command_list(runner, mock_session):
    """Test config command with list operation."""
    result = runner.invoke(config_command, ["list"])
    
    # Check that the command executed successfully
    assert result.exit_code == 0
    
    # Check that all config values are in the output
    assert "repository.language" in result.output
    assert "repository.owner" in result.output
    assert "repository.repo_name" in result.output
    assert "repository.full_name" in result.output
    assert "repository.path" in result.output
    assert "repository.user_name" in result.output
    assert "repository.user_email" in result.output
    
    # Check that the config values are in the output
    assert "PYTHON" in result.output
    assert "test-owner" in result.output
    assert "test-repo" in result.output
    assert "test-owner/test-repo" in result.output
    assert "/mock/repo" in result.output
    assert "Test User" in result.output
    assert "test@example.com" in result.output


def test_config_command_no_session(runner):
    """Test config command when no session is available."""
    # Mock CodegenSession.from_active_session to return None
    with patch("codegen.cli.commands.config.main.CodegenSession.from_active_session", return_value=None):
        result = runner.invoke(config_command, ["list"])
        
        # Check that the command failed
        assert result.exit_code != 0
        
        # Check that the error message is in the output
        assert "No active session found" in result.output


def test_config_command_invalid_key(runner, mock_session):
    """Test config command with an invalid key."""
    result = runner.invoke(config_command, ["get", "invalid.key"])
    
    # Check that the command failed
    assert result.exit_code != 0
    
    # Check that the error message is in the output
    assert "Invalid config key" in result.output


def test_config_command_invalid_operation(runner, mock_session):
    """Test config command with an invalid operation."""
    result = runner.invoke(config_command, ["invalid", "repository.language"])
    
    # Check that the command failed
    assert result.exit_code != 0
    
    # Check that the error message is in the output
    assert "Invalid operation" in result.output

