class CodeSuggestionEngine:
    def _load_python_patterns(self):
        return {
            "missing_docstring": {
                "pattern": r"def\s+(\w+)\([^)]*\):\s*(?!\s*[\"\\']{3})",
                "suggestion": "Add docstrings"
            }
        }
