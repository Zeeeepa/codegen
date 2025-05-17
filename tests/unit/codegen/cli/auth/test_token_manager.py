import os
from pathlib import Path
from unittest.mock import patch, mock_open

import pytest

from codegen.cli.auth.token_manager import (
    get_token_path,
    get_current_token,
    save_token,
    clear_token,
)


@pytest.fixture
def mock_home_dir(tmp_path):
    """Creates a mock home directory."""
    home_dir = tmp_path / "home"
    home_dir.mkdir()
    return home_dir


@pytest.fixture
def mock_token_path(mock_home_dir):
    """Mocks the token path."""
    token_path = mock_home_dir / ".codegen" / "token"
    token_path.parent.mkdir(exist_ok=True)
    return token_path


def test_get_token_path(mock_home_dir):
    """Test get_token_path function."""
    with patch.dict(os.environ, {"HOME": str(mock_home_dir)}):
        token_path = get_token_path()
        expected_path = mock_home_dir / ".codegen" / "token"
        assert token_path == expected_path


def test_get_current_token_exists(mock_token_path):
    """Test get_current_token when token file exists."""
    # Create a token file
    mock_token_path.parent.mkdir(exist_ok=True)
    mock_token_path.write_text("mock-token")
    
    with patch("codegen.cli.auth.token_manager.get_token_path", return_value=mock_token_path):
        token = get_current_token()
        assert token == "mock-token"


def test_get_current_token_not_exists():
    """Test get_current_token when token file does not exist."""
    # Mock a non-existent token path
    non_existent_path = Path("/non/existent/path")
    
    with patch("codegen.cli.auth.token_manager.get_token_path", return_value=non_existent_path):
        token = get_current_token()
        assert token is None


def test_save_token(mock_token_path):
    """Test save_token function."""
    with patch("codegen.cli.auth.token_manager.get_token_path", return_value=mock_token_path):
        save_token("new-token")
        
        # Check that the token was saved
        assert mock_token_path.read_text() == "new-token"
        
        # Check that the directory was created
        assert mock_token_path.parent.exists()


def test_clear_token_exists(mock_token_path):
    """Test clear_token when token file exists."""
    # Create a token file
    mock_token_path.parent.mkdir(exist_ok=True)
    mock_token_path.write_text("mock-token")
    
    with patch("codegen.cli.auth.token_manager.get_token_path", return_value=mock_token_path):
        clear_token()
        
        # Check that the token file was removed
        assert not mock_token_path.exists()


def test_clear_token_not_exists():
    """Test clear_token when token file does not exist."""
    # Mock a non-existent token path
    non_existent_path = Path("/non/existent/path")
    
    with patch("codegen.cli.auth.token_manager.get_token_path", return_value=non_existent_path):
        # This should not raise an exception
        clear_token()

