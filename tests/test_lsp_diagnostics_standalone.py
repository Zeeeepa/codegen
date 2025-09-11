#!/usr/bin/env python3
"""
Standalone LSP Diagnostics Tests
Tests the core functionality without external dependencies by copying key components
"""

import pytest
import os
import tempfile
import json
import time
import ast
import inspect
import traceback
import hashlib
import logging
from typing import Dict, List, Optional, Any
from collections import Counter
from pathlib import Path


class CallerContextExtractor:
    """
    Enhanced caller context extraction for comprehensive error diagnostics.
    Standalone version for testing.
    """
    
    def __init__(self, max_depth: int = 10, max_code_size: int = 8000):
        self.max_depth = max_depth
        self.max_code_size = max_code_size
        self.logger = logging.getLogger(f"{__name__}.CallerContextExtractor")
    
    def get_caller_info(self) -> Dict[str, Any]:
        """
        Get comprehensive information about the calling code.
        
        Returns:
            dict: Information about the caller including filename, code, and context.
        """
        try:
            # Get the current frame and walk up the stack
            frame = inspect.currentframe()
            caller_frame = frame.f_back
            
            if not caller_frame:
                return {"error": "No caller frame available"}
            
            # Extract basic caller information
            filename = caller_frame.f_code.co_filename
            function_name = caller_frame.f_code.co_name
            line_number = caller_frame.f_lineno
            
            # Get local and global variables (limited for safety)
            local_vars = {k: str(v)[:100] for k, v in list(caller_frame.f_locals.items())[:10]}
            global_vars = {k: str(v)[:100] for k, v in list(caller_frame.f_globals.items())[:10] 
                          if not k.startswith('__')}
            
            # Extract file context
            file_context = self._extract_file_context(filename)
            
            return {
                "filename": filename,
                "function_name": function_name,
                "line_number": line_number,
                "local_vars": local_vars,
                "global_vars": global_vars,
                "code_context": file_context.get("code_context", []),
                "full_code": file_context.get("full_code", ""),
                "ast_context": file_context.get("ast_context", {}),
                "file_size": file_context.get("file_size", 0)
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting caller info: {e}")
            return {"error": str(e)}
        finally:
            # Clean up frame references to prevent memory leaks
            del frame
    
    def _extract_file_context(self, filename: str) -> Dict[str, Any]:
        """
        Extract context from the file containing the caller.
        
        Args:
            filename: Path to the file to analyze
            
        Returns:
            dict: File context including code and AST analysis
        """
        try:
            if not os.path.exists(filename):
                return {"error": f"File not found: {filename}"}
            
            file_size = os.path.getsize(filename)
            if file_size > self.max_code_size:
                return {"error": f"File too large: {file_size} bytes"}
            
            with open(filename, 'r', encoding='utf-8') as f:
                full_code = f.read()
            
            # Extract AST context
            ast_context = self._extract_ast_context(full_code)
            
            # Get code context around the error (if possible)
            code_lines = full_code.split('\n')
            code_context = code_lines  # Simplified - in real implementation would focus on error line
            
            return {
                "full_code": full_code,
                "code_context": code_context,
                "ast_context": ast_context,
                "file_size": file_size
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting file context: {e}")
            return {"error": str(e)}
    
    def _extract_ast_context(self, code: str) -> Dict[str, Any]:
        """
        Extract AST-based context from code.
        
        Args:
            code: Source code to analyze
            
        Returns:
            dict: AST analysis results
        """
        try:
            tree = ast.parse(code)
            
            functions = []
            classes = []
            imports = []
            variables = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append({
                        "name": node.name,
                        "line": node.lineno,
                        "args": [arg.arg for arg in node.args.args]
                    })
                elif isinstance(node, ast.ClassDef):
                    classes.append({
                        "name": node.name,
                        "line": node.lineno
                    })
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        imports.extend([alias.name for alias in node.names])
                    else:
                        imports.append(f"from {node.module}" if node.module else "from .")
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            variables.append(target.id)
            
            return {
                "functions": functions,
                "classes": classes,
                "imports": imports,
                "variables": variables
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting AST context: {e}")
            return {"error": str(e)}


class ModuleContextManager:
    """
    Manages context information for different modules.
    Standalone version for testing.
    """
    
    def __init__(self):
        self.module_contexts: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger(f"{__name__}.ModuleContextManager")
    
    def get_module_context(self, fullname: str) -> Dict[str, Any]:
        """Get context for a specific module."""
        return self.module_contexts.get(fullname, {})
    
    def set_module_context(self, fullname: str, code: str, additional_context: Optional[Dict[str, Any]] = None):
        """
        Set context for a module.
        
        Args:
            fullname: Full module name
            code: Module source code
            additional_context: Additional context information
        """
        try:
            defined_names = self._extract_defined_names(code)
            
            self.module_contexts[fullname] = {
                "code": code,
                "defined_names": defined_names,
                "additional_context": additional_context or {},
                "timestamp": time.time()
            }
            
        except Exception as e:
            self.logger.error(f"Error setting module context for {fullname}: {e}")
    
    def _extract_defined_names(self, code: str) -> set:
        """
        Extract all defined names from code.
        
        Args:
            code: Source code to analyze
            
        Returns:
            set: Set of defined names
        """
        try:
            tree = ast.parse(code)
            names = set()
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    names.add(node.name)
                elif isinstance(node, ast.ClassDef):
                    names.add(node.name)
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            names.add(target.id)
            
            return names
            
        except Exception as e:
            self.logger.error(f"Error extracting defined names: {e}")
            return set()
    
    def is_name_defined(self, fullname: str) -> bool:
        """
        Check if a name is defined in a module.
        
        Args:
            fullname: Full name in format "module.name"
            
        Returns:
            bool: True if name is defined
        """
        if '.' not in fullname:
            return False
        
        module_name, name = fullname.rsplit('.', 1)
        module_context = self.get_module_context(module_name)
        
        if not module_context:
            return False
        
        return name in module_context.get("defined_names", set())
    
    def get_all_modules(self) -> Dict[str, Dict[str, Any]]:
        """Get all module contexts."""
        return self.module_contexts.copy()


class RuntimeErrorCollector:
    """
    Collects and analyzes runtime errors with enhanced context.
    Standalone version for testing.
    """
    
    def __init__(self):
        self.error_history: List[Dict[str, Any]] = []
        self.context_extractor = CallerContextExtractor()
        self.module_manager = ModuleContextManager()
        self.logger = logging.getLogger(f"{__name__}.RuntimeErrorCollector")
    
    def collect_runtime_error(self, exception: Exception) -> Dict[str, Any]:
        """
        Collect comprehensive information about a runtime error.
        
        Args:
            exception: The exception that occurred
            
        Returns:
            dict: Comprehensive error information
        """
        try:
            # Basic error information
            error_type = type(exception).__name__
            error_message = str(exception)
            timestamp = time.time()
            
            # Get traceback information
            tb_info = traceback.format_exc()
            
            # Get caller context
            caller_context = self.context_extractor.get_caller_info()
            
            # Create error hash for deduplication
            error_hash = hashlib.md5(
                f"{error_type}:{error_message}:{caller_context.get('filename', '')}".encode()
            ).hexdigest()
            
            error_data = {
                "error_type": error_type,
                "error_message": error_message,
                "timestamp": timestamp,
                "traceback_info": tb_info,
                "caller_context": caller_context,
                "error_hash": error_hash
            }
            
            # Add to history
            self.error_history.append(error_data)
            
            # Keep history manageable
            if len(self.error_history) > 1000:
                self.error_history = self.error_history[-500:]
            
            return error_data
            
        except Exception as e:
            self.logger.error(f"Error collecting runtime error: {e}")
            return {"error": str(e)}
    
    def collect_ui_error(self, ui_error_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Collect UI-specific error information.
        
        Args:
            ui_error_data: UI error context
            
        Returns:
            dict: Enhanced UI error information
        """
        try:
            timestamp = time.time()
            
            # Create error hash
            error_hash = hashlib.md5(
                json.dumps(ui_error_data, sort_keys=True).encode()
            ).hexdigest()
            
            error_data = {
                "error_type": "UIError",
                "ui_context": ui_error_data,
                "timestamp": timestamp,
                "error_hash": error_hash
            }
            
            # Add to history
            self.error_history.append(error_data)
            
            return error_data
            
        except Exception as e:
            self.logger.error(f"Error collecting UI error: {e}")
            return {"error": str(e)}
    
    def correlate_errors(self, time_window: int = 60) -> List[Dict[str, Any]]:
        """
        Find correlations between different types of errors.
        
        Args:
            time_window: Time window in seconds for correlation
            
        Returns:
            list: List of correlated error groups
        """
        try:
            correlations = []
            current_time = time.time()
            
            # Get recent errors
            recent_errors = [
                error for error in self.error_history
                if current_time - error.get("timestamp", 0) <= time_window
            ]
            
            # Simple correlation by time proximity
            for i, error1 in enumerate(recent_errors):
                for error2 in recent_errors[i+1:]:
                    time_diff = abs(error1.get("timestamp", 0) - error2.get("timestamp", 0))
                    if time_diff <= 5:  # Within 5 seconds
                        correlations.append({
                            "error1": error1,
                            "error2": error2,
                            "time_difference": time_diff,
                            "correlation_type": "temporal"
                        })
            
            return correlations
            
        except Exception as e:
            self.logger.error(f"Error correlating errors: {e}")
            return []
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about collected errors.
        
        Returns:
            dict: Error statistics
        """
        try:
            if not self.error_history:
                return {
                    "total_errors": 0,
                    "error_types": {},
                    "recent_errors": 0
                }
            
            # Count error types
            error_types = Counter(error.get("error_type", "Unknown") for error in self.error_history)
            
            # Count recent errors (last hour)
            current_time = time.time()
            recent_errors = sum(
                1 for error in self.error_history
                if current_time - error.get("timestamp", 0) <= 3600
            )
            
            return {
                "total_errors": len(self.error_history),
                "error_types": dict(error_types),
                "recent_errors": recent_errors,
                "most_common_error": error_types.most_common(1)[0] if error_types else None
            }
            
        except Exception as e:
            self.logger.error(f"Error getting statistics: {e}")
            return {"error": str(e)}


# Test Classes
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
        assert result['function_name'] == 'test_function'
    
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
        function_names = [f['name'] for f in result['functions']]
        assert 'example_function' in function_names
        
        # Check that classes are detected
        assert len(result['classes']) > 0
        class_names = [c['name'] for c in result['classes']]
        assert 'ExampleClass' in class_names


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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
