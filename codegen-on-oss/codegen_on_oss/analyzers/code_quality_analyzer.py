#!/usr/bin/env python3
"""
Code Quality Analyzer Module

This module provides analysis of code quality issues such as
dead code, complexity, style, and maintainability.
"""

import os
import sys
import math
import logging
from typing import Dict, List, Set, Tuple, Any, Optional, Union

from codegen_on_oss.analyzers.base_analyzer import BaseCodeAnalyzer
from codegen_on_oss.analyzers.issue_types import Issue, IssueSeverity, AnalysisType, IssueCategory

# Configure logging
logger = logging.getLogger(__name__)

class CodeQualityAnalyzer(BaseCodeAnalyzer):
    """
    Analyzer for code quality issues.
    
    This analyzer detects issues related to code quality, including
    dead code, complexity, style, and maintainability.
    """
    
    def analyze(self, analysis_type: AnalysisType = AnalysisType.CODE_QUALITY) -> Dict[str, Any]:
        """
        Perform code quality analysis on the codebase.
        
        Args:
            analysis_type: Type of analysis to perform
            
        Returns:
            Dictionary containing analysis results
        """
        if not self.base_codebase:
            raise ValueError("Codebase not initialized")
            
        result = {
            "metadata": {
                "analysis_time": str(datetime.now()),
                "analysis_type": analysis_type,
                "repo_name": getattr(self.base_codebase.ctx, 'repo_name', None),
                "language": str(getattr(self.base_codebase.ctx, 'programming_language', None)),
            },
            "summary": {},
        }
        
        # Reset issues list
        self.issues = []
        
        # Perform appropriate analysis based on type
        if analysis_type == AnalysisType.CODE_QUALITY:
            # Run all code quality checks
            result["dead_code"] = self._find_dead_code()
            result["complexity"] = self._analyze_code_complexity()
            result["style_issues"] = self._check_style_issues()
            result["maintainability"] = self._calculate_maintainability()
            
        # Add issues to the result
        result["issues"] = [issue.to_dict() for issue in self.issues]
        result["issue_counts"] = {
            "total": len(self.issues),
            "by_severity": {
                "critical": sum(1 for issue in self.issues if issue.severity == IssueSeverity.CRITICAL),
                "error": sum(1 for issue in self.issues if issue.severity == IssueSeverity.ERROR),
                "warning": sum(1 for issue in self.issues if issue.severity == IssueSeverity.WARNING),
                "info": sum(1 for issue in self.issues if issue.severity == IssueSeverity.INFO),
            },
            "by_category": {
                category.value: sum(1 for issue in self.issues if issue.category == category)
                for category in IssueCategory
                if any(issue.category == category for issue in self.issues)
            }
        }
        
        # Store results
        self.results = result
        
        return result
    
    def _find_dead_code(self) -> Dict[str, Any]:
        """
        Find unused code (dead code) in the codebase.
        
        Returns:
            Dictionary containing dead code analysis results
        """
        dead_code = {
            "unused_functions": [],
            "unused_classes": [],
            "unused_variables": [],
            "unused_imports": []
        }
        
        # Find unused functions
        if hasattr(self.base_codebase, 'functions'):
            for func in self.base_codebase.functions:
                # Skip test files
                if hasattr(func, 'file') and hasattr(func.file, 'filepath') and "test" in func.file.filepath:
                    continue
                
                # Skip decorated functions (as they might be used indirectly)
                if hasattr(func, 'decorators') and func.decorators:
                    continue
                
                # Check if function has no call sites or usages
                has_call_sites = hasattr(func, 'call_sites') and len(func.call_sites) > 0
                has_usages = hasattr(func, 'usages') and len(func.usages) > 0
                
                if not has_call_sites and not has_usages:
                    # Get file path and name safely
                    file_path = func.file.filepath if hasattr(func, 'file') and hasattr(func.file, 'filepath') else "unknown"
                    func_name = func.name if hasattr(func, 'name') else str(func)
                    
                    # Add to dead code list
                    dead_code["unused_functions"].append({
                        "name": func_name,
                        "file": file_path,
                        "line": func.line if hasattr(func, 'line') else None
                    })
                    
                    # Add issue
                    self.add_issue(Issue(
                        file=file_path,
                        line=func.line if hasattr(func, 'line') else None,
                        message=f"Unused function: {func_name}",
                        severity=IssueSeverity.WARNING,
                        category=IssueCategory.DEAD_CODE,
                        symbol=func_name,
                        suggestion="Consider removing this unused function or documenting why it's needed"
                    ))
        
        # Find unused classes
        if hasattr(self.base_codebase, 'classes'):
            for cls in self.base_codebase.classes:
                # Skip test files
                if hasattr(cls, 'file') and hasattr(cls.file, 'filepath') and "test" in cls.file.filepath:
                    continue
                
                # Check if class has no usages
                has_usages = hasattr(cls, 'usages') and len(cls.usages) > 0
                
                if not has_usages:
                    # Get file path and name safely
                    file_path = cls.file.filepath if hasattr(cls, 'file') and hasattr(cls.file, 'filepath') else "unknown"
                    cls_name = cls.name if hasattr(cls, 'name') else str(cls)
                    
                    # Add to dead code list
                    dead_code["unused_classes"].append({
                        "name": cls_name,
                        "file": file_path,
                        "line": cls.line if hasattr(cls, 'line') else None
                    })
                    
                    # Add issue
                    self.add_issue(Issue(
                        file=file_path,
                        line=cls.line if hasattr(cls, 'line') else None,
                        message=f"Unused class: {cls_name}",
                        severity=IssueSeverity.WARNING,
                        category=IssueCategory.DEAD_CODE,
                        symbol=cls_name,
                        suggestion="Consider removing this unused class or documenting why it's needed"
                    ))
        
        # Find unused variables
        if hasattr(self.base_codebase, 'functions'):
            for func in self.base_codebase.functions:
                if not hasattr(func, 'code_block') or not hasattr(func.code_block, 'local_var_assignments'):
                    continue
                
                for var_assignment in func.code_block.local_var_assignments:
                    # Check if variable has no usages
                    has_usages = hasattr(var_assignment, 'local_usages') and len(var_assignment.local_usages) > 0
                    
                    if not has_usages:
                        # Get file path and name safely
                        file_path = func.file.filepath if hasattr(func, 'file') and hasattr(func.file, 'filepath') else "unknown"
                        var_name = var_assignment.name if hasattr(var_assignment, 'name') else str(var_assignment)
                        
                        # Add to dead code list
                        dead_code["unused_variables"].append({
                            "name": var_name,
                            "file": file_path,
                            "line": var_assignment.line if hasattr(var_assignment, 'line') else None
                        })
                        
                        # Add issue
                        self.add_issue(Issue(
                            file=file_path,
                            line=var_assignment.line if hasattr(var_assignment, 'line') else None,
                            message=f"Unused variable: {var_name}",
                            severity=IssueSeverity.INFO,
                            category=IssueCategory.DEAD_CODE,
                            symbol=var_name,
                            suggestion="Consider removing this unused variable"
                        ))
        
        # Summarize findings
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
    
    def _analyze_code_complexity(self) -> Dict[str, Any]:
        """
        Analyze code complexity.
        
        Returns:
            Dictionary containing complexity analysis results
        """
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
        
        if hasattr(self.base_codebase, 'functions'):
            for func in self.base_codebase.functions:
                # Skip if no code block
                if not hasattr(func, 'code_block'):
                    continue
                
                # Calculate cyclomatic complexity
                complexity = self._calculate_cyclomatic_complexity(func)
                
                # Get file path and name safely
                file_path = func.file.filepath if hasattr(func, 'file') and hasattr(func.file, 'filepath') else "unknown"
                func_name = func.name if hasattr(func, 'name') else str(func)
                
                # Add to complexity list
                complexity_result["function_complexity"].append({
                    "name": func_name,
                    "file": file_path,
                    "line": func.line if hasattr(func, 'line') else None,
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
                        "line": func.line if hasattr(func, 'line') else None,
                        "complexity": complexity
                    })
                    
                    # Add issue
                    severity = IssueSeverity.WARNING if complexity <= 15 else IssueSeverity.ERROR
                    self.add_issue(Issue(
                        file=file_path,
                        line=func.line if hasattr(func, 'line') else None,
                        message=f"High cyclomatic complexity: {complexity}",
                        severity=severity,
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
        
        return complexity
    
    def _check_style_issues(self) -> Dict[str, Any]:
        """
        Check for code style issues.
        
        Returns:
            Dictionary containing style issues analysis results
        """
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
        if hasattr(self.base_codebase, 'functions'):
            for func in self.base_codebase.functions:
                # Get function code
                if hasattr(func, 'code_block') and hasattr(func.code_block, 'source'):
                    code = func.code_block.source
                    lines = code.split('\n')
                    
                    # Check function length
                    if len(lines) > 50:  # Threshold for "too long"
                        # Get file path and name safely
                        file_path = func.file.filepath if hasattr(func, 'file') and hasattr(func.file, 'filepath') else "unknown"
                        func_name = func.name if hasattr(func, 'name') else str(func)
                        
                        # Add to long functions list
                        style_result["long_functions"].append({
                            "name": func_name,
                            "file": file_path,
                            "line": func.line if hasattr(func, 'line') else None,
                            "line_count": len(lines)
                        })
                        
                        # Add issue
                        self.add_issue(Issue(
                            file=file_path,
                            line=func.line if hasattr(func, 'line') else None,
                            message=f"Long function: {len(lines)} lines",
                            severity=IssueSeverity.INFO,
                            category=IssueCategory.STYLE_ISSUE,
                            symbol=func_name,
                            suggestion="Consider breaking this function into smaller, more focused functions"
                        ))
        
        # Update summary
        style_result["summary"]["long_functions_count"] = len(style_result["long_functions"])
        style_result["summary"]["long_lines_count"] = len(style_result["long_lines"])
        style_result["summary"]["inconsistent_naming_count"] = len(style_result["inconsistent_naming"])
        
        return style_result
    
    def _calculate_maintainability(self) -> Dict[str, Any]:
        """
        Calculate maintainability metrics.
        
        Returns:
            Dictionary containing maintainability analysis results
        """
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
        
        if hasattr(self.base_codebase, 'functions'):
            for func in self.base_codebase.functions:
                # Skip if no code block
                if not hasattr(func, 'code_block'):
                    continue
                
                # Calculate metrics
                complexity = self._calculate_cyclomatic_complexity(func)
                
                # Calculate Halstead volume (approximation)
                operators = 0
                operands = 0
                
                if hasattr(func, 'code_block') and hasattr(func.code_block, 'source'):
                    code = func.code_block.source
                    # Simple approximation of operators and operands
                    operators = len([c for c in code if c in '+-*/=<>!&|^~%'])
                    # Counting words as potential operands
                    import re
                    operands = len(re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', code))
                
                halstead_volume = operators * operands * math.log2(operators + operands) if operators + operands > 0 else 0
                
                # Count lines of code
                loc = len(func.code_block.source.split('\n')) if hasattr(func, 'code_block') and hasattr(func.code_block, 'source') else 0
                
                # Calculate maintainability index
                # Formula: 171 - 5.2 * ln(Halstead Volume) - 0.23 * (Cyclomatic Complexity) - 16.2 * ln(LOC)
                halstead_term = 5.2 * math.log(max(1, halstead_volume)) if halstead_volume > 0 else 0
                complexity_term = 0.23 * complexity
                loc_term = 16.2 * math.log(max(1, loc)) if loc > 0 else 0
                
                maintainability = 171 - halstead_term - complexity_term - loc_term
                
                # Normalize to 0-100 scale
                maintainability = max(0, min(100, maintainability * 100 / 171))
                
                # Get file path and name safely
                file_path = func.file.filepath if hasattr(func, 'file') and hasattr(func.file, 'filepath') else "unknown"
                func_name = func.name if hasattr(func, 'name') else str(func)
                
                # Add to maintainability list
                maintainability_result["function_maintainability"].append({
                    "name": func_name,
                    "file": file_path,
                    "line": func.line if hasattr(func, 'line') else None,
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
                        "line": func.line if hasattr(func, 'line') else None,
                        "maintainability": maintainability,
                        "complexity": complexity,
                        "halstead_volume": halstead_volume,
                        "loc": loc
                    })
                    
                    # Add issue
                    self.add_issue(Issue(
                        file=file_path,
                        line=func.line if hasattr(func, 'line') else None,
                        message=f"Low maintainability index: {maintainability:.1f}",
                        severity=IssueSeverity.WARNING,
                        category=IssueCategory.COMPLEXITY,
                        symbol=func_name,
                        suggestion="Consider refactoring this function to improve maintainability"
                    ))
        
        # Calculate average maintainability
        maintainability_result["average_maintainability"] = total_maintainability / function_count if function_count > 0 else 0.0
        
        # Sort low maintainability functions
        maintainability_result["low_maintainability_functions"].sort(key=lambda x: x["maintainability"])
        
        return maintainability_result