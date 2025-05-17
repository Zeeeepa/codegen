import pytest

from codegen.cli.codemod.convert import convert_to_ui, convert_from_ui


def test_convert_to_ui():
    """Test convert_to_ui function."""
    # Test with a simple function
    source = """
def test_function():
    return "Hello, world!"
"""
    result = convert_to_ui(source)
    
    # Check that the result is a string
    assert isinstance(result, str)
    
    # Check that the result contains the function
    assert "def test_function()" in result
    assert 'return "Hello, world!"' in result
    
    # Test with a more complex function
    source = """
def complex_function(arg1, arg2=None):
    \"\"\"
    This is a complex function.
    
    Args:
        arg1: The first argument
        arg2: The second argument (optional)
        
    Returns:
        The result of the function
    \"\"\"
    if arg2 is None:
        arg2 = "default"
    
    return f"{arg1} {arg2}"
"""
    result = convert_to_ui(source)
    
    # Check that the result is a string
    assert isinstance(result, str)
    
    # Check that the result contains the function
    assert "def complex_function(arg1, arg2=None):" in result
    assert "This is a complex function." in result
    assert "if arg2 is None:" in result
    assert 'arg2 = "default"' in result
    assert 'return f"{arg1} {arg2}"' in result


def test_convert_from_ui():
    """Test convert_from_ui function."""
    # Test with a simple function
    ui_source = """
def test_function():
    return "Hello, world!"
"""
    result = convert_from_ui(ui_source)
    
    # Check that the result is a string
    assert isinstance(result, str)
    
    # Check that the result contains the function
    assert "def test_function()" in result
    assert 'return "Hello, world!"' in result
    
    # Test with a more complex function
    ui_source = """
def complex_function(arg1, arg2=None):
    \"\"\"
    This is a complex function.
    
    Args:
        arg1: The first argument
        arg2: The second argument (optional)
        
    Returns:
        The result of the function
    \"\"\"
    if arg2 is None:
        arg2 = "default"
    
    return f"{arg1} {arg2}"
"""
    result = convert_from_ui(ui_source)
    
    # Check that the result is a string
    assert isinstance(result, str)
    
    # Check that the result contains the function
    assert "def complex_function(arg1, arg2=None):" in result
    assert "This is a complex function." in result
    assert "if arg2 is None:" in result
    assert 'arg2 = "default"' in result
    assert 'return f"{arg1} {arg2}"' in result


def test_convert_roundtrip():
    """Test that convert_to_ui and convert_from_ui are inverses."""
    # Test with a simple function
    source = """
def test_function():
    return "Hello, world!"
"""
    # Convert to UI and back
    ui_source = convert_to_ui(source)
    result = convert_from_ui(ui_source)
    
    # Check that the result is the same as the original
    assert result.strip() == source.strip()
    
    # Test with a more complex function
    source = """
def complex_function(arg1, arg2=None):
    \"\"\"
    This is a complex function.
    
    Args:
        arg1: The first argument
        arg2: The second argument (optional)
        
    Returns:
        The result of the function
    \"\"\"
    if arg2 is None:
        arg2 = "default"
    
    return f"{arg1} {arg2}"
"""
    # Convert to UI and back
    ui_source = convert_to_ui(source)
    result = convert_from_ui(ui_source)
    
    # Check that the result is the same as the original
    assert result.strip() == source.strip()

