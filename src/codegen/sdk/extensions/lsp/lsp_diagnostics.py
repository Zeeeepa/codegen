#!/usr/bin/env python3
"""
Enhanced LSP Diagnostics Manager with Runtime Error Collection
Integrates with Graph-Sitter and AutoGenLib for comprehensive error context
"""

import os
import logging
import asyncio
import json
import re
import time
from typing import Dict, List, Optional, TypedDict, Any
from pathlib import Path
from collections import Counter
import inspect
import traceback
import hashlib
import ast

from solidlsp.ls import SolidLanguageServer
from solidlsp.ls_config import Language, LanguageServerConfig
from solidlsp.ls_logger import LanguageServerLogger
from solidlsp.lsp_protocol_handler.lsp_types import Diagnostic, DocumentUri, Range
from solidlsp.ls_utils import PathUtils

# Import GraphSitterAnalyzer for context enrichment
from graph_sitter import Codebase

logger = logging.getLogger(__name__)


class CallerContextExtractor:
    """
    Enhanced caller context extraction for comprehensive error diagnostics.
    Based on autogenlib's caller context extraction with improvements for LSP diagnostics.
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
            # Get the current stack frames
            stack = inspect.stack()
            
            # Debug stack information
            self.logger.debug(f"Stack depth: {len(stack)}")
            for i, frame_info in enumerate(stack[:self.max_depth]):
                filename = frame_info.filename
                lineno = frame_info.lineno
                function = frame_info.function
                self.logger.debug(f"Frame {i}: {filename}:{lineno} in {function}")
            
            # Find the first frame that's not from internal modules and is a real file
            caller_frame = None
            caller_filename = None
            
            for i, frame_info in enumerate(stack[1:self.max_depth]):  # Skip the first frame (our function)
                filename = frame_info.filename
                
                # Skip if it's internal to Python
                if filename.startswith("<") or not os.path.exists(filename):
                    continue
                
                # Skip if it's within our package (but allow _caller.py for testing)
                if ("lsp_diagnostics" in filename or "solidlsp" in filename) and "_caller.py" not in filename:
                    continue
                
                # We found a suitable caller
                caller_frame = frame_info.frame
                caller_filename = filename
                self.logger.debug(f"Found caller at frame {i + 1}: {filename}")
                break
            
            if not caller_filename:
                # Try a different approach - look for an importing file
                for i, frame_info in enumerate(stack[1:self.max_depth]):
                    filename = frame_info.filename
                    
                    # Skip non-file frames
                    if filename.startswith("<") or not os.path.exists(filename):
                        continue
                    
                    # Check if this frame is doing an import or is at module level
                    if (frame_info.function == "<module>" or 
                        (frame_info.code_context and 
                         any("import" in line.lower() for line in frame_info.code_context))):
                        caller_frame = frame_info.frame
                        caller_filename = filename
                        self.logger.debug(f"Found importing caller at frame {i + 1}: {filename}")
                        break
            
            # If we still didn't find a caller, use a simpler approach
            if not caller_filename:
                # Just use the top-level script
                for frame_info in reversed(stack[:self.max_depth]):
                    filename = frame_info.filename
                    if os.path.exists(filename) and not filename.startswith("<"):
                        caller_filename = filename
                        self.logger.debug(f"Using top-level script as caller: {filename}")
                        break
            
            if not caller_filename:
                self.logger.debug("No suitable caller file found")
                return {"code": "", "filename": "", "context": {}}
            
            # Read the file content and extract context
            return self._extract_file_context(caller_filename)
            
        except Exception as e:
            self.logger.debug(f"Error getting caller info: {e}")
            self.logger.debug(traceback.format_exc())
            return {"code": "", "filename": "", "context": {}}
    
    def _extract_file_context(self, filename: str) -> Dict[str, Any]:
        """Extract comprehensive context from a file."""
        try:
            with open(filename, "r", encoding="utf-8") as f:
                code = f.read()
            
            # Get the relative path to make logs cleaner
            try:
                rel_path = Path(filename).relative_to(Path.cwd())
                display_filename = str(rel_path)
            except ValueError:
                display_filename = filename
            
            # Extract AST-based context
            ast_context = self._extract_ast_context(code)
            
            # Limit code size if it's too large to avoid excessive prompt size
            if len(code) > self.max_code_size:
                self.logger.debug(
                    f"Truncating large caller file ({len(code)} chars) to {self.max_code_size} chars"
                )
                # Try to find a good place to cut (newline)
                cut_point = code[:self.max_code_size].rfind("\n")
                if cut_point == -1:
                    cut_point = self.max_code_size
                code = code[:cut_point] + "\n\n# ... [file truncated due to size] ..."
            
            self.logger.debug(
                f"Successfully extracted caller code from {display_filename} ({len(code)} chars)"
            )
            
            return {
                "code": code,
                "filename": display_filename,
                "full_path": filename,
                "context": ast_context,
                "file_hash": hashlib.md5(code.encode()).hexdigest()
            }
            
        except Exception as e:
            self.logger.debug(f"Error reading caller file {filename}: {e}")
            return {
                "code": "", 
                "filename": filename, 
                "full_path": filename,
                "context": {},
                "file_hash": ""
            }
    
    def _extract_ast_context(self, code: str) -> Dict[str, Any]:
        """Extract context information using AST parsing."""
        try:
            tree = ast.parse(code)
            context = {
                "functions": [],
                "classes": [],
                "variables": [],
                "imports": [],
                "defined_names": set()
            }
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_info = {
                        "name": node.name,
                        "line": node.lineno,
                        "args": [arg.arg for arg in node.args.args],
                        "decorators": [ast.unparse(dec) for dec in node.decorator_list] if hasattr(ast, 'unparse') else []
                    }
                    context["functions"].append(func_info)
                    context["defined_names"].add(node.name)
                    
                elif isinstance(node, ast.ClassDef):
                    class_info = {
                        "name": node.name,
                        "line": node.lineno,
                        "bases": [ast.unparse(base) for base in node.bases] if hasattr(ast, 'unparse') else [],
                        "methods": []
                    }
                    
                    # Extract methods
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            class_info["methods"].append({
                                "name": item.name,
                                "line": item.lineno
                            })
                    
                    context["classes"].append(class_info)
                    context["defined_names"].add(node.name)
                    
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            context["variables"].append({
                                "name": target.id,
                                "line": node.lineno
                            })
                            context["defined_names"].add(target.id)
                            
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            context["imports"].append({
                                "module": alias.name,
                                "alias": alias.asname,
                                "line": node.lineno,
                                "type": "import"
                            })
                    else:  # ImportFrom
                        for alias in node.names:
                            context["imports"].append({
                                "module": node.module,
                                "name": alias.name,
                                "alias": alias.asname,
                                "line": node.lineno,
                                "type": "from_import"
                            })
            
            # Convert set to list for JSON serialization
            context["defined_names"] = list(context["defined_names"])
            
            return context
            
        except SyntaxError as e:
            self.logger.debug(f"Syntax error parsing code: {e}")
            return {"error": f"Syntax error: {e}"}
        except Exception as e:
            self.logger.debug(f"Error extracting AST context: {e}")
            return {"error": f"AST extraction error: {e}"}


class ModuleContextManager:
    """
    Manages context for modules and tracks their state.
    Based on autogenlib's context management with enhancements for LSP diagnostics.
    """
    
    def __init__(self):
        self.module_contexts = {}
        self.logger = logging.getLogger(f"{__name__}.ModuleContextManager")
    
    def get_module_context(self, fullname: str) -> Dict[str, Any]:
        """Get the context of a module."""
        return self.module_contexts.get(fullname, {})
    
    def set_module_context(self, fullname: str, code: str, additional_context: Optional[Dict[str, Any]] = None):
        """Update the context of a module."""
        context = {
            "code": code,
            "defined_names": self._extract_defined_names(code),
            "last_updated": time.time(),
            "code_hash": hashlib.md5(code.encode()).hexdigest()
        }
        
        if additional_context:
            context.update(additional_context)
        
        self.module_contexts[fullname] = context
        self.logger.debug(f"Updated context for module {fullname}")
    
    def _extract_defined_names(self, code: str) -> set:
        """Extract all defined names (functions, classes, variables) from the code."""
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
        except SyntaxError:
            return set()
    
    def is_name_defined(self, fullname: str) -> bool:
        """Check if a name is defined in its module."""
        if "." not in fullname:
            return False
        
        module_path, name = fullname.rsplit(".", 1)
        context = self.get_module_context(module_path)
        
        if not context:
            # Module doesn't exist yet
            return False
        
        return name in context.get("defined_names", set())
    
    def get_all_modules(self) -> Dict[str, Dict[str, Any]]:
        """Get all cached modules."""
        return self.module_contexts.copy()
    
    def clear_module_context(self, fullname: str):
        """Clear the context for a specific module."""
        if fullname in self.module_contexts:
            del self.module_contexts[fullname]
            self.logger.debug(f"Cleared context for module {fullname}")
    
    def clear_all_contexts(self):
        """Clear all module contexts."""
        self.module_contexts.clear()
        self.logger.debug("Cleared all module contexts")

class EnhancedDiagnostic(TypedDict):
    """
    A diagnostic with comprehensive context for AI resolution.
    """
    diagnostic: Diagnostic
    file_content: str
    relevant_code_snippet: str
    file_path: str # Absolute path to the file
    relative_file_path: str # Path relative to codebase root
    
    # Enhanced context fields
    graph_sitter_context: Dict[str, Any]
    autogenlib_context: Dict[str, Any]
    runtime_context: Dict[str, Any]
    ui_interaction_context: Dict[str, Any]
    
    # New enhanced context fields from autogenlib integration
    caller_context: Dict[str, Any]  # Caller code context and AST analysis
    module_context: Dict[str, Any]  # Module-level context and definitions
    error_correlation: Dict[str, Any]  # Error correlation and pattern analysis

class RuntimeErrorCollector:
    """Collects runtime errors from various sources."""
    
    def __init__(self, codebase: Codebase):
        self.codebase = codebase
        self.runtime_errors = []
        self.ui_errors = []
        self.error_patterns = {}
        self.caller_extractor = CallerContextExtractor()
        self.module_manager = ModuleContextManager()
        self.logger = logging.getLogger(f"{__name__}.RuntimeErrorCollector")
        
    def collect_python_runtime_errors(self, log_file_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """Collect Python runtime errors from logs or exception handlers."""
        runtime_errors = []
        
        # If log file is provided, parse it for errors
        if log_file_path and os.path.exists(log_file_path):
            try:
                with open(log_file_path, 'r') as f:
                    log_content = f.read()
                    
                # Parse Python tracebacks
                traceback_pattern = r'Traceback \(most recent call last\):(.*?)(?=\n\w|\nTraceback|\Z)'
                tracebacks = re.findall(traceback_pattern, log_content, re.DOTALL)
                
                for traceback in tracebacks:
                    # Extract file, line, and error info
                    file_pattern = r'File "([^"]+)", line (\d+), in (\w+)'
                    error_pattern = r'(\w+Error): (.+)'
                    
                    file_matches = re.findall(file_pattern, traceback)
                    error_matches = re.findall(error_pattern, traceback)
                    
                    if file_matches and error_matches:
                        file_path, line_num, function_name = file_matches[-1]  # Last frame
                        error_type, error_message = error_matches[-1]
                        
                        runtime_errors.append({
                            "type": "runtime_error",
                            "error_type": error_type,
                            "message": error_message,
                            "file_path": file_path,
                            "line": int(line_num),
                            "function": function_name,
                            "traceback": traceback.strip(),
                            "severity": "critical",
                            "timestamp": time.time()
                        })
                        
            except Exception as e:
                logger.warning(f"Error parsing log file {log_file_path}: {e}")
        
        # Collect from in-memory exception handlers if available
        # This would require integration with the target application's exception handling
        runtime_errors.extend(self._collect_in_memory_errors())
        
        return runtime_errors
    
    def collect_ui_interaction_errors(self, ui_log_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """Collect UI interaction errors from frontend logs or error boundaries."""
        ui_errors = []
        
        # Parse JavaScript/TypeScript errors from UI logs
        if ui_log_path and os.path.exists(ui_log_path):
            try:
                with open(ui_log_path, 'r') as f:
                    log_content = f.read()
                    
                # Parse JavaScript errors
                js_error_pattern = r'(TypeError|ReferenceError|SyntaxError): (.+?) at (.+?):(\d+):(\d+)'
                js_errors = re.findall(js_error_pattern, log_content)
                
                for error_type, message, file_path, line, column in js_errors:
                    ui_errors.append({
                        "type": "ui_error",
                        "error_type": error_type,
                        "message": message,
                        "file_path": file_path,
                        "line": int(line),
                        "column": int(column),
                        "severity": "major",
                        "timestamp": time.time()
                    })
                    
                # Parse React component errors
                react_error_pattern = r'Error: (.+?) in (\w+) \(at (.+?):(\d+):(\d+)\)'
                react_errors = re.findall(react_error_pattern, log_content)
                
                for message, component, file_path, line, column in react_errors:
                    ui_errors.append({
                        "type": "react_error",
                        "error_type": "ComponentError",
                        "message": message,
                        "component": component,
                        "file_path": file_path,
                        "line": int(line),
                        "column": int(column),
                        "severity": "major",
                        "timestamp": time.time()
                    })
                    
                # Parse console errors
                console_error_pattern = r'console\.error: (.+)'
                console_errors = re.findall(console_error_pattern, log_content)
                
                for error_message in console_errors:
                    ui_errors.append({
                        "type": "console_error",
                        "error_type": "ConsoleError",
                        "message": error_message,
                        "severity": "minor",
                        "timestamp": time.time()
                    })
                    
            except Exception as e:
                logger.warning(f"Error parsing UI log file {ui_log_path}: {e}")
        
        # Collect from browser console if available
        ui_errors.extend(self._collect_browser_console_errors())
        
        return ui_errors

    def collect_network_errors(self) -> List[Dict[str, Any]]:
        """Collect network-related errors."""
        network_errors = []
        
        # Look for network error patterns in code
        for file_obj in self.codebase.files:
            if hasattr(file_obj, "source") and file_obj.source:
                # Find fetch/axios/request patterns
                network_patterns = [
                    r'fetch\(["\']([^"\']+)["\']',
                    r'axios\.(get|post|put|delete)\(["\']([^"\']+)["\']',
                    r'requests\.(get|post|put|delete)\(["\']([^"\']+)["\']'
                ]
                
                for pattern in network_patterns:
                    matches = re.findall(pattern, file_obj.source)
                    for match in matches:
                        network_errors.append({
                            "type": "network_call",
                            "file_path": file_obj.filepath,
                            "endpoint": match[1] if isinstance(match, tuple) else match,
                            "method": match[0] if isinstance(match, tuple) else "unknown",
                            "potential_failure_point": True
                        })
        
        return network_errors

    def _collect_in_memory_errors(self) -> List[Dict[str, Any]]:
        """Collect runtime errors from in-memory exception handlers."""
        # This would integrate with the application's exception handling system
        # For now, return empty list as this requires application-specific integration
        return []

    def _collect_browser_console_errors(self) -> List[Dict[str, Any]]:
        """Collect errors from browser console."""
        # This would require browser automation or console API integration
        # For now, return empty list as this requires browser-specific integration
        return []

class LSPDiagnosticsManager:
    """
    Enhanced LSP server lifecycle and diagnostic retrieval with comprehensive context enrichment.
    """
    def __init__(self, codebase: Codebase, language: Language, log_level=logging.INFO):
        self.codebase = codebase
        self.language = language
        self.logger = LanguageServerLogger(log_level=log_level)
        self.lsp_server: Optional[SolidLanguageServer] = None
        self.repository_root_path = codebase.root # Use codebase root
        self.runtime_collector = RuntimeErrorCollector(codebase)
        
        # Enhanced error tracking
        self.error_history = []
        self.error_frequency = {}
        self.resolution_attempts = {}
        
        # Enhanced context extraction
        self.caller_extractor = CallerContextExtractor()
        self.module_manager = ModuleContextManager()

    def start_server(self) -> None:
        """Starts the LSP server and initializes it."""
        if self.lsp_server is None:
            self.lsp_server = SolidLanguageServer.create(
                language=self.language,
                logger=self.logger,
                repository_root_path=self.repository_root_path,
                config=LanguageServerConfig(code_language=self.language, trace_lsp_communication=False)
            )
        self.logger.log(f"Starting LSP server for {self.language.value} at {self.repository_root_path}", logging.INFO)
        self.lsp_server.start()
        self.logger.log("LSP server started.", logging.INFO)

    def open_file(self, relative_file_path: str, content: str) -> None:
        """Notifies the LSP server that a file has been opened."""
        if self.lsp_server:
            self.lsp_server.open_file(relative_file_path, content)
        else:
            self.logger.log("LSP server not started. Cannot open file.", logging.WARNING)

    def change_file(self, relative_file_path: str, content: str) -> None:
        """Notifies the LSP server that a file has been changed."""
        if self.lsp_server:
            self.lsp_server.change_file(relative_file_path, content)
        else:
            self.logger.log("LSP server not started. Cannot change file.", logging.WARNING)

    def get_diagnostics(self, relative_file_path: str) -> List[Diagnostic]:
        """Retrieves diagnostics for a specific file."""
        if self.lsp_server:
            uri = PathUtils.path_to_uri(os.path.join(self.repository_root_path, relative_file_path))
            return self.lsp_server.get_diagnostics_for_uri(uri)
        else:
            self.logger.log("LSP server not started. Cannot get diagnostics.", logging.WARNING)
            return []

    def get_all_enhanced_diagnostics(self, 
                                   runtime_log_path: Optional[str] = None,
                                   ui_log_path: Optional[str] = None) -> List[EnhancedDiagnostic]:
        """
        Retrieves all collected diagnostics from the LSP server, enriched with comprehensive context.
        """
        if not self.lsp_server:
            self.logger.log("LSP server not started. No enhanced diagnostics available.", logging.WARNING)
            return []

        all_raw_diagnostics = self.lsp_server.get_all_diagnostics()
        enhanced_diagnostics: List[EnhancedDiagnostic] = []

        # Collect runtime errors
        runtime_errors = self.runtime_collector.collect_python_runtime_errors(runtime_log_path)
        ui_errors = self.runtime_collector.collect_ui_interaction_errors(ui_log_path)
        network_errors = self.runtime_collector.collect_network_errors()

        # Import autogenlib_context here to avoid circular dependency at module level
        from autogenlib_context import get_ai_fix_context

        for uri, diagnostics_list in all_raw_diagnostics.items():
            file_path = PathUtils.uri_to_path(uri)
            relative_file_path = os.path.relpath(file_path, self.repository_root_path)
            
            try:
                file_content = self.codebase.get_file(relative_file_path).content
            except ValueError:
                logger.warning(f"File {relative_file_path} not found in codebase. Skipping diagnostics for this file.")
                continue

            for diag in diagnostics_list:
                relevant_code = self._get_relevant_code_for_diagnostic(file_content, diag.range)
                
                # Find related runtime errors for this file/line
                related_runtime_errors = [
                    err for err in runtime_errors 
                    if err["file_path"].endswith(relative_file_path) and 
                    abs(err["line"] - (diag.range.line + 1)) <= 2  # Within 2 lines
                ]
                
                # Find related UI errors
                related_ui_errors = [
                    err for err in ui_errors 
                    if err["file_path"].endswith(relative_file_path) and 
                    abs(err["line"] - (diag.range.line + 1)) <= 2  # Within 2 lines
                ]
                
                # Find related network errors
                related_network_errors = [
                    err for err in network_errors
                    if err["file_path"] == relative_file_path
                ]
                
                # Track error frequency
                error_key = f"{diag.code}:{relative_file_path}:{diag.range.line}"
                self.error_frequency[error_key] = self.error_frequency.get(error_key, 0) + 1
                
                # Extract enhanced context using autogenlib-inspired techniques
                caller_context = self.caller_extractor.get_caller_info()
                module_context = self.module_manager.get_module_context(relative_file_path)
                
                # Analyze error correlation and patterns
                error_correlation = self._analyze_error_correlation(diag, related_runtime_errors, related_ui_errors)
                
                # Create a partial EnhancedDiagnostic
                partial_enhanced_diag: EnhancedDiagnostic = {
                    "diagnostic": diag,
                    "file_content": file_content,
                    "relevant_code_snippet": relevant_code,
                    "file_path": file_path,
                    "relative_file_path": relative_file_path,
                    "graph_sitter_context": {}, # Will be filled by get_ai_fix_context
                    "autogenlib_context": {},   # Will be filled by get_ai_fix_context
                    "runtime_context": {
                        "related_runtime_errors": related_runtime_errors,
                        "error_frequency": self.error_frequency.get(error_key, 0),
                        "last_runtime_error": related_runtime_errors[-1] if related_runtime_errors else None,
                        "network_errors": related_network_errors,
                        "error_history": self._get_error_history(error_key)
                    },
                    "ui_interaction_context": {
                        "related_ui_errors": related_ui_errors,
                        "ui_error_frequency": len(related_ui_errors),
                        "last_ui_error": related_ui_errors[-1] if related_ui_errors else None,
                        "component_errors": self._extract_component_errors(related_ui_errors)
                    },
                    "caller_context": caller_context,
                    "module_context": module_context,
                    "error_correlation": error_correlation
                }
                
                # Get the full enhanced context using autogenlib_context
                full_enhanced_diag = get_ai_fix_context(partial_enhanced_diag, self.codebase)
                enhanced_diagnostics.append(full_enhanced_diag)
                
                # Store in error history
                self.error_history.append({
                    "timestamp": time.time(),
                    "diagnostic": diag,
                    "file": relative_file_path,
                    "resolved": False
                })

        return enhanced_diagnostics

    def _get_relevant_code_for_diagnostic(self, file_content: str, diagnostic_range: Range, context_lines: int = 5) -> str:
        """
        Extracts the code snippet directly related to the diagnostic, plus surrounding context.
        """
        lines = file_content.splitlines()

        start_line = max(0, diagnostic_range.line - context_lines)
        end_line = min(len(lines), diagnostic_range.end.line + context_lines + 1) # +1 to include the end line

        snippet_lines = lines[start_line:end_line]

        # Simple highlighting: add markers around the problematic line
        if diagnostic_range.line >= start_line and diagnostic_range.line < end_line:
            line_in_snippet_index = diagnostic_range.line - start_line
            original_line = snippet_lines[line_in_snippet_index]
            
            # Attempt to highlight the exact character range if it's within the same line
            if diagnostic_range.line == diagnostic_range.end.line:
                char_start = diagnostic_range.character
                char_end = diagnostic_range.end.character
                highlighted_segment = original_line[char_start:char_end]
                
                # Avoid empty highlights or out-of-bounds access
                if highlighted_segment:
                    highlighted_line = (
                        original_line[:char_start] +
                        "**>>>" + highlighted_segment + "<<<**" +
                        original_line[char_end:]
                    )
                    snippet_lines[line_in_snippet_index] = highlighted_line
                else:
                    snippet_lines[line_in_snippet_index] = ">>> " + original_line + " <<<"
            else:
                # For multi-line diagnostics, just mark the start line
                snippet_lines[line_in_snippet_index] = ">>> " + original_line + " <<<"

        return "\n".join(snippet_lines)

    def _get_error_history(self, error_key: str) -> List[Dict[str, Any]]:
        """Get historical data for a specific error."""
        return [
            entry for entry in self.error_history 
            if f"{entry['diagnostic'].code}:{entry['file']}:{entry['diagnostic'].range.line}" == error_key
        ]

    def _extract_component_errors(self, ui_errors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract component-specific error information."""
        component_errors = []
        for error in ui_errors:
            if error.get("type") == "react_error":
                component_errors.append({
                    "component": error.get("component"),
                    "error_type": error.get("error_type"),
                    "message": error.get("message"),
                    "frequency": 1  # Could be enhanced with actual frequency tracking
                })
        return component_errors

    def _analyze_error_correlation(self, diagnostic, runtime_errors: List[Dict[str, Any]], ui_errors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze error correlation and patterns using enhanced context."""
        correlation_data = {
            "error_patterns": {},
            "cross_module_errors": [],
            "frequency_analysis": {},
            "temporal_patterns": {},
            "severity_correlation": {}
        }
        
        try:
            # Analyze error patterns
            error_signature = f"{diagnostic.code}:{diagnostic.message[:50]}"
            correlation_data["error_patterns"][error_signature] = {
                "count": self.error_frequency.get(error_signature, 0),
                "related_runtime_count": len(runtime_errors),
                "related_ui_count": len(ui_errors)
            }
            
            # Cross-module error analysis
            current_module = diagnostic.uri.split('/')[-1] if hasattr(diagnostic, 'uri') else "unknown"
            for runtime_error in runtime_errors:
                error_module = runtime_error.get("file_path", "").split('/')[-1]
                if error_module != current_module:
                    correlation_data["cross_module_errors"].append({
                        "source_module": current_module,
                        "error_module": error_module,
                        "error_type": runtime_error.get("error_type", "unknown")
                    })
            
            # Frequency analysis
            error_types = [err.get("error_type", "unknown") for err in runtime_errors + ui_errors]
            correlation_data["frequency_analysis"] = dict(Counter(error_types))
            
            # Severity correlation
            if hasattr(diagnostic, 'severity'):
                correlation_data["severity_correlation"] = {
                    "diagnostic_severity": diagnostic.severity,
                    "runtime_error_count": len(runtime_errors),
                    "ui_error_count": len(ui_errors),
                    "correlation_score": self._calculate_correlation_score(diagnostic, runtime_errors, ui_errors)
                }
                
        except Exception as e:
            self.logger.warning(f"Error analyzing error correlation: {e}")
            correlation_data["analysis_error"] = str(e)
            
        return correlation_data
    
    def _calculate_correlation_score(self, diagnostic, runtime_errors: List[Dict[str, Any]], ui_errors: List[Dict[str, Any]]) -> float:
        """Calculate a correlation score between diagnostic and runtime/UI errors."""
        try:
            # Simple correlation scoring based on proximity and frequency
            score = 0.0
            
            # Base score for having related errors
            if runtime_errors:
                score += 0.3
            if ui_errors:
                score += 0.2
                
            # Boost score for high frequency errors
            total_errors = len(runtime_errors) + len(ui_errors)
            if total_errors > 5:
                score += 0.3
            elif total_errors > 2:
                score += 0.2
                
            # Boost score for severity alignment
            if hasattr(diagnostic, 'severity') and diagnostic.severity <= 2:  # Error or Warning
                if any(err.get("error_type") == "exception" for err in runtime_errors):
                    score += 0.2
                    
            return min(score, 1.0)  # Cap at 1.0
        except Exception:
            return 0.0

    def collect_runtime_diagnostics(self, 
                                  runtime_log_path: Optional[str] = None,
                                  ui_log_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """Collect runtime errors and convert them to diagnostic-like format."""
        runtime_diagnostics = []
        
        # Collect Python runtime errors
        runtime_errors = self.runtime_collector.collect_python_runtime_errors(runtime_log_path)
        for error in runtime_errors:
            # Convert runtime error to diagnostic-like format
            try:
                relative_path = os.path.relpath(error["file_path"], self.repository_root_path)
                file_content = self.codebase.get_file(relative_path).content
                
                # Create a mock Range for the error line
                error_range = Range(
                    start={"line": error["line"] - 1, "character": 0},
                    end={"line": error["line"] - 1, "character": 100}
                )
                
                # Create a mock Diagnostic
                mock_diagnostic = Diagnostic(
                    uri=PathUtils.path_to_uri(error["file_path"]),
                    range=error_range,
                    severity=1,  # Error severity
                    message=f"Runtime {error['error_type']}: {error['message']}",
                    code="runtime_error",
                    source="runtime_collector"
                )
                
                runtime_diagnostics.append({
                    "diagnostic": mock_diagnostic,
                    "file_content": file_content,
                    "relevant_code_snippet": self._get_relevant_code_for_diagnostic(file_content, error_range),
                    "file_path": error["file_path"],
                    "relative_file_path": relative_path,
                    "runtime_error_data": error,
                    "error_source": "runtime"
                })
                
            except Exception as e:
                logger.warning(f"Error processing runtime error: {e}")
        
        # Collect UI interaction errors
        ui_errors = self.runtime_collector.collect_ui_interaction_errors(ui_log_path)
        for error in ui_errors:
            try:
                relative_path = os.path.relpath(error["file_path"], self.repository_root_path)
                file_content = self.codebase.get_file(relative_path).content
                
                # Create a mock Range for the error line
                error_range = Range(
                    start={"line": error["line"] - 1, "character": error.get("column", 0)},
                    end={"line": error["line"] - 1, "character": error.get("column", 0) + 10}
                )
                
                # Create a mock Diagnostic
                mock_diagnostic = Diagnostic(
                    uri=PathUtils.path_to_uri(error["file_path"]),
                    range=error_range,
                    severity=2,  # Warning severity
                    message=f"UI {error['error_type']}: {error['message']}",
                    code="ui_error",
                    source="ui_collector"
                )
                
                runtime_diagnostics.append({
                    "diagnostic": mock_diagnostic,
                    "file_content": file_content,
                    "relevant_code_snippet": self._get_relevant_code_for_diagnostic(file_content, error_range),
                    "file_path": error["file_path"],
                    "relative_file_path": relative_path,
                    "ui_error_data": error,
                    "error_source": "ui"
                })
                
            except Exception as e:
                logger.warning(f"Error processing UI error: {e}")
        
        return runtime_diagnostics

    def get_error_statistics(self) -> Dict[str, Any]:
        """Get comprehensive error statistics."""
        if not self.lsp_server:
            return {}
        
        all_diagnostics = self.lsp_server.get_all_diagnostics()
        runtime_errors = self.lsp_server.get_runtime_errors()
        ui_errors = self.lsp_server.get_ui_errors()
        error_patterns = self.lsp_server.get_error_patterns()
        
        return {
            "lsp_diagnostics": {
                "total": sum(len(diags) for diags in all_diagnostics.values()),
                "files_affected": len(all_diagnostics),
                "by_severity": self._categorize_diagnostics_by_severity(all_diagnostics)
            },
            "runtime_errors": {
                "total": len(runtime_errors),
                "by_type": Counter(err.get("type", "unknown") for err in runtime_errors),
                "recent_errors": runtime_errors[-10:]  # Last 10 errors
            },
            "ui_errors": {
                "total": len(ui_errors),
                "by_type": Counter(err.get("type", "unknown") for err in ui_errors),
                "component_errors": len([err for err in ui_errors if err.get("type") == "react_error"])
            },
            "error_patterns": error_patterns,
            "error_frequency": self.error_frequency,
            "resolution_success_rate": self._calculate_resolution_success_rate()
        }

    def add_runtime_error(self, error_data: Dict[str, Any]) -> None:
        """Add a runtime error to the LSP server's collection."""
        if self.lsp_server:
            self.lsp_server.add_runtime_error(error_data)

    def add_ui_error(self, error_data: Dict[str, Any]) -> None:
        """Add a UI error to the LSP server's collection."""
        if self.lsp_server:
            self.lsp_server.add_ui_error(error_data)

    def clear_diagnostics(self) -> None:
        """Clears all stored diagnostics in the LSP server."""
        if self.lsp_server:
            self.lsp_server.clear_diagnostics()
        self.error_history.clear()
        self.error_frequency.clear()
        self.resolution_attempts.clear()

    def shutdown_server(self) -> None:
        """Shuts down the LSP server."""
        if self.lsp_server:
            self.logger.log("Shutting down LSP server.", logging.INFO)
            self.lsp_server.stop()
            self.lsp_server = None
            self.logger.log("LSP server shut down.", logging.INFO)

    async def monitor_runtime_errors(self, callback_func=None, monitor_duration: int = 60):
        """Monitor for runtime errors in real-time."""
        logger.info(f"Starting runtime error monitoring for {monitor_duration} seconds...")
        
        start_time = asyncio.get_event_loop().time()
        collected_errors = []
        
        while (asyncio.get_event_loop().time() - start_time) < monitor_duration:
            # Collect new runtime errors
            new_runtime_errors = self.runtime_collector.collect_python_runtime_errors()
            new_ui_errors = self.runtime_collector.collect_ui_interaction_errors()
            
            all_new_errors = new_runtime_errors + new_ui_errors
            
            if all_new_errors:
                collected_errors.extend(all_new_errors)
                if callback_func:
                    await callback_func(all_new_errors)
                    
            await asyncio.sleep(1)  # Check every second
        
        logger.info(f"Runtime error monitoring completed. Collected {len(collected_errors)} errors.")
        return collected_errors

    def _categorize_diagnostics_by_severity(self, all_diagnostics: Dict[DocumentUri, List[Diagnostic]]) -> Dict[str, int]:
        """Categorize diagnostics by severity."""
        severity_counts = {"error": 0, "warning": 0, "information": 0, "hint": 0}
        
        for diagnostics_list in all_diagnostics.values():
            for diag in diagnostics_list:
                if diag.severity:
                    severity_name = diag.severity.name.lower()
                    if severity_name in severity_counts:
                        severity_counts[severity_name] += 1
        
        return severity_counts

    def _calculate_resolution_success_rate(self) -> float:
        """Calculate the success rate of error resolutions."""
        if not self.resolution_attempts:
            return 0.0
        
        successful = sum(1 for attempt in self.resolution_attempts.values() if attempt.get("success", False))
        return successful / len(self.resolution_attempts)

    def mark_error_resolved(self, error_key: str, success: bool, method: str) -> None:
        """Mark an error as resolved or failed."""
        self.resolution_attempts[error_key] = {
            "success": success,
            "method": method,
            "timestamp": time.time()
        }
