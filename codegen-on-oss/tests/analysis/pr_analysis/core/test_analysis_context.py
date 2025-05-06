"""
Tests for the Analysis Context
"""

import unittest
from unittest.mock import Mock, patch
from codegen_on_oss.analysis.pr_analysis.core.analysis_context import AnalysisContext, DiffContext


class TestAnalysisContext(unittest.TestCase):
    def setUp(self):
        self.codebase = Mock()
        self.pr_data = Mock()
        self.context = AnalysisContext(self.codebase, self.pr_data)
    
    def test_get_changed_files(self):
        # Mock _compute_file_changes
        self.context._compute_file_changes = Mock()
        self.context._file_changes = {"file1.py": "added", "file2.py": "modified"}
        
        # Call the method under test
        result = self.context.get_changed_files()
        
        # Verify the results
        self.assertEqual(result, {"file1.py": "added", "file2.py": "modified"})
        self.context._compute_file_changes.assert_not_called()  # Should not be called since _file_changes is already set
    
    def test_get_symbol_changes(self):
        # Mock _compute_symbol_changes
        self.context._compute_symbol_changes = Mock()
        self.context._symbol_changes = {"symbol1": {"type": "function"}, "symbol2": {"type": "class"}}
        
        # Call the method under test
        result = self.context.get_symbol_changes()
        
        # Verify the results
        self.assertEqual(result, {"symbol1": {"type": "function"}, "symbol2": {"type": "class"}})
        self.context._compute_symbol_changes.assert_not_called()  # Should not be called since _symbol_changes is already set
    
    def test_compute_file_changes(self):
        # Mock codebase.get_all_files
        file1 = Mock()
        file1.filepath = "file1.py"
        file2 = Mock()
        file2.filepath = "file2.py"
        self.codebase.get_all_files.return_value = [file1, file2]
        
        # Call the method under test
        self.context._compute_file_changes()
        
        # Verify the results
        self.assertEqual(self.context._file_changes, {"file1.py": "unchanged", "file2.py": "unchanged"})
    
    def test_compute_symbol_changes(self):
        # Mock codebase.get_all_symbols
        symbol1 = Mock()
        symbol1.name = "symbol1"
        symbol1.symbol_type.name = "Function"
        symbol1.filepath = "file1.py"
        symbol1.line_range = [10, 20]
        symbol1.column_range = [0, 10]
        
        symbol2 = Mock()
        symbol2.name = "symbol2"
        symbol2.symbol_type.name = "Class"
        symbol2.filepath = "file2.py"
        symbol2.line_range = [30, 40]
        symbol2.column_range = [0, 10]
        
        self.codebase.get_all_symbols.return_value = [symbol1, symbol2]
        
        # Call the method under test
        self.context._compute_symbol_changes()
        
        # Verify the results
        self.assertEqual(self.context._symbol_changes, {
            "symbol1": {"type": "Function", "file": "file1.py", "line": 10, "column": 0},
            "symbol2": {"type": "Class", "file": "file2.py", "line": 30, "column": 0},
        })
    
    def test_get_file_content(self):
        # Mock codebase.get_file
        file = Mock()
        file.content = "file content"
        self.codebase.get_file.return_value = file
        
        # Call the method under test
        result = self.context.get_file_content("file1.py")
        
        # Verify the results
        self.codebase.get_file.assert_called_once_with("file1.py")
        self.assertEqual(result, "file content")
        
        # Test with non-existent file
        self.codebase.get_file.return_value = None
        result = self.context.get_file_content("non-existent.py")
        self.assertIsNone(result)
    
    def test_get_file_symbols(self):
        # Mock codebase.get_file
        file = Mock()
        file.symbols = ["symbol1", "symbol2"]
        self.codebase.get_file.return_value = file
        
        # Call the method under test
        result = self.context.get_file_symbols("file1.py")
        
        # Verify the results
        self.codebase.get_file.assert_called_once_with("file1.py")
        self.assertEqual(result, ["symbol1", "symbol2"])
        
        # Test with non-existent file
        self.codebase.get_file.return_value = None
        result = self.context.get_file_symbols("non-existent.py")
        self.assertEqual(result, [])


