import re

# Test code with functions with and without docstrings
test_code = """
def function_without_docstring():
    pass

def function_with_docstring():
    \"\"\"This is a docstring\"\"\"
    pass
"""

# Original pattern
pattern1 = r"def\s+(\w+)\([^)]*\):\s*(?!\s*[\"\\']{3})"
compiled1 = re.compile(pattern1)
matches1 = compiled1.findall(test_code)
print(f"Original pattern matches: {matches1}")

# Fixed pattern
pattern2 = r"def\s+(\w+)\([^)]*\):\s*(?!\s*[\"\\']{\"3})"
compiled2 = re.compile(pattern2)
matches2 = compiled2.findall(test_code)
print(f"Fixed pattern matches: {matches2}")

# Let's try a third pattern with explicit escaping of curly braces
pattern3 = r"def\s+(\w+)\([^)]*\):\s*(?!\s*[\"\\']{\3})"
compiled3 = re.compile(pattern3)
matches3 = compiled3.findall(test_code)
print(f"Third pattern matches: {matches3}")
