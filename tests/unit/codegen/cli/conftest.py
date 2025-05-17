import os
import shutil
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from codegen.cli.auth.session import CodegenSession
from codegen.cli.auth.token_manager import get_current_token
from codegen.cli.api.client import RestAPI


@pytest.fixture
def runner():
    """Returns a Click CLI test runner."""
    return CliRunner(mix_stderr=False)


@pytest.fixture
def mock_repo_path(tmp_path):
    """Creates a temporary directory for a mock repository."""
    repo_path = tmp_path / "mock_repo"
    repo_path.mkdir()
    return repo_path


@pytest.fixture
def mock_git_repo(mock_repo_path):
    """Sets up a mock git repository."""
    os.chdir(mock_repo_path)
    subprocess.run(["git", "init", str(mock_repo_path)], check=True)
    subprocess.run(["git", "config", "--local", "user.email", "test@example.com"], check=True)
    subprocess.run(["git", "config", "--local", "user.name", "Test User"], check=True)
    subprocess.run(["git", "commit", "--allow-empty", "-m", "Initial commit"], check=True)
    subprocess.run(["git", "remote", "add", "origin", "https://github.com/test/test.git"], check=True)
    yield mock_repo_path
    try:
        shutil.rmtree(mock_repo_path)
    except FileNotFoundError:
        pass


@pytest.fixture
def mock_token():
    """Provides a mock GitHub token."""
    return "mock-github-token"


@pytest.fixture
def mock_api_token():
    """Provides a mock API token."""
    return "mock-api-token"


@pytest.fixture
def mock_session(mock_git_repo, mock_token):
    """Creates a mock CodegenSession."""
    with patch.object(CodegenSession, "_validate", return_value=None), \
         patch.object(CodegenSession, "_initialize", return_value=None):
        session = MagicMock(spec=CodegenSession)
        session.repo_path = mock_git_repo
        session.config.secrets.github_token = mock_token
        session.config.repository.full_name = "test/test"
        session.config.repository.owner = "test"
        session.config.repository.repo_name = "test"
        session.config.repository.language = "PYTHON"
        session.from_active_session.return_value = session
        
        with patch.object(CodegenSession, "from_active_session", return_value=session):
            yield session


@pytest.fixture
def mock_rest_api(mock_api_token):
    """Creates a mock RestAPI client."""
    with patch.object(RestAPI, "_make_request", return_value=None):
        api = MagicMock(spec=RestAPI)
        api.auth_token = mock_api_token
        yield api


@pytest.fixture
def mock_get_current_token(mock_api_token):
    """Mocks the get_current_token function to return a mock token."""
    with patch("codegen.cli.auth.token_manager.get_current_token", return_value=mock_api_token):
        yield mock_api_token

