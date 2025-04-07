import re

# Original pattern (with unescaped curly braces)
try:
    pattern1 = r"def\s+(\w+)\([^)]*\):\s*(?!\s*[\"\\']{3})"
    re.compile(pattern1)
    print("Original pattern compiles successfully")
except Exception as e:
    print(f"Original pattern error: {e}")

# Fixed pattern (with escaped curly braces)
try:
    pattern2 = r"def\s+(\w+)\([^)]*\):\s*(?!\s*[\"\\']{\"3})"
    re.compile(pattern2)
    print("Fixed pattern compiles successfully")
except Exception as e:
    print(f"Fixed pattern error: {e}")

# Test with actual Python code parsing
import ast

code_with_original = """
def _load_python_patterns(self):
    \"\"\"Load patterns for Python code suggestions.\"\"\"
    return {
        "missing_docstring": {
            "pattern": r"def\\s+(\\w+)\\([^)]*\\):\\s*(?!\\s*[\\\"\\\\']{3})",
            "suggestion": "Add docstrings to improve code documentation and maintainability.",
        }
    }
"""

code_with_fixed = """
def _load_python_patterns(self):
    \"\"\"Load patterns for Python code suggestions.\"\"\"
    return {
        "missing_docstring": {
            "pattern": r"def\\s+(\\w+)\\([^)]*\\):\\s*(?!\\s*[\\\"\\\\']{\\\"3})",
            "suggestion": "Add docstrings to improve code documentation and maintainability.",
        }
    }
"""

try:
    ast.parse(code_with_original)
    print("Code with original pattern parses successfully")
except SyntaxError as e:
    print(f"Code with original pattern syntax error: {e}")

try:
    ast.parse(code_with_fixed)
    print("Code with fixed pattern parses successfully")
except SyntaxError as e:
    print(f"Code with fixed pattern syntax error: {e}")
