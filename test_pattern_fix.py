import re

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

# Original pattern
pattern1 = r"def\s+(\w+)\([^)]*\):\s*(?!\s*[\"\\']{3})"
compiled1 = re.compile(pattern1)
matches1 = compiled1.findall(test_code)
print(f"Original pattern matches: {matches1}")

# Fixed pattern from PR
pattern2 = r"def\s+(\w+)\([^)]*\):\s*(?!\s*[\"\\']{\"3})"
compiled2 = re.compile(pattern2)
matches2 = compiled2.findall(test_code)
print(f"Fixed pattern from PR matches: {matches2}")

# Better pattern
pattern3 = r"def\s+(\w+)\([^)]*\):\s*(?!\s*(?:\"\"\"|'''))"
compiled3 = re.compile(pattern3)
matches3 = compiled3.findall(test_code)
print(f"Better pattern matches: {matches3}")