class TestDiffContext(unittest.TestCase):
    def setUp(self):
        self.base_context = Mock()
        self.head_context = Mock()
        self.diff_context = DiffContext(self.base_context, self.head_context)
    
    def test_get_file_changes(self):
        # Mock _compute_file_changes
        self.diff_context._compute_file_changes = Mock()
        self.diff_context._file_changes = {"file1.py": "added", "file2.py": "modified"}
        
        # Call the method under test
        result = self.diff_context.get_file_changes()
        
        # Verify the results
        self.assertEqual(result, {"file1.py": "added", "file2.py": "modified"})
        self.diff_context._compute_file_changes.assert_not_called()  # Should not be called since _file_changes is already set
    
    def test_get_function_changes(self):
        # Mock _compute_function_changes
        self.diff_context._compute_function_changes = Mock()
        self.diff_context._function_changes = {"func1": {"change_type": "added"}, "func2": {"change_type": "modified"}}
        
        # Call the method under test
        result = self.diff_context.get_function_changes()
        
        # Verify the results
        self.assertEqual(result, {"func1": {"change_type": "added"}, "func2": {"change_type": "modified"}})
        self.diff_context._compute_function_changes.assert_not_called()  # Should not be called since _function_changes is already set
    
    def test_get_class_changes(self):
        # Mock _compute_class_changes
        self.diff_context._compute_class_changes = Mock()
        self.diff_context._class_changes = {"class1": {"change_type": "added"}, "class2": {"change_type": "modified"}}
        
        # Call the method under test
        result = self.diff_context.get_class_changes()
        
        # Verify the results
        self.assertEqual(result, {"class1": {"change_type": "added"}, "class2": {"change_type": "modified"}})
        self.diff_context._compute_class_changes.assert_not_called()  # Should not be called since _class_changes is already set
    
    def test_compute_file_changes(self):
        # Mock base_context.codebase.get_all_files and head_context.codebase.get_all_files
        base_file1 = Mock()
        base_file1.filepath = "file1.py"
        base_file2 = Mock()
        base_file2.filepath = "file2.py"
        self.base_context.codebase.get_all_files.return_value = [base_file1, base_file2]
        
        head_file1 = Mock()
        head_file1.filepath = "file1.py"
        head_file3 = Mock()
        head_file3.filepath = "file3.py"
        self.head_context.codebase.get_all_files.return_value = [head_file1, head_file3]
        
        # Mock get_file_content
        self.base_context.get_file_content.return_value = "base content"
        self.head_context.get_file_content.return_value = "head content"
        
        # Call the method under test
        self.diff_context._compute_file_changes()
        
        # Verify the results
        self.assertEqual(self.diff_context._file_changes, {
            "file1.py": "modified",  # Content is different
            "file2.py": "deleted",   # Only in base
            "file3.py": "added",     # Only in head
        })
    
    def test_get_all_changes(self):
        # Mock get_file_changes, get_function_changes, and get_class_changes
        self.diff_context.get_file_changes = Mock(return_value={"file1.py": "added"})
        self.diff_context.get_function_changes = Mock(return_value={"func1": {"change_type": "added"}})
        self.diff_context.get_class_changes = Mock(return_value={"class1": {"change_type": "added"}})
        
        # Call the method under test
        result = self.diff_context.get_all_changes()
        
        # Verify the results
        self.assertEqual(result, {
            "file_changes": {"file1.py": "added"},
            "function_changes": {"func1": {"change_type": "added"}},
            "class_changes": {"class1": {"change_type": "added"}},
        })
    
    def test_get_changed_symbols(self):
        # Mock get_function_changes and get_class_changes
        self.diff_context.get_function_changes = Mock(return_value={
            "func1": {"change_type": "added"},
            "func2": {"change_type": "modified"},
        })
        self.diff_context.get_class_changes = Mock(return_value={
            "class1": {"change_type": "added"},
            "class2": {"change_type": "deleted"},
        })
        
        # Call the method under test
        result = self.diff_context.get_changed_symbols()
        
        # Verify the results
        self.assertEqual(result, {"func1", "func2", "class1", "class2"})

