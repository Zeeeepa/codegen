import re

# In Python, curly braces {} have special meaning in f-strings and string formatting
# When used in regex patterns, they need to be escaped with backslashes if they're meant to be quantifiers

# Test with a simple example
try:
    # This should work - escaped curly braces for quantifier
    pattern1 = r"a{3}"
    re.compile(pattern1)
    print("Pattern with quantifier compiles successfully")
except Exception as e:
    print(f"Pattern with quantifier error: {e}")

# Now let's try with the actual patterns from the PR
try:
    # Original pattern from the PR
    pattern2 = r"def\s+(\w+)\([^)]*\):\s*(?!\s*[\"\\']{3})"
    compiled = re.compile(pattern2)
    print("Original PR pattern compiles successfully")
    
    # Test if it matches a function without docstring
    test_str = "def test_func():\n    pass"
    match = compiled.search(test_str)
    print(f"Matches function without docstring: {bool(match)}")
    
    # Test if it doesn't match a function with docstring
    test_str2 = 'def test_func():\n    """This is a docstring"""\n    pass'
    match2 = compiled.search(test_str2)
    print(f"Doesn't match function with docstring: {not bool(match2)}")
    
except Exception as e:
    print(f"Original PR pattern error: {e}")

try:
    # Fixed pattern from the PR
    pattern3 = r"def\s+(\w+)\([^)]*\):\s*(?!\s*[\"\\']{\"3})"
    compiled = re.compile(pattern3)
    print("Fixed PR pattern compiles successfully")
    
    # Test if it matches a function without docstring
    test_str = "def test_func():\n    pass"
    match = compiled.search(test_str)
    print(f"Matches function without docstring: {bool(match)}")
    
    # Test if it doesn't match a function with docstring
    test_str2 = 'def test_func():\n    """This is a docstring"""\n    pass'
    match2 = compiled.search(test_str2)
    print(f"Doesn't match function with docstring: {not bool(match2)}")
    
except Exception as e:
    print(f"Fixed PR pattern error: {e}")

# Let's try to understand the context in which this would fail
print("\nTesting in different contexts:")

# Test in a dictionary context (similar to how it's used in the actual code)
try:
    code = """
patterns = {
    "missing_docstring": {
        "pattern": r"def\s+(\w+)\([^)]*\):\s*(?!\s*[\"\\']{3})",
        "suggestion": "Add docstrings"
    }
}
"""
    exec(code)
    print("Dictionary with original pattern executes successfully")
except SyntaxError as e:
    print(f"Dictionary with original pattern syntax error: {e}")

try:
    code = """
patterns = {
    "missing_docstring": {
        "pattern": r"def\s+(\w+)\([^)]*\):\s*(?!\s*[\"\\']{\"3})",
        "suggestion": "Add docstrings"
    }
}
"""
    exec(code)
    print("Dictionary with fixed pattern executes successfully")
except SyntaxError as e:
    print(f"Dictionary with fixed pattern syntax error: {e}")
