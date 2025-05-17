from unittest.mock import patch

import pytest
from rich.console import Console
from rich.syntax import Syntax

from codegen.cli.rich.codeblocks import format_code, format_command


def test_format_code():
    """Test format_code function."""
    # Test with Python code
    python_code = "def test_function():\n    pass"
    result = format_code(python_code, language="python")
    
    # Check that the result is a Syntax object
    assert isinstance(result, Syntax)
    assert result.code == python_code
    assert result.lexer_name == "python"
    
    # Test with JavaScript code
    js_code = "function testFunction() {\n    return true;\n}"
    result = format_code(js_code, language="javascript")
    
    # Check that the result is a Syntax object
    assert isinstance(result, Syntax)
    assert result.code == js_code
    assert result.lexer_name == "javascript"


def test_format_command():
    """Test format_command function."""
    command = "codegen init --token test-token"
    result = format_command(command)
    
    # Check that the result is a string
    assert isinstance(result, str)
    
    # The result should contain the command
    assert command in result

