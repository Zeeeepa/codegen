#!/usr/bin/env python3
"""
Test script for the Module Disassembler.

This script tests the functionality of the module disassembler
by creating a simple test codebase with known duplicates and
verifying that they are correctly identified.
"""

import os
import sys
import tempfile
import shutil
import json
from pathlib import Path
import unittest
from module_disassembler import ModuleDisassembler

class TestModuleDisassembler(unittest.TestCase):
    """Test cases for the Module Disassembler."""
    
    def setUp(self):
        """Set up a test codebase with known duplicates."""
        # Create a temporary directory for the test codebase
        self.test_dir = tempfile.mkdtemp()
        self.output_dir = tempfile.mkdtemp()
        self.report_file = os.path.join(self.test_dir, "report.json")
        
        # Create a simple test codebase
        self._create_test_codebase()
    
    def tearDown(self):
        """Clean up temporary directories."""
        shutil.rmtree(self.test_dir)
        shutil.rmtree(self.output_dir)
    
    def _create_test_codebase(self):
        """Create a simple test codebase with known duplicates."""
        # Create directory structure
        os.makedirs(os.path.join(self.test_dir, "module1"))
        os.makedirs(os.path.join(self.test_dir, "module2"))
        
        # Create test files with duplicate functions
        
        # File 1: module1/file1.py
        with open(os.path.join(self.test_dir, "module1", "file1.py"), "w") as f:
            f.write("""
def analyze_data(data):
    \"\"\"Analyze the given data.\"\"\"
    result = {}
    for item in data:
        if item in result:
            result[item] += 1
        else:
            result[item] = 1
    return result

def format_output(data):
    \"\"\"Format the output data.\"\"\"
    return "\\n".join([f"{k}: {v}" for k, v in data.items()])
""")
        
        # File 2: module1/file2.py
        with open(os.path.join(self.test_dir, "module1", "file2.py"), "w") as f:
            f.write("""
def process_data(data):
    \"\"\"Process the given data.\"\"\"
    result = {}
    for item in data:
        if item in result:
            result[item] += 1
        else:
            result[item] = 1
    return result

def validate_input(data):
    \"\"\"Validate the input data.\"\"\"
    if not isinstance(data, list):
        raise ValueError("Input must be a list")
    return True
""")
        
        # File 3: module2/file3.py
        with open(os.path.join(self.test_dir, "module2", "file3.py"), "w") as f:
            f.write("""
def analyze_data(data):
    \"\"\"Analyze the given data.\"\"\"
    result = {}
    for item in data:
        if item in result:
            result[item] += 1
        else:
            result[item] = 1
    return result

def display_results(data):
    \"\"\"Display the results.\"\"\"
    for key, value in data.items():
        print(f"{key}: {value}")
""")
        
        # File 4: module2/file4.py
        with open(os.path.join(self.test_dir, "module2", "file4.py"), "w") as f:
            f.write("""
def format_results(data):
    \"\"\"Format the results.\"\"\"
    return "\\n".join([f"{k}: {v}" for k, v in data.items()])

def save_results(data, filename):
    \"\"\"Save the results to a file.\"\"\"
    with open(filename, "w") as f:
        f.write(format_results(data))
""")
    
    def test_function_extraction(self):
        """Test that functions are correctly extracted from the codebase."""
        disassembler = ModuleDisassembler(repo_path=self.test_dir)
        disassembler._extract_functions()
        
        # We should have 6 functions in total
        self.assertEqual(len(disassembler.functions), 6)
        
        # Check that all expected functions are found
        function_names = [func.name for func in disassembler.functions.values()]
        expected_names = ["analyze_data", "format_output", "process_data", 
                          "validate_input", "display_results", "format_results", 
                          "save_results"]
        
        for name in expected_names:
            self.assertIn(name, function_names)
    
    def test_duplicate_detection(self):
        """Test that duplicates are correctly identified."""
        disassembler = ModuleDisassembler(repo_path=self.test_dir)
        disassembler._extract_functions()
        disassembler._identify_duplicates(similarity_threshold=0.8)
        
        # We should have 1 duplicate group (analyze_data appears twice)
        self.assertEqual(len(disassembler.duplicate_groups), 1)
        
        # We should have 1 similar group (format_output and format_results are similar)
        self.assertEqual(len(disassembler.similar_groups), 1)
    
    def test_categorization(self):
        """Test that functions are correctly categorized."""
        disassembler = ModuleDisassembler(repo_path=self.test_dir)
        disassembler._extract_functions()
        disassembler._categorize_functions()
        
        # Check that functions are categorized correctly
        self.assertIn("analysis", disassembler.categorized_functions)
        self.assertIn("validation", disassembler.categorized_functions)
        self.assertIn("visualization", disassembler.categorized_functions)
        
        # analyze_data and process_data should be in the analysis category
        analysis_names = [func.name for func in disassembler.categorized_functions["analysis"]]
        self.assertIn("analyze_data", analysis_names)
        self.assertIn("process_data", analysis_names)
        
        # validate_input should be in the validation category
        validation_names = [func.name for func in disassembler.categorized_functions["validation"]]
        self.assertIn("validate_input", validation_names)
        
        # display_results should be in the visualization category
        visualization_names = [func.name for func in disassembler.categorized_functions["visualization"]]
        self.assertIn("display_results", visualization_names)
    
    def test_full_analysis(self):
        """Test the full analysis process."""
        disassembler = ModuleDisassembler(repo_path=self.test_dir)
        disassembler.analyze(similarity_threshold=0.8)
        disassembler.generate_restructured_modules(output_dir=self.output_dir)
        disassembler.generate_report(output_file=self.report_file)
        
        # Check that the output directory contains the expected structure
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "__init__.py")))
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "README.md")))
        
        # Check that the report file was created
        self.assertTrue(os.path.exists(self.report_file))
        
        # Load the report and check its structure
        with open(self.report_file, "r") as f:
            report = json.load(f)
        
        self.assertIn("summary", report)
        self.assertIn("duplicates", report)
        self.assertIn("similar", report)
        self.assertIn("categories", report)

if __name__ == "__main__":
    unittest.main()

