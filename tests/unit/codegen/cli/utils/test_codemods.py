import os
from pathlib import Path
from unittest.mock import patch, mock_open

import pytest

from codegen.cli.utils.codemods import Codemod, get_codemod_path


@pytest.fixture
def mock_codemod_file():
    """Creates a mock codemod file content."""
    return """
def test_codemod():
    \"\"\"
    This is a test codemod.
    
    It does something useful.
    \"\"\"
    return "Hello, world!"
"""


@pytest.fixture
def mock_codemod_path(tmp_path):
    """Creates a mock codemod path."""
    codemod_path = tmp_path / ".codegen" / "codemods" / "test_codemod.py"
    codemod_path.parent.mkdir(parents=True)
    return codemod_path


def test_get_codemod_path(mock_codemod_path):
    """Test get_codemod_path function."""
    with patch("codegen.cli.utils.codemods.CodegenSession") as mock_session_class:
        # Set up the mock session
        mock_session = mock_session_class.from_active_session.return_value
        mock_session.codegen_dir = mock_codemod_path.parent.parent
        
        # Call the function
        path = get_codemod_path("test_codemod")
        
        # Check the result
        assert path == mock_codemod_path.parent / "test_codemod.py"


def test_codemod_init(mock_codemod_path, mock_codemod_file):
    """Test Codemod initialization."""
    # Write the mock codemod file
    mock_codemod_path.write_text(mock_codemod_file)
    
    # Create a Codemod instance
    codemod = Codemod(mock_codemod_path)
    
    # Check the properties
    assert codemod.name == "test_codemod"
    assert codemod.path == mock_codemod_path
    assert codemod.source == mock_codemod_file.strip()
    assert codemod.description == "This is a test codemod.\n\nIt does something useful."


def test_codemod_get_current_source(mock_codemod_path, mock_codemod_file):
    """Test Codemod.get_current_source method."""
    # Write the mock codemod file
    mock_codemod_path.write_text(mock_codemod_file)
    
    # Create a Codemod instance
    codemod = Codemod(mock_codemod_path)
    
    # Get the current source
    source = codemod.get_current_source()
    
    # Check the result
    assert source == mock_codemod_file.strip()


def test_codemod_save(mock_codemod_path):
    """Test Codemod.save method."""
    # Create a Codemod instance
    codemod = Codemod(mock_codemod_path)
    
    # Set the source
    new_source = "def new_codemod():\n    return 'New codemod!'"
    codemod.source = new_source
    
    # Save the codemod
    codemod.save()
    
    # Check that the file was written with the new source
    assert mock_codemod_path.read_text() == new_source


def test_codemod_str(mock_codemod_path, mock_codemod_file):
    """Test Codemod.__str__ method."""
    # Write the mock codemod file
    mock_codemod_path.write_text(mock_codemod_file)
    
    # Create a Codemod instance
    codemod = Codemod(mock_codemod_path)
    
    # Check the string representation
    assert str(codemod) == f"Codemod(name=test_codemod, path={mock_codemod_path})"

