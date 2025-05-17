"""Tests for error handling in the CLI module."""

import os
from unittest.mock import patch, MagicMock

import pytest
import click
from click.testing import CliRunner

from codegen.cli.errors import InvalidTokenError, ServerError
from codegen.cli.commands.login.main import login_command
from codegen.cli.commands.create.main import create_command
from codegen.cli.commands.deploy.main import deploy_command
from codegen.cli.commands.run.main import run_command
from codegen.cli.api.client import RestAPI


@pytest.fixture
def mock_rest_api_error():
    """Mocks the RestAPI client to raise an error."""
    with patch("codegen.cli.api.client.RestAPI") as mock_class:
        mock_instance = MagicMock(spec=RestAPI)
        mock_class.return_value = mock_instance
        yield mock_instance


def test_invalid_token_error_handling(runner, mock_rest_api_error, mock_get_current_token):
    """Test handling of InvalidTokenError."""
    # Set up the mock API client to raise an InvalidTokenError
    mock_rest_api_error.create.side_effect = InvalidTokenError("Invalid token")
    
    # Run the create command
    result = runner.invoke(create_command, ["test_codemod", "Test description"])
    
    # Check that the command failed
    assert result.exit_code != 0
    
    # Check that the error message is in the output
    assert "Invalid token" in result.output


def test_server_error_handling(runner, mock_rest_api_error, mock_get_current_token):
    """Test handling of ServerError."""
    # Set up the mock API client to raise a ServerError
    mock_rest_api_error.create.side_effect = ServerError("Server error")
    
    # Run the create command
    result = runner.invoke(create_command, ["test_codemod", "Test description"])
    
    # Check that the command failed
    assert result.exit_code != 0
    
    # Check that the error message is in the output
    assert "Server error" in result.output


def test_click_abort_handling(runner):
    """Test handling of click.Abort."""
    # Mock get_current_token to return a token (already authenticated)
    with patch("codegen.cli.commands.login.main.get_current_token", return_value="existing-token"):
        # Run the login command - should raise click.Abort
        result = runner.invoke(login_command)
        
        # Check that the command failed
        assert result.exit_code != 0
        
        # Check that the error message is in the output
        assert "Already authenticated" in result.output


def test_file_not_found_handling(runner, mock_get_current_token):
    """Test handling of file not found errors."""
    # Mock os.path.exists to return False
    with patch("os.path.exists", return_value=False):
        # Run the deploy command with a non-existent file
        result = runner.invoke(deploy_command, ["non_existent_codemod"])
        
        # Check that the command failed
        assert result.exit_code != 0
        
        # Check that the error message is in the output
        assert "Codemod file not found" in result.output


def test_invalid_argument_handling(runner, mock_run_local, mock_run_cloud, mock_run_daemon):
    """Test handling of invalid arguments."""
    # Run the run command with invalid arguments
    result = runner.invoke(run_command, ["--local", "--cloud", "test_codemod"])
    
    # Check that the command failed
    assert result.exit_code != 0
    
    # Check that the error message is in the output
    assert "Cannot specify multiple run modes" in result.output


def test_missing_argument_handling(runner, mock_get_current_token):
    """Test handling of missing required arguments."""
    # Run the create command without required arguments
    result = runner.invoke(create_command, [])
    
    # Check that the command failed
    assert result.exit_code != 0
    
    # Check that the error message is in the output
    assert "Missing argument" in result.output

