"""
Feature Analyzer Module

This module provides functionality for analyzing code features and functions.
"""

import os
import ast
import logging
from typing import Dict, List, Optional, Any, Union, Set, cast
from pathlib import Path
from dataclasses import dataclass, field

# Import from codegen SDK
from codegen import Codebase
from codegen.sdk.core.file import SourceFile
from codegen.sdk.core.function import Function
from codegen.sdk.core.class_definition import Class
from codegen.sdk.core.symbol import Symbol
from codegen.sdk.enums import EdgeType, SymbolType

# Import from existing analysis modules
from codegen_on_oss.analysis.analysis import CodeAnalyzer
from codegen_on_oss.analysis.codebase_context import CodebaseContext
from codegen_on_oss.analysis.codebase_analysis import (
    get_codebase_summary,
    get_file_summary,
    get_class_summary,
    get_function_summary,
    get_symbol_summary
)

logger = logging.getLogger(__name__)

@dataclass
class FunctionAnalysisResult:
    """
    Result of analyzing a function.
    """
    function_name: str
    complexity: int
    parameters: List[str]
    return_type: str
    line_count: int
    dependencies: List[str] = field(default_factory=list)
    callers: List[str] = field(default_factory=list)
    is_tested: bool = False
    test_coverage: Optional[float] = None
    issues: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary."""
        return {
            "function_name": self.function_name,
            "complexity": self.complexity,
            "parameters": self.parameters,
            "return_type": self.return_type,
            "line_count": self.line_count,
            "dependencies": self.dependencies,
            "callers": self.callers,
            "is_tested": self.is_tested,
            "test_coverage": self.test_coverage,
            "issues": self.issues
        }


@dataclass
class FeatureAnalysisResult:
    """
    Result of analyzing a feature (file or directory).
    """
    feature_path: str
    is_file: bool
    line_count: int
    function_count: int
    class_count: int
    complexity: float
    functions: List[FunctionAnalysisResult] = field(default_factory=list)
    issues: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary."""
        return {
            "feature_path": self.feature_path,
            "is_file": self.is_file,
            "line_count": self.line_count,
            "function_count": self.function_count,
            "class_count": self.class_count,
            "complexity": self.complexity,
            "functions": [func.to_dict() for func in self.functions],
            "issues": self.issues
        }


