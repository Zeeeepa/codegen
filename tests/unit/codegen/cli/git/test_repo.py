"""Tests for the git repository module."""

import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import git

from codegen.cli.git.repo import get_git_repo, get_repo_root


@pytest.fixture
def mock_git_repo():
    """Mocks a git.Repo object."""
    mock_repo = MagicMock(spec=git.Repo)
    mock_repo.working_dir = "/mock/repo"
    
    # Mock the remotes
    mock_origin = MagicMock()
    mock_origin.name = "origin"
    mock_origin.url = "https://github.com/test-owner/test-repo.git"
    
    mock_repo.remotes = [mock_origin]
    
    # Mock the config
    mock_config = MagicMock()
    mock_config.get_value.side_effect = lambda section, option: {
        ("user", "name"): "Test User",
        ("user", "email"): "test@example.com",
    }.get((section, option))
    
    mock_repo.config_reader.return_value = mock_config
    
    return mock_repo


def test_get_git_repo(mock_git_repo):
    """Test get_git_repo function."""
    # Mock git.Repo.init to return the mock repo
    with patch("git.Repo", return_value=mock_git_repo):
        # Call the function
        repo = get_git_repo(Path("/mock/repo"))
        
        # Check that the repo is the mock repo
        assert repo is mock_git_repo


def test_get_git_repo_not_a_repo():
    """Test get_git_repo function when the path is not a git repository."""
    # Mock git.Repo to raise a git.exc.InvalidGitRepositoryError
    with patch("git.Repo", side_effect=git.exc.InvalidGitRepositoryError):
        # Call the function
        repo = get_git_repo(Path("/not/a/repo"))
        
        # Check that the repo is None
        assert repo is None


def test_get_repo_root(mock_git_repo):
    """Test get_repo_root function."""
    # Mock get_git_repo to return the mock repo
    with patch("codegen.cli.git.repo.get_git_repo", return_value=mock_git_repo):
        # Call the function
        root = get_repo_root(Path("/mock/repo/subdir"))
        
        # Check that the root is the repo's working directory
        assert root == Path("/mock/repo")


def test_get_repo_root_not_a_repo():
    """Test get_repo_root function when the path is not in a git repository."""
    # Mock get_git_repo to return None
    with patch("codegen.cli.git.repo.get_git_repo", return_value=None):
        # Call the function
        root = get_repo_root(Path("/not/a/repo"))
        
        # Check that the root is None
        assert root is None

