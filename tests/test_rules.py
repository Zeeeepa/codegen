"""
Tests for the PR static analysis rules.
"""

import ast
from typing import Dict, List

import pytest

from pr_static_analysis.rules.code_integrity import CodeSmellRule, SyntaxErrorRule
from pr_static_analysis.rules.implementation_validation import MissingEdgeCaseRule
from pr_static_analysis.rules.parameter_validation import UnusedParameterRule


class TestSyntaxErrorRule:
    """Tests for the SyntaxErrorRule."""
    
    def test_valid_syntax(self):
        """Test that valid syntax doesn't trigger the rule."""
        rule = SyntaxErrorRule()
        context = {
            "files": [
                {
                    "filepath": "test.py",
                    "content": "def foo():\n    return 42\n",
                }
            ]
        }
        results = rule.analyze(context)
        assert len(results) == 0
    
    def test_invalid_syntax(self):
        """Test that invalid syntax triggers the rule."""
        rule = SyntaxErrorRule()
        context = {
            "files": [
                {
                    "filepath": "test.py",
                    "content": "def foo()\n    return 42\n",
                }
            ]
        }
        results = rule.analyze(context)
        assert len(results) == 1
        assert results[0].rule_id == "syntax-error"
        assert results[0].filepath == "test.py"
        assert results[0].line == 1


class TestCodeSmellRule:
    """Tests for the CodeSmellRule."""
    
    def test_long_function(self):
        """Test that long functions trigger the rule."""
        rule = CodeSmellRule({"max_function_length": 3})
        context = {
            "files": [
                {
                    "filepath": "test.py",
                    "content": "def foo():\n    a = 1\n    b = 2\n    c = 3\n    d = 4\n    return a + b + c + d\n",
                }
            ]
        }
        results = rule.analyze(context)
        assert any(
            result.rule_id == "code-smell" and "too long" in result.message
            for result in results
        )
    
    def test_magic_numbers(self):
        """Test that magic numbers trigger the rule."""
        rule = CodeSmellRule({"ignore_magic_numbers": [0, 1]})
        context = {
            "files": [
                {
                    "filepath": "test.py",
                    "content": "def foo():\n    return 42\n",
                }
            ]
        }
        results = rule.analyze(context)
        assert any(
            result.rule_id == "code-smell" and "Magic number: 42" in result.message
            for result in results
        )


class TestUnusedParameterRule:
    """Tests for the UnusedParameterRule."""
    
    def test_used_parameter(self):
        """Test that used parameters don't trigger the rule."""
        rule = UnusedParameterRule()
        context = {
            "files": [
                {
                    "filepath": "test.py",
                    "content": "def foo(x):\n    return x\n",
                }
            ]
        }
        results = rule.analyze(context)
        assert len(results) == 0
    
    def test_unused_parameter(self):
        """Test that unused parameters trigger the rule."""
        rule = UnusedParameterRule()
        context = {
            "files": [
                {
                    "filepath": "test.py",
                    "content": "def foo(x, y):\n    return x\n",
                }
            ]
        }
        results = rule.analyze(context)
        assert len(results) == 1
        assert results[0].rule_id == "unused-parameter"
        assert "y" in results[0].message


class TestMissingEdgeCaseRule:
    """Tests for the MissingEdgeCaseRule."""
    
    def test_division_by_zero(self):
        """Test that potential division by zero triggers the rule."""
        rule = MissingEdgeCaseRule()
        context = {
            "files": [
                {
                    "filepath": "test.py",
                    "content": "def foo(x, y):\n    return x / y\n",
                }
            ]
        }
        results = rule.analyze(context)
        assert any(
            result.rule_id == "missing-edge-case" and "division by zero" in result.message.lower()
            for result in results
        )

