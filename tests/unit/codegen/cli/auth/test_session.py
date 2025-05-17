import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import rich
import click
from github.MainClass import Github

from codegen.cli.auth.session import CodegenSession
from codegen.configs.session_manager import session_manager


@pytest.fixture
def mock_git_repo_obj():
    """Mocks the git repo object returned by get_git_repo."""
    mock_repo = MagicMock()
    with patch("codegen.cli.auth.session.get_git_repo", return_value=mock_repo):
        yield mock_repo


@pytest.fixture
def mock_local_git_repo():
    """Mocks the LocalGitRepo class."""
    with patch("codegen.cli.auth.session.LocalGitRepo") as mock_class:
        mock_instance = MagicMock()
        mock_instance.repo_path = Path("/mock/repo")
        mock_instance.owner = "test-owner"
        mock_instance.user_name = "Test User"
        mock_instance.user_email = "test@example.com"
        mock_instance.get_language.return_value = "python"
        mock_instance.full_name = "test-owner/test-repo"
        mock_instance.origin_remote = "https://github.com/test-owner/test-repo.git"
        
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_user_config():
    """Mocks the UserConfig class."""
    with patch("codegen.cli.auth.session.UserConfig") as mock_class:
        mock_instance = MagicMock()
        mock_instance.secrets.github_token = "mock-token"
        mock_instance.repository.path = "/mock/repo"
        mock_instance.repository.owner = "test-owner"
        mock_instance.repository.user_name = "Test User"
        mock_instance.repository.user_email = "test@example.com"
        mock_instance.repository.language = "PYTHON"
        mock_instance.repository.full_name = "test-owner/test-repo"
        mock_instance.repository.repo_name = "test-repo"
        
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_session_manager():
    """Mocks the session_manager."""
    with patch("codegen.cli.auth.session.session_manager") as mock:
        mock.get_session.return_value = None
        mock.get_active_session.return_value = None
        yield mock


@pytest.fixture
def mock_github():
    """Mocks the Github class."""
    with patch("codegen.cli.auth.session.Github") as mock_class:
        mock_instance = MagicMock()
        mock_github_repo = MagicMock()
        mock_instance.get_repo.return_value = mock_github_repo
        
        mock_class.return_value = mock_instance
        yield mock_instance


def test_codegen_session_init(mock_git_repo_obj, mock_local_git_repo, mock_user_config, mock_session_manager, mock_github):
    """Test CodegenSession initialization."""
    # Set up the mock repo path
    repo_path = Path("/mock/repo")
    
    # Create a session
    session = CodegenSession(repo_path=repo_path, git_token="mock-token")
    
    # Check that the session was initialized correctly
    assert session.repo_path == repo_path
    assert session.local_git == mock_local_git_repo
    assert session.config == mock_user_config
    
    # Check that the session was validated and initialized
    mock_github.get_repo.assert_called_once_with(mock_local_git_repo.full_name)
    mock_session_manager.set_active_session.assert_called_once_with(repo_path)


def test_codegen_session_init_no_git_repo():
    """Test CodegenSession initialization with no git repo."""
    # Set up the mock repo path
    repo_path = Path("/mock/repo")
    
    # Mock get_git_repo to return None
    with patch("codegen.cli.auth.session.get_git_repo", return_value=None), \
         patch("rich.print") as mock_print, \
         pytest.raises(click.Abort):
        # Create a session - should raise click.Abort
        CodegenSession(repo_path=repo_path)
    
    # Check that the error message was printed
    mock_print.assert_called()


def test_codegen_session_init_no_token(mock_git_repo_obj, mock_local_git_repo, mock_user_config, mock_session_manager, mock_github):
    """Test CodegenSession initialization with no token."""
    # Set up the mock repo path
    repo_path = Path("/mock/repo")
    
    # Set the token to None
    mock_user_config.secrets.github_token = None
    
    # Mock rich.print to check for warnings
    with patch("rich.print") as mock_print:
        # Create a session
        session = CodegenSession(repo_path=repo_path)
    
    # Check that the warning was printed
    mock_print.assert_called()
    
    # Check that the session was initialized correctly
    assert session.repo_path == repo_path
    assert session.local_git == mock_local_git_repo
    assert session.config == mock_user_config


def test_codegen_session_init_no_remote(mock_git_repo_obj, mock_local_git_repo, mock_user_config, mock_session_manager, mock_github):
    """Test CodegenSession initialization with no remote."""
    # Set up the mock repo path
    repo_path = Path("/mock/repo")
    
    # Set the origin_remote to None
    mock_local_git_repo.origin_remote = None
    
    # Mock rich.print to check for warnings
    with patch("rich.print") as mock_print:
        # Create a session
        session = CodegenSession(repo_path=repo_path)
    
    # Check that the warning was printed
    mock_print.assert_called()
    
    # Check that the session was initialized correctly
    assert session.repo_path == repo_path
    assert session.local_git == mock_local_git_repo
    assert session.config == mock_user_config


def test_codegen_session_init_invalid_token(mock_git_repo_obj, mock_local_git_repo, mock_user_config, mock_session_manager):
    """Test CodegenSession initialization with an invalid token."""
    # Set up the mock repo path
    repo_path = Path("/mock/repo")
    
    # Mock Github to raise BadCredentialsException
    with patch("codegen.cli.auth.session.Github") as mock_github, \
         patch("rich.print") as mock_print, \
         pytest.raises(click.Abort):
        mock_github.return_value.get_repo.side_effect = Exception("Bad credentials")
        
        # Create a session - should raise click.Abort
        CodegenSession(repo_path=repo_path)
    
    # Check that the error message was printed
    mock_print.assert_called()


def test_codegen_session_from_active_session(mock_git_repo_obj, mock_local_git_repo, mock_user_config, mock_session_manager, mock_github):
    """Test CodegenSession.from_active_session."""
    # Set up the mock repo path
    repo_path = Path("/mock/repo")
    
    # Mock session_manager.get_active_session to return a path
    mock_session_manager.get_active_session.return_value = repo_path
    
    # Create a session using from_active_session
    with patch.object(CodegenSession, "__init__", return_value=None) as mock_init:
        session = CodegenSession.from_active_session()
    
    # Check that __init__ was called with the correct arguments
    mock_init.assert_called_once_with(repo_path)


def test_codegen_session_from_active_session_no_session(mock_session_manager):
    """Test CodegenSession.from_active_session with no active session."""
    # Mock session_manager.get_active_session to return None
    mock_session_manager.get_active_session.return_value = None
    
    # Create a session using from_active_session - should return None
    session = CodegenSession.from_active_session()
    
    # Check that the session is None
    assert session is None


def test_codegen_session_str(mock_git_repo_obj, mock_local_git_repo, mock_user_config, mock_session_manager, mock_github):
    """Test CodegenSession.__str__."""
    # Set up the mock repo path
    repo_path = Path("/mock/repo")
    
    # Create a session
    session = CodegenSession(repo_path=repo_path)
    
    # Check the string representation
    assert str(session) == "CodegenSession(user=Test User, repo=test-repo)"

