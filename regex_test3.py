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

# Fixed pattern from PR
pattern2 = r"def\s+(\w+)\([^)]*\):\s*(?!\s*[\"\\']{\"3})"
compiled2 = re.compile(pattern2)
matches2 = compiled2.findall(test_code)
print(f"Fixed pattern from PR matches: {matches2}")

# Alternative fix with double curly braces
pattern3 = r"def\s+(\w+)\([^)]*\):\s*(?!\s*[\"\\']{3})"
compiled3 = re.compile(pattern3)
matches3 = compiled3.findall(test_code)
print(f"Alternative fix matches: {matches3}")

# Let's try a better fix that actually works correctly
pattern4 = r"def\s+(\w+)\([^)]*\):\s*(?!\s*[\"\\']{{3}})"
compiled4 = re.compile(pattern4)
matches4 = compiled4.findall(test_code)
print(f"Better fix matches: {matches4}")

# Let's try one more pattern with a different approach
pattern5 = r"def\s+(\w+)\([^)]*\):\s*(?!\s*(?:\"\"\"|\'\'\'))"
compiled5 = re.compile(pattern5)
matches5 = compiled5.findall(test_code)
print(f"Alternative approach matches: {matches5}")
