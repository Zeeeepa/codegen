"""
Tests for the current_code_codebase module.

This module contains tests for the functionality provided by the
current_code_codebase module in the analyzers directory.
"""

import os
import sys
import unittest
from unittest import mock
from pathlib import Path

# Add the parent directory to sys.path to allow importing the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from codegen_on_oss.analyzers.current_code_codebase import (
    CodebaseError,
    CodebaseInitError,
    ModuleImportError,
    DocumentationError,
    ProgrammingLanguage,
    RepoConfig,
    RepoOperator,
    CodebaseConfig,
    SecretsConfig,
    ProjectConfig,
    Codebase,
    DocumentedObject,
    get_repo_path,
    get_base_path,
    detect_programming_language,
    get_selected_codebase,
    import_modules_from_path,
    get_documented_objects,
    get_codebase_with_docs,
    set_log_level
)


class TestCurrentCodeCodebase(unittest.TestCase):
    """Test cases for the current_code_codebase module."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_repo_path = "/test/repo/path"
        self.test_base_path = "src"

    def test_repo_config(self):
        """Test RepoConfig class."""
        # Test initialization
        config = RepoConfig(repo_path=self.test_repo_path, respect_gitignore=True)
        self.assertEqual(config.repo_path, self.test_repo_path)
        self.assertTrue(config.respect_gitignore)

        # Test from_repo_path class method
        config_from_path = RepoConfig.from_repo_path(self.test_repo_path)
        self.assertEqual(config_from_path.repo_path, self.test_repo_path)

    def test_repo_operator(self):
        """Test RepoOperator class."""
        config = RepoConfig(repo_path=self.test_repo_path)
        operator = RepoOperator(repo_config=config, bot_commit=True)
        self.assertEqual(operator.repo_config, config)
        self.assertTrue(operator.bot_commit)
        self.assertEqual(operator.repo_path, self.test_repo_path)

    def test_codebase_config(self):
        """Test CodebaseConfig class."""
        # Test initialization
        config = CodebaseConfig(base_path=self.test_base_path, option1="value1")
        self.assertEqual(config.base_path, self.test_base_path)
        self.assertEqual(config.options["option1"], "value1")

        # Test model_copy method
        updated_config = config.model_copy(update={"base_path": "new_path"})
        self.assertEqual(updated_config.base_path, "new_path")
        self.assertEqual(updated_config.options["option1"], "value1")

    def test_project_config(self):
        """Test ProjectConfig class."""
        repo_config = RepoConfig(repo_path=self.test_repo_path)
        repo_operator = RepoOperator(repo_config=repo_config)
        
        # Test initialization with defaults
        project_config = ProjectConfig(repo_operator=repo_operator)
        self.assertEqual(project_config.repo_operator, repo_operator)
        self.assertEqual(project_config.programming_language, ProgrammingLanguage.PYTHON)
        self.assertEqual(project_config.subdirectories, [])
        self.assertEqual(project_config.base_path, "")
        
        # Test initialization with custom values
        subdirs = ["dir1", "dir2"]
        project_config = ProjectConfig(
            repo_operator=repo_operator,
            programming_language=ProgrammingLanguage.TYPESCRIPT,
            subdirectories=subdirs,
            base_path=self.test_base_path
        )
        self.assertEqual(project_config.programming_language, ProgrammingLanguage.TYPESCRIPT)
        self.assertEqual(project_config.subdirectories, subdirs)
        self.assertEqual(project_config.base_path, self.test_base_path)

    def test_codebase(self):
        """Test Codebase class."""
        repo_config = RepoConfig(repo_path=self.test_repo_path)
        repo_operator = RepoOperator(repo_config=repo_config)
        project_config = ProjectConfig(repo_operator=repo_operator, base_path=self.test_base_path)
        
        # Test initialization
        codebase = Codebase(projects=[project_config])
        self.assertEqual(codebase.projects, [project_config])
        self.assertEqual(codebase.repo_paths, [self.test_repo_path])
        self.assertEqual(codebase.base_paths, [self.test_base_path])
        
        # Test initialization with empty projects list
        with self.assertRaises(CodebaseInitError):
            Codebase(projects=[])

    @mock.patch('os.getcwd')
    def test_get_repo_path(self, mock_getcwd):
        """Test get_repo_path function."""
        mock_getcwd.return_value = self.test_repo_path
        self.assertEqual(get_repo_path(), self.test_repo_path)
        
        # Test error handling
        mock_getcwd.side_effect = Exception("Test error")
        # Should not raise an exception, but fall back to os.getcwd
        self.assertEqual(get_repo_path(), os.getcwd())

    @mock.patch('os.path.isdir')
    def test_get_base_path(self, mock_isdir):
        """Test get_base_path function."""
        # Test with src directory
        mock_isdir.side_effect = lambda path: path.endswith('/src')
        self.assertEqual(get_base_path(self.test_repo_path), "src")
        
        # Test with no common directories
        mock_isdir.return_value = False
        self.assertEqual(get_base_path(self.test_repo_path), "")
        
        # Test error handling
        mock_isdir.side_effect = Exception("Test error")
        # Should not raise an exception, but fall back to empty string
        self.assertEqual(get_base_path(self.test_repo_path), "")

    @mock.patch('os.walk')
    def test_detect_programming_language(self, mock_walk):
        """Test detect_programming_language function."""
        # Mock file extensions
        mock_walk.return_value = [
            ("/path", [], ["file1.py", "file2.py", "file3.js"])
        ]
        
        # Should detect Python as the most common language
        self.assertEqual(detect_programming_language(self.test_repo_path), ProgrammingLanguage.PYTHON)
        
        # Test with different file extensions
        mock_walk.return_value = [
            ("/path", [], ["file1.ts", "file2.tsx", "file3.js"])
        ]
        
        # Should detect TypeScript as the most common language
        self.assertEqual(detect_programming_language(self.test_repo_path), ProgrammingLanguage.TYPESCRIPT)
        
        # Test with no files
        mock_walk.return_value = [
            ("/path", [], [])
        ]
        
        # Should default to Python
        self.assertEqual(detect_programming_language(self.test_repo_path), ProgrammingLanguage.PYTHON)
        
        # Test error handling
        mock_walk.side_effect = Exception("Test error")
        # Should not raise an exception, but fall back to Python
        self.assertEqual(detect_programming_language(self.test_repo_path), ProgrammingLanguage.PYTHON)

    @mock.patch('codegen_on_oss.analyzers.current_code_codebase.get_repo_path')
    @mock.patch('codegen_on_oss.analyzers.current_code_codebase.get_base_path')
    @mock.patch('codegen_on_oss.analyzers.current_code_codebase.detect_programming_language')
    def test_get_selected_codebase(self, mock_detect_lang, mock_get_base_path, mock_get_repo_path):
        """Test get_selected_codebase function."""
        mock_get_repo_path.return_value = self.test_repo_path
        mock_get_base_path.return_value = self.test_base_path
        mock_detect_lang.return_value = ProgrammingLanguage.PYTHON
        
        # Test with default parameters
        codebase = get_selected_codebase()
        self.assertEqual(codebase.repo_paths[0], self.test_repo_path)
        self.assertEqual(codebase.base_paths[0], self.test_base_path)
        
        # Test with custom parameters
        config = CodebaseConfig(base_path="custom_base")
        secrets = SecretsConfig(api_key="test_key")
        subdirs = ["dir1", "dir2"]
        
        codebase = get_selected_codebase(
            repo_path="custom_repo",
            base_path="custom_base",
            config=config,
            secrets=secrets,
            subdirectories=subdirs,
            programming_language=ProgrammingLanguage.TYPESCRIPT
        )
        
        self.assertEqual(codebase.repo_paths[0], "custom_repo")
        self.assertEqual(codebase.base_paths[0], "custom_base")
        self.assertEqual(codebase.projects[0].programming_language, ProgrammingLanguage.TYPESCRIPT)
        self.assertEqual(codebase.projects[0].subdirectories, subdirs)
        
        # Test error handling
        mock_get_repo_path.side_effect = Exception("Test error")
        with self.assertRaises(CodebaseInitError):
            get_selected_codebase()

    @mock.patch('pathlib.Path.rglob')
    @mock.patch('importlib.import_module')
    def test_import_modules_from_path(self, mock_import_module, mock_rglob):
        """Test import_modules_from_path function."""
        # Mock file paths
        mock_file1 = mock.MagicMock()
        mock_file1.name = "module1.py"
        mock_file1.relative_to.return_value = Path("module1.py")
        
        mock_file2 = mock.MagicMock()
        mock_file2.name = "module2.py"
        mock_file2.relative_to.return_value = Path("subdir/module2.py")
        
        mock_file3 = mock.MagicMock()
        mock_file3.name = "__init__.py"
        
        mock_rglob.return_value = [mock_file1, mock_file2, mock_file3]
        
        # Test successful imports
        imported_modules = import_modules_from_path("/test/path", "test_package.")
        self.assertEqual(len(imported_modules), 2)
        self.assertIn("test_package.module1", imported_modules)
        self.assertIn("test_package.subdir.module2", imported_modules)
        
        # Test import errors
        mock_import_module.side_effect = ImportError("Test import error")
        imported_modules = import_modules_from_path("/test/path", "test_package.")
        self.assertEqual(len(imported_modules), 0)
        
        # Test critical error
        mock_rglob.side_effect = Exception("Test critical error")
        with self.assertRaises(ModuleImportError):
            import_modules_from_path("/test/path", "test_package.")

    @mock.patch('codegen_on_oss.analyzers.current_code_codebase.get_repo_path')
    @mock.patch('codegen_on_oss.analyzers.current_code_codebase.get_base_path')
    @mock.patch('codegen_on_oss.analyzers.current_code_codebase.import_modules_from_path')
    @mock.patch('os.path.exists')
    @mock.patch('os.path.isdir')
    def test_get_documented_objects(self, mock_isdir, mock_exists, mock_import_modules, mock_get_base_path, mock_get_repo_path):
        """Test get_documented_objects function."""
        mock_get_repo_path.return_value = self.test_repo_path
        mock_get_base_path.return_value = self.test_base_path
        mock_exists.return_value = True
        mock_isdir.return_value = True
        mock_import_modules.return_value = ["module1", "module2"]
        
        # Test with default parameters
        docs = get_documented_objects()
        self.assertIn("apidoc", docs)
        self.assertIn("py_apidoc", docs)
        self.assertIn("ts_apidoc", docs)
        self.assertIn("no_apidoc", docs)
        
        # Test with custom parameters
        import_paths = ["/custom/path1", "/custom/path2"]
        docs = get_documented_objects(
            repo_path="custom_repo",
            package_prefix="custom_package.",
            import_paths=import_paths
        )
        self.assertIn("apidoc", docs)
        
        # Test error handling
        mock_import_modules.side_effect = Exception("Test error")
        with self.assertRaises(DocumentationError):
            get_documented_objects()

    @mock.patch('codegen_on_oss.analyzers.current_code_codebase.get_selected_codebase')
    @mock.patch('codegen_on_oss.analyzers.current_code_codebase.get_documented_objects')
    def test_get_codebase_with_docs(self, mock_get_docs, mock_get_codebase):
        """Test get_codebase_with_docs function."""
        # Mock return values
        mock_codebase = mock.MagicMock()
        mock_docs = {"apidoc": [], "py_apidoc": [], "ts_apidoc": [], "no_apidoc": []}
        
        mock_get_codebase.return_value = mock_codebase
        mock_get_docs.return_value = mock_docs
        
        # Test with default parameters
        codebase, docs = get_codebase_with_docs()
        self.assertEqual(codebase, mock_codebase)
        self.assertEqual(docs, mock_docs)
        
        # Test with custom parameters
        config = CodebaseConfig(base_path="custom_base")
        secrets = SecretsConfig(api_key="test_key")
        subdirs = ["dir1", "dir2"]
        import_paths = ["/custom/path1", "/custom/path2"]
        
        codebase, docs = get_codebase_with_docs(
            repo_path="custom_repo",
            base_path="custom_base",
            config=config,
            secrets=secrets,
            subdirectories=subdirs,
            programming_language=ProgrammingLanguage.TYPESCRIPT,
            package_prefix="custom_package.",
            import_paths=import_paths
        )
        
        self.assertEqual(codebase, mock_codebase)
        self.assertEqual(docs, mock_docs)
        
        # Test error handling
        mock_get_codebase.side_effect = Exception("Test error")
        with self.assertRaises(CodebaseError):
            get_codebase_with_docs()

    @mock.patch('logging.Logger.setLevel')
    def test_set_log_level(self, mock_set_level):
        """Test set_log_level function."""
        import logging
        
        # Test setting log level
        set_log_level(logging.DEBUG)
        mock_set_level.assert_called_with(logging.DEBUG)
        
        set_log_level(logging.INFO)
        mock_set_level.assert_called_with(logging.INFO)


if __name__ == '__main__':
    unittest.main()

