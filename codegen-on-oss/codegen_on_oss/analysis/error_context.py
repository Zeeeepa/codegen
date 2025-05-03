"""
Error Context Module for Codegen-on-OSS

This module provides robust and dynamic error context analysis for code files and functions.
It helps identify and contextualize errors in code, providing detailed information about
the error location, type, and potential fixes.
"""

import ast
import inspect
import re
import tokenize
from io import StringIO
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import networkx as nx
from codegen.sdk.core.class_definition import Class
from codegen.sdk.core.codebase import Codebase
from codegen.sdk.core.file import SourceFile
from codegen.sdk.core.function import Function
from codegen.sdk.core.import_resolution import Import
from codegen.sdk.core.symbol import Symbol
from codegen.sdk.enums import EdgeType, SymbolType

# Error types
class ErrorType:
    SYNTAX_ERROR = "syntax_error"
    TYPE_ERROR = "type_error"
    NAME_ERROR = "name_error"
    IMPORT_ERROR = "import_error"
    ATTRIBUTE_ERROR = "attribute_error"
    PARAMETER_ERROR = "parameter_error"
    CALL_ERROR = "call_error"
    UNDEFINED_VARIABLE = "undefined_variable"
    UNUSED_IMPORT = "unused_import"
    UNUSED_VARIABLE = "unused_variable"
    CIRCULAR_IMPORT = "circular_import"
    CIRCULAR_DEPENDENCY = "circular_dependency"


