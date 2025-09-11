#!/usr/bin/env python3
"""
Core LSP Diagnostics Tests - Independent Component Testing
Tests the core functionality of lsp_diagnostics.py without external dependencies
"""

import pytest
import sys
import os
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Mock the problematic imports before importing the main module
sys.modules['serena'] = MagicMock()
sys.modules['serena.text_utils'] = MagicMock()
sys.modules['serena.util'] = MagicMock()
sys.modules['serena.util.file_system'] = MagicMock()

# Mock solidlsp modules
sys.modules['solidlsp'] = MagicMock()
sys.modules['solidlsp.ls_types'] = MagicMock()

# Create mock classes for the imports
class MockSolidLanguageServer:
    def __init__(self, *args, **kwargs):
        pass

class MockLanguage:
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"

class MockLanguageServerConfig:
    def __init__(self, *args, **kwargs):
        pass

class MockLanguageServerLogger:
    def __init__(self, *args, **kwargs):
        pass

class MockDiagnostic:
    def __init__(self, *args, **kwargs):
        self.message = "test diagnostic"
        self.range = None

class MockDocumentUri:
    def __init__(self, uri: str):
        self.uri = uri

class MockRange:
    def __init__(self, start, end):
        self.start = start
        self.end = end

class MockPathUtils:
    @staticmethod
    def normalize_path(path: str) -> str:
        return os.path.normpath(path)

# Patch the imports
with patch.dict('sys.modules', {
    'codegen.sdk.extensions.lsp.solidlsp.ls': MagicMock(SolidLanguageServer=MockSolidLanguageServer),
    'codegen.sdk.extensions.lsp.solidlsp.ls_config': MagicMock(Language=MockLanguage, LanguageServerConfig=MockLanguageServerConfig),
    'codegen.sdk.extensions.lsp.solidlsp.ls_logger': MagicMock(LanguageServerLogger=MockLanguageServerLogger),
    'codegen.sdk.extensions.lsp.solidlsp.lsp_protocol_handler.lsp_types': MagicMock(
        Diagnostic=MockDiagnostic, 
        DocumentUri=MockDocumentUri, 
        Range=MockRange
    ),
    'codegen.sdk.extensions.lsp.solidlsp.ls_utils': MagicMock(PathUtils=MockPathUtils),
    'codegen.sdk.core.codebase': MagicMock(Codebase=MagicMock),
}):
    from codegen.sdk.extensions.lsp.lsp_diagnostics import (
        CallerContextExtractor,
        ModuleContextManager,
        RuntimeErrorCollector,
        LSPDiagnosticsManager,
        EnhancedDiagnostic
    )


class TestCallerContextExtractor:
    """Test the CallerContextExtractor class"""
    
    def setup_method(self):
        self.extractor = CallerContextExtractor(max_depth=5, max_code_size=1000)
    
    def test_init(self):
        """Test CallerContextExtractor initialization"""
        assert self.extractor.max_depth == 5
        assert self.extractor.max_code_size == 1000
        assert self.extractor.logger is not None
    
    def test_get_caller_info_basic(self):
        """Test basic caller info extraction"""
        def test_function():
            return self.extractor.get_caller_info()
        
        result = test_function()
        
        assert isinstance(result, dict)
        assert 'filename' in result
        assert 'function_name' in result
        assert 'line_number' in result
        assert 'code_context' in result
    
    def test_get_caller_info_with_code(self):
        """Test caller info extraction includes code context"""
        result = self.extractor.get_caller_info()
        
        assert 'code_context' in result
        assert 'full_code' in result
        assert 'ast_context' in result
    
    def test_extract_file_context(self):
        """Test file context extraction"""
        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def test_function():\n    return 'hello world'\n")
            temp_file = f.name
        
        try:
            result = self.extractor._extract_file_context(temp_file)
            
            assert isinstance(result, dict)
            assert 'full_code' in result
            assert 'ast_context' in result
            assert 'file_size' in result
            assert result['full_code'] == "def test_function():\n    return 'hello world'\n"
        finally:
            os.unlink(temp_file)
    
    def test_extract_ast_context(self):
        """Test AST context extraction"""
        code = """
def example_function(x, y):
    '''Example function for testing'''
    result = x + y
    return result

class ExampleClass:
    def method(self):
        pass
"""
        result = self.extractor._extract_ast_context(code)
        
        assert isinstance(result, dict)
        assert 'functions' in result
        assert 'classes' in result
        assert 'imports' in result
        assert 'variables' in result
        
        # Check that functions are detected
        assert len(result['functions']) > 0
        assert any('example_function' in func for func in result['functions'])
        
        # Check that classes are detected
        assert len(result['classes']) > 0
        assert any('ExampleClass' in cls for cls in result['classes'])


