# Test with a very simple case
patterns = {
    "test": {
        "pattern": r"a{3}",  # Unescaped curly braces
        "value": "test"
    }
}
print("This works fine with unescaped curly braces as quantifiers")

# Now let's try with escaped curly braces
patterns = {
    "test": {
        "pattern": r"a\{3\}",  # Escaped curly braces
        "value": "test"
    }
}
print("This also works with escaped curly braces")

# Let's try with the specific pattern from the PR
try:
    patterns = {
        "test": {
            "pattern": r"def\s+(\w+)\([^)]*\):\s*(?!\s*[\"\\']{3})",
            "value": "test"
        }
    }
    print("Original pattern works")
except SyntaxError as e:
    print(f"Original pattern error: {e}")

try:
    patterns = {
        "test": {
            "pattern": r"def\s+(\w+)\([^)]*\):\s*(?!\s*[\"\\']{\"3})",
            "value": "test"
        }
    }
    print("Fixed pattern works")
except SyntaxError as e:
    print(f"Fixed pattern error: {e}")
