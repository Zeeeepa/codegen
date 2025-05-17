from unittest.mock import patch, MagicMock

import pytest
from rich.console import Console

from codegen.cli.rich.pretty_print import print_error, print_success, print_warning, print_info


@pytest.fixture
def mock_console():
    """Mocks the rich.console.Console."""
    with patch("codegen.cli.rich.pretty_print.Console") as mock_class:
        mock_instance = MagicMock(spec=Console)
        mock_class.return_value = mock_instance
        yield mock_instance


def test_print_error(mock_console):
    """Test print_error function."""
    print_error("Test error message")
    
    # Check that the console.print method was called with the correct arguments
    mock_console.print.assert_called_once()
    args, kwargs = mock_console.print.call_args
    assert "Test error message" in str(args)
    assert "bold red" in str(args) or "bold red" in str(kwargs)


def test_print_success(mock_console):
    """Test print_success function."""
    print_success("Test success message")
    
    # Check that the console.print method was called with the correct arguments
    mock_console.print.assert_called_once()
    args, kwargs = mock_console.print.call_args
    assert "Test success message" in str(args)
    assert "bold green" in str(args) or "bold green" in str(kwargs)


def test_print_warning(mock_console):
    """Test print_warning function."""
    print_warning("Test warning message")
    
    # Check that the console.print method was called with the correct arguments
    mock_console.print.assert_called_once()
    args, kwargs = mock_console.print.call_args
    assert "Test warning message" in str(args)
    assert "bold yellow" in str(args) or "bold yellow" in str(kwargs)


def test_print_info(mock_console):
    """Test print_info function."""
    print_info("Test info message")
    
    # Check that the console.print method was called with the correct arguments
    mock_console.print.assert_called_once()
    args, kwargs = mock_console.print.call_args
    assert "Test info message" in str(args)
    assert "bold blue" in str(args) or "bold blue" in str(kwargs)