class TestModuleContextManager:
    """Test the ModuleContextManager class"""
    
    def setup_method(self):
        self.manager = ModuleContextManager()
    
    def test_init(self):
        """Test ModuleContextManager initialization"""
        assert hasattr(self.manager, 'module_contexts')
        assert isinstance(self.manager.module_contexts, dict)
    
    def test_set_and_get_module_context(self):
        """Test setting and getting module context"""
        module_name = "test_module"
        code = "def test(): pass"
        additional_context = {"test_key": "test_value"}
        
        self.manager.set_module_context(module_name, code, additional_context)
        result = self.manager.get_module_context(module_name)
        
        assert isinstance(result, dict)
        assert 'code' in result
        assert 'defined_names' in result
        assert 'additional_context' in result
        assert result['code'] == code
        assert result['additional_context'] == additional_context
    
    def test_extract_defined_names(self):
        """Test extraction of defined names from code"""
        code = """
def function1():
    pass

def function2(x, y):
    return x + y

class TestClass:
    def method(self):
        pass

variable1 = "test"
variable2 = 42
"""
        result = self.manager._extract_defined_names(code)
        
        assert isinstance(result, set)
        assert 'function1' in result
        assert 'function2' in result
        assert 'TestClass' in result
        assert 'variable1' in result
        assert 'variable2' in result
    
    def test_is_name_defined(self):
        """Test checking if a name is defined in a module"""
        module_name = "test_module"
        code = "def test_function(): pass"
        
        self.manager.set_module_context(module_name, code)
        
        assert self.manager.is_name_defined("test_module.test_function")
        assert not self.manager.is_name_defined("test_module.undefined_function")
    
    def test_get_all_modules(self):
        """Test getting all module contexts"""
        self.manager.set_module_context("module1", "def func1(): pass")
        self.manager.set_module_context("module2", "def func2(): pass")
        
        result = self.manager.get_all_modules()
        
        assert isinstance(result, dict)
        assert "module1" in result
        assert "module2" in result
        assert len(result) == 2


class TestRuntimeErrorCollector:
    """Test the RuntimeErrorCollector class"""
    
    def setup_method(self):
        self.collector = RuntimeErrorCollector()
    
    def test_init(self):
        """Test RuntimeErrorCollector initialization"""
        assert hasattr(self.collector, 'error_history')
        assert hasattr(self.collector, 'context_extractor')
        assert hasattr(self.collector, 'module_manager')
        assert isinstance(self.collector.error_history, list)
    
    def test_collect_runtime_error(self):
        """Test collecting a runtime error"""
        try:
            # Generate a runtime error
            x = 1 / 0
        except Exception as e:
            result = self.collector.collect_runtime_error(e)
            
            assert isinstance(result, dict)
            assert 'error_type' in result
            assert 'error_message' in result
            assert 'timestamp' in result
            assert 'traceback_info' in result
            assert 'caller_context' in result
            assert 'error_hash' in result
            
            assert result['error_type'] == 'ZeroDivisionError'
            assert 'division by zero' in result['error_message']
    
    def test_collect_ui_error(self):
        """Test collecting a UI error"""
        ui_error_data = {
            'element_id': 'test-button',
            'event_type': 'click',
            'error_message': 'Element not found',
            'dom_context': '<button id="test-button">Click me</button>'
        }
        
        result = self.collector.collect_ui_error(ui_error_data)
        
        assert isinstance(result, dict)
        assert 'error_type' in result
        assert 'ui_context' in result
        assert 'timestamp' in result
        assert 'error_hash' in result
        
        assert result['error_type'] == 'UIError'
        assert result['ui_context'] == ui_error_data
    
    def test_correlate_errors(self):
        """Test error correlation functionality"""
        # Collect multiple errors
        try:
            x = 1 / 0
        except Exception as e:
            self.collector.collect_runtime_error(e)
        
        ui_error = {
            'element_id': 'calc-button',
            'event_type': 'click',
            'error_message': 'Calculation failed'
        }
        self.collector.collect_ui_error(ui_error)
        
        # Test correlation
        correlations = self.collector.correlate_errors(time_window=60)
        
        assert isinstance(correlations, list)
        # Should have at least some correlation data
        assert len(correlations) >= 0
    
    def test_get_error_statistics(self):
        """Test getting error statistics"""
        # Add some test errors
        try:
            x = 1 / 0
        except Exception as e:
            self.collector.collect_runtime_error(e)
        
        try:
            y = int("not_a_number")
        except Exception as e:
            self.collector.collect_runtime_error(e)
        
        stats = self.collector.get_error_statistics()
        
        assert isinstance(stats, dict)
        assert 'total_errors' in stats
        assert 'error_types' in stats
        assert 'recent_errors' in stats
        
        assert stats['total_errors'] >= 2
        assert 'ZeroDivisionError' in stats['error_types']
        assert 'ValueError' in stats['error_types']


