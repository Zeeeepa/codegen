#!/usr/bin/env python3
"""
Code Quality Analyzer Module

This module provides analysis of code quality issues such as dead code,
complexity, style, and maintainability. It identifies issues like unused variables,
functions with excessive complexity, parameter errors, and implementation problems.
"""

import os
import re
import sys
import math
import logging
from typing import Dict, List, Set, Tuple, Any, Optional, Union, cast

# Import from our own modules
from codegen_on_oss.analyzers.issues import (
    Issue, IssueSeverity, IssueCategory, IssueCollection,
    CodeLocation, create_issue, AnalysisType
)
from codegen_on_oss.analyzers.codebase_context import CodebaseContext

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class CodeQualityAnalyzer:
    """
    Analyzer for code quality issues.
    
    This class analyzes code quality issues in a codebase, including dead code,
    complexity, style, and maintainability issues.
    """
    
    def __init__(
        self, 
        codebase_context: CodebaseContext,
        issue_collection: Optional[IssueCollection] = None
    ):
        """
        Initialize the analyzer.
        
        Args:
            codebase_context: Context for the codebase to analyze
            issue_collection: Collection for storing issues
        """
        self.context = codebase_context
        self.issues = issue_collection or IssueCollection()
        
        # Register default issue filters
        self._register_default_filters()
    
    def _register_default_filters(self):
        """Register default issue filters."""
        # Filter out issues in test files
        self.issues.add_filter(
            lambda issue: "test" not in issue.location.file.lower(),
            "Skip issues in test files"
        )
        
        # Filter out issues in generated files
        self.issues.add_filter(
            lambda issue: "generated" not in issue.location.file.lower(),
            "Skip issues in generated files"
        )
    
    def analyze(self) -> Dict[str, Any]:
        """
        Perform code quality analysis.
        
        Returns:
            Dictionary containing analysis results
        """
        logger.info("Starting code quality analysis")
        
        # Clear existing issues
        self.issues = IssueCollection()
        self._register_default_filters()
        
        # Analyze dead code
        dead_code = self._find_dead_code()
        
        # Analyze complexity
        complexity = self._analyze_complexity()
        
        # Analyze parameters
        parameter_issues = self._check_function_parameters()
        
        # Analyze style issues
        style_issues = self._check_style_issues()
        
        # Analyze implementations
        implementation_issues = self._check_implementations()
        
        # Analyze maintainability
        maintainability = self._calculate_maintainability()
        
        # Combine results
        results = {
            "summary": {
                "issue_count": len(self.issues.issues),
                "analyzed_functions": len(self.context.get_functions()),
                "analyzed_classes": len(self.context.get_classes()),
                "analyzed_files": len(self.context.get_files())
            },
            "dead_code": dead_code,
            "complexity": complexity,
            "parameter_issues": parameter_issues,
            "style_issues": style_issues,
            "implementation_issues": implementation_issues,
            "maintainability": maintainability,
            "issues": self.issues.to_dict()
        }
        
        logger.info(f"Code quality analysis complete. Found {len(self.issues.issues)} issues.")
        
        return results
    
    def _find_dead_code(self) -> Dict[str, Any]:
        """
        Find unused code (dead code) in the codebase.
        
        Returns:
            Dictionary containing dead code analysis results
        """
        logger.info("Analyzing dead code")
        
        dead_code = {
            "unused_functions": [],
            "unused_classes": [],
            "unused_variables": [],
            "unused_imports": []
        }
        
        # Find unused functions
        for function in self.context.get_functions():
            # Skip if function should be excluded
            if self._should_skip_symbol(function):
                continue
            
            # Skip decorated functions (as they might be used indirectly)
            if hasattr(function, 'decorators') and function.decorators:
                continue
            
            # Check if function has no call sites or usages
            has_call_sites = hasattr(function, 'call_sites') and len(function.call_sites) > 0
            has_usages = hasattr(function, 'usages') and len(function.usages) > 0
            
            if not has_call_sites and not has_usages:
                # Skip magic methods and main functions
                if (hasattr(function, 'is_magic') and function.is_magic) or (
                    hasattr(function, 'name') and function.name in ['main', '__main__']):
                    continue
                
                # Get file path and name safely
                file_path = function.file.file_path if hasattr(function, 'file') and hasattr(function.file, 'file_path') else "unknown"
                func_name = function.name if hasattr(function, 'name') else str(function)
                
                # Add to dead code list
                dead_code["unused_functions"].append({
                    "name": func_name,
                    "file": file_path,
                    "line": function.line if hasattr(function, 'line') else None
                })
                
                # Add issue
                self.issues.add_issue(create_issue(
                    message=f"Unused function: {func_name}",
                    severity=IssueSeverity.WARNING,
                    file=file_path,
                    line=function.line if hasattr(function, 'line') else None,
                    category=IssueCategory.DEAD_CODE,
                    symbol=func_name,
                    suggestion="Consider removing this unused function or documenting why it's needed"
                ))
        
        # Find unused classes
        for cls in self.context.get_classes():
            # Skip if class should be excluded
            if self._should_skip_symbol(cls):
                continue
            
            # Check if class has no usages
            has_usages = hasattr(cls, 'usages') and len(cls.usages) > 0
            
            if not has_usages:
                # Get file path and name safely
                file_path = cls.file.file_path if hasattr(cls, 'file') and hasattr(cls.file, 'file_path') else "unknown"
                cls_name = cls.name if hasattr(cls, 'name') else str(cls)
                
                # Add to dead code list
                dead_code["unused_classes"].append({
                    "name": cls_name,
                    "file": file_path,
                    "line": cls.line if hasattr(cls, 'line') else None
                })
                
                # Add issue
                self.issues.add_issue(create_issue(
                    message=f"Unused class: {cls_name}",
                    severity=IssueSeverity.WARNING,
                    file=file_path,
                    line=cls.line if hasattr(cls, 'line') else None,
                    category=IssueCategory.DEAD_CODE,
                    symbol=cls_name,
                    suggestion="Consider removing this unused class or documenting why it's needed"
                ))
        
        # Find unused variables
        for function in self.context.get_functions():
            if not hasattr(function, 'code_block') or not hasattr(function.code_block, 'local_var_assignments'):
                continue
            
            for var_assignment in function.code_block.local_var_assignments:
                # Check if variable has no usages
                has_usages = hasattr(var_assignment, 'local_usages') and len(var_assignment.local_usages) > 0
                
                if not has_usages:
                    # Skip if variable name indicates it's intentionally unused (e.g., _)
                    var_name = var_assignment.name if hasattr(var_assignment, 'name') else str(var_assignment)
                    if var_name == "_" or var_name.startswith("_unused"):
                        continue
                    
                    # Get file path
                    file_path = function.file.file_path if hasattr(function, 'file') and hasattr(function.file, 'file_path') else "unknown"
                    
                    # Add to dead code list
                    dead_code["unused_variables"].append({
                        "name": var_name,
                        "file": file_path,
                        "line": var_assignment.line if hasattr(var_assignment, 'line') else None,
                        "function": function.name if hasattr(function, 'name') else str(function)
                    })
                    
                    # Add issue
                    self.issues.add_issue(create_issue(
                        message=f"Unused variable '{var_name}' in function '{function.name if hasattr(function, 'name') else 'unknown'}'",
                        severity=IssueSeverity.INFO,
                        file=file_path,
                        line=var_assignment.line if hasattr(var_assignment, 'line') else None,
                        category=IssueCategory.DEAD_CODE,
                        symbol=var_name,
                        suggestion="Consider removing this unused variable"
                    ))
        
        # Find unused imports
        for file in self.context.get_files():
            if hasattr(file, 'is_binary') and file.is_binary:
                continue
                
            if not hasattr(file, 'imports'):
                continue
                
            file_path = file.file_path if hasattr(file, 'file_path') else str(file)
            
            for imp in file.imports:
                if not hasattr(imp, 'usages'):
                    continue
                    
                if len(imp.usages) == 0:
                    # Get import source safely
                    import_source = imp.source if hasattr(imp, 'source') else str(imp)
                    
                    # Add to dead code list
                    dead_code["unused_imports"].append({
                        "import": import_source,
                        "file": file_path,
                        "line": imp.line if hasattr(imp, 'line') else None
                    })
                    
                    # Add issue
                    self.issues.add_issue(create_issue(
                        message=f"Unused import: {import_source}",
                        severity=IssueSeverity.INFO,
                        file=file_path,
                        line=imp.line if hasattr(imp, 'line') else None,
                        category=IssueCategory.DEAD_CODE,
                        code=import_source,
                        suggestion="Remove this unused import"
                    ))
        
        # Add summary statistics
        dead_code["summary"] = {
            "unused_functions_count": len(dead_code["unused_functions"]),
            "unused_classes_count": len(dead_code["unused_classes"]),
            "unused_variables_count": len(dead_code["unused_variables"]),
            "unused_imports_count": len(dead_code["unused_imports"]),
            "total_dead_code_count": (
                len(dead_code["unused_functions"]) +
                len(dead_code["unused_classes"]) +
                len(dead_code["unused_variables"]) +
                len(dead_code["unused_imports"])
            )
        }
        
        return dead_code
    
    def _analyze_complexity(self) -> Dict[str, Any]:
        """
        Analyze code complexity.
        
        Returns:
            Dictionary containing complexity analysis results
        """
        logger.info("Analyzing code complexity")
        
        complexity_result = {
            "function_complexity": [],
            "high_complexity_functions": [],
            "average_complexity": 0.0,
            "complexity_distribution": {
                "low": 0,
                "medium": 0,
                "high": 0,
                "very_high": 0
            }
        }
        
        # Process all functions to calculate complexity
        total_complexity = 0
        function_count = 0
        
        for function in self.context.get_functions():
            # Skip if function should be excluded
            if self._should_skip_symbol(function):
                continue
            
            # Skip if no code block
            if not hasattr(function, 'code_block'):
                continue
            
            # Calculate cyclomatic complexity
            complexity = self._calculate_cyclomatic_complexity(function)
            
            # Get file path and name safely
            file_path = function.file.file_path if hasattr(function, 'file') and hasattr(function.file, 'file_path') else "unknown"
            func_name = function.name if hasattr(function, 'name') else str(function)
            
            # Add to complexity list
            complexity_result["function_complexity"].append({
                "name": func_name,
                "file": file_path,
                "line": function.line if hasattr(function, 'line') else None,
                "complexity": complexity
            })
            
            # Track total complexity
            total_complexity += complexity
            function_count += 1
            
            # Categorize complexity
            if complexity <= 5:
                complexity_result["complexity_distribution"]["low"] += 1
            elif complexity <= 10:
                complexity_result["complexity_distribution"]["medium"] += 1
            elif complexity <= 15:
                complexity_result["complexity_distribution"]["high"] += 1
            else:
                complexity_result["complexity_distribution"]["very_high"] += 1
            
            # Flag high complexity functions
            if complexity > 10:
                complexity_result["high_complexity_functions"].append({
                    "name": func_name,
                    "file": file_path,
                    "line": function.line if hasattr(function, 'line') else None,
                    "complexity": complexity
                })
                
                # Add issue
                severity = IssueSeverity.WARNING if complexity <= 15 else IssueSeverity.ERROR
                self.issues.add_issue(create_issue(
                    message=f"Function '{func_name}' has high cyclomatic complexity ({complexity})",
                    severity=severity,
                    file=file_path,
                    line=function.line if hasattr(function, 'line') else None,
                    category=IssueCategory.COMPLEXITY,
                    symbol=func_name,
                    suggestion="Consider refactoring this function to reduce complexity"
                ))
        
        # Calculate average complexity
        complexity_result["average_complexity"] = total_complexity / function_count if function_count > 0 else 0.0
        
        # Sort high complexity functions by complexity
        complexity_result["high_complexity_functions"].sort(key=lambda x: x["complexity"], reverse=True)
        
        return complexity_result
    
    def _calculate_cyclomatic_complexity(self, function) -> int:
        """
        Calculate cyclomatic complexity for a function.
        
        Args:
            function: Function to analyze
            
        Returns:
            Cyclomatic complexity score
        """
        complexity = 1  # Base complexity
        
        def analyze_statement(statement):
            nonlocal complexity
            
            # Check for if statements (including elif branches)
            if hasattr(statement, 'if_clause'):
                complexity += 1
            
            # Count elif branches
            if hasattr(statement, 'elif_statements'):
                complexity += len(statement.elif_statements)
            
            # Count else branches
            if hasattr(statement, 'else_clause') and statement.else_clause:
                complexity += 1
            
            # Count for loops
            if hasattr(statement, 'is_for_loop') and statement.is_for_loop:
                complexity += 1
            
            # Count while loops
            if hasattr(statement, 'is_while_loop') and statement.is_while_loop:
                complexity += 1
            
            # Count try/except blocks (each except adds a path)
            if hasattr(statement, 'is_try_block') and statement.is_try_block:
                if hasattr(statement, 'except_clauses'):
                    complexity += len(statement.except_clauses)
            
            # Recursively process nested statements
            if hasattr(statement, 'statements'):
                for nested_stmt in statement.statements:
                    analyze_statement(nested_stmt)
        
        # Process all statements in the function's code block
        if hasattr(function, 'code_block') and hasattr(function.code_block, 'statements'):
            for statement in function.code_block.statements:
                analyze_statement(statement)
        
        # If we can't analyze the AST, fall back to simple pattern matching
        elif hasattr(function, 'source'):
            source = function.source
            # Count branch points
            complexity += source.count('if ')
            complexity += source.count('elif ')
            complexity += source.count('for ')
            complexity += source.count('while ')
            complexity += source.count('except:')
            complexity += source.count('except ')
            complexity += source.count('case ')
        
        return complexity
    
    def _check_function_parameters(self) -> Dict[str, Any]:
        """
        Check for function parameter issues.
        
        Returns:
            Dictionary containing parameter analysis results
        """
        logger.info("Analyzing function parameters")
        
        parameter_issues = {
            "missing_types": [],
            "inconsistent_types": [],
            "unused_parameters": [],
            "incorrect_usage": []
        }
        
        for function in self.context.get_functions():
            # Skip if function should be excluded
            if self._should_skip_symbol(function):
                continue
            
            # Skip if no parameters
            if not hasattr(function, 'parameters'):
                continue
            
            file_path = function.file.file_path if hasattr(function, 'file') and hasattr(function.file, 'file_path') else "unknown"
            func_name = function.name if hasattr(function, 'name') else str(function)
            
            # Check for missing type annotations
            missing_types = []
            for param in function.parameters:
                if not hasattr(param, 'name'):
                    continue
                
                if not hasattr(param, 'type') or not param.type:
                    missing_types.append(param.name)
            
            if missing_types:
                parameter_issues["missing_types"].append({
                    "function": func_name,
                    "file": file_path,
                    "line": function.line if hasattr(function, 'line') else None,
                    "parameters": missing_types
                })
                
                self.issues.add_issue(create_issue(
                    message=f"Function '{func_name}' has parameters without type annotations: {', '.join(missing_types)}",
                    severity=IssueSeverity.WARNING,
                    file=file_path,
                    line=function.line if hasattr(function, 'line') else None,
                    category=IssueCategory.TYPE_ERROR,
                    symbol=func_name,
                    suggestion="Add type annotations to all parameters"
                ))
            
            # Check for unused parameters
            if hasattr(function, 'source'):
                # This is a simple check that looks for parameter names in the function body
                # A more sophisticated check would analyze the AST
                unused_params = []
                for param in function.parameters:
                    if not hasattr(param, 'name'):
                        continue
                    
                    # Skip self/cls parameter in methods
                    if param.name in ['self', 'cls'] and hasattr(function, 'parent') and function.parent:
                        continue
                    
                    # Check if parameter name appears in function body
                    # This is a simple heuristic and may produce false positives
                    param_regex = r'\b' + re.escape(param.name) + r'\b'
                    body_lines = function.source.split('\n')[1:] if function.source.count('\n') > 0 else []
                    body_text = '\n'.join(body_lines)
                    
                    if not re.search(param_regex, body_text):
                        unused_params.append(param.name)
                
                if unused_params:
                    parameter_issues["unused_parameters"].append({
                        "function": func_name,
                        "file": file_path,
                        "line": function.line if hasattr(function, 'line') else None,
                        "parameters": unused_params
                    })
                    
                    self.issues.add_issue(create_issue(
                        message=f"Function '{func_name}' has unused parameters: {', '.join(unused_params)}",
                        severity=IssueSeverity.INFO,
                        file=file_path,
                        line=function.line if hasattr(function, 'line') else None,
                        category=IssueCategory.DEAD_CODE,
                        symbol=func_name,
                        suggestion="Remove unused parameters or use them in the function body"
                    ))
            
            # Check for incorrect parameter usage at call sites
            if hasattr(function, 'call_sites'):
                for call_site in function.call_sites:
                    # Skip if call site has no arguments
                    if not hasattr(call_site, 'args'):
                        continue
                    
                    # Get required parameter count (excluding those with defaults)
                    required_count = 0
                    if hasattr(function, 'parameters'):
                        required_count = sum(1 for p in function.parameters 
                                           if not hasattr(p, 'has_default') or not p.has_default)
                    
                    # Get call site file info
                    call_file = call_site.file.file_path if hasattr(call_site, 'file') and hasattr(call_site.file, 'file_path') else "unknown"
                    call_line = call_site.line if hasattr(call_site, 'line') else None
                    
                    # Check parameter count
                    arg_count = len(call_site.args)
                    if arg_count < required_count:
                        parameter_issues["incorrect_usage"].append({
                            "function": func_name,
                            "caller_file": call_file,
                            "caller_line": call_line,
                            "required_count": required_count,
                            "provided_count": arg_count
                        })
                        
                        self.issues.add_issue(create_issue(
                            message=f"Call to '{func_name}' has too few arguments ({arg_count} provided, {required_count} required)",
                            severity=IssueSeverity.ERROR,
                            file=call_file,
                            line=call_line,
                            category=IssueCategory.PARAMETER_MISMATCH,
                            symbol=func_name,
                            suggestion=f"Provide all required arguments to '{func_name}'"
                        ))
        
        # Check for inconsistent parameter types across overloaded functions
        functions_by_name = {}
        for function in self.context.get_functions():
            if hasattr(function, 'name'):
                if function.name not in functions_by_name:
                    functions_by_name[function.name] = []
                functions_by_name[function.name].append(function)
        
        for func_name, overloads in functions_by_name.items():
            if len(overloads) > 1:
                # Check for inconsistent parameter types
                for i, func1 in enumerate(overloads):
                    for func2 in overloads[i+1:]:
                        inconsistent_types = []
                        
                        # Skip if either function has no parameters
                        if not hasattr(func1, 'parameters') or not hasattr(func2, 'parameters'):
                            continue
                        
                        # Get common parameter names
                        func1_param_names = {p.name for p in func1.parameters if hasattr(p, 'name')}
                        func2_param_names = {p.name for p in func2.parameters if hasattr(p, 'name')}
                        common_params = func1_param_names.intersection(func2_param_names)
                        
                        # Check parameter types
                        for param_name in common_params:
                            # Get parameter objects
                            param1 = next((p for p in func1.parameters if hasattr(p, 'name') and p.name == param_name), None)
                            param2 = next((p for p in func2.parameters if hasattr(p, 'name') and p.name == param_name), None)
                            
                            if param1 and param2 and hasattr(param1, 'type') and hasattr(param2, 'type'):
                                if param1.type and param2.type and str(param1.type) != str(param2.type):
                                    inconsistent_types.append({
                                        "parameter": param_name,
                                        "type1": str(param1.type),
                                        "type2": str(param2.type),
                                        "function1": f"{func1.file.file_path}:{func1.line}" if hasattr(func1, 'file') and hasattr(func1.file, 'file_path') and hasattr(func1, 'line') else str(func1),
                                        "function2": f"{func2.file.file_path}:{func2.line}" if hasattr(func2, 'file') and hasattr(func2.file, 'file_path') and hasattr(func2, 'line') else str(func2)
                                    })
                        
                        if inconsistent_types:
                            parameter_issues["inconsistent_types"].extend(inconsistent_types)
                            
                            for issue in inconsistent_types:
                                func1_file = func1.file.file_path if hasattr(func1, 'file') and hasattr(func1.file, 'file_path') else "unknown"
                                func1_line = func1.line if hasattr(func1, 'line') else None
                                
                                self.issues.add_issue(create_issue(
                                    message=f"Inconsistent types for parameter '{issue['parameter']}': {issue['type1']} vs {issue['type2']}",
                                    severity=IssueSeverity.ERROR,
                                    file=func1_file,
                                    line=func1_line,
                                    category=IssueCategory.TYPE_ERROR,
                                    symbol=func_name,
                                    suggestion="Use consistent parameter types across function overloads"
                                ))
        
        # Add summary statistics
        parameter_issues["summary"] = {
            "missing_types_count": len(parameter_issues["missing_types"]),
            "inconsistent_types_count": len(parameter_issues["inconsistent_types"]),
            "unused_parameters_count": len(parameter_issues["unused_parameters"]),
            "incorrect_usage_count": len(parameter_issues["incorrect_usage"]),
            "total_issues": (
                len(parameter_issues["missing_types"]) +
                len(parameter_issues["inconsistent_types"]) +
                len(parameter_issues["unused_parameters"]) +
                len(parameter_issues["incorrect_usage"])
            )
        }
        
        return parameter_issues
    
    def _check_style_issues(self) -> Dict[str, Any]:
        """
        Check for code style issues.
        
        Returns:
            Dictionary containing style analysis results
        """
        logger.info("Analyzing code style")
        
        style_result = {
            "long_functions": [],
            "long_lines": [],
            "inconsistent_naming": [],
            "summary": {
                "long_functions_count": 0,
                "long_lines_count": 0,
                "inconsistent_naming_count": 0
            }
        }
        
        # Check for long functions (too many lines)
        for function in self.context.get_functions():
            # Skip if function should be excluded
            if self._should_skip_symbol(function):
                continue
            
            # Get function code
            if hasattr(function, 'source'):
                code = function.source
                lines = code.split('\n')
                
                # Check function length
                if len(lines) > 50:  # Threshold for "too long"
                    # Get file path and name safely
                    file_path = function.file.file_path if hasattr(function, 'file') and hasattr(function.file, 'file_path') else "unknown"
                    func_name = function.name if hasattr(function, 'name') else str(function)
                    
                    # Add to long functions list
                    style_result["long_functions"].append({
                        "name": func_name,
                        "file": file_path,
                        "line": function.line if hasattr(function, 'line') else None,
                        "line_count": len(lines)
                    })
                    
                    # Add issue
                    self.issues.add_issue(create_issue(
                        message=f"Function '{func_name}' is too long ({len(lines)} lines)",
                        severity=IssueSeverity.INFO,
                        file=file_path,
                        line=function.line if hasattr(function, 'line') else None,
                        category=IssueCategory.STYLE_ISSUE,
                        symbol=func_name,
                        suggestion="Consider breaking this function into smaller, more focused functions"
                    ))
        
        # Check for long lines
        for file in self.context.get_files():
            # Skip binary files
            if hasattr(file, 'is_binary') and file.is_binary:
                continue
            
            # Get file content
            if hasattr(file, 'content'):
                lines = file.content.split('\n')
                file_path = file.file_path if hasattr(file, 'file_path') else str(file)
                
                # Find long lines
                for i, line in enumerate(lines):
                    if len(line) > 100:  # Threshold for "too long"
                        # Skip comment lines
                        if line.lstrip().startswith('#') or line.lstrip().startswith('//'):
                            continue
                        
                        # Skip lines with strings that can't be easily broken
                        if '"' in line or "'" in line:
                            # If the line is mostly a string, skip it
                            if line.count('"') >= 2 or line.count("'") >= 2:
                                continue
                        
                        # Add to long lines list
                        style_result["long_lines"].append({
                            "file": file_path,
                            "line_number": i + 1,
                            "line_length": len(line),
                            "line_content": line[:50] + "..." if len(line) > 50 else line
                        })
                        
                        # Add issue (only for very long lines)
                        if len(line) > 120:
                            self.issues.add_issue(create_issue(
                                message=f"Line is too long ({len(line)} characters)",
                                severity=IssueSeverity.INFO,
                                file=file_path,
                                line=i + 1,
                                category=IssueCategory.STYLE_ISSUE,
                                suggestion="Consider breaking this line into multiple lines"
                            ))
        
        # Update summary
        style_result["summary"]["long_functions_count"] = len(style_result["long_functions"])
        style_result["summary"]["long_lines_count"] = len(style_result["long_lines"])
        style_result["summary"]["inconsistent_naming_count"] = len(style_result["inconsistent_naming"])
        
        return style_result
    
    def _check_implementations(self) -> Dict[str, Any]:
        """
        Check for implementation issues.
        
        Returns:
            Dictionary containing implementation analysis results
        """
        logger.info("Analyzing implementations")
        
        implementation_issues = {
            "unimplemented_functions": [],
            "empty_functions": [],
            "abstract_methods_without_implementation": [],
            "interface_methods_not_implemented": [],
            "summary": {
                "unimplemented_functions_count": 0,
                "empty_functions_count": 0,
                "abstract_methods_without_implementation_count": 0,
                "interface_methods_not_implemented_count": 0
            }
        }
        
        # Check for empty functions
        for function in self.context.get_functions():
            # Skip if function should be excluded
            if self._should_skip_symbol(function):
                continue
            
            # Get function source
            if hasattr(function, 'source'):
                source = function.source
                
                # Check if function is empty or just has 'pass'
                is_empty = False
                
                if not source or source.strip() == "":
                    is_empty = True
                else:
                    # Extract function body (skip the first line with the def)
                    body_lines = source.split('\n')[1:] if '\n' in source else []
                    
                    # Check if body is empty or just has whitespace, docstring, or pass
                    non_empty_lines = [
                        line for line in body_lines
                        if line.strip() and 
                        not line.strip().startswith('#') and
                        not (line.strip().startswith('"""') or line.strip().startswith("'''")) and
                        not line.strip() == 'pass'
                    ]
                    
                    if not non_empty_lines:
                        is_empty = True
                
                if is_empty:
                    # Get file path and name safely
                    file_path = function.file.file_path if hasattr(function, 'file') and hasattr(function.file, 'file_path') else "unknown"
                    func_name = function.name if hasattr(function, 'name') else str(function)
                    
                    # Skip interface/abstract methods that are supposed to be empty
                    is_abstract = (
                        hasattr(function, 'is_abstract') and function.is_abstract or
                        hasattr(function, 'parent') and hasattr(function.parent, 'is_interface') and function.parent.is_interface
                    )
                    
                    if not is_abstract:
                        # Add to empty functions list
                        implementation_issues["empty_functions"].append({
                            "name": func_name,
                            "file": file_path,
                            "line": function.line if hasattr(function, 'line') else None
                        })
                        
                        # Add issue
                        self.issues.add_issue(create_issue(
                            message=f"Function '{func_name}' is empty",
                            severity=IssueSeverity.WARNING,
                            file=file_path,
                            line=function.line if hasattr(function, 'line') else None,
                            category=IssueCategory.MISSING_IMPLEMENTATION,
                            symbol=func_name,
                            suggestion="Implement this function or remove it if not needed"
                        ))
        
        # Check for abstract methods without implementations
        abstract_methods = []
        for function in self.context.get_functions():
            # Skip if function should be excluded
            if self._should_skip_symbol(function):
                continue
                
            # Check if function is abstract
            is_abstract = (
                hasattr(function, 'is_abstract') and function.is_abstract or
                hasattr(function, 'decorators') and any(
                    hasattr(d, 'name') and d.name in ['abstractmethod', 'abc.abstractmethod']
                    for d in function.decorators
                )
            )
            
            if is_abstract and hasattr(function, 'parent') and hasattr(function, 'name'):
                abstract_methods.append((function.parent, function.name))
        
        # For each abstract method, check if it has implementations in subclasses
        for parent, method_name in abstract_methods:
            if not hasattr(parent, 'name'):
                continue
                
            parent_name = parent.name
            
            # Find all subclasses
            subclasses = []
            for cls in self.context.get_classes():
                if hasattr(cls, 'superclasses'):
                    for superclass in cls.superclasses:
                        if hasattr(superclass, 'name') and superclass.name == parent_name:
                            subclasses.append(cls)
            
            # Check if method is implemented in all subclasses
            for subclass in subclasses:
                if not hasattr(subclass, 'methods'):
                    continue
                    
                # Check if method is implemented
                implemented = any(
                    hasattr(m, 'name') and m.name == method_name
                    for m in subclass.methods
                )
                
                if not implemented:
                    # Get file path and name safely
                    file_path = subclass.file.file_path if hasattr(subclass, 'file') and hasattr(subclass.file, 'file_path') else "unknown"
                    cls_name = subclass.name if hasattr(subclass, 'name') else str(subclass)
                    
                    # Add to unimplemented list
                    implementation_issues["abstract_methods_without_implementation"].append({
                        "method": method_name,
                        "parent_class": parent_name,
                        "subclass": cls_name,
                        "file": file_path,
                        "line": subclass.line if hasattr(subclass, 'line') else None
                    })
                    
                    # Add issue
                    self.issues.add_issue(create_issue(
                        message=f"Class '{cls_name}' does not implement abstract method '{method_name}' from '{parent_name}'",
                        severity=IssueSeverity.ERROR,
                        file=file_path,
                        line=subclass.line if hasattr(subclass, 'line') else None,
                        category=IssueCategory.MISSING_IMPLEMENTATION,
                        symbol=cls_name,
                        suggestion=f"Implement the '{method_name}' method in '{cls_name}'"
                    ))
        
        # Update summary
        implementation_issues["summary"]["unimplemented_functions_count"] = len(implementation_issues["unimplemented_functions"])
        implementation_issues["summary"]["empty_functions_count"] = len(implementation_issues["empty_functions"])
        implementation_issues["summary"]["abstract_methods_without_implementation_count"] = len(implementation_issues["abstract_methods_without_implementation"])
        implementation_issues["summary"]["interface_methods_not_implemented_count"] = len(implementation_issues["interface_methods_not_implemented"])
        
        return implementation_issues
    
    def _calculate_maintainability(self) -> Dict[str, Any]:
        """
        Calculate maintainability metrics.
        
        Returns:
            Dictionary containing maintainability analysis results
        """
        logger.info("Analyzing maintainability")
        
        maintainability_result = {
            "function_maintainability": [],
            "low_maintainability_functions": [],
            "average_maintainability": 0.0,
            "maintainability_distribution": {
                "high": 0,
                "medium": 0,
                "low": 0
            }
        }
        
        # Process all functions to calculate maintainability
        total_maintainability = 0
        function_count = 0
        
        for function in self.context.get_functions():
            # Skip if function should be excluded
            if self._should_skip_symbol(function):
                continue
            
            # Skip if no code block
            if not hasattr(function, 'code_block'):
                continue
            
            # Calculate metrics
            complexity = self._calculate_cyclomatic_complexity(function)
            
            # Calculate Halstead volume (approximation)
            operators = 0
            operands = 0
            
            if hasattr(function, 'source'):
                code = function.source
                # Simple approximation of operators and operands
                operators = len([c for c in code if c in '+-*/=<>!&|^~%'])
                # Counting words as potential operands
                operands = len(re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', code))
            
            halstead_volume = operators * operands * math.log2(operators + operands) if operators + operands > 0 else 0
            
            # Count lines of code
            loc = len(function.source.split('\n')) if hasattr(function, 'source') else 0
            
            # Calculate maintainability index
            # Formula: 171 - 5.2 * ln(Halstead Volume) - 0.23 * (Cyclomatic Complexity) - 16.2 * ln(LOC)
            halstead_term = 5.2 * math.log(max(1, halstead_volume)) if halstead_volume > 0 else 0
            complexity_term = 0.23 * complexity
            loc_term = 16.2 * math.log(max(1, loc)) if loc > 0 else 0
            
            maintainability = 171 - halstead_term - complexity_term - loc_term
            
            # Normalize to 0-100 scale
            maintainability = max(0, min(100, maintainability * 100 / 171))
            
            # Get file path and name safely
            file_path = function.file.file_path if hasattr(function, 'file') and hasattr(function.file, 'file_path') else "unknown"
            func_name = function.name if hasattr(function, 'name') else str(function)
            
            # Add to maintainability list
            maintainability_result["function_maintainability"].append({
                "name": func_name,
                "file": file_path,
                "line": function.line if hasattr(function, 'line') else None,
                "maintainability": maintainability,
                "complexity": complexity,
                "halstead_volume": halstead_volume,
                "loc": loc
            })
            
            # Track total maintainability
            total_maintainability += maintainability
            function_count += 1
            
            # Categorize maintainability
            if maintainability >= 70:
                maintainability_result["maintainability_distribution"]["high"] += 1
            elif maintainability >= 50:
                maintainability_result["maintainability_distribution"]["medium"] += 1
            else:
                maintainability_result["maintainability_distribution"]["low"] += 1
                
                # Flag low maintainability functions
                maintainability_result["low_maintainability_functions"].append({
                    "name": func_name,
                    "file": file_path,
                    "line": function.line if hasattr(function, 'line') else None,
                    "maintainability": maintainability,
                    "complexity": complexity,
                    "halstead_volume": halstead_volume,
                    "loc": loc
                })
                
                # Add issue
                self.issues.add_issue(create_issue(
                    message=f"Function '{func_name}' has low maintainability index ({maintainability:.1f})",
                    severity=IssueSeverity.WARNING,
                    file=file_path,
                    line=function.line if hasattr(function, 'line') else None,
                    category=IssueCategory.COMPLEXITY,
                    symbol=func_name,
                    suggestion="Consider refactoring this function to improve maintainability"
                ))
        
        # Calculate average maintainability
        maintainability_result["average_maintainability"] = total_maintainability / function_count if function_count > 0 else 0.0
        
        # Sort low maintainability functions
        maintainability_result["low_maintainability_functions"].sort(key=lambda x: x["maintainability"])
        
        return maintainability_result
    
    def _should_skip_symbol(self, symbol) -> bool:
        """
        Check if a symbol should be skipped during analysis.
        
        Args:
            symbol: Symbol to check
            
        Returns:
            True if the symbol should be skipped, False otherwise
        """
        # Skip if no file
        if not hasattr(symbol, 'file'):
            return True
        
        # Skip if file should be skipped
        if self._should_skip_file(symbol.file):
            return True
        
        return False
    
    def _should_skip_file(self, file) -> bool:
        """
        Check if a file should be skipped during analysis.
        
        Args:
            file: File to check
            
        Returns:
            True if the file should be skipped, False otherwise
        """
        # Skip binary files
        if hasattr(file, 'is_binary') and file.is_binary:
            return True
        
        # Get file path
        file_path = file.file_path if hasattr(file, 'file_path') else str(file)
        
        # Skip test files
        if "test" in file_path.lower():
            return True
        
        # Skip generated files
        if "generated" in file_path.lower():
            return True
        
        # Skip files in ignore list
        for pattern in self.context.file_ignore_list:
            if pattern in file_path:
                return True
        
        return False