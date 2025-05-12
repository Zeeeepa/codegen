"""
Tests for the codegen_sdk_codebase module.
"""

import os
import unittest
from unittest.mock import patch, MagicMock

from codegen.sdk.core.codebase import Codebase
from codegen_on_oss.analyzers.codegen_sdk_codebase import (
    get_codegen_sdk_base_path,
    get_codegen_sdk_subdirectories,
    get_codegen_sdk_codebase,
)


class TestCodegenSdkCodebase(unittest.TestCase):
    """Test cases for the codegen_sdk_codebase module."""

    @patch('codegen_on_oss.analyzers.codegen_sdk_codebase.get_repo_path')
    @patch('os.path.exists')
    @patch('os.path.isdir')
    def test_get_codegen_sdk_base_path(self, mock_isdir, mock_exists, mock_get_repo_path):
        """Test the get_codegen_sdk_base_path function."""
        # Setup
        mock_get_repo_path.return_value = '/repo'
        
        # Test case 1: SDK found in src directory
        mock_exists.side_effect = lambda path: path == '/repo/src/codegen/sdk'
        mock_isdir.side_effect = lambda path: path == '/repo/src/codegen/sdk'
        
        result = get_codegen_sdk_base_path()
        self.assertEqual(result, '/repo/src')
        
        # Test case 2: SDK found in codegen directory
        mock_exists.side_effect = lambda path: path == '/repo/codegen/sdk'
        mock_isdir.side_effect = lambda path: path == '/repo/codegen/sdk'
        
        result = get_codegen_sdk_base_path()
        self.assertEqual(result, '/repo')
        
        # Test case 3: SDK not found
        mock_exists.return_value = False
        mock_isdir.return_value = False
        
        result = get_codegen_sdk_base_path()
        self.assertEqual(result, '/repo')

    @patch('codegen_on_oss.analyzers.codegen_sdk_codebase.get_codegen_sdk_base_path')
    @patch('os.path.exists')
    @patch('os.path.isdir')
    def test_get_codegen_sdk_subdirectories(self, mock_isdir, mock_exists, mock_get_base_path):
        """Test the get_codegen_sdk_subdirectories function."""
        # Setup
        mock_get_base_path.return_value = '/repo'
        
        # Test case 1: Both directories exist
        mock_exists.return_value = True
        mock_isdir.return_value = True
        
        result = get_codegen_sdk_subdirectories()
        self.assertEqual(result, ['/repo/codegen/sdk', '/repo/codemods'])
        
        # Test case 2: Only SDK directory exists
        mock_exists.side_effect = lambda path: path == '/repo/codegen/sdk'
        mock_isdir.side_effect = lambda path: path == '/repo/codegen/sdk'
        
        result = get_codegen_sdk_subdirectories()
        self.assertEqual(result, ['/repo/codegen/sdk'])
        
        # Test case 3: No directories exist
        mock_exists.return_value = False
        mock_isdir.return_value = False
        
        result = get_codegen_sdk_subdirectories()
        self.assertEqual(result, [])

    @patch('codegen_on_oss.analyzers.codegen_sdk_codebase.get_codegen_sdk_subdirectories')
    @patch('codegen_on_oss.analyzers.codegen_sdk_codebase.get_repo_path')
    @patch('codegen_on_oss.analyzers.codegen_sdk_codebase.get_codegen_sdk_base_path')
    @patch('codegen_on_oss.analyzers.codegen_sdk_codebase.get_selected_codebase')
    def test_get_codegen_sdk_codebase(self, mock_get_selected_codebase, mock_get_base_path, 
                                     mock_get_repo_path, mock_get_subdirs):
        """Test the get_codegen_sdk_codebase function."""
        # Setup
        mock_get_repo_path.return_value = '/repo'
        mock_get_base_path.return_value = '/repo/src'
        mock_get_subdirs.return_value = ['/repo/src/codegen/sdk', '/repo/src/codemods']
        mock_codebase = MagicMock(spec=Codebase)
        mock_get_selected_codebase.return_value = mock_codebase
        
        # Test case: Normal execution
        result = get_codegen_sdk_codebase()
        
        self.assertEqual(result, mock_codebase)
        mock_get_selected_codebase.assert_called_once()
        
        # Verify the parameters passed to get_selected_codebase
        args, kwargs = mock_get_selected_codebase.call_args
        self.assertEqual(kwargs['repo_path'], '/repo')
        self.assertEqual(kwargs['base_path'], '/repo/src')
        self.assertEqual(kwargs['subdirectories'], ['/repo/src/codegen/sdk', '/repo/src/codemods'])


if __name__ == '__main__':
    unittest.main()

