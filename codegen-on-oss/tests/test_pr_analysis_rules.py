"""
Tests for PR static analysis rules.

This module contains tests for the PR static analysis rules.
"""

import unittest
from unittest.mock import Mock, patch

from codegen_on_oss.analysis.pr_analysis.rules import (
    BaseRule,
    AnalysisResult,
    SyntaxErrorRule,
    UndefinedReferenceRule,
    UnusedImportRule,
    CircularDependencyRule,
    ParameterTypeMismatchRule,
    MissingParameterRule,
    IncorrectParameterUsageRule,
    FeatureCompletenessRule,
    TestCoverageRule,
    PerformanceImplicationRule,
    SecurityConsiderationRule,
    ALL_RULES,
)


class TestBaseRule(unittest.TestCase):
    """Tests for the BaseRule class."""
    
    def test_base_rule_initialization(self):
        """Test that BaseRule can be initialized with the correct attributes."""
        # Create a concrete subclass of BaseRule for testing
        class ConcreteRule(BaseRule):
            def apply(self, context):
                return []
        
        rule = ConcreteRule("TEST001", "Test Rule", "A rule for testing")
        
        self.assertEqual(rule.rule_id, "TEST001")
        self.assertEqual(rule.name, "Test Rule")
        self.assertEqual(rule.description, "A rule for testing")
    
    def test_analysis_result_initialization(self):
        """Test that AnalysisResult can be initialized with the correct attributes."""
        result = AnalysisResult(
            rule_id="TEST001",
            severity="error",
            message="Test error message",
            file="test.py",
            line=10,
            column=5,
            details={"error_type": "test_error"}
        )
        
        self.assertEqual(result.rule_id, "TEST001")
        self.assertEqual(result.severity, "error")
        self.assertEqual(result.message, "Test error message")
        self.assertEqual(result.file, "test.py")
        self.assertEqual(result.line, 10)
        self.assertEqual(result.column, 5)
        self.assertEqual(result.details, {"error_type": "test_error"})
    
    def test_analysis_result_to_dict(self):
        """Test that AnalysisResult.to_dict() returns the correct dictionary."""
        result = AnalysisResult(
            rule_id="TEST001",
            severity="error",
            message="Test error message",
            file="test.py",
            line=10,
            column=5,
            details={"error_type": "test_error"}
        )
        
        expected_dict = {
            "rule_id": "TEST001",
            "severity": "error",
            "message": "Test error message",
            "file": "test.py",
            "line": 10,
            "column": 5,
            "details": {"error_type": "test_error"}
        }
        
        self.assertEqual(result.to_dict(), expected_dict)


class TestSyntaxErrorRule(unittest.TestCase):
    """Tests for the SyntaxErrorRule class."""
    
    def test_syntax_error_detection(self):
        """Test that SyntaxErrorRule detects syntax errors."""
        rule = SyntaxErrorRule()
        
        # Mock context
        context = Mock()
        context.get_file_changes.return_value = {"test.py": "added"}
        context.head_context.get_file_content.return_value = "def invalid_syntax("
        
        results = rule.apply(context)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].rule_id, "CI001")
        self.assertEqual(results[0].severity, "error")
        self.assertTrue("Syntax error" in results[0].message)
        self.assertEqual(results[0].file, "test.py")
    
    def test_valid_syntax(self):
        """Test that SyntaxErrorRule doesn't report errors for valid syntax."""
        rule = SyntaxErrorRule()
        
        # Mock context
        context = Mock()
        context.get_file_changes.return_value = {"test.py": "added"}
        context.head_context.get_file_content.return_value = "def valid_syntax(): pass"
        
        results = rule.apply(context)
        
        self.assertEqual(len(results), 0)


# Add more test classes for other rules...


if __name__ == "__main__":
    unittest.main()

