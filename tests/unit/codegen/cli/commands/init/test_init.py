import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from codegen.cli.commands.init.main import init_command
from codegen.cli.auth.session import CodegenSession


@pytest.fixture
def mock_initialize_workspace():
    """Mocks the initialize_workspace function."""
    with patch("codegen.cli.commands.init.main.initialize_workspace") as mock:
        yield mock


@pytest.fixture
def mock_codegen_session():
    """Mocks the CodegenSession class."""
    with patch("codegen.cli.commands.init.main.CodegenSession") as mock:
        mock_session = MagicMock(spec=CodegenSession)
        mock.return_value = mock_session
        yield mock, mock_session


def test_init_command_with_defaults(runner, mock_git_repo, mock_initialize_workspace, mock_codegen_session):
    """Test init command with default arguments."""
    mock_class, mock_instance = mock_codegen_session
    
    # Change to the mock repo directory
    os.chdir(mock_git_repo)
    
    result = runner.invoke(init_command)
    
    # Check that the command executed successfully
    assert result.exit_code == 0
    
    # Check that CodegenSession was initialized with the correct arguments
    mock_class.assert_called_once_with(repo_path=Path(mock_git_repo), git_token=None)
    
    # Check that initialize_workspace was called
    mock_initialize_workspace.assert_called_once()


def test_init_command_with_token(runner, mock_git_repo, mock_initialize_workspace, mock_codegen_session):
    """Test init command with a token."""
    mock_class, mock_instance = mock_codegen_session
    
    # Change to the mock repo directory
    os.chdir(mock_git_repo)
    
    result = runner.invoke(init_command, ["--token", "test-token"])
    
    # Check that the command executed successfully
    assert result.exit_code == 0
    
    # Check that CodegenSession was initialized with the correct arguments
    mock_class.assert_called_once_with(repo_path=Path(mock_git_repo), git_token="test-token")
    
    # Check that initialize_workspace was called
    mock_initialize_workspace.assert_called_once()


def test_init_command_with_path(runner, mock_git_repo, mock_initialize_workspace, mock_codegen_session):
    """Test init command with a custom path."""
    mock_class, mock_instance = mock_codegen_session
    
    # Use a different directory than the current one
    custom_path = str(mock_git_repo / "subdir")
    os.makedirs(custom_path, exist_ok=True)
    
    result = runner.invoke(init_command, ["--path", custom_path])
    
    # Check that the command executed successfully
    assert result.exit_code == 0
    
    # Check that CodegenSession was initialized with the correct arguments
    mock_class.assert_called_once_with(repo_path=Path(custom_path), git_token=None)
    
    # Check that initialize_workspace was called
    mock_initialize_workspace.assert_called_once()

