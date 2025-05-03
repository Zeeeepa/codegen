"""
Tests for the error context analysis functionality.

This module contains unit tests for the ErrorContextAnalyzer and related classes.
"""

import ast
import unittest
from unittest.mock import MagicMock, patch

from codegen.sdk.core.codebase import Codebase
from codegen.sdk.core.file import SourceFile
from codegen.sdk.core.function import Function
from codegen.sdk.core.symbol import Symbol
from codegen_on_oss.analysis.error_context import (
    CodeError,
    ErrorContextAnalyzer,
    ErrorSeverity,
    ErrorType
)


class TestCodeError(unittest.TestCase):
    """Tests for the CodeError class."""
    
    def test_code_error_initialization(self):
        """Test that a CodeError can be initialized with all parameters."""
        error = CodeError(
            error_type=ErrorType.SYNTAX_ERROR,
            message="Invalid syntax",
            file_path="test.py",
            line_number=10,
            column=5,
            severity=ErrorSeverity.CRITICAL,
            symbol_name="test_function",
            context_lines={9: "def test_function():", 10: "    print('Hello world'"},
            suggested_fix="Fix the syntax error"
        )
        
        self.assertEqual(error.error_type, ErrorType.SYNTAX_ERROR)
        self.assertEqual(error.message, "Invalid syntax")
        self.assertEqual(error.file_path, "test.py")
        self.assertEqual(error.line_number, 10)
        self.assertEqual(error.column, 5)
        self.assertEqual(error.severity, ErrorSeverity.CRITICAL)
        self.assertEqual(error.symbol_name, "test_function")
        self.assertEqual(error.context_lines, {9: "def test_function():", 10: "    print('Hello world'"})
        self.assertEqual(error.suggested_fix, "Fix the syntax error")
    
    def test_code_error_to_dict(self):
        """Test that a CodeError can be converted to a dictionary."""
        error = CodeError(
            error_type=ErrorType.SYNTAX_ERROR,
            message="Invalid syntax",
            file_path="test.py",
            line_number=10,
            severity=ErrorSeverity.CRITICAL
        )
        
        error_dict = error.to_dict()
        
        self.assertEqual(error_dict["error_type"], ErrorType.SYNTAX_ERROR)
        self.assertEqual(error_dict["message"], "Invalid syntax")
        self.assertEqual(error_dict["file_path"], "test.py")
        self.assertEqual(error_dict["line_number"], 10)
        self.assertEqual(error_dict["severity"], ErrorSeverity.CRITICAL)
    
    def test_code_error_str(self):
        """Test the string representation of a CodeError."""
        error = CodeError(
            error_type=ErrorType.SYNTAX_ERROR,
            message="Invalid syntax",
            file_path="test.py",
            line_number=10,
            severity=ErrorSeverity.CRITICAL
        )
        
        error_str = str(error)
        
        self.assertIn(ErrorType.SYNTAX_ERROR.upper(), error_str)
        self.assertIn("Invalid syntax", error_str)
        self.assertIn("test.py:10", error_str)
        self.assertIn(ErrorSeverity.CRITICAL, error_str)


