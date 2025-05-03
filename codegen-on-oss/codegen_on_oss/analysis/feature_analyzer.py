"""
Feature Analyzer Module

This module provides functionality for analyzing features (files, directories, functions)
in a codebase.
"""

import os
import re
import ast
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Set, Union

from codegen import Codebase
from codegen.sdk.core.function import Function
from codegen.sdk.core.file import SourceFile
from codegen.sdk.core.class_definition import Class
from codegen.sdk.core.symbol import Symbol

class CodeAnalyzer:
    """
    Analyzer for code in a codebase.
    
    This class provides functionality to analyze code structures, complexity,
    and other metrics in a codebase.
    """
    
    def __init__(self, codebase: Codebase):
        """
        Initialize the CodeAnalyzer.
        
        Args:
            codebase: The codebase to analyze
        """
        self.codebase = codebase
        
    def calculate_complexity(self, function: Function) -> int:
        """
        Calculate the cyclomatic complexity of a function.
        
        Args:
            function: The function to analyze
            
        Returns:
            The cyclomatic complexity score
        """
        # Start with 1 (base complexity)
        complexity = 1
        
        # Get the function's code
        if not hasattr(function, "code_block") or not function.code_block:
            return complexity
            
        code = function.code_block.source
        
        # Count decision points
        complexity += code.count("if ")
        complexity += code.count("elif ")
        complexity += code.count("for ")
        complexity += code.count("while ")
        complexity += code.count("except")
        complexity += code.count("with ")
        complexity += code.count(" and ")
        complexity += code.count(" or ")
        complexity += code.count("?")  # Ternary operator
        
        return complexity


