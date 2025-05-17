"""
Tests for the codebase analyzer.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from codegen_on_oss.analysis.codebase_analyzer import CodebaseAnalyzer


class TestCodebaseAnalyzer(unittest.TestCase):
    """Test cases for the CodebaseAnalyzer class."""

    @patch('codegen_on_oss.analysis.codebase_analyzer.Codebase')
    def test_init_from_path(self, mock_codebase):
        """Test initializing the analyzer from a local path."""
        # Setup
        mock_codebase_instance = MagicMock()
        mock_codebase.return_value = mock_codebase_instance
        
        # Execute
        analyzer = CodebaseAnalyzer(repo_path='/path/to/repo')
        
        # Assert
        self.assertEqual(analyzer.repo_path, '/path/to/repo')
        self.assertIsNone(analyzer.repo_url)
        self.assertEqual(analyzer.codebase, mock_codebase_instance)
    
    @patch('codegen_on_oss.analysis.codebase_analyzer.Codebase')
    def test_init_from_url(self, mock_codebase):
        """Test initializing the analyzer from a URL."""
        # Setup
        mock_codebase_instance = MagicMock()
        mock_codebase.from_github.return_value = mock_codebase_instance
        
        # Execute
        analyzer = CodebaseAnalyzer(repo_url='https://github.com/username/repo')
        
        # Assert
        self.assertEqual(analyzer.repo_url, 'https://github.com/username/repo')
        self.assertIsNone(analyzer.repo_path)
        self.assertEqual(analyzer.codebase, mock_codebase_instance)
    
    @patch('codegen_on_oss.analysis.codebase_analyzer.CodebaseAnalyzer._init_from_url')
    @patch('codegen_on_oss.analysis.codebase_analyzer.CodebaseAnalyzer._init_from_path')
    def test_init_priority(self, mock_init_from_path, mock_init_from_url):
        """Test that URL initialization takes priority over path."""
        # Execute
        CodebaseAnalyzer(repo_url='https://github.com/username/repo', repo_path='/path/to/repo')
        
        # Assert
        mock_init_from_url.assert_called_once()
        mock_init_from_path.assert_not_called()
    
    @patch('codegen_on_oss.analysis.codebase_analyzer.CodebaseAnalyzer._init_from_path')
    def test_analyze_without_init(self, _):
        """Test that analyze raises an error if codebase is not initialized."""
        # Setup
        analyzer = CodebaseAnalyzer(repo_path='/path/to/repo')
        analyzer.codebase = None
        
        # Execute and Assert
        with self.assertRaises(ValueError):
            analyzer.analyze()


if __name__ == '__main__':
    unittest.main()