class TestErrorContextAnalyzer(unittest.TestCase):
    """Tests for the ErrorContextAnalyzer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock codebase
        self.codebase = MagicMock(spec=Codebase)
        
        # Create a mock file
        self.file = MagicMock(spec=SourceFile)
        self.file.name = "test.py"
        self.file.source = "def test_function():\n    x = 'hello' + 5\n    return x"
        
        # Create a mock function
        self.function = MagicMock(spec=Function)
        self.function.name = "test_function"
        self.function.file = self.file
        self.function.line_number = 1
        self.function.code_block = MagicMock()
        self.function.code_block.source = "def test_function():\n    x = 'hello' + 5\n    return x"
        
        # Set up the codebase with the file and function
        self.codebase.files = [self.file]
        self.codebase.functions = [self.function]
        self.codebase.get_file.return_value = self.file
        
        # Create the analyzer
        self.analyzer = ErrorContextAnalyzer(self.codebase)
    
    def test_get_context_lines(self):
        """Test getting context lines around a specific line."""
        context_lines = self.analyzer.get_context_lines("test.py", 2, context_size=1)
        
        self.assertEqual(context_lines, {
            1: "def test_function():",
            2: "    x = 'hello' + 5",
            3: "    return x"
        })
    
    def test_analyze_function(self):
        """Test analyzing a function for errors."""
        errors = self.analyzer.analyze_function(self.function)
        
        # We should find at least one error (type error)
        self.assertGreaterEqual(len(errors), 1)
        
        # Check that we found a type error
        type_errors = [e for e in errors if e.error_type == ErrorType.TYPE_ERROR]
        self.assertGreaterEqual(len(type_errors), 1)
        
        # Check the error details
        error = type_errors[0]
        self.assertEqual(error.file_path, "test.py")
        self.assertEqual(error.symbol_name, "test_function")
        self.assertEqual(error.severity, ErrorSeverity.HIGH)
        self.assertIn("'hello' + 5", str(error.context_lines))
    
    def test_analyze_file(self):
        """Test analyzing a file for errors."""
        errors = self.analyzer.analyze_file(self.file)
        
        # We should find at least one error (type error)
        self.assertGreaterEqual(len(errors), 1)
        
        # Check that we found a type error
        type_errors = [e for e in errors if e.error_type == ErrorType.TYPE_ERROR]
        self.assertGreaterEqual(len(type_errors), 1)
    
    def test_analyze_codebase(self):
        """Test analyzing the entire codebase for errors."""
        error_dict = self.analyzer.analyze_codebase()
        
        # We should have errors for our test file
        self.assertIn("test.py", error_dict)
        self.assertGreaterEqual(len(error_dict["test.py"]), 1)
    
    def test_find_circular_imports(self):
        """Test finding circular imports."""
        # Mock the build_import_graph method to return a graph with a cycle
        import networkx as nx
        G = nx.DiGraph()
        G.add_edge("a.py", "b.py")
        G.add_edge("b.py", "c.py")
        G.add_edge("c.py", "a.py")
        
        with patch.object(self.analyzer, 'build_import_graph', return_value=G):
            cycles = self.analyzer.find_circular_imports()
            
            # We should find one cycle
            self.assertEqual(len(cycles), 1)
            
            # The cycle should contain a.py, b.py, and c.py
            cycle = cycles[0]
            self.assertIn("a.py", cycle)
            self.assertIn("b.py", cycle)
            self.assertIn("c.py", cycle)
    
    def test_get_function_error_context(self):
        """Test getting detailed error context for a function."""
        # Mock the analyze_function method to return a specific error
        error = CodeError(
            error_type=ErrorType.TYPE_ERROR,
            message="Cannot add string and integer",
            file_path="test.py",
            line_number=2,
            severity=ErrorSeverity.HIGH,
            symbol_name="test_function",
            context_lines={1: "def test_function():", 2: "    x = 'hello' + 5", 3: "    return x"},
            suggested_fix="Convert the integer to a string: 'hello' + str(5)"
        )
        
        with patch.object(self.analyzer, 'analyze_function', return_value=[error]):
            context = self.analyzer.get_function_error_context("test_function")
            
            # Check the context
            self.assertEqual(context["function_name"], "test_function")
            self.assertEqual(context["file_path"], "test.py")
            self.assertEqual(len(context["errors"]), 1)
            
            # Check the error details
            error_dict = context["errors"][0]
            self.assertEqual(error_dict["error_type"], ErrorType.TYPE_ERROR)
            self.assertEqual(error_dict["message"], "Cannot add string and integer")
            self.assertEqual(error_dict["line_number"], 2)
            self.assertEqual(error_dict["severity"], ErrorSeverity.HIGH)
            self.assertEqual(error_dict["suggested_fix"], "Convert the integer to a string: 'hello' + str(5)")
    
    def test_get_file_error_context(self):
        """Test getting detailed error context for a file."""
        # Mock the analyze_file method to return a specific error
        error = CodeError(
            error_type=ErrorType.TYPE_ERROR,
            message="Cannot add string and integer",
            file_path="test.py",
            line_number=2,
            severity=ErrorSeverity.HIGH,
            symbol_name="test_function",
            context_lines={1: "def test_function():", 2: "    x = 'hello' + 5", 3: "    return x"},
            suggested_fix="Convert the integer to a string: 'hello' + str(5)"
        )
        
        with patch.object(self.analyzer, 'analyze_file', return_value=[error]):
            context = self.analyzer.get_file_error_context("test.py")
            
            # Check the context
            self.assertEqual(context["file_path"], "test.py")
            self.assertEqual(len(context["errors"]), 1)
            
            # Check the error details
            error_dict = context["errors"][0]
            self.assertEqual(error_dict["error_type"], ErrorType.TYPE_ERROR)
            self.assertEqual(error_dict["message"], "Cannot add string and integer")
            self.assertEqual(error_dict["line_number"], 2)
            self.assertEqual(error_dict["severity"], ErrorSeverity.HIGH)
            self.assertEqual(error_dict["suggested_fix"], "Convert the integer to a string: 'hello' + str(5)")


if __name__ == '__main__':
    unittest.main()

