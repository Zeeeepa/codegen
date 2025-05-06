"""
Tests for the PR static analysis rules.
"""

import unittest
from typing import Dict, List

from pr_static_analysis import PRStaticAnalyzer
from pr_static_analysis.rules import (
    CodeSmellRule,
    MissingEdgeCaseRule,
    SyntaxErrorRule,
    UnusedParameterRule,
)


class TestRules(unittest.TestCase):
    """Tests for the PR static analysis rules."""
    
    def setUp(self):
        """Set up the test case."""
        self.analyzer = PRStaticAnalyzer()
    
    def test_syntax_error_rule(self):
        """Test the syntax error rule."""
        # Create a file with a syntax error
        context = self._create_context(
            [
                {
                    "filepath": "syntax_error.py",
                    "content": "def foo(x, y)\n    return x + y",  # Missing colon
                }
            ]
        )
        
        # Analyze the context
        results = self.analyzer.analyze(context)
        
        # Check that the syntax error was detected
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0].rule_id, "syntax-error")
        self.assertEqual(results[0].filepath, "syntax_error.py")
    
    def test_code_smell_rule(self):
        """Test the code smell rule."""
        # Create a file with a code smell (long function)
        context = self._create_context(
            [
                {
                    "filepath": "code_smell.py",
                    "content": "def foo(x, y):\n" + "    print(x + y)\n" * 101,
                }
            ]
        )
        
        # Analyze the context
        results = self.analyzer.analyze(context)
        
        # Check that the code smell was detected
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0].rule_id, "code-smell")
        self.assertEqual(results[0].filepath, "code_smell.py")
    
    def test_unused_parameter_rule(self):
        """Test the unused parameter rule."""
        # Create a file with an unused parameter
        context = self._create_context(
            [
                {
                    "filepath": "unused_parameter.py",
                    "content": "def foo(x, y):\n    return x",  # y is unused
                }
            ]
        )
        
        # Analyze the context
        results = self.analyzer.analyze(context)
        
        # Check that the unused parameter was detected
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0].rule_id, "unused-parameter")
        self.assertEqual(results[0].filepath, "unused_parameter.py")
    
    def test_missing_edge_case_rule(self):
        """Test the missing edge case rule."""
        # Create a file with a missing edge case (division by zero)
        context = self._create_context(
            [
                {
                    "filepath": "missing_edge_case.py",
                    "content": "def foo(x, y):\n    return x / y",  # No check for y == 0
                }
            ]
        )
        
        # Analyze the context
        results = self.analyzer.analyze(context)
        
        # Check that the missing edge case was detected
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0].rule_id, "missing-edge-case")
        self.assertEqual(results[0].filepath, "missing_edge_case.py")
    
    def _create_context(self, files: List[Dict]) -> Dict:
        """
        Create a context for testing.
        
        Args:
            files: List of file information dictionaries
        
        Returns:
            A context dictionary
        """
        return {
            "files": files,
            "pr": {
                "title": "Test PR",
                "description": "This is a test PR.",
                "author": "test-user",
                "branch": "feature/test",
            },
            "config": {},
        }


if __name__ == "__main__":
    unittest.main()

