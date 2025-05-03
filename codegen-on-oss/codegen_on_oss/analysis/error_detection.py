"""
Error detection module for code analysis.

This module provides classes and functions for detecting errors in code,
including parameter errors, type errors, and call-in/call-out point errors.
"""

from enum import Enum, auto
from typing import Dict, List, Optional, Set, Tuple, Union, Any

from codegen import Codebase
from codegen.sdk.core.function import Function
from codegen.sdk.core.class_definition import Class
from codegen.sdk.core.symbol import Symbol


class ErrorSeverity(Enum):
    """Severity levels for code errors."""
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()


class ErrorCategory(Enum):
    """Categories of code errors."""
    PARAMETER_TYPE_MISMATCH = auto()
    PARAMETER_COUNT_MISMATCH = auto()
    UNUSED_PARAMETER = auto()
    UNDEFINED_PARAMETER = auto()
    MISSING_REQUIRED_PARAMETER = auto()
    RETURN_TYPE_MISMATCH = auto()
    UNDEFINED_VARIABLE = auto()
    UNUSED_IMPORT = auto()
    UNUSED_VARIABLE = auto()
    POTENTIAL_EXCEPTION = auto()
    CALL_POINT_ERROR = auto()
    CIRCULAR_DEPENDENCY = auto()
    INCONSISTENT_RETURN = auto()
    UNREACHABLE_CODE = auto()
    COMPLEX_FUNCTION = auto()


