import re

# Define the pattern
pattern = r"def\s+(\w+)\([^)]*\):\s*(?!\s*(?:\"\"\"|'''))"

# Test code with functions with and without docstrings
test_code = """
def function_without_docstring():
    pass

def function_with_docstring():
    \"\"\"This is a docstring\"\"\"
    pass

def function_with_single_quotes():
    '''This is a docstring with single quotes'''
    pass
"""

# Test the pattern
compiled = re.compile(pattern)
matches = compiled.findall(test_code)
print(f"Matches: {matches}")
