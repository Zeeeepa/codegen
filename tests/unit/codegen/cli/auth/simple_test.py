import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from codegen.cli.auth.token_manager import TokenManager


def test_token_manager_init():
    """Test that TokenManager initializes correctly."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        with patch("codegen.cli.auth.token_manager.CONFIG_DIR", temp_path):
            with patch("codegen.cli.auth.token_manager.AUTH_FILE", temp_path / "auth.json"):
                # Create a token manager
                token_manager = TokenManager()

                # Verify the config directory was created
                assert os.path.exists(temp_path)


def test_token_manager_save_and_get():
    """Test that TokenManager can save and retrieve a token."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        with patch("codegen.cli.auth.token_manager.CONFIG_DIR", temp_path):
            with patch("codegen.cli.auth.token_manager.AUTH_FILE", temp_path / "auth.json"):
                # Create a token manager
                token_manager = TokenManager()

                # Save a token
                test_token = "test_token_123"
                token_manager.save_token(test_token)

                # Verify the token was saved correctly
                assert os.path.exists(token_manager.token_file)
                with open(token_manager.token_file) as f:
                    data = json.load(f)
                    assert data["token"] == test_token

                # Retrieve the token
                retrieved_token = token_manager.get_token()
                assert retrieved_token == test_token
