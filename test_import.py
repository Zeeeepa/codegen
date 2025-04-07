# This file simulates importing the CodeSuggestionEngine class

# First, let's create a file with the original pattern
cat > code_suggestions_original.py << 'INNER_EOF'
class CodeSuggestionEngine:
    def _load_python_patterns(self):
        return {
            "missing_docstring": {
                "pattern": r"def\s+(\w+)\([^)]*\):\s*(?!\s*[\"\\']{3})",
                "suggestion": "Add docstrings"
            }
        }
INNER_EOF

# Now, let's create a file with the fixed pattern
cat > code_suggestions_fixed.py << 'INNER_EOF'
class CodeSuggestionEngine:
    def _load_python_patterns(self):
        return {
            "missing_docstring": {
                "pattern": r"def\s+(\w+)\([^)]*\):\s*(?!\s*[\"\\']{\"3})",
                "suggestion": "Add docstrings"
            }
        }
INNER_EOF

# Try to import both files
echo "Trying to import original pattern file:"
python3 -c "import code_suggestions_original; print('Import successful')"

echo "Trying to import fixed pattern file:"
python3 -c "import code_suggestions_fixed; print('Import successful')"
