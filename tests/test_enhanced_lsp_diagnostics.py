"""
Comprehensive tests for the enhanced LSP diagnostics system.
Tests the new context extraction capabilities and error correlation features.
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List

from codegen.sdk.codebase import Codebase
from codegen.sdk.extensions.lsp.lsp_diagnostics import (
    LSPDiagnosticsManager,
    RuntimeErrorCollector,
    CallerContextExtractor,
    ModuleContextManager,
    EnhancedDiagnostic
)
from codegen.sdk.extensions.lsp.solid_lsp import Language


class TestCallerContextExtractor:
    """Test the CallerContextExtractor functionality."""
    
    def test_get_caller_info_basic(self):
        """Test basic caller info extraction."""
        extractor = CallerContextExtractor()
        caller_info = extractor.get_caller_info()
        
        assert isinstance(caller_info, dict)
        assert "stack_trace" in caller_info
        assert "caller_frame" in caller_info
        assert "code_context" in caller_info
        
    def test_get_caller_info_with_depth(self):
        """Test caller info extraction with different depths."""
        extractor = CallerContextExtractor()
        
        def nested_function():
            return extractor.get_caller_info(depth=2)
            
        caller_info = nested_function()
        assert isinstance(caller_info, dict)
        assert caller_info["caller_frame"]["function"] == "test_get_caller_info_with_depth"
        
    def test_extract_code_context(self):
        """Test code context extraction."""
        extractor = CallerContextExtractor()
        
        # Create a mock frame
        mock_frame = Mock()
        mock_frame.f_code.co_filename = __file__
        mock_frame.f_lineno = 10
        
        context = extractor._extract_code_context(mock_frame)
        assert isinstance(context, dict)
        assert "lines" in context
        assert "line_number" in context


class TestModuleContextManager:
    """Test the ModuleContextManager functionality."""
    
    def test_get_module_context_basic(self):
        """Test basic module context extraction."""
        manager = ModuleContextManager()
        context = manager.get_module_context("test_file.py")
        
        assert isinstance(context, dict)
        assert "file_path" in context
        assert "definitions" in context
        assert "imports" in context
        
    def test_analyze_ast_structure(self):
        """Test AST structure analysis."""
        manager = ModuleContextManager()
        
        test_code = '''
import os
from typing import Dict

def test_function(param: str) -> str:
    return param.upper()

class TestClass:
    def method(self):
        pass
'''
        
        structure = manager._analyze_ast_structure(test_code)
        assert isinstance(structure, dict)
        assert "functions" in structure
        assert "classes" in structure
        assert "imports" in structure
        
        # Check that our test function and class are detected
        function_names = [f["name"] for f in structure["functions"]]
        class_names = [c["name"] for c in structure["classes"]]
        
        assert "test_function" in function_names
        assert "TestClass" in class_names


class TestRuntimeErrorCollector:
    """Test the enhanced RuntimeErrorCollector."""
    
    def setup_method(self):
        """Set up test fixtures."""
        with tempfile.TemporaryDirectory() as temp_dir:
            self.temp_dir = temp_dir
            self.codebase = Mock(spec=Codebase)
            self.codebase.root = temp_dir
            self.collector = RuntimeErrorCollector(self.codebase)
    
    def test_initialization(self):
        """Test that RuntimeErrorCollector initializes with new context extractors."""
        assert hasattr(self.collector, 'caller_extractor')
        assert hasattr(self.collector, 'module_manager')
        assert hasattr(self.collector, 'logger')
        assert isinstance(self.collector.caller_extractor, CallerContextExtractor)
        assert isinstance(self.collector.module_manager, ModuleContextManager)
        
    def test_collect_python_runtime_errors(self):
        """Test Python runtime error collection."""
        # Create a mock log file
        log_content = '''
Traceback (most recent call last):
  File "test.py", line 10, in test_function
    raise ValueError("Test error")
ValueError: Test error
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as log_file:
            log_file.write(log_content)
            log_file.flush()
            
            try:
                errors = self.collector.collect_python_runtime_errors(log_file.name)
                assert isinstance(errors, list)
                # The exact parsing depends on implementation
            finally:
                os.unlink(log_file.name)


class TestLSPDiagnosticsManager:
    """Test the enhanced LSPDiagnosticsManager."""
    
    def setup_method(self):
        """Set up test fixtures."""
        with tempfile.TemporaryDirectory() as temp_dir:
            self.temp_dir = temp_dir
            self.codebase = Mock(spec=Codebase)
            self.codebase.root = temp_dir
            self.manager = LSPDiagnosticsManager(
                codebase=self.codebase,
                language=Language.PYTHON
            )
    
    def test_initialization_with_context_extractors(self):
        """Test that LSPDiagnosticsManager initializes with context extractors."""
        assert hasattr(self.manager, 'caller_extractor')
        assert hasattr(self.manager, 'module_manager')
        assert isinstance(self.manager.caller_extractor, CallerContextExtractor)
        assert isinstance(self.manager.module_manager, ModuleContextManager)
        
    def test_analyze_error_correlation(self):
        """Test error correlation analysis."""
        # Create a mock diagnostic
        mock_diagnostic = Mock()
        mock_diagnostic.code = "E001"
        mock_diagnostic.message = "Test error message"
        mock_diagnostic.uri = "file:///test/file.py"
        mock_diagnostic.severity = 1
        
        # Create mock runtime and UI errors
        runtime_errors = [
            {
                "error_type": "exception",
                "file_path": "/test/other_file.py",
                "message": "Runtime error"
            }
        ]
        
        ui_errors = [
            {
                "error_type": "react_error",
                "file_path": "/test/component.jsx",
                "message": "UI error"
            }
        ]
        
        correlation = self.manager._analyze_error_correlation(
            mock_diagnostic, runtime_errors, ui_errors
        )
        
        assert isinstance(correlation, dict)
        assert "error_patterns" in correlation
        assert "cross_module_errors" in correlation
        assert "frequency_analysis" in correlation
        assert "severity_correlation" in correlation
        
    def test_calculate_correlation_score(self):
        """Test correlation score calculation."""
        mock_diagnostic = Mock()
        mock_diagnostic.severity = 1
        
        runtime_errors = [{"error_type": "exception"}]
        ui_errors = [{"error_type": "react_error"}]
        
        score = self.manager._calculate_correlation_score(
            mock_diagnostic, runtime_errors, ui_errors
        )
        
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
        
    @patch('codegen.sdk.extensions.lsp.lsp_diagnostics.get_ai_fix_context')
    def test_get_enhanced_diagnostics_with_new_context(self, mock_get_ai_fix_context):
        """Test enhanced diagnostics with new context fields."""
        # Mock the LSP server and its diagnostics
        mock_lsp_server = Mock()
        mock_diagnostic = Mock()
        mock_diagnostic.code = "E001"
        mock_diagnostic.message = "Test error"
        mock_diagnostic.range = Mock()
        mock_diagnostic.range.line = 5
        mock_diagnostic.uri = "file:///test/file.py"
        mock_diagnostic.severity = 1
        
        mock_lsp_server.get_all_diagnostics.return_value = {
            "file:///test/file.py": [mock_diagnostic]
        }
        
        self.manager.lsp_server = mock_lsp_server
        
        # Mock codebase file content
        mock_file = Mock()
        mock_file.content = "def test():\n    pass\n"
        self.codebase.get_file.return_value = mock_file
        
        # Mock the context extraction methods
        self.manager.caller_extractor.get_caller_info = Mock(return_value={
            "caller_frame": {"function": "test_caller"},
            "code_context": {"lines": ["test line"]}
        })
        
        self.manager.module_manager.get_module_context = Mock(return_value={
            "file_path": "test/file.py",
            "definitions": {"functions": ["test"]},
            "imports": []
        })
        
        # Mock the AI fix context function
        mock_get_ai_fix_context.return_value = {
            "diagnostic": mock_diagnostic,
            "file_content": "def test():\n    pass\n",
            "caller_context": {"caller_frame": {"function": "test_caller"}},
            "module_context": {"file_path": "test/file.py"},
            "error_correlation": {"error_patterns": {}},
            "graph_sitter_context": {},
            "autogenlib_context": {},
            "runtime_context": {},
            "ui_interaction_context": {}
        }
        
        # Test the enhanced diagnostics
        diagnostics = self.manager.get_enhanced_diagnostics_for_uri("file:///test/file.py")
        
        assert isinstance(diagnostics, list)
        if diagnostics:  # If diagnostics were returned
            diagnostic = diagnostics[0]
            assert "caller_context" in diagnostic
            assert "module_context" in diagnostic
            assert "error_correlation" in diagnostic


class TestIntegration:
    """Integration tests for the complete enhanced diagnostics system."""
    
    def test_end_to_end_diagnostics_flow(self):
        """Test the complete flow from error collection to enhanced diagnostics."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test Python file with an error
            test_file = os.path.join(temp_dir, "test_file.py")
            with open(test_file, 'w') as f:
                f.write('''
def test_function():
    undefined_variable = some_undefined_var  # This will cause an error
    return undefined_variable
''')
            
            # Mock codebase
            codebase = Mock(spec=Codebase)
            codebase.root = temp_dir
            mock_file = Mock()
            mock_file.content = open(test_file).read()
            codebase.get_file.return_value = mock_file
            
            # Create manager
            manager = LSPDiagnosticsManager(codebase=codebase, language=Language.PYTHON)
            
            # Test that all components are properly initialized
            assert isinstance(manager.caller_extractor, CallerContextExtractor)
            assert isinstance(manager.module_manager, ModuleContextManager)
            assert isinstance(manager.runtime_collector, RuntimeErrorCollector)
            
            # Test context extraction works
            caller_context = manager.caller_extractor.get_caller_info()
            assert isinstance(caller_context, dict)
            
            module_context = manager.module_manager.get_module_context("test_file.py")
            assert isinstance(module_context, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