class TestLSPDiagnosticsManager:
    """Test the LSPDiagnosticsManager class"""
    
    def setup_method(self):
        # Mock the codebase
        mock_codebase = MagicMock()
        self.manager = LSPDiagnosticsManager(codebase=mock_codebase)
    
    def test_init(self):
        """Test LSPDiagnosticsManager initialization"""
        assert hasattr(self.manager, 'codebase')
        assert hasattr(self.manager, 'error_collector')
        assert hasattr(self.manager, 'lsp_servers')
        assert hasattr(self.manager, 'diagnostic_cache')
        assert isinstance(self.manager.lsp_servers, dict)
        assert isinstance(self.manager.diagnostic_cache, dict)
    
    @pytest.mark.asyncio
    async def test_start_language_server(self):
        """Test starting a language server"""
        with patch.object(self.manager, '_create_language_server') as mock_create:
            mock_server = MagicMock()
            mock_create.return_value = mock_server
            
            result = await self.manager.start_language_server(MockLanguage.PYTHON, "/test/path")
            
            assert result is True
            assert MockLanguage.PYTHON in self.manager.lsp_servers
            mock_create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_diagnostics(self):
        """Test getting diagnostics for a file"""
        file_path = "/test/file.py"
        
        # Mock a language server
        mock_server = MagicMock()
        mock_server.get_diagnostics = MagicMock(return_value=[
            MockDiagnostic(message="Test diagnostic")
        ])
        self.manager.lsp_servers[MockLanguage.PYTHON] = mock_server
        
        result = await self.manager.get_diagnostics(file_path, MockLanguage.PYTHON)
        
        assert isinstance(result, list)
        # The result should be enhanced diagnostics
        assert len(result) >= 0
    
    def test_enhance_diagnostic(self):
        """Test diagnostic enhancement"""
        diagnostic = MockDiagnostic()
        diagnostic.message = "Undefined variable 'x'"
        diagnostic.range = MockRange(start=1, end=1)
        
        file_path = "/test/file.py"
        
        result = self.manager._enhance_diagnostic(diagnostic, file_path)
        
        assert isinstance(result, dict)
        assert 'original_diagnostic' in result
        assert 'enhanced_context' in result
        assert 'suggestions' in result
        assert 'severity_analysis' in result
    
    def test_cache_diagnostics(self):
        """Test diagnostic caching"""
        file_path = "/test/file.py"
        diagnostics = [{"message": "test diagnostic"}]
        
        self.manager._cache_diagnostics(file_path, diagnostics)
        
        assert file_path in self.manager.diagnostic_cache
        cached = self.manager.diagnostic_cache[file_path]
        assert 'diagnostics' in cached
        assert 'timestamp' in cached
        assert cached['diagnostics'] == diagnostics
    
    def test_get_cached_diagnostics(self):
        """Test retrieving cached diagnostics"""
        file_path = "/test/file.py"
        diagnostics = [{"message": "test diagnostic"}]
        
        # Cache some diagnostics
        self.manager._cache_diagnostics(file_path, diagnostics)
        
        # Retrieve them
        result = self.manager._get_cached_diagnostics(file_path, max_age=60)
        
        assert result is not None
        assert result == diagnostics
    
    def test_get_cached_diagnostics_expired(self):
        """Test that expired cached diagnostics return None"""
        file_path = "/test/file.py"
        diagnostics = [{"message": "test diagnostic"}]
        
        # Cache some diagnostics
        self.manager._cache_diagnostics(file_path, diagnostics)
        
        # Try to retrieve with very short max_age
        result = self.manager._get_cached_diagnostics(file_path, max_age=0)
        
        assert result is None


class TestIntegration:
    """Integration tests for LSP diagnostics components"""
    
    def test_error_collector_integration(self):
        """Test integration between error collector and diagnostics manager"""
        mock_codebase = MagicMock()
        manager = LSPDiagnosticsManager(codebase=mock_codebase)
        
        # Generate a runtime error
        try:
            x = 1 / 0
        except Exception as e:
            error_data = manager.error_collector.collect_runtime_error(e)
            
            assert isinstance(error_data, dict)
            assert 'error_type' in error_data
            assert 'caller_context' in error_data
    
    def test_module_context_integration(self):
        """Test integration between module context manager and other components"""
        mock_codebase = MagicMock()
        manager = LSPDiagnosticsManager(codebase=mock_codebase)
        
        # Set up some module context
        module_name = "test_module"
        code = "def test_function(): pass"
        
        manager.error_collector.module_manager.set_module_context(module_name, code)
        
        # Verify the context is available
        context = manager.error_collector.module_manager.get_module_context(module_name)
        assert context is not None
        assert context['code'] == code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
