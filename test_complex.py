# Create a more complex test case that might trigger the issue

# First with the original pattern
cat > complex_original.py << 'INNER_EOF'
import re

class CodeSuggestionEngine:
    def __init__(self):
        self.patterns = self._load_patterns()
        
    def _load_patterns(self):
        return {
            "python": {
                "missing_docstring": {
                    "pattern": r"def\s+(\w+)\([^)]*\):\s*(?!\s*[\"\\']{3})",
                    "suggestion": "Add docstrings"
                }
            }
        }
        
    def analyze(self, code):
        pattern = self.patterns["python"]["missing_docstring"]["pattern"]
        compiled = re.compile(pattern)
        matches = compiled.findall(code)
        return matches

# Test the engine
engine = CodeSuggestionEngine()
test_code = """
def function_without_docstring():
    pass

def function_with_docstring():
    \"\"\"This is a docstring\"\"\"
    pass
"""

matches = engine.analyze(test_code)
print(f"Functions without docstrings: {matches}")
INNER_EOF

# Now with the fixed pattern
cat > complex_fixed.py << 'INNER_EOF'
import re

class CodeSuggestionEngine:
    def __init__(self):
        self.patterns = self._load_patterns()
        
    def _load_patterns(self):
        return {
            "python": {
                "missing_docstring": {
                    "pattern": r"def\s+(\w+)\([^)]*\):\s*(?!\s*[\"\\']{\"3})",
                    "suggestion": "Add docstrings"
                }
            }
        }
        
    def analyze(self, code):
        pattern = self.patterns["python"]["missing_docstring"]["pattern"]
        compiled = re.compile(pattern)
        matches = compiled.findall(code)
        return matches

# Test the engine
engine = CodeSuggestionEngine()
test_code = """
def function_without_docstring():
    pass

def function_with_docstring():
    \"\"\"This is a docstring\"\"\"
    pass
"""

matches = engine.analyze(test_code)
print(f"Functions without docstrings: {matches}")
INNER_EOF

# Try running both files
echo "Running original pattern file:"
python3 complex_original.py

echo "Running fixed pattern file:"
python3 complex_fixed.py
