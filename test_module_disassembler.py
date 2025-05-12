#!/usr/bin/env python3
"""
Test script for the Module Disassembler.

This script tests the functionality of the module disassembler
to ensure it correctly analyzes and restructures code.
"""

import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path
from module_disassembler import ModuleDisassembler, FunctionInfo

class TestModuleDisassembler(unittest.TestCase):
    """Test cases for the Module Disassembler."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test outputs
        self.test_dir = tempfile.mkdtemp()
        self.output_dir = os.path.join(self.test_dir, "output")
        self.report_file = os.path.join(self.test_dir, "report.json")
        
        # Get the repository path (current directory)
        self.repo_path = os.path.dirname(os.path.abspath(__file__))
        
    def tearDown(self):
        """Tear down test fixtures."""
        # Remove the temporary directory
        shutil.rmtree(self.test_dir)
    
    def test_function_info(self):
        """Test the FunctionInfo class."""
        # Create a FunctionInfo object
        func_info = FunctionInfo(
            name="test_function",
            source="def test_function():\n    return 'test'",
            file_path="test.py",
            start_line=1,
            end_line=2
        )
        
        # Test basic properties
        self.assertEqual(func_info.name, "test_function")
        self.assertEqual(func_info.file_path, "test.py")
        self.assertEqual(func_info.start_line, 1)
        self.assertEqual(func_info.end_line, 2)
        
        # Test hash computation
        self.assertIsNotNone(func_info.hash)
        self.assertIsNotNone(func_info.normalized_hash)
        
        # Test similarity computation
        func_info2 = FunctionInfo(
            name="test_function2",
            source="def test_function2():\n    return 'test'",
            file_path="test.py",
            start_line=4,
            end_line=5
        )
        similarity = func_info.compute_similarity(func_info2)
        self.assertGreater(similarity, 0.5)  # Should be quite similar
        
    def test_disassembler_initialization(self):
        """Test initialization of the ModuleDisassembler."""
        disassembler = ModuleDisassembler(repo_path=self.repo_path)
        self.assertEqual(disassembler.repo_path, Path(self.repo_path))
        self.assertEqual(len(disassembler.functions), 0)
        self.assertEqual(len(disassembler.duplicate_groups), 0)
        self.assertEqual(len(disassembler.similar_groups), 0)
        
    def test_small_analysis(self):
        """Test analysis on a small subset of the codebase."""
        # Create a disassembler
        disassembler = ModuleDisassembler(repo_path=self.repo_path)
        
        try:
            # Try to analyze the module_disassembler.py file itself
            # This is a minimal test that doesn't require loading the full codebase
            disassembler.analyze(focus_dir=".")
            
            # Check that some functions were extracted
            self.assertGreater(len(disassembler.functions), 0)
            
            # Generate restructured modules
            disassembler.generate_restructured_modules(output_dir=self.output_dir)
            
            # Check that the output directory was created
            self.assertTrue(os.path.exists(self.output_dir))
            
            # Generate report
            disassembler.generate_report(output_file=self.report_file)
            
            # Check that the report file was created
            self.assertTrue(os.path.exists(self.report_file))
            
        except Exception as e:
            # If the test fails due to SDK initialization issues, skip it
            if "SDK" in str(e):
                self.skipTest(f"Skipping test due to SDK initialization issue: {e}")
            else:
                raise
    
    def test_categorize_functions(self):
        """Test function categorization."""
        # Create a disassembler
        disassembler = ModuleDisassembler(repo_path=self.repo_path)
        
        # Create some test functions
        analyze_func = FunctionInfo(
            name="analyze_code",
            source="def analyze_code():\n    pass",
            file_path="test.py",
            start_line=1,
            end_line=2
        )
        
        util_func = FunctionInfo(
            name="helper_function",
            source="def helper_function():\n    pass",
            file_path="test.py",
            start_line=4,
            end_line=5
        )
        
        other_func = FunctionInfo(
            name="some_function",
            source="def some_function():\n    pass",
            file_path="test.py",
            start_line=7,
            end_line=8
        )
        
        # Add functions to the disassembler
        disassembler.functions = {
            "test.py:analyze_code": analyze_func,
            "test.py:helper_function": util_func,
            "test.py:some_function": other_func
        }
        
        # Categorize functions
        disassembler._categorize_functions()
        
        # Check categorization
        self.assertEqual(analyze_func.category, "analysis")
        self.assertEqual(util_func.category, "utility")
        self.assertEqual(other_func.category, "other")
        
        # Check categorized_functions dictionary
        self.assertIn(analyze_func, disassembler.categorized_functions["analysis"])
        self.assertIn(util_func, disassembler.categorized_functions["utility"])
        self.assertIn(other_func, disassembler.categorized_functions["other"])


if __name__ == "__main__":
    unittest.main()

