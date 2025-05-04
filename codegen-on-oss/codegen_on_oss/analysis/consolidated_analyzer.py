"""
Consolidated Analyzer Module

This module provides a unified interface for all code analysis functionality,
integrating various analysis components into a cohesive system.
"""

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

# Import from codegen SDK
from codegen import Codebase
from codegen.sdk.core.class_definition import Class
from codegen.sdk.core.expressions.binary_expression import BinaryExpression
from codegen.sdk.core.expressions.comparison_expression import ComparisonExpression
from codegen.sdk.core.expressions.unary_expression import UnaryExpression
from codegen.sdk.core.file import SourceFile
from codegen.sdk.core.function import Function
from codegen.sdk.core.statements.for_loop_statement import ForLoopStatement
from codegen.sdk.core.statements.if_block_statement import IfBlockStatement
from codegen.sdk.core.statements.try_catch_statement import TryCatchStatement
from codegen.sdk.core.statements.while_statement import WhileStatement

# Import from existing analysis modules
from codegen_on_oss.analysis.codebase_context import CodebaseContext

logger = logging.getLogger(__name__)


@dataclass
class AnalysisIssue:
    """Represents an issue found during code analysis."""
    
    issue_type: str
    severity: str
    file_path: str
    line_number: Optional[int] = None
    description: str = ""
    suggested_fix: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the issue to a dictionary."""
        return {
            "issue_type": self.issue_type,
            "severity": self.severity,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "description": self.description,
            "suggested_fix": self.suggested_fix,
        }


@dataclass
class AnalysisResult:
    """Represents the result of a code analysis operation."""
    
    success: bool
    issues: List[AnalysisIssue] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    summary: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary."""
        return {
            "success": self.success,
            "issues": [issue.to_dict() for issue in self.issues],
            "metrics": self.metrics,
            "summary": self.summary,
            "timestamp": self.timestamp.isoformat(),
        }