class ErrorSeverity:
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class CodeError:
    """Represents an error in code with context."""
    
    def __init__(
        self,
        error_type: str,
        message: str,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
        column: Optional[int] = None,
        severity: str = ErrorSeverity.MEDIUM,
        symbol_name: Optional[str] = None,
        context_lines: Optional[Dict[int, str]] = None,
        suggested_fix: Optional[str] = None,
    ):
        self.error_type = error_type
        self.message = message
        self.file_path = file_path
        self.line_number = line_number
        self.column = column
        self.severity = severity
        self.symbol_name = symbol_name
        self.context_lines = context_lines or {}
        self.suggested_fix = suggested_fix
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the error to a dictionary representation."""
        return {
            "error_type": self.error_type,
            "message": self.message,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "column": self.column,
            "severity": self.severity,
            "symbol_name": self.symbol_name,
            "context_lines": self.context_lines,
            "suggested_fix": self.suggested_fix,
        }
    
    def __str__(self) -> str:
        """String representation of the error."""
        location = f"{self.file_path}:{self.line_number}" if self.file_path and self.line_number else "Unknown location"
        return f"{self.error_type.upper()} ({self.severity}): {self.message} at {location}"


class ErrorContextAnalyzer:
    """
    Analyzes code for errors and provides rich context information.
    
    This class is responsible for detecting various types of errors in code
    and providing detailed context information to help understand and fix them.
    """
    
    def __init__(self, codebase: Codebase):
        """
        Initialize the ErrorContextAnalyzer with a codebase.
        
        Args:
            codebase: The Codebase object to analyze
        """
        self.codebase = codebase
        self._call_graph = None
        self._dependency_graph = None
        self._import_graph = None
    
    def get_context_lines(self, file_path: str, line_number: int, context_size: int = 3) -> Dict[int, str]:
        """
        Get context lines around a specific line in a file.
        
        Args:
            file_path: Path to the file
            line_number: The line number to get context for
            context_size: Number of lines before and after to include
            
        Returns:
            Dictionary mapping line numbers to line content
        """
        file = self.codebase.get_file(file_path)
        if not file or not hasattr(file, "source"):
            return {}
        
        lines = file.source.splitlines()
        start_line = max(0, line_number - context_size - 1)
        end_line = min(len(lines), line_number + context_size)
        
        return {i + 1: lines[i] for i in range(start_line, end_line)}
    
    def build_call_graph(self) -> nx.DiGraph:
        """
        Build a call graph for the codebase.
        
        Returns:
            A directed graph representing function calls
        """
        if self._call_graph is not None:
            return self._call_graph
        
        G = nx.DiGraph()
        
        # Add nodes for all functions
        for func in self.codebase.functions:
            G.add_node(func.name, type="function", function=func)
        
        # Add edges for function calls
        for func in self.codebase.functions:
            if not hasattr(func, "function_calls"):
                continue
                
            for call in func.function_calls:
                if call.name in G:
                    G.add_edge(func.name, call.name, type="call")
        
        self._call_graph = G
        return G
    
    def build_dependency_graph(self) -> nx.DiGraph:
        """
        Build a dependency graph for the codebase.
        
        Returns:
            A directed graph representing symbol dependencies
        """
        if self._dependency_graph is not None:
            return self._dependency_graph
        
        G = nx.DiGraph()
        
        # Add nodes for all symbols
        for symbol in self.codebase.symbols:
            G.add_node(symbol.name, type="symbol", symbol=symbol)
        
        # Add edges for dependencies
        for symbol in self.codebase.symbols:
            if not hasattr(symbol, "dependencies"):
                continue
                
            for dep in symbol.dependencies:
                if isinstance(dep, Symbol):
                    G.add_edge(symbol.name, dep.name, type="dependency")
        
        self._dependency_graph = G
        return G
    
    def build_import_graph(self) -> nx.DiGraph:
        """
        Build an import graph for the codebase.
        
        Returns:
            A directed graph representing file imports
        """
        if self._import_graph is not None:
            return self._import_graph
        
        G = nx.DiGraph()
        
        # Add nodes for all files
        for file in self.codebase.files:
            G.add_node(file.name, type="file", file=file)
        
        # Add edges for imports
        for file in self.codebase.files:
            for imp in file.imports:
                if imp.imported_symbol and hasattr(imp.imported_symbol, "file"):
                    imported_file = imp.imported_symbol.file
                    if imported_file and imported_file.name != file.name:
                        G.add_edge(file.name, imported_file.name, type="import")
        
        self._import_graph = G
        return G
    
    def find_circular_imports(self) -> List[List[str]]:
        """
        Find circular imports in the codebase.
        
        Returns:
            A list of cycles, where each cycle is a list of file names
        """
        import_graph = self.build_import_graph()
        return list(nx.simple_cycles(import_graph))
    
    def find_circular_dependencies(self) -> List[List[str]]:
        """
        Find circular dependencies between symbols.
        
        Returns:
            A list of cycles, where each cycle is a list of symbol names
        """
        dependency_graph = self.build_dependency_graph()
        return list(nx.simple_cycles(dependency_graph))
    
    def analyze_function_parameters(self, function: Function) -> List[CodeError]:
        """
        Analyze function parameters for errors.
        
        Args:
            function: The function to analyze
            
        Returns:
            A list of parameter-related errors
        """
        errors = []
        
        if not hasattr(function, "parameters") or not hasattr(function, "function_calls"):
            return errors
        
        # Check for parameter type mismatches
        for param in function.parameters:
            if not hasattr(param, "type_annotation") or not param.type_annotation:
                continue
                
            # Check if parameter is used with correct type
            # This is a simplified check and would need more sophisticated type inference in practice
            param_name = param.name
            param_type = param.type_annotation
            
            # Look for usage of this parameter in the function body
            if hasattr(function, "code_block") and hasattr(function.code_block, "source"):
                source = function.code_block.source
                
                # Simple pattern matching for potential type errors
                # This is a simplified approach and would need more sophisticated analysis in practice
                if re.search(rf"\b{param_name}\s*\+\s*\d+\b", source) and "str" in param_type:
                    line_number = self._find_line_number(function.code_block.source, rf"\b{param_name}\s*\+\s*\d+\b")
                    errors.append(CodeError(
                        error_type=ErrorType.TYPE_ERROR,
                        message=f"Potential type error: adding integer to string parameter '{param_name}'",
                        file_path=function.file.name if hasattr(function, "file") else None,
                        line_number=line_number,
                        severity=ErrorSeverity.HIGH,
                        symbol_name=function.name,
                        context_lines=self.get_context_lines(function.file.name, line_number) if hasattr(function, "file") else None,
                        suggested_fix=f"Ensure '{param_name}' is converted to int before addition or use string concatenation"
                    ))
        
        # Check for call parameter mismatches
        call_graph = self.build_call_graph()
        for call in function.function_calls:
            called_func_name = call.name
            
            # Find the called function
            called_func = None
            for func in self.codebase.functions:
                if func.name == called_func_name:
                    called_func = func
                    break
            
            if not called_func or not hasattr(called_func, "parameters"):
                continue
            
            # Check if number of arguments matches
            if hasattr(call, "args") and len(call.args) != len(called_func.parameters):
                # Find the line number of the call
                line_number = self._find_line_number(function.code_block.source, rf"\b{called_func_name}\s*\(")
                
                errors.append(CodeError(
                    error_type=ErrorType.PARAMETER_ERROR,
                    message=f"Function '{called_func_name}' called with {len(call.args)} arguments but expects {len(called_func.parameters)}",
                    file_path=function.file.name if hasattr(function, "file") else None,
                    line_number=line_number,
                    severity=ErrorSeverity.HIGH,
                    symbol_name=function.name,
                    context_lines=self.get_context_lines(function.file.name, line_number) if hasattr(function, "file") else None,
                    suggested_fix=f"Update call to provide {len(called_func.parameters)} arguments"
                ))
        
        return errors
    
    def analyze_function_returns(self, function: Function) -> List[CodeError]:
        """
        Analyze function return statements for errors.
        
        Args:
            function: The function to analyze
            
        Returns:
            A list of return-related errors
        """
        errors = []
        
        if not hasattr(function, "return_type") or not function.return_type:
            return errors
        
        if not hasattr(function, "return_statements") or not function.return_statements:
            # Function has return type but no return statements
            errors.append(CodeError(
                error_type=ErrorType.TYPE_ERROR,
                message=f"Function '{function.name}' has return type '{function.return_type}' but no return statements",
                file_path=function.file.name if hasattr(function, "file") else None,
                line_number=function.line_number if hasattr(function, "line_number") else None,
                severity=ErrorSeverity.MEDIUM,
                symbol_name=function.name,
                context_lines=self.get_context_lines(function.file.name, function.line_number) if hasattr(function, "file") and hasattr(function, "line_number") else None,
                suggested_fix=f"Add return statement or change return type to 'None'"
            ))
            return errors
        
        # Check if return statements match the declared return type
        return_type = function.return_type
        for ret_stmt in function.return_statements:
            # This is a simplified check and would need more sophisticated type inference in practice
            if hasattr(ret_stmt, "expression") and hasattr(ret_stmt.expression, "source"):
                expr_source = ret_stmt.expression.source
                
                # Simple pattern matching for potential type errors
                if "int" in return_type and re.search(r"\".*\"", expr_source):
                    line_number = self._find_line_number(function.code_block.source, rf"return\s+{re.escape(expr_source)}")
                    errors.append(CodeError(
                        error_type=ErrorType.TYPE_ERROR,
                        message=f"Function '{function.name}' returns string but declares return type '{return_type}'",
                        file_path=function.file.name if hasattr(function, "file") else None,
                        line_number=line_number,
                        severity=ErrorSeverity.HIGH,
                        symbol_name=function.name,
                        context_lines=self.get_context_lines(function.file.name, line_number) if hasattr(function, "file") else None,
                        suggested_fix=f"Convert return value to {return_type} or update return type annotation"
                    ))
        
        return errors
    
    def analyze_unused_imports(self, file: SourceFile) -> List[CodeError]:
        """
        Find unused imports in a file.
        
        Args:
            file: The file to analyze
            
        Returns:
            A list of unused import errors
        """
        errors = []
        
        if not hasattr(file, "imports") or not hasattr(file, "symbols"):
            return errors
        
        # Get all imported symbols
        imported_symbols = set()
        for imp in file.imports:
            if hasattr(imp, "imported_symbol") and imp.imported_symbol:
                imported_symbols.add(imp.imported_symbol.name)
        
        # Get all used symbols
        used_symbols = set()
        for symbol in file.symbols:
            if hasattr(symbol, "dependencies"):
                for dep in symbol.dependencies:
                    if isinstance(dep, Symbol):
                        used_symbols.add(dep.name)
        
        # Find unused imports
        unused_imports = imported_symbols - used_symbols
        for unused in unused_imports:
            # Find the import statement
            for imp in file.imports:
                if hasattr(imp, "imported_symbol") and imp.imported_symbol and imp.imported_symbol.name == unused:
                    errors.append(CodeError(
                        error_type=ErrorType.UNUSED_IMPORT,
                        message=f"Unused import: '{unused}'",
                        file_path=file.name,
                        line_number=imp.line_number if hasattr(imp, "line_number") else None,
                        severity=ErrorSeverity.LOW,
                        context_lines=self.get_context_lines(file.name, imp.line_number) if hasattr(imp, "line_number") else None,
                        suggested_fix=f"Remove unused import of '{unused}'"
                    ))
        
        return errors
    
    def analyze_undefined_variables(self, function: Function) -> List[CodeError]:
        """
        Find undefined variables in a function.
        
        Args:
            function: The function to analyze
            
        Returns:
            A list of undefined variable errors
        """
        errors = []
        
        if not hasattr(function, "code_block") or not hasattr(function.code_block, "source"):
            return errors
        
        # Get parameter names
        param_names = set()
        if hasattr(function, "parameters"):
            for param in function.parameters:
                param_names.add(param.name)
        
        # Parse the function body to find variable definitions and usages
        try:
            tree = ast.parse(function.code_block.source)
            
            # Find all variable assignments
            assigned_vars = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            assigned_vars.add(target.id)
                elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                    assigned_vars.add(node.target.id)
            
            # Find all variable usages
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                    var_name = node.id
                    if var_name not in assigned_vars and var_name not in param_names and not var_name.startswith("__"):
                        # This is a potential undefined variable
                        # Find the line number in the source code
                        line_number = node.lineno
                        
                        errors.append(CodeError(
                            error_type=ErrorType.UNDEFINED_VARIABLE,
                            message=f"Potentially undefined variable: '{var_name}'",
                            file_path=function.file.name if hasattr(function, "file") else None,
                            line_number=line_number,
                            severity=ErrorSeverity.HIGH,
                            symbol_name=function.name,
                            context_lines=self.get_context_lines(function.file.name, line_number) if hasattr(function, "file") else None,
                            suggested_fix=f"Define '{var_name}' before use or check for typos"
                        ))
        except SyntaxError:
            # If there's a syntax error, we can't analyze the function body
            pass
        
        return errors
    
    def analyze_function(self, function: Function) -> List[CodeError]:
        """
        Analyze a function for errors.
        
        Args:
            function: The function to analyze
            
        Returns:
            A list of errors found in the function
        """
        errors = []
        
        # Analyze parameters
        errors.extend(self.analyze_function_parameters(function))
        
        # Analyze return statements
        errors.extend(self.analyze_function_returns(function))
        
        # Analyze undefined variables
        errors.extend(self.analyze_undefined_variables(function))
        
        return errors
    
    def analyze_file(self, file: SourceFile) -> List[CodeError]:
        """
        Analyze a file for errors.
        
        Args:
            file: The file to analyze
            
        Returns:
            A list of errors found in the file
        """
        errors = []
        
        # Analyze unused imports
        errors.extend(self.analyze_unused_imports(file))
        
        # Analyze syntax errors
        if hasattr(file, "source"):
            try:
                ast.parse(file.source)
            except SyntaxError as e:
                errors.append(CodeError(
                    error_type=ErrorType.SYNTAX_ERROR,
                    message=f"Syntax error: {str(e)}",
                    file_path=file.name,
                    line_number=e.lineno,
                    column=e.offset,
                    severity=ErrorSeverity.CRITICAL,
                    context_lines=self.get_context_lines(file.name, e.lineno),
                    suggested_fix="Fix the syntax error"
                ))
        
        # Analyze functions in the file
        for func in file.functions:
            errors.extend(self.analyze_function(func))
        
        return errors
    
    def analyze_codebase(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Analyze the entire codebase for errors.
        
        Returns:
            A dictionary mapping file paths to lists of errors
        """
        results = {}
        
        # Analyze each file
        for file in self.codebase.files:
            file_errors = self.analyze_file(file)
            if file_errors:
                results[file.name] = [error.to_dict() for error in file_errors]
        
        # Find circular imports
        circular_imports = self.find_circular_imports()
        for cycle in circular_imports:
            for file_name in cycle:
                if file_name not in results:
                    results[file_name] = []
                
                results[file_name].append(CodeError(
                    error_type=ErrorType.CIRCULAR_IMPORT,
                    message=f"Circular import detected: {' -> '.join(cycle)}",
                    file_path=file_name,
                    severity=ErrorSeverity.HIGH,
                    suggested_fix="Refactor imports to break the circular dependency"
                ).to_dict())
        
        # Find circular dependencies
        circular_deps = self.find_circular_dependencies()
        for cycle in circular_deps:
            for symbol_name in cycle:
                # Find the file containing this symbol
                symbol_file = None
                for symbol in self.codebase.symbols:
                    if symbol.name == symbol_name and hasattr(symbol, "file"):
                        symbol_file = symbol.file.name
                        break
                
                if not symbol_file:
                    continue
                
                if symbol_file not in results:
                    results[symbol_file] = []
                
                results[symbol_file].append(CodeError(
                    error_type=ErrorType.CIRCULAR_DEPENDENCY,
                    message=f"Circular dependency detected: {' -> '.join(cycle)}",
                    file_path=symbol_file,
                    symbol_name=symbol_name,
                    severity=ErrorSeverity.MEDIUM,
                    suggested_fix="Refactor code to break the circular dependency"
                ).to_dict())
        
        return results
    
    def get_error_context(self, error: CodeError) -> Dict[str, Any]:
        """
        Get detailed context information for an error.
        
        Args:
            error: The error to get context for
            
        Returns:
            A dictionary with detailed context information
        """
        context = error.to_dict()
        
        # Add additional context based on error type
        if error.error_type == ErrorType.PARAMETER_ERROR and error.symbol_name:
            # Get information about the function
            func = None
            for function in self.codebase.functions:
                if function.name == error.symbol_name:
                    func = function
                    break
            
            if func and hasattr(func, "parameters"):
                context["function_info"] = {
                    "name": func.name,
                    "parameters": [{"name": p.name, "type": p.type_annotation if hasattr(p, "type_annotation") else None} for p in func.parameters],
                    "return_type": func.return_type if hasattr(func, "return_type") else None
                }
        
        elif error.error_type == ErrorType.CIRCULAR_IMPORT:
            # Add information about the import cycle
            import_graph = self.build_import_graph()
            if error.file_path in import_graph:
                context["import_info"] = {
                    "imports": [n for n in import_graph.successors(error.file_path)],
                    "imported_by": [n for n in import_graph.predecessors(error.file_path)]
                }
        
        elif error.error_type == ErrorType.UNDEFINED_VARIABLE and error.symbol_name:
            # Get information about the function
            func = None
            for function in self.codebase.functions:
                if function.name == error.symbol_name:
                    func = function
                    break
            
            if func and hasattr(func, "parameters"):
                context["function_info"] = {
                    "name": func.name,
                    "parameters": [p.name for p in func.parameters],
                    "local_variables": self._extract_local_variables(func)
                }
        
        return context
    
    def _extract_local_variables(self, function: Function) -> List[str]:
        """
        Extract local variables defined in a function.
        
        Args:
            function: The function to analyze
            
        Returns:
            A list of local variable names
        """
        if not hasattr(function, "code_block") or not hasattr(function.code_block, "source"):
            return []
        
        local_vars = []
        try:
            tree = ast.parse(function.code_block.source)
            
            # Find all variable assignments
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            local_vars.append(target.id)
                elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                    local_vars.append(node.target.id)
        except SyntaxError:
            pass
        
        return local_vars
    
    def _find_line_number(self, source: str, pattern: str) -> Optional[int]:
        """
        Find the line number where a pattern appears in source code.
        
        Args:
            source: The source code to search
            pattern: The regex pattern to search for
            
        Returns:
            The line number (1-based) or None if not found
        """
        lines = source.splitlines()
        for i, line in enumerate(lines):
            if re.search(pattern, line):
                return i + 1
        return None
    
    def get_function_error_context(self, function_name: str) -> Dict[str, Any]:
        """
        Get detailed error context for a specific function.
        
        Args:
            function_name: The name of the function to analyze
            
        Returns:
            A dictionary with detailed error context
        """
        # Find the function
        function = None
        for func in self.codebase.functions:
            if func.name == function_name:
                function = func
                break
        
        if not function:
            return {"error": f"Function not found: {function_name}"}
        
        # Analyze the function
        errors = self.analyze_function(function)
        
        # Get call graph information
        call_graph = self.build_call_graph()
        callers = []
        callees = []
        
        if function_name in call_graph:
            callers = [{"name": caller} for caller in call_graph.predecessors(function_name)]
            callees = [{"name": callee} for callee in call_graph.successors(function_name)]
        
        # Get parameter information
        parameters = []
        if hasattr(function, "parameters"):
            for param in function.parameters:
                param_info = {
                    "name": param.name,
                    "type": param.type_annotation if hasattr(param, "type_annotation") else None,
                    "default": param.default_value if hasattr(param, "default_value") else None
                }
                parameters.append(param_info)
        
        # Get return information
        return_info = {
            "type": function.return_type if hasattr(function, "return_type") else None,
            "statements": []
        }
        
        if hasattr(function, "return_statements"):
            for ret_stmt in function.return_statements:
                if hasattr(ret_stmt, "expression") and hasattr(ret_stmt.expression, "source"):
                    return_info["statements"].append(ret_stmt.expression.source)
        
        # Combine all information
        result = {
            "function_name": function_name,
            "file_path": function.file.name if hasattr(function, "file") else None,
            "errors": [error.to_dict() for error in errors],
            "callers": callers,
            "callees": callees,
            "parameters": parameters,
            "return_info": return_info,
            "source": function.source if hasattr(function, "source") else None
        }
        
        return result
    
    def get_file_error_context(self, file_path: str) -> Dict[str, Any]:
        """
        Get detailed error context for a specific file.
        
        Args:
            file_path: The path of the file to analyze
            
        Returns:
            A dictionary with detailed error context
        """
        # Find the file
        file = self.codebase.get_file(file_path)
        if not file:
            return {"error": f"File not found: {file_path}"}
        
        # Analyze the file
        errors = self.analyze_file(file)
        
        # Get import graph information
        import_graph = self.build_import_graph()
        importers = []
        imported = []
        
        if file.name in import_graph:
            importers = [{"name": importer} for importer in import_graph.predecessors(file.name)]
            imported = [{"name": imp} for imp in import_graph.successors(file.name)]
        
        # Get function information
        functions = []
        for func in file.functions:
            func_errors = [error for error in errors if error.symbol_name == func.name]
            functions.append({
                "name": func.name,
                "line_number": func.line_number if hasattr(func, "line_number") else None,
                "errors": [error.to_dict() for error in func_errors]
            })
        
        # Get class information
        classes = []
        for cls in file.classes:
            classes.append({
                "name": cls.name,
                "line_number": cls.line_number if hasattr(cls, "line_number") else None
            })
        
        # Combine all information
        result = {
            "file_path": file_path,
            "errors": [error.to_dict() for error in errors],
            "importers": importers,
            "imported": imported,
            "functions": functions,
            "classes": classes
        }
        
        return result