class FeatureAnalyzer:
    """
    Analyzer for code features and functions.
    
    This class provides functionality for analyzing specific features (files or directories)
    and functions in a codebase.
    """
    
    def __init__(self, codebase: Codebase):
        """
        Initialize a new FeatureAnalyzer.
        
        Args:
            codebase: The codebase to analyze
        """
        self.codebase = codebase
        self.code_analyzer = CodeAnalyzer(codebase)
    
    def analyze_function(self, function_name: str) -> FunctionAnalysisResult:
        """
        Analyze a specific function in the codebase.
        
        Args:
            function_name: Name of the function to analyze
            
        Returns:
            A FunctionAnalysisResult object containing the analysis results
        """
        # Find the function in the codebase
        function = self._find_function(function_name)
        
        if not function:
            raise ValueError(f"Function '{function_name}' not found in the codebase")
        
        # Calculate complexity
        complexity = self._calculate_complexity(function)
        
        # Get parameters
        parameters = [param.name for param in function.parameters]
        
        # Get return type
        return_type = str(function.return_type) if function.return_type else "None"
        
        # Get line count
        line_count = len(function.code_block.source.splitlines()) if function.code_block else 0
        
        # Get dependencies
        dependencies = self._get_function_dependencies(function)
        
        # Get callers
        callers = self._get_function_callers(function)
        
        # Check if the function is tested
        is_tested, test_coverage = self._check_function_tests(function)
        
        # Check for issues
        issues = self._check_function_issues(function)
        
        # Create the result
        result = FunctionAnalysisResult(
            function_name=function.name,
            complexity=complexity,
            parameters=parameters,
            return_type=return_type,
            line_count=line_count,
            dependencies=dependencies,
            callers=callers,
            is_tested=is_tested,
            test_coverage=test_coverage,
            issues=issues
        )
        
        return result
    
    def analyze_feature(self, feature_path: str) -> FeatureAnalysisResult:
        """
        Analyze a specific feature (file or directory) in the codebase.
        
        Args:
            feature_path: Path to the feature to analyze
            
        Returns:
            A FeatureAnalysisResult object containing the analysis results
        """
        # Check if the feature is a file or directory
        is_file = self._is_file_path(feature_path)
        
        # Get files in the feature
        files = self._get_files_in_feature(feature_path)
        
        if not files:
            raise ValueError(f"Feature '{feature_path}' not found in the codebase")
        
        # Get functions in the feature
        functions = self._get_functions_in_feature(feature_path)
        
        # Get classes in the feature
        classes = self._get_classes_in_feature(feature_path)
        
        # Calculate line count
        line_count = sum(len(file.content.splitlines()) for file in files)
        
        # Calculate function count
        function_count = len(functions)
        
        # Calculate class count
        class_count = len(classes)
        
        # Calculate average complexity
        complexity = self._calculate_average_complexity(functions)
        
        # Analyze each function
        function_results = []
        for func in functions:
            try:
                result = self.analyze_function(func.name)
                function_results.append(result)
            except Exception as e:
                logger.warning(f"Failed to analyze function '{func.name}': {e}")
        
        # Check for issues
        issues = self._check_feature_issues(feature_path, files, functions, classes)
        
        # Create the result
        result = FeatureAnalysisResult(
            feature_path=feature_path,
            is_file=is_file,
            line_count=line_count,
            function_count=function_count,
            class_count=class_count,
            complexity=complexity,
            functions=function_results,
            issues=issues
        )
        
        return result
    
    def _find_function(self, function_name: str) -> Optional[Function]:
        """
        Find a function in the codebase by name.
        
        Args:
            function_name: Name of the function to find
            
        Returns:
            The function object, or None if not found
        """
        for func in self.codebase.functions:
            if func.name == function_name:
                return func
        return None
    
    def _is_file_path(self, path: str) -> bool:
        """
        Check if a path is a file or directory.
        
        Args:
            path: Path to check
            
        Returns:
            True if the path is a file, False if it's a directory
        """
        for file in self.codebase.files:
            if file.path == path:
                return True
        return False
    
    def _get_files_in_feature(self, feature_path: str) -> List[SourceFile]:
        """
        Get all files in a feature.
        
        Args:
            feature_path: Path to the feature
            
        Returns:
            A list of SourceFile objects
        """
        if self._is_file_path(feature_path):
            # Feature is a file
            for file in self.codebase.files:
                if file.path == feature_path:
                    return [file]
            return []
        else:
            # Feature is a directory
            return [file for file in self.codebase.files if file.path.startswith(feature_path)]
    
    def _get_functions_in_feature(self, feature_path: str) -> List[Function]:
        """
        Get all functions in a feature.
        
        Args:
            feature_path: Path to the feature
            
        Returns:
            A list of Function objects
        """
        if self._is_file_path(feature_path):
            # Feature is a file
            return [func for func in self.codebase.functions if func.file_path == feature_path]
        else:
            # Feature is a directory
            return [func for func in self.codebase.functions if func.file_path.startswith(feature_path)]
    
    def _get_classes_in_feature(self, feature_path: str) -> List[Class]:
        """
        Get all classes in a feature.
        
        Args:
            feature_path: Path to the feature
            
        Returns:
            A list of Class objects
        """
        if self._is_file_path(feature_path):
            # Feature is a file
            return [cls for cls in self.codebase.classes if cls.file_path == feature_path]
        else:
            # Feature is a directory
            return [cls for cls in self.codebase.classes if cls.file_path.startswith(feature_path)]
    
    def _calculate_complexity(self, function: Function) -> int:
        """
        Calculate the cyclomatic complexity of a function.
        
        Args:
            function: The function to analyze
            
        Returns:
            The cyclomatic complexity value
        """
        # Start with 1 (base complexity)
        complexity = 1
        
        # Count decision points
        if hasattr(function, "code_block") and function.code_block:
            code = function.code_block.source
            complexity += code.count("if ")
            complexity += code.count("elif ")
            complexity += code.count("else:")
            complexity += code.count("for ")
            complexity += code.count("while ")
            complexity += code.count("except ")
            complexity += code.count(" and ")
            complexity += code.count(" or ")
        
        return complexity
    
    def _calculate_average_complexity(self, functions: List[Function]) -> float:
        """
        Calculate the average cyclomatic complexity of a list of functions.
        
        Args:
            functions: The functions to analyze
            
        Returns:
            The average cyclomatic complexity value
        """
        if not functions:
            return 0.0
        
        total_complexity = sum(self._calculate_complexity(func) for func in functions)
        return total_complexity / len(functions)
    
    def _get_function_dependencies(self, function: Function) -> List[str]:
        """
        Get the dependencies of a function.
        
        Args:
            function: The function to analyze
            
        Returns:
            A list of function names that this function depends on
        """
        dependencies = []
        
        # Get function calls
        if hasattr(function, "function_calls"):
            for call in function.function_calls:
                if call.name not in dependencies:
                    dependencies.append(call.name)
        
        return dependencies
    
    def _get_function_callers(self, function: Function) -> List[str]:
        """
        Get the callers of a function.
        
        Args:
            function: The function to analyze
            
        Returns:
            A list of function names that call this function
        """
        callers = []
        
        # Find functions that call this function
        for func in self.codebase.functions:
            if hasattr(func, "function_calls"):
                for call in func.function_calls:
                    if call.name == function.name and func.name not in callers:
                        callers.append(func.name)
        
        return callers
    
    def _check_function_tests(self, function: Function) -> Tuple[bool, Optional[float]]:
        """
        Check if a function is tested.
        
        Args:
            function: The function to analyze
            
        Returns:
            A tuple of (is_tested, test_coverage)
        """
        # This is a simplified implementation
        # In a real implementation, you would check for test files and coverage data
        
        # Check if there's a test file for this function
        function_name = function.name
        file_path = function.file_path
        
        # Check if there's a test file with a test for this function
        for file in self.codebase.files:
            if "test_" in file.path and file_path.split("/")[-1] in file.path:
                # Check if the function name is mentioned in the test file
                if function_name in file.content:
                    return True, None
        
        return False, None
    
    def _check_function_issues(self, function: Function) -> List[Dict[str, Any]]:
        """
        Check for issues in a function.
        
        Args:
            function: The function to analyze
            
        Returns:
            A list of issues found in the function
        """
        issues = []
        
        # Check for high complexity
        complexity = self._calculate_complexity(function)
        if complexity > 10:
            issues.append({
                "type": "high_complexity",
                "severity": "warning",
                "message": f"Function has high cyclomatic complexity ({complexity})"
            })
        
        # Check for long function
        if hasattr(function, "code_block") and function.code_block:
            line_count = len(function.code_block.source.splitlines())
            if line_count > 50:
                issues.append({
                    "type": "long_function",
                    "severity": "warning",
                    "message": f"Function is too long ({line_count} lines)"
                })
        
        # Check for missing return type
        if not function.return_type:
            issues.append({
                "type": "missing_return_type",
                "severity": "info",
                "message": "Function is missing a return type annotation"
            })
        
        # Check for missing parameter types
        for param in function.parameters:
            if not param.type:
                issues.append({
                    "type": "missing_parameter_type",
                    "severity": "info",
                    "message": f"Parameter '{param.name}' is missing a type annotation"
                })
        
        # Check for missing docstring
        if not function.docstring:
            issues.append({
                "type": "missing_docstring",
                "severity": "info",
                "message": "Function is missing a docstring"
            })
        
        return issues
    
    def _check_feature_issues(
        self,
        feature_path: str,
        files: List[SourceFile],
        functions: List[Function],
        classes: List[Class]
    ) -> List[Dict[str, Any]]:
        """
        Check for issues in a feature.
        
        Args:
            feature_path: Path to the feature
            files: Files in the feature
            functions: Functions in the feature
            classes: Classes in the feature
            
        Returns:
            A list of issues found in the feature
        """
        issues = []
        
        # Check for large files
        for file in files:
            line_count = len(file.content.splitlines())
            if line_count > 500:
                issues.append({
                    "type": "large_file",
                    "severity": "warning",
                    "message": f"File '{file.path}' is too large ({line_count} lines)"
                })
        
        # Check for high complexity
        complexity = self._calculate_average_complexity(functions)
        if complexity > 7:
            issues.append({
                "type": "high_average_complexity",
                "severity": "warning",
                "message": f"Feature has high average cyclomatic complexity ({complexity:.2f})"
            })
        
        # Check for missing tests
        tested_functions = 0
        for func in functions:
            is_tested, _ = self._check_function_tests(func)
            if is_tested:
                tested_functions += 1
        
        if functions and tested_functions / len(functions) < 0.5:
            issues.append({
                "type": "low_test_coverage",
                "severity": "warning",
                "message": f"Feature has low test coverage ({tested_functions}/{len(functions)} functions tested)"
            })
        
        return issues