class CodeAnalyzer:
    """
    Central class for code analysis that integrates all analysis components.
    
    This class serves as the main entry point for all code analysis functionality,
    including complexity analysis, feature analysis, code integrity checks,
    and diff analysis.
    """
    
    def __init__(
        self,
        codebase: Optional[Codebase] = None,
        repo_path: Optional[str] = None,
        context: Optional[CodebaseContext] = None,
    ):
        """
        Initialize the code analyzer.
        
        Args:
            codebase: A Codebase object to analyze
            repo_path: Path to the repository to analyze
            context: Optional CodebaseContext for additional context
        """
        self.codebase = codebase
        self.repo_path = repo_path
        self.context = context or CodebaseContext()
        
        if self.codebase is None and self.repo_path:
            self.codebase = Codebase.from_directory(self.repo_path)
    
    # Basic Analysis Methods
    
    def get_codebase_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the entire codebase.
        
        Returns:
            A dictionary containing summary information about the codebase
        """
        if not self.codebase:
            return {"error": "No codebase loaded"}
        
        return {
            "files": len(self.codebase.files),
            "functions": len(list(self.codebase.functions)),
            "classes": len(list(self.codebase.classes)),
            "imports": len(list(self.codebase.imports)),
            "lines_of_code": sum(len(file.source.splitlines()) for file in self.codebase.files),
        }
    
    def get_file_summary(self, file_path: str) -> Dict[str, Any]:
        """
        Get a summary of a specific file.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            A dictionary containing summary information about the file
        """
        if not self.codebase:
            return {"error": "No codebase loaded"}
        
        for file in self.codebase.files:
            if file.file_path == file_path:
                return {
                    "file_path": file.file_path,
                    "functions": len(list(file.functions)),
                    "classes": len(list(file.classes)),
                    "imports": len(list(file.imports)),
                    "lines_of_code": len(file.source.splitlines()),
                }
        
        return {"error": f"File not found: {file_path}"}
    
    def get_function_summary(self, function_name: str) -> Dict[str, Any]:
        """
        Get a summary of a specific function.
        
        Args:
            function_name: Name of the function to analyze
            
        Returns:
            A dictionary containing summary information about the function
        """
        if not self.codebase:
            return {"error": "No codebase loaded"}
        
        for func in self.codebase.functions:
            if func.name == function_name:
                return {
                    "name": func.name,
                    "file_path": func.file.file_path if hasattr(func, "file") else "Unknown",
                    "parameters": [param.name for param in func.parameters],
                    "lines_of_code": len(func.source.splitlines()),
                    "complexity": self._calculate_cyclomatic_complexity(func),
                }
        
        return {"error": f"Function not found: {function_name}"}
    
    def get_class_summary(self, class_name: str) -> Dict[str, Any]:
        """
        Get a summary of a specific class.
        
        Args:
            class_name: Name of the class to analyze
            
        Returns:
            A dictionary containing summary information about the class
        """
        if not self.codebase:
            return {"error": "No codebase loaded"}
        
        for cls in self.codebase.classes:
            if cls.name == class_name:
                return {
                    "name": cls.name,
                    "file_path": cls.file.file_path if hasattr(cls, "file") else "Unknown",
                    "methods": [method.name for method in cls.methods],
                    "attributes": [attr.name for attr in cls.attributes],
                    "parent_classes": cls.parent_class_names if hasattr(cls, "parent_class_names") else [],
                }
        
        return {"error": f"Class not found: {class_name}"}
    
    # Complexity Analysis Methods
    
    def analyze_complexity(self, file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze the complexity of the codebase or a specific file.
        
        Args:
            file_path: Optional path to a specific file to analyze
            
        Returns:
            A dictionary containing complexity metrics
        """
        if not self.codebase:
            return {"error": "No codebase loaded"}
        
        complexity_metrics = {
            "cyclomatic_complexity": {},
            "maintainability_index": {},
            "average_function_complexity": 0,
            "max_function_complexity": 0,
            "complex_functions": [],
        }
        
        files_to_analyze = []
        if file_path:
            for file in self.codebase.files:
                if file.file_path == file_path:
                    files_to_analyze.append(file)
                    break
        else:
            files_to_analyze = self.codebase.files
        
        if not files_to_analyze:
            return {"error": f"File not found: {file_path}" if file_path else "No files to analyze"}
        
        total_complexity = 0
        max_complexity = 0
        function_count = 0
        
        for file in files_to_analyze:
            file_complexity = 0
            file_functions = list(file.functions)
            
            # Add methods from classes
            for cls in file.classes:
                file_functions.extend(cls.methods)
            
            for func in file_functions:
                complexity = self._calculate_cyclomatic_complexity(func)
                
                complexity_metrics["cyclomatic_complexity"][func.name] = complexity
                file_complexity += complexity
                total_complexity += complexity
                function_count += 1
                
                if complexity > max_complexity:
                    max_complexity = complexity
                
                if complexity > 10:  # Threshold for complex functions
                    complexity_metrics["complex_functions"].append({
                        "name": func.name,
                        "file_path": file.file_path,
                        "complexity": complexity,
                    })
            
            # Calculate maintainability index for the file
            lines_of_code = len(file.source.splitlines())
            avg_complexity = file_complexity / len(file_functions) if file_functions else 0
            maintainability = self._calculate_maintainability_index(lines_of_code, avg_complexity)
            complexity_metrics["maintainability_index"][file.file_path] = maintainability
        
        complexity_metrics["average_function_complexity"] = total_complexity / function_count if function_count else 0
        complexity_metrics["max_function_complexity"] = max_complexity
        
        return complexity_metrics
    
    def _calculate_cyclomatic_complexity(self, func: Function) -> int:
        """
        Calculate the cyclomatic complexity of a function.
        
        Args:
            func: The function to analyze
            
        Returns:
            The cyclomatic complexity score
        """
        # Start with 1 (base complexity)
        complexity = 1
        
        # Count decision points
        for node in func.walk():
            if isinstance(node, IfBlockStatement):
                complexity += 1
                # Add complexity for elif and else blocks
                complexity += len(node.elif_blocks)
                if node.else_block:
                    complexity += 1
            elif isinstance(node, ForLoopStatement):
                complexity += 1
            elif isinstance(node, WhileStatement):
                complexity += 1
            elif isinstance(node, TryCatchStatement):
                complexity += len(node.catch_blocks)
            elif isinstance(node, BinaryExpression):
                if node.operator in ("&&", "||"):
                    complexity += 1
            elif isinstance(node, ComparisonExpression):
                complexity += 1
        
        return complexity
    
    def _calculate_maintainability_index(self, lines_of_code: int, avg_complexity: float) -> float:
        """
        Calculate the maintainability index of a file.
        
        Args:
            lines_of_code: Number of lines of code in the file
            avg_complexity: Average cyclomatic complexity of functions in the file
            
        Returns:
            The maintainability index score (0-100)
        """
        # Simplified maintainability index calculation
        # MI = 171 - 5.2 * ln(avg_complexity) - 0.23 * ln(lines_of_code)
        import math
        
        if lines_of_code <= 0 or avg_complexity <= 0:
            return 100
        
        mi = 171 - 5.2 * math.log(avg_complexity) - 0.23 * math.log(lines_of_code)
        
        # Normalize to 0-100 scale
        mi = max(0, min(100, mi))
        
        return mi
    
    # Feature Analysis Methods
    
    def analyze_features(self) -> Dict[str, Any]:
        """
        Analyze the features and patterns used in the codebase.
        
        Returns:
            A dictionary containing feature analysis results
        """
        if not self.codebase:
            return {"error": "No codebase loaded"}
        
        feature_metrics = {
            "design_patterns": self._detect_design_patterns(),
            "api_usage": self._analyze_api_usage(),
            "language_features": self._analyze_language_features(),
            "framework_usage": self._analyze_framework_usage(),
        }
        
        return feature_metrics
    
    def _detect_design_patterns(self) -> Dict[str, List[Dict[str, str]]]:
        """
        Detect common design patterns in the codebase.
        
        Returns:
            A dictionary mapping pattern names to lists of occurrences
        """
        patterns = {
            "singleton": [],
            "factory": [],
            "observer": [],
            "strategy": [],
            "decorator": [],
        }
        
        # Singleton pattern detection
        for cls in self.codebase.classes:
            # Check for singleton pattern
            has_private_constructor = False
            has_instance_method = False
            has_instance_attribute = False
            
            for method in cls.methods:
                if method.name == "__init__" and "private" in method.source.lower():
                    has_private_constructor = True
                if method.name.lower() in ("getinstance", "get_instance", "instance"):
                    has_instance_method = True
            
            for attr in cls.attributes:
                if attr.name.lower() in ("_instance", "instance", "_singleton"):
                    has_instance_attribute = True
            
            if has_instance_method and (has_private_constructor or has_instance_attribute):
                patterns["singleton"].append({
                    "name": cls.name,
                    "file_path": cls.file.file_path if hasattr(cls, "file") else "Unknown",
                })
        
        # Factory pattern detection
        for cls in self.codebase.classes:
            if "factory" in cls.name.lower():
                patterns["factory"].append({
                    "name": cls.name,
                    "file_path": cls.file.file_path if hasattr(cls, "file") else "Unknown",
                })
            
            for method in cls.methods:
                if "create" in method.name.lower() and method.return_type:
                    patterns["factory"].append({
                        "name": f"{cls.name}.{method.name}",
                        "file_path": cls.file.file_path if hasattr(cls, "file") else "Unknown",
                    })
        
        return patterns
    
    def _analyze_api_usage(self) -> Dict[str, int]:
        """
        Analyze API usage in the codebase.
        
        Returns:
            A dictionary mapping API names to usage counts
        """
        api_usage = {}
        
        for file in self.codebase.files:
            for import_stmt in file.imports:
                module_name = import_stmt.module_name
                
                if module_name in api_usage:
                    api_usage[module_name] += 1
                else:
                    api_usage[module_name] = 1
        
        return api_usage
    
    def _analyze_language_features(self) -> Dict[str, int]:
        """
        Analyze language feature usage in the codebase.
        
        Returns:
            A dictionary mapping language features to usage counts
        """
        features = {
            "decorators": 0,
            "list_comprehensions": 0,
            "async_await": 0,
            "type_annotations": 0,
            "dataclasses": 0,
        }
        
        for file in self.codebase.files:
            source = file.source.lower()
            
            # Count decorators
            features["decorators"] += source.count("@")
            
            # Count list comprehensions
            features["list_comprehensions"] += source.count("[") - source.count("[]")
            
            # Count async/await
            features["async_await"] += source.count("async def") + source.count("await")
            
            # Count type annotations
            features["type_annotations"] += source.count(":") - source.count(":")
            
            # Count dataclasses
            features["dataclasses"] += source.count("@dataclass")
        
        return features
    
    def _analyze_framework_usage(self) -> Dict[str, int]:
        """
        Analyze framework usage in the codebase.
        
        Returns:
            A dictionary mapping framework names to usage counts
        """
        frameworks = {
            "flask": 0,
            "django": 0,
            "fastapi": 0,
            "sqlalchemy": 0,
            "pytest": 0,
            "numpy": 0,
            "pandas": 0,
            "tensorflow": 0,
            "pytorch": 0,
        }
        
        for file in self.codebase.files:
            source = file.source.lower()
            
            for framework in frameworks:
                if framework in source:
                    frameworks[framework] += source.count(framework)
        
        return frameworks
    
    # Code Integrity Analysis Methods
    
    def analyze_code_integrity(self) -> AnalysisResult:
        """
        Analyze the integrity of the codebase, checking for issues and violations.
        
        Returns:
            An AnalysisResult containing integrity analysis results
        """
        if not self.codebase:
            return AnalysisResult(
                success=False,
                summary="No codebase loaded",
            )
        
        issues = []
        
        # Check for unused imports
        unused_imports = self._find_unused_imports()
        for import_name, file_path in unused_imports:
            issues.append(
                AnalysisIssue(
                    issue_type="unused_import",
                    severity="warning",
                    file_path=file_path,
                    description=f"Unused import: {import_name}",
                    suggested_fix=f"Remove the import statement for {import_name}",
                )
            )
        
        # Check for unused functions
        unused_functions = self._find_unused_functions()
        for func_name, file_path in unused_functions:
            issues.append(
                AnalysisIssue(
                    issue_type="unused_function",
                    severity="warning",
                    file_path=file_path,
                    description=f"Unused function: {func_name}",
                    suggested_fix=f"Remove the function {func_name} or add it to __all__",
                )
            )
        
        # Check for long functions
        long_functions = self._find_long_functions()
        for func_name, file_path, line_count in long_functions:
            issues.append(
                AnalysisIssue(
                    issue_type="long_function",
                    severity="warning",
                    file_path=file_path,
                    description=f"Long function: {func_name} ({line_count} lines)",
                    suggested_fix=f"Consider refactoring {func_name} into smaller functions",
                )
            )
        
        # Check for complex functions
        complex_functions = self._find_complex_functions()
        for func_name, file_path, complexity in complex_functions:
            issues.append(
                AnalysisIssue(
                    issue_type="complex_function",
                    severity="warning",
                    file_path=file_path,
                    description=f"Complex function: {func_name} (complexity: {complexity})",
                    suggested_fix=f"Consider refactoring {func_name} to reduce complexity",
                )
            )
        
        # Check for large classes
        large_classes = self._find_large_classes()
        for class_name, file_path, method_count in large_classes:
            issues.append(
                AnalysisIssue(
                    issue_type="large_class",
                    severity="warning",
                    file_path=file_path,
                    description=f"Large class: {class_name} ({method_count} methods)",
                    suggested_fix=f"Consider splitting {class_name} into smaller classes",
                )
            )
        
        # Calculate metrics
        metrics = {
            "total_issues": len(issues),
            "issue_types": {},
            "severity_counts": {
                "error": 0,
                "warning": 0,
                "info": 0,
            },
        }
        
        for issue in issues:
            if issue.issue_type in metrics["issue_types"]:
                metrics["issue_types"][issue.issue_type] += 1
            else:
                metrics["issue_types"][issue.issue_type] = 1
            
            metrics["severity_counts"][issue.severity] += 1
        
        # Generate summary
        summary = f"Found {len(issues)} issues: "
        summary += ", ".join(f"{count} {issue_type}" for issue_type, count in metrics["issue_types"].items())
        
        return AnalysisResult(
            success=True,
            issues=issues,
            metrics=metrics,
            summary=summary,
        )
    
    def _find_unused_imports(self) -> List[Tuple[str, str]]:
        """
        Find unused imports in the codebase.
        
        Returns:
            A list of tuples containing (import_name, file_path)
        """
        unused_imports = []
        
        for file in self.codebase.files:
            file_source = file.source
            
            for import_stmt in file.imports:
                if hasattr(import_stmt, "imported_names"):
                    for name in import_stmt.imported_names:
                        if name not in file_source or name in file_source.split("import")[0]:
                            unused_imports.append((name, file.file_path))
        
        return unused_imports
    
    def _find_unused_functions(self) -> List[Tuple[str, str]]:
        """
        Find unused functions in the codebase.
        
        Returns:
            A list of tuples containing (function_name, file_path)
        """
        unused_functions = []
        
        # Build a set of all function calls
        function_calls = set()
        for file in self.codebase.files:
            for func in file.functions:
                for node in func.walk():
                    if hasattr(node, "name") and hasattr(node, "args"):
                        function_calls.add(node.name)
        
        # Check each function to see if it's called
        for file in self.codebase.files:
            for func in file.functions:
                # Skip if function is in __all__ or is a special method
                if func.name.startswith("__") and func.name.endswith("__"):
                    continue
                
                # Skip if function is in __all__
                if "__all__" in file.source and func.name in file.source.split("__all__")[1]:
                    continue
                
                if func.name not in function_calls:
                    unused_functions.append((func.name, file.file_path))
        
        return unused_functions
    
    def _find_long_functions(self) -> List[Tuple[str, str, int]]:
        """
        Find long functions in the codebase.
        
        Returns:
            A list of tuples containing (function_name, file_path, line_count)
        """
        long_functions = []
        
        for file in self.codebase.files:
            for func in file.functions:
                line_count = len(func.source.splitlines())
                
                if line_count > 50:  # Threshold for long functions
                    long_functions.append((func.name, file.file_path, line_count))
        
        return long_functions
    
    def _find_complex_functions(self) -> List[Tuple[str, str, int]]:
        """
        Find complex functions in the codebase.
        
        Returns:
            A list of tuples containing (function_name, file_path, complexity)
        """
        complex_functions = []
        
        for file in self.codebase.files:
            for func in file.functions:
                complexity = self._calculate_cyclomatic_complexity(func)
                
                if complexity > 10:  # Threshold for complex functions
                    complex_functions.append((func.name, file.file_path, complexity))
        
        return complex_functions
    
    def _find_large_classes(self) -> List[Tuple[str, str, int]]:
        """
        Find large classes in the codebase.
        
        Returns:
            A list of tuples containing (class_name, file_path, method_count)
        """
        large_classes = []
        
        for file in self.codebase.files:
            for cls in file.classes:
                method_count = len(list(cls.methods))
                
                if method_count > 20:  # Threshold for large classes
                    large_classes.append((cls.name, file.file_path, method_count))
        
        return large_classes
    
    # Diff Analysis Methods
    
    def analyze_diff(self, base_path: str, head_path: str) -> Dict[str, Any]:
        """
        Analyze the differences between two codebases.
        
        Args:
            base_path: Path to the base codebase
            head_path: Path to the head codebase
            
        Returns:
            A dictionary containing diff analysis results
        """
        base_codebase = Codebase.from_directory(base_path)
        head_codebase = Codebase.from_directory(head_path)
        
        diff_metrics = {
            "added_files": [],
            "removed_files": [],
            "modified_files": [],
            "added_functions": [],
            "removed_functions": [],
            "modified_functions": [],
            "added_classes": [],
            "removed_classes": [],
            "modified_classes": [],
        }
        
        # Analyze file differences
        base_files = {file.file_path for file in base_codebase.files}
        head_files = {file.file_path for file in head_codebase.files}
        
        diff_metrics["added_files"] = list(head_files - base_files)
        diff_metrics["removed_files"] = list(base_files - head_files)
        
        # Find modified files
        common_files = base_files.intersection(head_files)
        for file_path in common_files:
            base_file = next(file for file in base_codebase.files if file.file_path == file_path)
            head_file = next(file for file in head_codebase.files if file.file_path == file_path)
            
            if base_file.source != head_file.source:
                diff_metrics["modified_files"].append(file_path)
        
        # Analyze function differences
        base_functions = {func.name: func for func in base_codebase.functions}
        head_functions = {func.name: func for func in head_codebase.functions}
        
        for func_name in head_functions:
            if func_name not in base_functions:
                diff_metrics["added_functions"].append({
                    "name": func_name,
                    "file_path": head_functions[func_name].file.file_path if hasattr(head_functions[func_name], "file") else "Unknown",
                })
        
        for func_name in base_functions:
            if func_name not in head_functions:
                diff_metrics["removed_functions"].append({
                    "name": func_name,
                    "file_path": base_functions[func_name].file.file_path if hasattr(base_functions[func_name], "file") else "Unknown",
                })
        
        # Find modified functions
        common_functions = set(base_functions.keys()).intersection(set(head_functions.keys()))
        for func_name in common_functions:
            base_func = base_functions[func_name]
            head_func = head_functions[func_name]
            
            if base_func.source != head_func.source:
                diff_metrics["modified_functions"].append({
                    "name": func_name,
                    "file_path": head_func.file.file_path if hasattr(head_func, "file") else "Unknown",
                })
        
        # Analyze class differences
        base_classes = {cls.name: cls for cls in base_codebase.classes}
        head_classes = {cls.name: cls for cls in head_codebase.classes}
        
        for cls_name in head_classes:
            if cls_name not in base_classes:
                diff_metrics["added_classes"].append({
                    "name": cls_name,
                    "file_path": head_classes[cls_name].file.file_path if hasattr(head_classes[cls_name], "file") else "Unknown",
                })
        
        for cls_name in base_classes:
            if cls_name not in head_classes:
                diff_metrics["removed_classes"].append({
                    "name": cls_name,
                    "file_path": base_classes[cls_name].file.file_path if hasattr(base_classes[cls_name], "file") else "Unknown",
                })
        
        # Find modified classes
        common_classes = set(base_classes.keys()).intersection(set(head_classes.keys()))
        for cls_name in common_classes:
            base_cls = base_classes[cls_name]
            head_cls = head_classes[cls_name]
            
            # Compare methods and attributes
            base_methods = {method.name: method.source for method in base_cls.methods}
            head_methods = {method.name: method.source for method in head_cls.methods}
            
            base_attrs = {attr.name: attr.source if hasattr(attr, "source") else "" for attr in base_cls.attributes}
            head_attrs = {attr.name: attr.source if hasattr(attr, "source") else "" for attr in head_cls.attributes}
            
            if base_methods != head_methods or base_attrs != head_attrs:
                diff_metrics["modified_classes"].append({
                    "name": cls_name,
                    "file_path": head_cls.file.file_path if hasattr(head_cls, "file") else "Unknown",
                })
        
        return diff_metrics

