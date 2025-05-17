from pathlib import Path
from unittest.mock import MagicMock, patch

import click
import pytest
from github.MainClass import Github

from codegen.cli.auth.session import CodegenSession
from codegen.configs.constants import CODEGEN_DIR_NAME


@pytest.fixture
def mock_repo_path():
    return Path("/fake/repo/path")


@pytest.fixture
def mock_git_repo():
    mock_repo = MagicMock()
    mock_repo.working_dir = "/fake/repo/path"
    return mock_repo


@pytest.fixture
def mock_local_git():
    mock_git = MagicMock()
    mock_git.repo_path = Path("/fake/repo/path")
    mock_git.owner = "test-owner"
    mock_git.user_name = "Test User"
    mock_git.user_email = "test@example.com"
    mock_git.full_name = "test-owner/test-repo"
    mock_git.get_language.return_value = "python"
    return mock_git


class TestCodegenSession:
    def test_init_with_valid_repo(self, mock_repo_path, mock_git_repo, mock_local_git):
        """Test initializing a session with a valid repository."""
        with patch("codegen.cli.auth.session.get_git_repo", return_value=mock_git_repo):
            with patch("codegen.cli.auth.session.LocalGitRepo", return_value=mock_local_git):
                with patch("codegen.cli.auth.session.UserConfig") as mock_user_config_class:
                    mock_config = mock_user_config_class.return_value
                    mock_config.secrets.github_token = "test-token"

                    with patch("codegen.cli.auth.session.session_manager") as mock_session_manager:
                        mock_session_manager.get_session.return_value = None

                        with patch.object(CodegenSession, "_validate"):
                            with patch.object(CodegenSession, "_initialize"):
                                # Initialize a session
                                session = CodegenSession(mock_repo_path)

                                # Verify the session was set as active
                                mock_session_manager.set_active_session.assert_called_once_with(mock_repo_path)

                                # Verify the session properties
                                assert session.repo_path == mock_repo_path
                                assert session.local_git == mock_local_git
                                assert session.codegen_dir == mock_repo_path / CODEGEN_DIR_NAME
                                assert session.config == mock_config
                                assert session.existing is False

    def test_init_with_invalid_repo(self, mock_repo_path):
        """Test initializing a session with an invalid repository."""
        with patch("codegen.cli.auth.session.get_git_repo", return_value=None):
            with pytest.raises(click.Abort):
                CodegenSession(mock_repo_path)

    def test_from_active_session_with_no_active_session(self):
        """Test from_active_session when there is no active session."""
        with patch("codegen.cli.auth.session.session_manager") as mock_session_manager:
            mock_session_manager.get_active_session.return_value = None

            # Should return None
            assert CodegenSession.from_active_session() is None

    def test_from_active_session_with_active_session(self, mock_repo_path):
        """Test from_active_session when there is an active session."""
        with patch("codegen.cli.auth.session.session_manager") as mock_session_manager:
            mock_session_manager.get_active_session.return_value = mock_repo_path

            with patch.object(CodegenSession, "__init__", return_value=None) as mock_init:
                # Call from_active_session
                CodegenSession.from_active_session()

                # Verify __init__ was called with the active session path
                mock_init.assert_called_once_with(mock_repo_path)

    def test_initialize(self, mock_repo_path, mock_local_git):
        """Test the _initialize method."""
        with patch.object(CodegenSession, "__init__", return_value=None):
            with patch.object(CodegenSession, "_validate"):
                session = CodegenSession(None)
                session.local_git = mock_local_git
                session.repo_path = mock_repo_path
                session.codegen_dir = mock_repo_path / CODEGEN_DIR_NAME

                # Create a mock config
                mock_config = MagicMock()
                mock_config.repository.path = None
                mock_config.repository.owner = None
                mock_config.repository.user_name = None
                mock_config.repository.user_email = None
                mock_config.repository.language = None
                mock_config.secrets.github_token = "test-token"
                session.config = mock_config

                # Call _initialize
                session._initialize()

                # Verify the config was updated
                assert mock_config.repository.path == str(mock_local_git.repo_path)
                assert mock_config.repository.owner == mock_local_git.owner
                assert mock_config.repository.user_name == mock_local_git.user_name
                assert mock_config.repository.user_email == mock_local_git.user_email
                assert mock_config.repository.language == mock_local_git.get_language().upper()
                mock_config.save.assert_called_once()

    def test_validate_creates_codegen_dir(self, mock_repo_path):
        """Test that _validate creates the codegen directory if it doesn't exist."""
        with patch.object(CodegenSession, "__init__", return_value=None):
            session = CodegenSession(None)
            session.repo_path = mock_repo_path
            session.codegen_dir = mock_repo_path / CODEGEN_DIR_NAME

            # Create a mock config
            mock_config = MagicMock()
            mock_config.secrets.github_token = "test-token"
            session.config = mock_config

            # Create a mock local_git
            mock_local_git = MagicMock()
            mock_local_git.origin_remote = "origin"
            mock_local_git.full_name = "test-owner/test-repo"
            session.local_git = mock_local_git

            with patch("os.path.exists", return_value=False):
                with patch("pathlib.Path.mkdir") as mock_mkdir:
                    with patch.object(Github, "get_repo"):
                        # Call _validate
                        session._validate()

                        # Verify the directory was created
                        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_validate_warns_if_no_github_token(self, mock_repo_path):
        """Test that _validate warns if no GitHub token is provided."""
        with patch.object(CodegenSession, "__init__", return_value=None):
            session = CodegenSession(None)
            session.repo_path = mock_repo_path
            session.codegen_dir = mock_repo_path / CODEGEN_DIR_NAME

            # Create a mock config with no GitHub token
            mock_config = MagicMock()
            mock_config.secrets.github_token = None
            session.config = mock_config

            # Create a mock local_git
            mock_local_git = MagicMock()
            mock_local_git.origin_remote = "origin"
            session.local_git = mock_local_git

            with patch("os.path.exists", return_value=True):
                with patch("rich.print") as mock_print:
                    # Call _validate
                    session._validate()

                    # Verify a warning was printed
                    assert mock_print.call_count >= 1
                    assert any("GitHub token not found" in str(call) for call in mock_print.call_args_list)

    def test_validate_warns_if_no_remote(self, mock_repo_path):
        """Test that _validate warns if no remote is configured."""
        with patch.object(CodegenSession, "__init__", return_value=None):
            session = CodegenSession(None)
            session.repo_path = mock_repo_path
            session.codegen_dir = mock_repo_path / CODEGEN_DIR_NAME

            # Create a mock config
            mock_config = MagicMock()
            mock_config.secrets.github_token = "test-token"
            session.config = mock_config

            # Create a mock local_git with no remote
            mock_local_git = MagicMock()
            mock_local_git.origin_remote = None
            mock_local_git.full_name = "test-owner/test-repo"
            session.local_git = mock_local_git

            with patch("os.path.exists", return_value=True):
                with patch("rich.print") as mock_print:
                    with patch.object(Github, "get_repo"):
                        # Call _validate
                        session._validate()

                        # Verify a warning was printed
                        assert mock_print.call_count >= 1
                        assert any("No remote found" in str(call) for call in mock_print.call_args_list)

    def test_validate_raises_error_on_invalid_token(self, mock_repo_path):
        """Test that _validate raises an error if the GitHub token is invalid."""
        with patch.object(CodegenSession, "__init__", return_value=None):
            session = CodegenSession(None)
            session.repo_path = mock_repo_path
            session.codegen_dir = mock_repo_path / CODEGEN_DIR_NAME

            # Create a mock config
            mock_config = MagicMock()
            mock_config.secrets.github_token = "invalid-token"
            session.config = mock_config

            # Create a mock local_git
            mock_local_git = MagicMock()
            mock_local_git.origin_remote = "origin"
            mock_local_git.full_name = "test-owner/test-repo"
            session.local_git = mock_local_git

            with patch("os.path.exists", return_value=True):
                with patch.object(Github, "get_repo", side_effect=Exception("Bad credentials")):
                    with patch("rich.print"):
                        # Should raise a click.Abort
                        with pytest.raises(click.Abort):
                            session._validate()

    def test_str_representation(self):
        """Test the string representation of a CodegenSession."""
        with patch.object(CodegenSession, "__init__", return_value=None):
            session = CodegenSession(None)

            # Create a mock config
            mock_config = MagicMock()
            mock_config.repository.user_name = "Test User"
            mock_config.repository.repo_name = "test-repo"
            session.config = mock_config

            # Verify the string representation
            assert str(session) == "CodegenSession(user=Test User, repo=test-repo)"
