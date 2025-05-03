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
        """
        Convert the function analysis result to a dictionary.
        
        Returns:
            Dictionary representation of the function analysis result.
        """
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
    Result of analyzing a feature.
    """
    feature_path: str
    functions: List[Dict[str, Any]] = field(default_factory=list)
    classes: List[Dict[str, Any]] = field(default_factory=list)
    complexity: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    issues: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the feature analysis result to a dictionary.
        
        Returns:
            Dictionary representation of the feature analysis result.
        """
        return {
            "feature_path": self.feature_path,
            "functions": self.functions,
            "classes": self.classes,
            "complexity": self.complexity,
            "dependencies": self.dependencies,
            "issues": self.issues
        }

class FeatureAnalyzer:
    """
    Analyzer for features in a codebase.
    
    This class provides functionality to analyze specific functions, classes,
    and features (files or directories) in a codebase.
    """
    
    def __init__(self, codebase: Codebase):
        """
        Initialize a new FeatureAnalyzer.
        
        Args:
            codebase: The codebase to analyze
        """
        self.codebase = codebase
    
    def analyze_function(self, function_name: str) -> FunctionAnalysisResult:
        """
        Analyze a specific function in the codebase.
        
        Args:
            function_name: The fully qualified name of the function to analyze
            
        Returns:
            A FunctionAnalysisResult with the analysis results
            
        Raises:
            ValueError: If the function is not found in the codebase
        """
        # Find the function in the codebase
        function = None
        
        for func in self.codebase.functions:
            if func.qualified_name == function_name:
                function = func
                break
        
        if not function:
            raise ValueError(f"Function {function_name} not found in the codebase")
        
        # Calculate cyclomatic complexity
        complexity = self._calculate_cyclomatic_complexity(function)
        
        # Get parameters
        parameters = []
        
        if hasattr(function, "parameters"):
            for param in function.parameters:
                param_name = param.name if hasattr(param, "name") else str(param)
                param_type = param.type if hasattr(param, "type") else "unknown"
                parameters.append(f"{param_name}: {param_type}")
        
        # Get return type
        return_type = "unknown"
        
        if hasattr(function, "return_type"):
            return_type = function.return_type
        
        # Get line count
        line_count = 0
        
        if hasattr(function, "code_block") and hasattr(function.code_block, "source"):
            line_count = len(function.code_block.source.splitlines())
        
        # Get dependencies (functions and classes called by this function)
        dependencies = []
        
        if hasattr(function, "calls"):
            for call in function.calls:
                if hasattr(call, "target") and hasattr(call.target, "qualified_name"):
                    dependencies.append(call.target.qualified_name)
        
        # Get callers (functions that call this function)
        callers = []
        
        for func in self.codebase.functions:
            if hasattr(func, "calls"):
                for call in func.calls:
                    if hasattr(call, "target") and hasattr(call.target, "qualified_name"):
                        if call.target.qualified_name == function_name:
                            callers.append(func.qualified_name)
        
        # Check if the function is tested
        is_tested = False
        test_coverage = None
        
        # Look for test files that might test this function
        function_name_parts = function_name.split(".")
        function_short_name = function_name_parts[-1]
        
        for file in self.codebase.files:
            if "test" in file.filepath.lower() and function_short_name.lower() in file.content.lower():
                is_tested = True
                break
        
        # Identify potential issues
        issues = []
        
        # Check for high complexity
        if complexity > 10:
            issues.append({
                "issue_type": "high_complexity",
                "severity": "warning",
                "message": f"Function has high cyclomatic complexity ({complexity})"
            })
        
        # Check for long functions
        if line_count > 50:
            issues.append({
                "issue_type": "long_function",
                "severity": "warning",
                "message": f"Function is very long ({line_count} lines)"
            })
        
        # Check for many parameters
        if len(parameters) > 5:
            issues.append({
                "issue_type": "many_parameters",
                "severity": "warning",
                "message": f"Function has many parameters ({len(parameters)})"
            })
        
        # Check for lack of testing
        if not is_tested:
            issues.append({
                "issue_type": "not_tested",
                "severity": "info",
                "message": "Function does not appear to be tested"
            })
        
        return FunctionAnalysisResult(
            function_name=function_name,
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
    
    def analyze_class(self, class_name: str) -> Dict[str, Any]:
        """
        Analyze a specific class in the codebase.
        
        Args:
            class_name: The fully qualified name of the class to analyze
            
        Returns:
            A dictionary with the analysis results
            
        Raises:
            ValueError: If the class is not found in the codebase
        """
        # Find the class in the codebase
        cls = None
        
        for c in self.codebase.classes:
            if c.qualified_name == class_name:
                cls = c
                break
        
        if not cls:
            raise ValueError(f"Class {class_name} not found in the codebase")
        
        # Get methods
        methods = []
        
        if hasattr(cls, "methods"):
            for method in cls.methods:
                if hasattr(method, "qualified_name"):
                    methods.append(method.qualified_name)
        
        # Get attributes
        attributes = []
        
        if hasattr(cls, "attributes"):
            for attr in cls.attributes:
                if hasattr(attr, "name"):
                    attr_name = attr.name
                    attr_type = attr.type if hasattr(attr, "type") else "unknown"
                    attributes.append(f"{attr_name}: {attr_type}")
        
        # Get parent classes
        parent_classes = []
        
        if hasattr(cls, "parent_classes"):
            for parent in cls.parent_classes:
                if hasattr(parent, "qualified_name"):
                    parent_classes.append(parent.qualified_name)
        
        # Get child classes
        child_classes = []
        
        for c in self.codebase.classes:
            if hasattr(c, "parent_classes"):
                for parent in c.parent_classes:
                    if hasattr(parent, "qualified_name") and parent.qualified_name == class_name:
                        child_classes.append(c.qualified_name)
        
        # Calculate class complexity (average of method complexities)
        method_complexities = []
        
        if hasattr(cls, "methods"):
            for method in cls.methods:
                if hasattr(method, "qualified_name"):
                    try:
                        complexity = self._calculate_cyclomatic_complexity(method)
                        method_complexities.append(complexity)
                    except Exception as e:
                        logger.warning(f"Error calculating complexity for method {method.qualified_name}: {e}")
        
        avg_complexity = sum(method_complexities) / len(method_complexities) if method_complexities else 0
        
        # Check if the class is tested
        is_tested = False
        
        # Look for test files that might test this class
        class_name_parts = class_name.split(".")
        class_short_name = class_name_parts[-1]
        
        for file in self.codebase.files:
            if "test" in file.filepath.lower() and class_short_name.lower() in file.content.lower():
                is_tested = True
                break
        
        # Identify potential issues
        issues = []
        
        # Check for high complexity
        if avg_complexity > 10:
            issues.append({
                "issue_type": "high_complexity",
                "severity": "warning",
                "message": f"Class has high average method complexity ({avg_complexity:.2f})"
            })
        
        # Check for many methods
        if len(methods) > 20:
            issues.append({
                "issue_type": "many_methods",
                "severity": "warning",
                "message": f"Class has many methods ({len(methods)})"
            })
        
        # Check for many attributes
        if len(attributes) > 15:
            issues.append({
                "issue_type": "many_attributes",
                "severity": "warning",
                "message": f"Class has many attributes ({len(attributes)})"
            })
        
        # Check for lack of testing
        if not is_tested:
            issues.append({
                "issue_type": "not_tested",
                "severity": "info",
                "message": "Class does not appear to be tested"
            })
        
        return {
            "class_name": class_name,
            "methods": methods,
            "attributes": attributes,
            "parent_classes": parent_classes,
            "child_classes": child_classes,
            "avg_complexity": avg_complexity,
            "is_tested": is_tested,
            "issues": issues
        }
    
    def analyze_feature(self, feature_path: str) -> FeatureAnalysisResult:
        """
        Analyze a specific feature (file or directory) in the codebase.
        
        Args:
            feature_path: The path to the feature to analyze
            
        Returns:
            A FeatureAnalysisResult with the analysis results
            
        Raises:
            ValueError: If the feature is not found in the codebase
        """
        # Normalize the feature path
        feature_path = os.path.normpath(feature_path)
        
        # Find all files in the feature path
        feature_files = []
        
        for file in self.codebase.files:
            file_path = os.path.normpath(file.filepath)
            
            if file_path == feature_path or file_path.startswith(feature_path + os.sep):
                feature_files.append(file)
        
        if not feature_files:
            raise ValueError(f"Feature {feature_path} not found in the codebase")
        
        # Find all functions in the feature
        feature_functions = []
        
        for func in self.codebase.functions:
            if hasattr(func, "filepath"):
                func_path = os.path.normpath(func.filepath)
                
                if func_path == feature_path or func_path.startswith(feature_path + os.sep):
                    feature_functions.append(func)
        
        # Find all classes in the feature
        feature_classes = []
        
        for cls in self.codebase.classes:
            if hasattr(cls, "filepath"):
                cls_path = os.path.normpath(cls.filepath)
                
                if cls_path == feature_path or cls_path.startswith(feature_path + os.sep):
                    feature_classes.append(cls)
        
        # Analyze each function
        function_analyses = []
        
        for func in feature_functions:
            if hasattr(func, "qualified_name"):
                try:
                    analysis = self.analyze_function(func.qualified_name)
                    function_analyses.append(analysis.to_dict())
                except Exception as e:
                    logger.warning(f"Error analyzing function {func.qualified_name}: {e}")
        
        # Analyze each class
        class_analyses = []
        
        for cls in feature_classes:
            if hasattr(cls, "qualified_name"):
                try:
                    analysis = self.analyze_class(cls.qualified_name)
                    class_analyses.append(analysis)
                except Exception as e:
                    logger.warning(f"Error analyzing class {cls.qualified_name}: {e}")
        
        # Calculate overall complexity metrics
        total_complexity = sum(analysis["complexity"] for analysis in function_analyses)
        avg_complexity = total_complexity / len(function_analyses) if function_analyses else 0
        
        complexity_metrics = {
            "total_complexity": total_complexity,
            "avg_complexity": avg_complexity,
            "num_functions": len(function_analyses),
            "num_classes": len(class_analyses),
            "num_files": len(feature_files)
        }
        
        # Get dependencies (imports from outside the feature)
        dependencies = set()
        
        for file in feature_files:
            if hasattr(file, "imports"):
                for imp in file.imports:
                    if hasattr(imp, "module_name"):
                        # Check if the import is from outside the feature
                        is_external = True
                        
                        for feature_file in feature_files:
                            if hasattr(feature_file, "module_name") and feature_file.module_name == imp.module_name:
                                is_external = False
                                break
                        
                        if is_external:
                            dependencies.add(imp.module_name)
        
        # Identify potential issues
        issues = []
        
        # Check for high complexity
        if avg_complexity > 10:
            issues.append({
                "issue_type": "high_complexity",
                "severity": "warning",
                "message": f"Feature has high average function complexity ({avg_complexity:.2f})"
            })
        
        # Check for many dependencies
        if len(dependencies) > 20:
            issues.append({
                "issue_type": "many_dependencies",
                "severity": "warning",
                "message": f"Feature has many external dependencies ({len(dependencies)})"
            })
        
        # Check for untested functions
        untested_functions = [
            analysis["function_name"] for analysis in function_analyses
            if not analysis["is_tested"]
        ]
        
        if untested_functions:
            issues.append({
                "issue_type": "untested_functions",
                "severity": "info",
                "message": f"{len(untested_functions)} functions appear to be untested",
                "details": untested_functions[:5]  # Show up to 5 untested functions
            })
        
        return FeatureAnalysisResult(
            feature_path=feature_path,
            functions=function_analyses,
            classes=class_analyses,
            complexity=complexity_metrics,
            dependencies=list(dependencies),
            issues=issues
        )
    
    def _calculate_cyclomatic_complexity(self, function: CodegenFunction) -> int:
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
        if hasattr(function, "code_block"):
            # Count if statements
            if_statements = function.code_block.find_all("if_statement")
            complexity += len(if_statements)
            
            # Count for loops
            for_loops = function.code_block.find_all("for_statement")
            complexity += len(for_loops)
            
            # Count while loops
            while_loops = function.code_block.find_all("while_statement")
            complexity += len(while_loops)
            
            # Count try-catch blocks
            try_catches = function.code_block.find_all("try_statement")
            complexity += len(try_catches)
            
            # Count logical operators in conditions
            binary_expressions = function.code_block.find_all("binary_expression")
            for expr in binary_expressions:
                if hasattr(expr, "operator") and expr.operator in ["&&", "||", "and", "or"]:
                    complexity += 1
            
            # Count ternary expressions
            ternary_expressions = function.code_block.find_all("ternary_expression")
            complexity += len(ternary_expressions)
            
            # Count switch cases
            switch_statements = function.code_block.find_all("switch_statement")
            for switch in switch_statements:
                if hasattr(switch, "cases"):
                    complexity += len(switch.cases)
        
        return complexity
