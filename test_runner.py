#!/usr/bin/env python3
"""
Simple test runner to validate the enhanced LSP diagnostics functionality.
"""

import sys
import os
import tempfile
from unittest.mock import Mock

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from codegen.sdk.codebase import Codebase
    from codegen.sdk.extensions.lsp.lsp_diagnostics import (
        LSPDiagnosticsManager,
        RuntimeErrorCollector,
        CallerContextExtractor,
        ModuleContextManager,
        EnhancedDiagnostic
    )
    from codegen.sdk.extensions.lsp.solid_lsp import Language
    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def test_caller_context_extractor():
    """Test CallerContextExtractor functionality."""
    print("\n🔍 Testing CallerContextExtractor...")
    
    try:
        extractor = CallerContextExtractor()
        caller_info = extractor.get_caller_info()
        
        assert isinstance(caller_info, dict), "caller_info should be a dict"
        assert "stack_trace" in caller_info, "Missing stack_trace"
        assert "caller_frame" in caller_info, "Missing caller_frame"
        assert "code_context" in caller_info, "Missing code_context"
        
        print("✅ CallerContextExtractor basic functionality works")
        return True
    except Exception as e:
        print(f"❌ CallerContextExtractor test failed: {e}")
        return False

def test_module_context_manager():
    """Test ModuleContextManager functionality."""
    print("\n🔍 Testing ModuleContextManager...")
    
    try:
        manager = ModuleContextManager()
        context = manager.get_module_context("test_file.py")
        
        assert isinstance(context, dict), "context should be a dict"
        assert "file_path" in context, "Missing file_path"
        assert "definitions" in context, "Missing definitions"
        assert "imports" in context, "Missing imports"
        
        print("✅ ModuleContextManager basic functionality works")
        return True
    except Exception as e:
        print(f"❌ ModuleContextManager test failed: {e}")
        return False

def test_runtime_error_collector():
    """Test RuntimeErrorCollector functionality."""
    print("\n🔍 Testing RuntimeErrorCollector...")
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            codebase = Mock(spec=Codebase)
            codebase.root = temp_dir
            collector = RuntimeErrorCollector(codebase)
            
            # Check that new attributes are present
            assert hasattr(collector, 'caller_extractor'), "Missing caller_extractor"
            assert hasattr(collector, 'module_manager'), "Missing module_manager"
            assert hasattr(collector, 'logger'), "Missing logger"
            
            assert isinstance(collector.caller_extractor, CallerContextExtractor)
            assert isinstance(collector.module_manager, ModuleContextManager)
            
            print("✅ RuntimeErrorCollector enhanced initialization works")
            return True
    except Exception as e:
        print(f"❌ RuntimeErrorCollector test failed: {e}")
        return False

def test_lsp_diagnostics_manager():
    """Test LSPDiagnosticsManager functionality."""
    print("\n🔍 Testing LSPDiagnosticsManager...")
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            codebase = Mock(spec=Codebase)
            codebase.root = temp_dir
            manager = LSPDiagnosticsManager(codebase=codebase, language=Language.PYTHON)
            
            # Check that new attributes are present
            assert hasattr(manager, 'caller_extractor'), "Missing caller_extractor"
            assert hasattr(manager, 'module_manager'), "Missing module_manager"
            
            assert isinstance(manager.caller_extractor, CallerContextExtractor)
            assert isinstance(manager.module_manager, ModuleContextManager)
            
            # Test error correlation analysis
            mock_diagnostic = Mock()
            mock_diagnostic.code = "E001"
            mock_diagnostic.message = "Test error message"
            mock_diagnostic.uri = "file:///test/file.py"
            mock_diagnostic.severity = 1
            
            runtime_errors = [{"error_type": "exception", "file_path": "/test/file.py"}]
            ui_errors = [{"error_type": "react_error", "file_path": "/test/component.jsx"}]
            
            correlation = manager._analyze_error_correlation(mock_diagnostic, runtime_errors, ui_errors)
            
            assert isinstance(correlation, dict), "correlation should be a dict"
            assert "error_patterns" in correlation, "Missing error_patterns"
            assert "cross_module_errors" in correlation, "Missing cross_module_errors"
            assert "frequency_analysis" in correlation, "Missing frequency_analysis"
            assert "severity_correlation" in correlation, "Missing severity_correlation"
            
            # Test correlation score calculation
            score = manager._calculate_correlation_score(mock_diagnostic, runtime_errors, ui_errors)
            assert isinstance(score, float), "score should be a float"
            assert 0.0 <= score <= 1.0, "score should be between 0.0 and 1.0"
            
            print("✅ LSPDiagnosticsManager enhanced functionality works")
            return True
    except Exception as e:
        print(f"❌ LSPDiagnosticsManager test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Starting Enhanced LSP Diagnostics Tests")
    print("=" * 50)
    
    tests = [
        test_caller_context_extractor,
        test_module_context_manager,
        test_runtime_error_collector,
        test_lsp_diagnostics_manager,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Enhanced LSP diagnostics system is working properly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
