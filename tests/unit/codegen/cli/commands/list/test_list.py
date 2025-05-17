import os
from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from codegen.cli.commands.list.main import list_command
from codegen.cli.utils.codemods import Codemod


@pytest.fixture
def mock_codemods_dir(tmp_path):
    """Creates a mock codemods directory."""
    codemods_dir = tmp_path / ".codegen" / "codemods"
    codemods_dir.mkdir(parents=True)
    return codemods_dir


@pytest.fixture
def mock_codemod_files(mock_codemods_dir):
    """Creates mock codemod files."""
    # Create some mock codemod files
    (mock_codemods_dir / "codemod1.py").write_text("def codemod1():\n    pass")
    (mock_codemods_dir / "codemod2.py").write_text("def codemod2():\n    pass")
    (mock_codemods_dir / "not_a_codemod.txt").write_text("This is not a codemod")
    return mock_codemods_dir


@pytest.fixture
def mock_session(mock_codemods_dir):
    """Mocks the CodegenSession."""
    with patch("codegen.cli.commands.list.main.CodegenSession") as mock_class:
        mock_instance = MagicMock()
        mock_instance.codegen_dir = mock_codemods_dir.parent
        mock_class.from_active_session.return_value = mock_instance
        yield mock_instance


def test_list_command(runner, mock_codemod_files, mock_session):
    """Test list command."""
    # Mock the Codemod class to return mock codemods
    with patch("codegen.cli.commands.list.main.Codemod") as mock_codemod_class:
        # Create mock codemod instances
        mock_codemod1 = MagicMock(spec=Codemod)
        mock_codemod1.name = "codemod1"
        mock_codemod1.description = "Codemod 1 description"
        
        mock_codemod2 = MagicMock(spec=Codemod)
        mock_codemod2.name = "codemod2"
        mock_codemod2.description = "Codemod 2 description"
        
        # Set up the mock to return different instances based on the path
        def mock_codemod_init(path, *args, **kwargs):
            if "codemod1.py" in str(path):
                return mock_codemod1
            elif "codemod2.py" in str(path):
                return mock_codemod2
            else:
                raise ValueError(f"Unexpected path: {path}")
        
        mock_codemod_class.side_effect = mock_codemod_init
        
        result = runner.invoke(list_command)
        
        # Check that the command executed successfully
        assert result.exit_code == 0
        
        # Check that both codemods are listed in the output
        assert "codemod1" in result.output
        assert "codemod2" in result.output
        
        # Check that the non-codemod file is not listed
        assert "not_a_codemod" not in result.output


def test_list_command_no_codemods(runner, mock_codemods_dir, mock_session):
    """Test list command when no codemods are available."""
    result = runner.invoke(list_command)
    
    # Check that the command executed successfully
    assert result.exit_code == 0
    
    # Check that the "No codemods found" message is in the output
    assert "No codemods found" in result.output


def test_list_command_no_session(runner):
    """Test list command when no session is available."""
    # Mock CodegenSession.from_active_session to return None
    with patch("codegen.cli.commands.list.main.CodegenSession.from_active_session", return_value=None):
        result = runner.invoke(list_command)
        
        # Check that the command failed
        assert result.exit_code != 0
        
        # Check that the error message is in the output
        assert "No active session found" in result.output