class CodeError:
    """Represents an error detected in the code."""
    
    def __init__(
        self,
        category: ErrorCategory,
        severity: ErrorSeverity,
        message: str,
        file_path: str,
        line_number: Optional[int] = None,
        column_number: Optional[int] = None,
        function_name: Optional[str] = None,
        class_name: Optional[str] = None,
        code_snippet: Optional[str] = None,
        related_symbols: Optional[List[str]] = None,
        fix_suggestion: Optional[str] = None
    ):
        """
        Initialize a CodeError.
        
        Args:
            category: The category of the error
            severity: The severity level of the error
            message: A descriptive message about the error
            file_path: Path to the file containing the error
            line_number: Line number where the error occurs (optional)
            column_number: Column number where the error occurs (optional)
            function_name: Name of the function containing the error (optional)
            class_name: Name of the class containing the error (optional)
            code_snippet: A snippet of the code containing the error (optional)
            related_symbols: List of symbol names related to the error (optional)
            fix_suggestion: A suggestion for fixing the error (optional)
        """
        self.category = category
        self.severity = severity
        self.message = message
        self.file_path = file_path
        self.line_number = line_number
        self.column_number = column_number
        self.function_name = function_name
        self.class_name = class_name
        self.code_snippet = code_snippet
        self.related_symbols = related_symbols or []
        self.fix_suggestion = fix_suggestion
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the error to a dictionary."""
        return {
            "category": self.category.name,
            "severity": self.severity.name,
            "message": self.message,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "column_number": self.column_number,
            "function_name": self.function_name,
            "class_name": self.class_name,
            "code_snippet": self.code_snippet,
            "related_symbols": self.related_symbols,
            "fix_suggestion": self.fix_suggestion
        }
    
    def __str__(self) -> str:
        """String representation of the error."""
        location = f"{self.file_path}"
        if self.line_number:
            location += f":{self.line_number}"
            if self.column_number:
                location += f":{self.column_number}"
        
        context = ""
        if self.function_name:
            context += f" in function '{self.function_name}'"
        if self.class_name:
            context += f" in class '{self.class_name}'"
        
        return f"[{self.severity.name}] {self.category.name}: {self.message} at {location}{context}"


class ErrorDetector:
    """Base class for error detectors."""
    
    def __init__(self, codebase: Codebase):
        """
        Initialize the error detector.
        
        Args:
            codebase: The codebase to analyze
        """
        self.codebase = codebase
        self.errors: List[CodeError] = []
    
    def detect_errors(self) -> List[CodeError]:
        """
        Detect errors in the codebase.
        
        Returns:
            A list of detected errors
        """
        raise NotImplementedError("Subclasses must implement detect_errors")
    
    def clear_errors(self) -> None:
        """Clear the list of detected errors."""
        self.errors = []


class ParameterErrorDetector(ErrorDetector):
    """Detector for parameter-related errors."""
    
    def detect_errors(self) -> List[CodeError]:
        """
        Detect parameter-related errors in the codebase.
        
        Returns:
            A list of detected parameter errors
        """
        self.clear_errors()
        
        for func in self.codebase.functions:
            # Check for unused parameters
            self._check_unused_parameters(func)
            
            # Check for parameter count mismatches in function calls
            self._check_parameter_count_mismatches(func)
            
            # Check for missing required parameters
            self._check_missing_required_parameters(func)
            
            # Check for parameter type mismatches
            self._check_parameter_type_mismatches(func)
        
        return self.errors
    
    def _check_unused_parameters(self, func: Function) -> None:
        """Check for unused parameters in a function."""
        if not hasattr(func, "parameters") or not hasattr(func, "code_block"):
            return
        
        for param in func.parameters:
            # Skip self parameter in methods
            if param.name == "self" and hasattr(func, "parent") and isinstance(func.parent, Class):
                continue
                
            # Check if parameter is used in the function body
            if hasattr(func, "code_block") and func.code_block and hasattr(func.code_block, "source"):
                source = func.code_block.source
                # Simple check - this could be improved with AST analysis
                if param.name not in source or param.name + "=" in source:
                    self.errors.append(CodeError(
                        category=ErrorCategory.UNUSED_PARAMETER,
                        severity=ErrorSeverity.WARNING,
                        message=f"Parameter '{param.name}' is declared but never used",
                        file_path=func.filepath,
                        function_name=func.name,
                        fix_suggestion=f"Remove the unused parameter '{param.name}' or use it in the function body"
                    ))
    
    def _check_parameter_count_mismatches(self, func: Function) -> None:
        """Check for parameter count mismatches in function calls."""
        if not hasattr(func, "function_calls"):
            return
            
        for call in func.function_calls:
            if hasattr(call, "target") and hasattr(call.target, "parameters"):
                expected_count = len(call.target.parameters)
                actual_count = len(call.arguments)
                
                # Account for self parameter in method calls
                if hasattr(call.target, "parent") and isinstance(call.target.parent, Class):
                    expected_count -= 1
                
                # Account for *args and **kwargs
                has_args = any(p.name == "args" and p.is_variadic for p in call.target.parameters)
                has_kwargs = any(p.name == "kwargs" and p.is_keyword_variadic for p in call.target.parameters)
                
                if not has_args and not has_kwargs and actual_count != expected_count:
                    self.errors.append(CodeError(
                        category=ErrorCategory.PARAMETER_COUNT_MISMATCH,
                        severity=ErrorSeverity.ERROR,
                        message=f"Function call has {actual_count} arguments but {expected_count} were expected",
                        file_path=func.filepath,
                        function_name=func.name,
                        related_symbols=[call.target.name],
                        fix_suggestion=f"Adjust the number of arguments to match the function signature"
                    ))
    
    def _check_missing_required_parameters(self, func: Function) -> None:
        """Check for missing required parameters in function calls."""
        if not hasattr(func, "function_calls"):
            return
            
        for call in func.function_calls:
            if hasattr(call, "target") and hasattr(call.target, "parameters"):
                # Get required parameters (those without default values)
                required_params = [p.name for p in call.target.parameters if not p.has_default_value]
                
                # Skip self parameter in method calls
                if hasattr(call.target, "parent") and isinstance(call.target.parent, Class):
                    if "self" in required_params:
                        required_params.remove("self")
                
                # Check if all required parameters are provided
                provided_params = [arg.name for arg in call.arguments if hasattr(arg, "name")]
                
                for param in required_params:
                    if param not in provided_params:
                        self.errors.append(CodeError(
                            category=ErrorCategory.MISSING_REQUIRED_PARAMETER,
                            severity=ErrorSeverity.ERROR,
                            message=f"Required parameter '{param}' is missing in function call",
                            file_path=func.filepath,
                            function_name=func.name,
                            related_symbols=[call.target.name],
                            fix_suggestion=f"Add the required parameter '{param}' to the function call"
                        ))
    
    def _check_parameter_type_mismatches(self, func: Function) -> None:
        """Check for parameter type mismatches in function calls."""
        if not hasattr(func, "function_calls"):
            return
            
        for call in func.function_calls:
            if hasattr(call, "target") and hasattr(call.target, "parameters"):
                for i, arg in enumerate(call.arguments):
                    if i < len(call.target.parameters) and hasattr(arg, "type_annotation") and hasattr(call.target.parameters[i], "type_annotation"):
                        arg_type = arg.type_annotation
                        param_type = call.target.parameters[i].type_annotation
                        
                        if arg_type and param_type and arg_type != param_type:
                            self.errors.append(CodeError(
                                category=ErrorCategory.PARAMETER_TYPE_MISMATCH,
                                severity=ErrorSeverity.WARNING,
                                message=f"Argument type '{arg_type}' does not match parameter type '{param_type}'",
                                file_path=func.filepath,
                                function_name=func.name,
                                related_symbols=[call.target.name],
                                fix_suggestion=f"Convert the argument to the expected type '{param_type}'"
                            ))


class ReturnErrorDetector(ErrorDetector):
    """Detector for return-related errors."""
    
    def detect_errors(self) -> List[CodeError]:
        """
        Detect return-related errors in the codebase.
        
        Returns:
            A list of detected return errors
        """
        self.clear_errors()
        
        for func in self.codebase.functions:
            # Check for return type mismatches
            self._check_return_type_mismatches(func)
            
            # Check for inconsistent return statements
            self._check_inconsistent_returns(func)
        
        return self.errors
    
    def _check_return_type_mismatches(self, func: Function) -> None:
        """Check for return type mismatches in a function."""
        if not hasattr(func, "return_statements") or not hasattr(func, "return_type"):
            return
            
        for ret in func.return_statements:
            if hasattr(ret, "value") and hasattr(ret.value, "type_annotation") and func.return_type:
                ret_type = ret.value.type_annotation
                
                if ret_type and ret_type != func.return_type:
                    self.errors.append(CodeError(
                        category=ErrorCategory.RETURN_TYPE_MISMATCH,
                        severity=ErrorSeverity.WARNING,
                        message=f"Return value type '{ret_type}' does not match declared return type '{func.return_type}'",
                        file_path=func.filepath,
                        function_name=func.name,
                        fix_suggestion=f"Convert the return value to the declared type '{func.return_type}'"
                    ))
    
    def _check_inconsistent_returns(self, func: Function) -> None:
        """Check for inconsistent return statements in a function."""
        if not hasattr(func, "return_statements"):
            return
            
        # Check if some paths return values and others don't
        has_value_returns = any(hasattr(ret, "value") and ret.value for ret in func.return_statements)
        has_void_returns = any(not hasattr(ret, "value") or not ret.value for ret in func.return_statements)
        
        if has_value_returns and has_void_returns:
            self.errors.append(CodeError(
                category=ErrorCategory.INCONSISTENT_RETURN,
                severity=ErrorSeverity.ERROR,
                message=f"Function has inconsistent return statements (some with values, some without)",
                file_path=func.filepath,
                function_name=func.name,
                fix_suggestion=f"Ensure all return statements consistently return values or None"
            ))


class CallGraphErrorDetector(ErrorDetector):
    """Detector for call graph related errors."""
    
    def detect_errors(self) -> List[CodeError]:
        """
        Detect call graph related errors in the codebase.
        
        Returns:
            A list of detected call graph errors
        """
        self.clear_errors()
        
        # Build call graph
        call_graph = self._build_call_graph()
        
        # Check for circular dependencies
        self._check_circular_dependencies(call_graph)
        
        # Check for call-in/call-out point errors
        self._check_call_point_errors()
        
        return self.errors
    
    def _build_call_graph(self) -> Dict[str, Set[str]]:
        """Build a call graph for the codebase."""
        call_graph = {}
        
        for func in self.codebase.functions:
            if not hasattr(func, "function_calls"):
                continue
                
            caller = func.name
            if caller not in call_graph:
                call_graph[caller] = set()
                
            for call in func.function_calls:
                if hasattr(call, "target") and hasattr(call.target, "name"):
                    callee = call.target.name
                    call_graph[caller].add(callee)
                    
                    # Ensure callee is in the graph
                    if callee not in call_graph:
                        call_graph[callee] = set()
        
        return call_graph
    
    def _check_circular_dependencies(self, call_graph: Dict[str, Set[str]]) -> None:
        """Check for circular dependencies in the call graph."""
        visited = set()
        path = []
        
        def dfs(node):
            if node in path:
                # Found a cycle
                cycle = path[path.index(node):] + [node]
                self._report_circular_dependency(cycle)
                return
                
            if node in visited:
                return
                
            visited.add(node)
            path.append(node)
            
            for neighbor in call_graph.get(node, set()):
                dfs(neighbor)
                
            path.pop()
        
        for node in call_graph:
            dfs(node)
    
    def _report_circular_dependency(self, cycle: List[str]) -> None:
        """Report a circular dependency."""
        cycle_str = " -> ".join(cycle)
        
        # Find the functions involved in the cycle
        functions = []
        for name in cycle:
            for func in self.codebase.functions:
                if func.name == name:
                    functions.append(func)
                    break
        
        if not functions:
            return
            
        # Report the error for the first function in the cycle
        func = functions[0]
        self.errors.append(CodeError(
            category=ErrorCategory.CIRCULAR_DEPENDENCY,
            severity=ErrorSeverity.WARNING,
            message=f"Circular dependency detected: {cycle_str}",
            file_path=func.filepath,
            function_name=func.name,
            related_symbols=cycle,
            fix_suggestion="Break the circular dependency by refactoring one of the functions"
        ))
    
    def _check_call_point_errors(self) -> None:
        """Check for call-in/call-out point errors."""
        for func in self.codebase.functions:
            if not hasattr(func, "function_calls") or not hasattr(func, "call_sites"):
                continue
                
            # Check if function is called with consistent arguments
            call_sites = func.call_sites
            if len(call_sites) > 1:
                arg_counts = set(len(call.arguments) for call in call_sites if hasattr(call, "arguments"))
                
                if len(arg_counts) > 1:
                    self.errors.append(CodeError(
                        category=ErrorCategory.CALL_POINT_ERROR,
                        severity=ErrorSeverity.WARNING,
                        message=f"Function is called with inconsistent number of arguments ({', '.join(map(str, arg_counts))})",
                        file_path=func.filepath,
                        function_name=func.name,
                        fix_suggestion="Ensure the function is called consistently with the same number of arguments"
                    ))


class CodeQualityErrorDetector(ErrorDetector):
    """Detector for code quality related errors."""
    
    def detect_errors(self) -> List[CodeError]:
        """
        Detect code quality related errors in the codebase.
        
        Returns:
            A list of detected code quality errors
        """
        self.clear_errors()
        
        for func in self.codebase.functions:
            # Check for complex functions
            self._check_complex_function(func)
            
            # Check for unreachable code
            self._check_unreachable_code(func)
            
            # Check for potential exceptions
            self._check_potential_exceptions(func)
        
        # Check for unused imports
        self._check_unused_imports()
        
        # Check for unused variables
        self._check_unused_variables()
        
        return self.errors
    
    def _check_complex_function(self, func: Function) -> None:
        """Check if a function is too complex."""
        if not hasattr(func, "code_block"):
            return
            
        # Calculate cyclomatic complexity
        complexity = self._calculate_cyclomatic_complexity(func)
        
        if complexity > 10:
            self.errors.append(CodeError(
                category=ErrorCategory.COMPLEX_FUNCTION,
                severity=ErrorSeverity.WARNING,
                message=f"Function has high cyclomatic complexity ({complexity})",
                file_path=func.filepath,
                function_name=func.name,
                fix_suggestion="Refactor the function into smaller, more manageable pieces"
            ))
    
    def _calculate_cyclomatic_complexity(self, func: Function) -> int:
        """Calculate the cyclomatic complexity of a function."""
        if not hasattr(func, "code_block") or not func.code_block:
            return 1
            
        # Base complexity is 1
        complexity = 1
        
        # Count if statements
        if hasattr(func, "if_statements"):
            complexity += len(func.if_statements)
        
        # Count for loops
        if hasattr(func, "for_loops"):
            complexity += len(func.for_loops)
        
        # Count while loops
        if hasattr(func, "while_loops"):
            complexity += len(func.while_loops)
        
        # Count except blocks
        if hasattr(func, "except_blocks"):
            complexity += len(func.except_blocks)
        
        # Count boolean operators
        if hasattr(func, "code_block") and hasattr(func.code_block, "source"):
            source = func.code_block.source
            complexity += source.count(" and ") + source.count(" or ")
        
        return complexity
    
    def _check_unreachable_code(self, func: Function) -> None:
        """Check for unreachable code in a function."""
        if not hasattr(func, "code_block") or not hasattr(func, "return_statements"):
            return
            
        # Simple check for code after return statements
        # This is a simplified approach - a proper implementation would use AST analysis
        if hasattr(func.code_block, "source"):
            source_lines = func.code_block.source.splitlines()
            
            for i, line in enumerate(source_lines):
                if line.strip().startswith("return "):
                    # Check if there's non-empty code after this return
                    for j in range(i + 1, len(source_lines)):
                        if source_lines[j].strip() and not source_lines[j].strip().startswith(("#", "\"\"\"", "'''", "else:", "except ", "finally:")):
                            self.errors.append(CodeError(
                                category=ErrorCategory.UNREACHABLE_CODE,
                                severity=ErrorSeverity.WARNING,
                                message=f"Code after return statement will never be executed",
                                file_path=func.filepath,
                                line_number=j + 1,  # +1 because line numbers are 1-based
                                function_name=func.name,
                                code_snippet=source_lines[j],
                                fix_suggestion="Remove or move the unreachable code"
                            ))
                            break
    
    def _check_potential_exceptions(self, func: Function) -> None:
        """Check for potential exceptions in a function."""
        if not hasattr(func, "code_block"):
            return
            
        # Check for common error-prone patterns
        if hasattr(func.code_block, "source"):
            source = func.code_block.source
            
            # Check for dictionary access without get()
            if "[" in source and not "try:" in source:
                self.errors.append(CodeError(
                    category=ErrorCategory.POTENTIAL_EXCEPTION,
                    severity=ErrorSeverity.INFO,
                    message=f"Function may raise KeyError when accessing dictionary",
                    file_path=func.filepath,
                    function_name=func.name,
                    fix_suggestion="Use dict.get() or try-except to handle potential KeyError"
                ))
            
            # Check for division without checking for zero
            if "/" in source and not "try:" in source and not "if " in source:
                self.errors.append(CodeError(
                    category=ErrorCategory.POTENTIAL_EXCEPTION,
                    severity=ErrorSeverity.INFO,
                    message=f"Function may raise ZeroDivisionError",
                    file_path=func.filepath,
                    function_name=func.name,
                    fix_suggestion="Check for zero before division or use try-except"
                ))
    
    def _check_unused_imports(self) -> None:
        """Check for unused imports in the codebase."""
        for file in self.codebase.files:
            if not hasattr(file, "imports") or not hasattr(file, "source"):
                continue
                
            for imp in file.imports:
                if hasattr(imp, "imported_symbol") and hasattr(imp.imported_symbol, "name"):
                    symbol_name = imp.imported_symbol.name
                    
                    # Check if the import is used in the file
                    if symbol_name not in file.source or symbol_name + " " not in file.source:
                        self.errors.append(CodeError(
                            category=ErrorCategory.UNUSED_IMPORT,
                            severity=ErrorSeverity.INFO,
                            message=f"Import '{symbol_name}' is never used",
                            file_path=file.filepath,
                            fix_suggestion=f"Remove the unused import"
                        ))
    
    def _check_unused_variables(self) -> None:
        """Check for unused variables in the codebase."""
        for func in self.codebase.functions:
            if not hasattr(func, "code_block") or not hasattr(func, "variables"):
                continue
                
            for var in func.variables:
                if hasattr(var, "name") and hasattr(func.code_block, "source"):
                    var_name = var.name
                    source = func.code_block.source
                    
                    # Count occurrences of the variable name
                    # This is a simplified approach - a proper implementation would use AST analysis
                    occurrences = source.count(var_name)
                    
                    # If the variable only appears once (its declaration), it's unused
                    if occurrences == 1:
                        self.errors.append(CodeError(
                            category=ErrorCategory.UNUSED_VARIABLE,
                            severity=ErrorSeverity.INFO,
                            message=f"Variable '{var_name}' is defined but never used",
                            file_path=func.filepath,
                            function_name=func.name,
                            fix_suggestion=f"Remove the unused variable"
                        ))


class CodeAnalysisError:
    """Main class for code error analysis."""
    
    def __init__(self, codebase: Codebase):
        """
        Initialize the code error analyzer.
        
        Args:
            codebase: The codebase to analyze
        """
        self.codebase = codebase
        self.detectors = [
            ParameterErrorDetector(codebase),
            ReturnErrorDetector(codebase),
            CallGraphErrorDetector(codebase),
            CodeQualityErrorDetector(codebase)
        ]
    
    def analyze(self) -> List[CodeError]:
        """
        Analyze the codebase for errors.
        
        Returns:
            A list of all detected errors
        """
        all_errors = []
        
        for detector in self.detectors:
            errors = detector.detect_errors()
            all_errors.extend(errors)
        
        return all_errors
    
    def analyze_by_category(self, category: ErrorCategory) -> List[CodeError]:
        """
        Analyze the codebase for errors of a specific category.
        
        Args:
            category: The error category to filter by
            
        Returns:
            A list of errors of the specified category
        """
        all_errors = self.analyze()
        return [error for error in all_errors if error.category == category]
    
    def analyze_by_severity(self, severity: ErrorSeverity) -> List[CodeError]:
        """
        Analyze the codebase for errors of a specific severity.
        
        Args:
            severity: The error severity to filter by
            
        Returns:
            A list of errors of the specified severity
        """
        all_errors = self.analyze()
        return [error for error in all_errors if error.severity == severity]
    
    def analyze_file(self, file_path: str) -> List[CodeError]:
        """
        Analyze a specific file for errors.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            A list of errors in the specified file
        """
        all_errors = self.analyze()
        return [error for error in all_errors if error.file_path == file_path]
    
    def analyze_function(self, function_name: str) -> List[CodeError]:
        """
        Analyze a specific function for errors.
        
        Args:
            function_name: Name of the function to analyze
            
        Returns:
            A list of errors in the specified function
        """
        all_errors = self.analyze()
        return [error for error in all_errors if error.function_name == function_name]
    
    def analyze_class(self, class_name: str) -> List[CodeError]:
        """
        Analyze a specific class for errors.
        
        Args:
            class_name: Name of the class to analyze
            
        Returns:
            A list of errors in the specified class
        """
        all_errors = self.analyze()
        return [error for error in all_errors if error.class_name == class_name]
    
    def get_error_summary(self) -> Dict[str, int]:
        """
        Get a summary of errors by category.
        
        Returns:
            A dictionary mapping error categories to counts
        """
        all_errors = self.analyze()
        summary = {}
        
        for error in all_errors:
            category = error.category.name
            if category in summary:
                summary[category] += 1
            else:
                summary[category] = 1
        
        return summary
    
    def get_severity_summary(self) -> Dict[str, int]:
        """
        Get a summary of errors by severity.
        
        Returns:
            A dictionary mapping error severities to counts
        """
        all_errors = self.analyze()
        summary = {}
        
        for error in all_errors:
            severity = error.severity.name
            if severity in summary:
                summary[severity] += 1
            else:
                summary[severity] = 1
        
        return summary

