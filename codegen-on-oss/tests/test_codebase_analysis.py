#!/usr/bin/env python3
"""
Tests for the codebase_analysis module.

This module tests the functionality of the codebase_analysis.py module
in the analyzers directory, ensuring it provides the expected functionality
for codebase and file summaries.
"""

import unittest
import os
import sys
from unittest.mock import MagicMock, patch

# Add the parent directory to the path so we can import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from codegen_on_oss.analyzers.codebase_analysis import (
    get_codebase_summary,
    get_file_summary,
    get_class_summary,
    get_function_summary,
    get_symbol_summary,
    get_dependency_graph,
    get_symbol_references,
    get_file_complexity_metrics
)


class TestCodebaseAnalysis(unittest.TestCase):
    """Test cases for the codebase_analysis module."""

    def setUp(self):
        """Set up test fixtures."""
        # Create mock objects for testing
        self.mock_codebase = MagicMock()
        self.mock_file = MagicMock()
        self.mock_class = MagicMock()
        self.mock_function = MagicMock()
        self.mock_symbol = MagicMock()
        
        # Set up mock codebase
        self.mock_codebase.ctx.get_nodes.return_value = [1, 2, 3]
        self.mock_codebase.ctx.edges = [(1, 2, MagicMock(type=MagicMock(name="SYMBOL_USAGE"))), 
                                        (2, 3, MagicMock(type=MagicMock(name="IMPORT_SYMBOL_RESOLUTION"))),
                                        (3, 1, MagicMock(type=MagicMock(name="EXPORT")))]
        self.mock_codebase.files = [MagicMock(), MagicMock()]
        self.mock_codebase.imports = [MagicMock()]
        self.mock_codebase.external_modules = [MagicMock()]
        self.mock_codebase.symbols = [MagicMock()]
        self.mock_codebase.classes = [MagicMock()]
        self.mock_codebase.functions = [MagicMock()]
        self.mock_codebase.global_vars = [MagicMock()]
        self.mock_codebase.interfaces = [MagicMock()]
        
        # Set up mock file
        self.mock_file.name = "test_file.py"
        self.mock_file.file_path = "/path/to/test_file.py"
        self.mock_file.imports = [MagicMock()]
        self.mock_file.symbols = [MagicMock()]
        self.mock_file.classes = [MagicMock()]
        self.mock_file.functions = [MagicMock()]
        self.mock_file.global_vars = [MagicMock()]
        self.mock_file.interfaces = [MagicMock()]
        self.mock_file.source = "def test_function():\n    if True:\n        return 1\n    else:\n        return 0"
        
        # Set up mock class
        self.mock_class.name = "TestClass"
        self.mock_class.parent_class_names = ["BaseClass"]
        self.mock_class.methods = [MagicMock()]
        self.mock_class.attributes = [MagicMock()]
        self.mock_class.decorators = [MagicMock()]
        self.mock_class.dependencies = [MagicMock()]
        self.mock_class.symbol_usages = [MagicMock()]
        
        # Set up mock function
        self.mock_function.name = "test_function"
        self.mock_function.return_statements = [MagicMock()]
        self.mock_function.parameters = [MagicMock()]
        self.mock_function.function_calls = [MagicMock()]
        self.mock_function.call_sites = [MagicMock()]
        self.mock_function.decorators = [MagicMock()]
        self.mock_function.dependencies = [MagicMock()]
        self.mock_function.symbol_usages = [MagicMock()]
        self.mock_function.source = "def test_function():\n    if True:\n        return 1\n    else:\n        return 0"
        
        # Set up mock symbol
        self.mock_symbol.name = "test_symbol"
        self.mock_symbol.symbol_usages = [MagicMock()]

    def test_get_codebase_summary(self):
        """Test the get_codebase_summary function."""
        summary = get_codebase_summary(self.mock_codebase)
        
        # Check that the summary contains expected information
        self.assertIn("Contains 3 nodes", summary)
        self.assertIn("2 files", summary)
        self.assertIn("1 imports", summary)
        self.assertIn("1 external_modules", summary)
        self.assertIn("1 symbols", summary)
        self.assertIn("1 classes", summary)
        self.assertIn("1 functions", summary)
        self.assertIn("1 global_vars", summary)
        self.assertIn("1 interfaces", summary)
        self.assertIn("Contains 3 edges", summary)
        self.assertIn("1 symbol -> used symbol", summary)
        self.assertIn("1 import -> used symbol", summary)
        self.assertIn("1 export -> exported symbol", summary)

    def test_get_file_summary(self):
        """Test the get_file_summary function."""
        summary = get_file_summary(self.mock_file)
        
        # Check that the summary contains expected information
        self.assertIn("`test_file.py` (SourceFile) Dependency Summary", summary)
        self.assertIn("1 imports", summary)
        self.assertIn("1 symbol references", summary)
        self.assertIn("1 classes", summary)
        self.assertIn("1 functions", summary)
        self.assertIn("1 global variables", summary)
        self.assertIn("1 interfaces", summary)
        self.assertIn("`test_file.py` Usage Summary", summary)
        self.assertIn("1 importers", summary)

    def test_get_class_summary(self):
        """Test the get_class_summary function."""
        with patch('codegen_on_oss.analyzers.codebase_analysis.get_symbol_summary', return_value="SYMBOL SUMMARY"):
            summary = get_class_summary(self.mock_class)
            
            # Check that the summary contains expected information
            self.assertIn("`TestClass` (Class) Dependency Summary", summary)
            self.assertIn("parent classes: ['BaseClass']", summary)
            self.assertIn("1 methods", summary)
            self.assertIn("1 attributes", summary)
            self.assertIn("1 decorators", summary)
            self.assertIn("1 dependencies", summary)
            self.assertIn("SYMBOL SUMMARY", summary)

    def test_get_function_summary(self):
        """Test the get_function_summary function."""
        with patch('codegen_on_oss.analyzers.codebase_analysis.get_symbol_summary', return_value="SYMBOL SUMMARY"):
            summary = get_function_summary(self.mock_function)
            
            # Check that the summary contains expected information
            self.assertIn("`test_function` (Function) Dependency Summary", summary)
            self.assertIn("1 return statements", summary)
            self.assertIn("1 parameters", summary)
            self.assertIn("1 function calls", summary)
            self.assertIn("1 call sites", summary)
            self.assertIn("1 decorators", summary)
            self.assertIn("1 dependencies", summary)
            self.assertIn("SYMBOL SUMMARY", summary)

    def test_get_file_complexity_metrics(self):
        """Test the get_file_complexity_metrics function."""
        metrics = get_file_complexity_metrics(self.mock_file)
        
        # Check that the metrics contain expected information
        self.assertEqual(metrics['file_path'], "/path/to/test_file.py")
        self.assertEqual(metrics['name'], "test_file.py")
        self.assertEqual(metrics['num_lines'], 5)
        self.assertEqual(metrics['num_imports'], 1)
        self.assertEqual(metrics['num_classes'], 1)
        self.assertEqual(metrics['num_functions'], 1)
        self.assertEqual(metrics['num_global_vars'], 1)
        
        # Test with a function that has control flow
        self.mock_function.source = """def complex_function(a, b):
            if a > 0:
                if b > 0:
                    return a + b
                else:
                    return a - b
            elif a < 0 and b < 0:
                return -a - b
            else:
                for i in range(10):
                    if i % 2 == 0:
                        continue
                    a += i
                return a
        """
        
        # Mock the functions list to include our complex function
        self.mock_file.functions = [self.mock_function]
        
        metrics = get_file_complexity_metrics(self.mock_file)
        self.assertGreater(metrics['cyclomatic_complexity'], 1)


if __name__ == '__main__':
    unittest.main()