@dataclass
class FunctionAnalysisResult:
    """
    Result of analyzing a function.
    """
    function_name: str
    complexity: int
    line_count: int
    parameter_count: int
    return_type: str
    docstring: Optional[str] = None
    parameters: List[str] = field(default_factory=list)
    issues: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary."""
        return {
            "function_name": self.function_name,
            "complexity": self.complexity,
            "line_count": self.line_count,
            "parameter_count": self.parameter_count,
            "return_type": self.return_type,
            "docstring": self.docstring,
            "parameters": self.parameters,
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
        Initialize the FeatureAnalyzer.
        
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
        
        # Get docstring
        docstring = function.docstring if hasattr(function, "docstring") else None
        
        # Create the result
        result = FunctionAnalysisResult(
            function_name=function.name,
            complexity=complexity,
            line_count=line_count,
            parameter_count=len(parameters),
            return_type=return_type,
            docstring=docstring,
            parameters=parameters
        )
        
        # Add issues
        if complexity > 10:
            result.issues.append({
                "type": "complexity",
                "message": f"Function has high cyclomatic complexity ({complexity})",
                "severity": "warning"
            })
            
        if line_count > 50:
            result.issues.append({
                "type": "length",
                "message": f"Function is too long ({line_count} lines)",
                "severity": "warning"
            })
            
        if not docstring:
            result.issues.append({
                "type": "documentation",
                "message": "Function lacks a docstring",
                "severity": "info"
            })
            
        return result
    
    def analyze_feature(self, feature_path: str) -> FeatureAnalysisResult:
        """
        Analyze a specific feature (file or directory) in the codebase.
        
        Args:
            feature_path: Path to the feature to analyze
            
        Returns:
            A FeatureAnalysisResult object containing the analysis results
        """
        # Check if the feature is a file
        file = self.codebase.get_file(feature_path)
        is_file = file is not None
        
        if is_file and file is not None:
            return self._analyze_file(file)
        else:
            return self._analyze_directory(feature_path)
    
    def _find_function(self, function_name: str) -> Optional[Function]:
        """
        Find a function by name in the codebase.
        
        Args:
            function_name: Name of the function to find
            
        Returns:
            The Function object if found, None otherwise
        """
        for func in self.codebase.functions:
            if func.name == function_name or func.qualified_name == function_name:
                return func
        return None
    
    def _calculate_complexity(self, function: Function) -> int:
        """
        Calculate the cyclomatic complexity of a function.
        
        Args:
            function: The function to analyze
            
        Returns:
            The cyclomatic complexity score
        """
        return self.code_analyzer.calculate_complexity(function)
    
    def _analyze_file(self, file: SourceFile) -> FeatureAnalysisResult:
        """
        Analyze a file.
        
        Args:
            file: The file to analyze
            
        Returns:
            A FeatureAnalysisResult object containing the analysis results
        """
        # Get functions in the file
        functions = []
        for func in self.codebase.functions:
            if hasattr(func, "file") and func.file and func.file.name == file.name:
                functions.append(func)
        
        # Get classes in the file
        classes = []
        for cls in self.codebase.classes:
            if hasattr(cls, "file") and cls.file and cls.file.name == file.name:
                classes.append(cls)
        
        # Calculate line count
        line_count = len(file.source.splitlines()) if hasattr(file, "source") else 0
        
        # Analyze functions
        function_results = []
        total_complexity = 0
        
        for func in functions:
            try:
                result = self.analyze_function(func.name)
                function_results.append(result)
                total_complexity += result.complexity
            except Exception as e:
                # Skip functions that can't be analyzed
                pass
        
        # Calculate average complexity
        avg_complexity = total_complexity / len(function_results) if function_results else 0
        
        # Create the result
        feature_result: FeatureAnalysisResult = FeatureAnalysisResult(
            feature_path=file.name,
            is_file=True,
            line_count=line_count,
            function_count=len(functions),
            class_count=len(classes),
            complexity=avg_complexity,
            functions=function_results
        )
        
        # Add issues
        if avg_complexity > 8:
            feature_result.issues.append({
                "type": "complexity",
                "message": f"File has high average complexity ({avg_complexity:.2f})",
                "severity": "warning"
            })
            
        if line_count > 500:
            feature_result.issues.append({
                "type": "length",
                "message": f"File is too long ({line_count} lines)",
                "severity": "warning"
            })
            
        return feature_result
    
    def _analyze_directory(self, directory_path: str) -> FeatureAnalysisResult:
        """
        Analyze a directory.
        
        Args:
            directory_path: Path to the directory to analyze
            
        Returns:
            A FeatureAnalysisResult object containing the analysis results
        """
        # Get files in the directory
        files = []
        for file in self.codebase.files:
            if file.name.startswith(directory_path):
                files.append(file)
        
        # Get functions in the directory
        functions = []
        for func in self.codebase.functions:
            if hasattr(func, "file") and func.file and func.file.name.startswith(directory_path):
                functions.append(func)
        
        # Get classes in the directory
        classes = []
        for cls in self.codebase.classes:
            if hasattr(cls, "file") and cls.file and cls.file.name.startswith(directory_path):
                classes.append(cls)
        
        # Calculate total line count
        line_count = 0
        for file in files:
            line_count += len(file.source.splitlines()) if hasattr(file, "source") else 0
        
        # Analyze functions
        function_results = []
        total_complexity = 0
        
        for func in functions:
            try:
                result = self.analyze_function(func.name)
                function_results.append(result)
                total_complexity += result.complexity
            except Exception as e:
                # Skip functions that can't be analyzed
                pass
        
        # Calculate average complexity
        avg_complexity = total_complexity / len(function_results) if function_results else 0
        
        # Create the result
        feature_result: FeatureAnalysisResult = FeatureAnalysisResult(
            feature_path=directory_path,
            is_file=False,
            line_count=line_count,
            function_count=len(functions),
            class_count=len(classes),
            complexity=avg_complexity,
            functions=function_results
        )
        
        # Add issues
        if avg_complexity > 8:
            feature_result.issues.append({
                "type": "complexity",
                "message": f"Directory has high average complexity ({avg_complexity:.2f})",
                "severity": "warning"
            })
            
        if len(files) > 20:
            feature_result.issues.append({
                "type": "structure",
                "message": f"Directory contains too many files ({len(files)})",
                "severity": "info"
            })
            
        return feature_result
    
    def get_function_dependencies(self, function_name: str) -> Tuple[List[str], List[str]]:
        """
        Get the dependencies and dependents of a function.
        
        Args:
            function_name: Name of the function to analyze
            
        Returns:
            A tuple of (dependencies, dependents)
        """
        function = self._find_function(function_name)
        if not function:
            return ([], [])
        
        # Get dependencies
        dependencies = []
        if hasattr(function, "dependencies"):
            for dep in function.dependencies:
                if hasattr(dep, "name"):
                    dependencies.append(dep.name)
        
        # Get dependents
        dependents = []
        for func in self.codebase.functions:
            if hasattr(func, "dependencies"):
                for dep in func.dependencies:
                    if hasattr(dep, "name") and dep.name == function.name:
                        dependents.append(func.name)
        
        return (dependencies, dependents)
