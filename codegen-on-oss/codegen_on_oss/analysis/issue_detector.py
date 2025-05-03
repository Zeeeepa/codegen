"""
Issue Detector for Codegen-on-OSS

This module provides an issue detector that detects code quality issues
in a codebase, such as high complexity, low maintainability, and code smells.
"""

import logging
import os
import re
from typing import Dict, List, Optional, Any, Union, Set, Tuple

from codegen import Codebase
from codegen.sdk.core.file import SourceFile
from codegen.sdk.core.function import Function
from codegen.sdk.core.class_definition import Class
from codegen.sdk.core.symbol import Symbol

from codegen_on_oss.database import get_db_session, IssueRepository
from codegen_on_oss.analysis.coordinator import AnalysisContext
from codegen_on_oss.analysis.analysis import (
    calculate_cyclomatic_complexity,
    calculate_halstead_volume,
    calculate_maintainability_index,
    count_lines,
    get_operators_and_operands,
    cc_rank,
    get_maintainability_rank
)

logger = logging.getLogger(__name__)

class IssueDetector:
    """
    Issue detector for detecting code quality issues.
    
    This class detects code quality issues in a codebase, such as high complexity,
    low maintainability, and code smells.
    """
    
    def __init__(self):
        """Initialize the issue detector."""
        self.issue_repo = IssueRepository()
        
        # Issue thresholds
        self.thresholds = {
            "cyclomatic_complexity": {
                "warning": 10,
                "error": 20
            },
            "maintainability_index": {
                "warning": 65,
                "error": 50
            },
            "halstead_volume": {
                "warning": 1000,
                "error": 2000
            },
            "loc": {
                "warning": 500,
                "error": 1000
            },
            "comment_ratio": {
                "warning": 0.1,
                "error": 0.05
            },
            "method_count": {
                "warning": 20,
                "error": 30
            }
        }
    
    async def detect(self, context: AnalysisContext) -> Dict[str, Any]:
        """
        Detect issues in a codebase.
        
        Args:
            context: The analysis context.
            
        Returns:
            Detected issues.
        """
        logger.info(f"Detecting issues for repository: {context.repo_url}")
        
        codebase = context.codebase
        
        # Detect file-level issues
        file_issues = {}
        for file_path in codebase.get_all_file_paths():
            try:
                source_file = codebase.get_source_file(file_path)
                
                # Skip non-source files
                if not source_file or not source_file.content:
                    continue
                
                # Detect file issues
                file_issues[file_path] = await self._detect_file_issues(context, source_file)
            except Exception as e:
                logger.warning(f"Error detecting issues for file {file_path}: {e}")
                continue
        
        # Detect symbol-level issues
        symbol_issues = {}
        for file_path, issues in file_issues.items():
            try:
                source_file = codebase.get_source_file(file_path)
                
                # Detect function issues
                for function in source_file.get_functions():
                    symbol_id = f"{file_path}:{function.name}:{function.start_line}"
                    symbol_issues[symbol_id] = await self._detect_function_issues(context, function)
                
                # Detect class issues
                for class_def in source_file.get_classes():
                    symbol_id = f"{file_path}:{class_def.name}:{class_def.start_line}"
                    symbol_issues[symbol_id] = await self._detect_class_issues(context, class_def)
            except Exception as e:
                logger.warning(f"Error detecting issues for symbols in {file_path}: {e}")
                continue
        
        # Detect code smells
        code_smells = await self._detect_code_smells(context)
        
        # Aggregate issues
        all_issues = {
            "files": file_issues,
            "symbols": symbol_issues,
            "code_smells": code_smells
        }
        
        # Add issues to context
        context.add_result("issues", all_issues)
        
        return all_issues
    
    async def _detect_file_issues(self, context: AnalysisContext, source_file: SourceFile) -> List[Dict[str, Any]]:
        """
        Detect issues in a file.
        
        Args:
            context: The analysis context.
            source_file: The source file.
            
        Returns:
            A list of detected issues.
        """
        file_path = source_file.path
        content = source_file.content
        
        issues = []
        
        # Check file size
        loc = count_lines(content)
        if loc > self.thresholds["loc"]["error"]:
            issue = {
                "type": "error",
                "severity": 4,
                "message": f"File is too large ({loc} lines)",
                "file_path": file_path,
                "remediation": {
                    "description": "Split the file into smaller modules",
                    "effort": "high"
                }
            }
            issues.append(issue)
            context.add_issue(**issue)
        elif loc > self.thresholds["loc"]["warning"]:
            issue = {
                "type": "warning",
                "severity": 3,
                "message": f"File is large ({loc} lines)",
                "file_path": file_path,
                "remediation": {
                    "description": "Consider splitting the file into smaller modules",
                    "effort": "medium"
                }
            }
            issues.append(issue)
            context.add_issue(**issue)
        
        # Check comment ratio
        comment_lines = self._count_comment_lines(content, file_path)
        comment_ratio = comment_lines / loc if loc > 0 else 0
        
        if comment_ratio < self.thresholds["comment_ratio"]["error"]:
            issue = {
                "type": "error",
                "severity": 3,
                "message": f"File has very low comment ratio ({comment_ratio:.2f})",
                "file_path": file_path,
                "remediation": {
                    "description": "Add comments to explain complex logic and document functions",
                    "effort": "medium"
                }
            }
            issues.append(issue)
            context.add_issue(**issue)
        elif comment_ratio < self.thresholds["comment_ratio"]["warning"]:
            issue = {
                "type": "warning",
                "severity": 2,
                "message": f"File has low comment ratio ({comment_ratio:.2f})",
                "file_path": file_path,
                "remediation": {
                    "description": "Consider adding more comments to improve code readability",
                    "effort": "low"
                }
            }
            issues.append(issue)
            context.add_issue(**issue)
        
        # Check cyclomatic complexity
        cc = calculate_cyclomatic_complexity(content)
        if cc > self.thresholds["cyclomatic_complexity"]["error"]:
            issue = {
                "type": "error",
                "severity": 4,
                "message": f"File has very high cyclomatic complexity ({cc})",
                "file_path": file_path,
                "remediation": {
                    "description": "Refactor the code to reduce complexity by breaking it into smaller functions",
                    "effort": "high"
                }
            }
            issues.append(issue)
            context.add_issue(**issue)
        elif cc > self.thresholds["cyclomatic_complexity"]["warning"]:
            issue = {
                "type": "warning",
                "severity": 3,
                "message": f"File has high cyclomatic complexity ({cc})",
                "file_path": file_path,
                "remediation": {
                    "description": "Consider refactoring the code to reduce complexity",
                    "effort": "medium"
                }
            }
            issues.append(issue)
            context.add_issue(**issue)
        
        # Check maintainability index
        operators, operands = get_operators_and_operands(content)
        halstead_volume = calculate_halstead_volume(operators, operands)
        mi = calculate_maintainability_index(content, cc, halstead_volume)
        
        if mi < self.thresholds["maintainability_index"]["error"]:
            issue = {
                "type": "error",
                "severity": 4,
                "message": f"File has very low maintainability index ({mi:.2f})",
                "file_path": file_path,
                "remediation": {
                    "description": "Refactor the code to improve maintainability by reducing complexity and improving structure",
                    "effort": "high"
                }
            }
            issues.append(issue)
            context.add_issue(**issue)
        elif mi < self.thresholds["maintainability_index"]["warning"]:
            issue = {
                "type": "warning",
                "severity": 3,
                "message": f"File has low maintainability index ({mi:.2f})",
                "file_path": file_path,
                "remediation": {
                    "description": "Consider refactoring the code to improve maintainability",
                    "effort": "medium"
                }
            }
            issues.append(issue)
            context.add_issue(**issue)
        
        return issues
    
    async def _detect_function_issues(self, context: AnalysisContext, function: Function) -> List[Dict[str, Any]]:
        """
        Detect issues in a function.
        
        Args:
            context: The analysis context.
            function: The function.
            
        Returns:
            A list of detected issues.
        """
        file_path = function.source_file.path
        content = function.content
        
        issues = []
        
        # Check function size
        loc = count_lines(content)
        if loc > self.thresholds["loc"]["error"] / 10:
            issue = {
                "type": "error",
                "severity": 4,
                "message": f"Function '{function.name}' is too large ({loc} lines)",
                "file_path": file_path,
                "symbol_name": function.name,
                "line_start": function.start_line,
                "line_end": function.end_line,
                "remediation": {
                    "description": "Split the function into smaller functions",
                    "effort": "high"
                }
            }
            issues.append(issue)
            context.add_issue(**issue)
        elif loc > self.thresholds["loc"]["warning"] / 10:
            issue = {
                "type": "warning",
                "severity": 3,
                "message": f"Function '{function.name}' is large ({loc} lines)",
                "file_path": file_path,
                "symbol_name": function.name,
                "line_start": function.start_line,
                "line_end": function.end_line,
                "remediation": {
                    "description": "Consider splitting the function into smaller functions",
                    "effort": "medium"
                }
            }
            issues.append(issue)
            context.add_issue(**issue)
        
        # Check cyclomatic complexity
        cc = calculate_cyclomatic_complexity(content)
        if cc > self.thresholds["cyclomatic_complexity"]["error"]:
            issue = {
                "type": "error",
                "severity": 4,
                "message": f"Function '{function.name}' has very high cyclomatic complexity ({cc})",
                "file_path": file_path,
                "symbol_name": function.name,
                "line_start": function.start_line,
                "line_end": function.end_line,
                "remediation": {
                    "description": "Refactor the function to reduce complexity by breaking it into smaller functions",
                    "effort": "high"
                }
            }
            issues.append(issue)
            context.add_issue(**issue)
        elif cc > self.thresholds["cyclomatic_complexity"]["warning"]:
            issue = {
                "type": "warning",
                "severity": 3,
                "message": f"Function '{function.name}' has high cyclomatic complexity ({cc})",
                "file_path": file_path,
                "symbol_name": function.name,
                "line_start": function.start_line,
                "line_end": function.end_line,
                "remediation": {
                    "description": "Consider refactoring the function to reduce complexity",
                    "effort": "medium"
                }
            }
            issues.append(issue)
            context.add_issue(**issue)
        
        # Check maintainability index
        operators, operands = get_operators_and_operands(content)
        halstead_volume = calculate_halstead_volume(operators, operands)
        mi = calculate_maintainability_index(content, cc, halstead_volume)
        
        if mi < self.thresholds["maintainability_index"]["error"]:
            issue = {
                "type": "error",
                "severity": 4,
                "message": f"Function '{function.name}' has very low maintainability index ({mi:.2f})",
                "file_path": file_path,
                "symbol_name": function.name,
                "line_start": function.start_line,
                "line_end": function.end_line,
                "remediation": {
                    "description": "Refactor the function to improve maintainability by reducing complexity and improving structure",
                    "effort": "high"
                }
            }
            issues.append(issue)
            context.add_issue(**issue)
        elif mi < self.thresholds["maintainability_index"]["warning"]:
            issue = {
                "type": "warning",
                "severity": 3,
                "message": f"Function '{function.name}' has low maintainability index ({mi:.2f})",
                "file_path": file_path,
                "symbol_name": function.name,
                "line_start": function.start_line,
                "line_end": function.end_line,
                "remediation": {
                    "description": "Consider refactoring the function to improve maintainability",
                    "effort": "medium"
                }
            }
            issues.append(issue)
            context.add_issue(**issue)
        
        # Check for too many parameters
        param_count = len(function.parameters)
        if param_count > 7:
            issue = {
                "type": "warning",
                "severity": 3,
                "message": f"Function '{function.name}' has too many parameters ({param_count})",
                "file_path": file_path,
                "symbol_name": function.name,
                "line_start": function.start_line,
                "line_end": function.end_line,
                "remediation": {
                    "description": "Consider refactoring the function to use fewer parameters, possibly by grouping related parameters into objects",
                    "effort": "medium"
                }
            }
            issues.append(issue)
            context.add_issue(**issue)
        
        return issues
    
    async def _detect_class_issues(self, context: AnalysisContext, class_def: Class) -> List[Dict[str, Any]]:
        """
        Detect issues in a class.
        
        Args:
            context: The analysis context.
            class_def: The class definition.
            
        Returns:
            A list of detected issues.
        """
        file_path = class_def.source_file.path
        content = class_def.content
        
        issues = []
        
        # Check class size
        loc = count_lines(content)
        if loc > self.thresholds["loc"]["error"] / 5:
            issue = {
                "type": "error",
                "severity": 4,
                "message": f"Class '{class_def.name}' is too large ({loc} lines)",
                "file_path": file_path,
                "symbol_name": class_def.name,
                "line_start": class_def.start_line,
                "line_end": class_def.end_line,
                "remediation": {
                    "description": "Split the class into smaller classes",
                    "effort": "high"
                }
            }
            issues.append(issue)
            context.add_issue(**issue)
        elif loc > self.thresholds["loc"]["warning"] / 5:
            issue = {
                "type": "warning",
                "severity": 3,
                "message": f"Class '{class_def.name}' is large ({loc} lines)",
                "file_path": file_path,
                "symbol_name": class_def.name,
                "line_start": class_def.start_line,
                "line_end": class_def.end_line,
                "remediation": {
                    "description": "Consider splitting the class into smaller classes",
                    "effort": "medium"
                }
            }
            issues.append(issue)
            context.add_issue(**issue)
        
        # Check method count
        method_count = len(class_def.get_methods())
        if method_count > self.thresholds["method_count"]["error"]:
            issue = {
                "type": "error",
                "severity": 4,
                "message": f"Class '{class_def.name}' has too many methods ({method_count})",
                "file_path": file_path,
                "symbol_name": class_def.name,
                "line_start": class_def.start_line,
                "line_end": class_def.end_line,
                "remediation": {
                    "description": "Split the class into smaller classes with fewer responsibilities",
                    "effort": "high"
                }
            }
            issues.append(issue)
            context.add_issue(**issue)
        elif method_count > self.thresholds["method_count"]["warning"]:
            issue = {
                "type": "warning",
                "severity": 3,
                "message": f"Class '{class_def.name}' has many methods ({method_count})",
                "file_path": file_path,
                "symbol_name": class_def.name,
                "line_start": class_def.start_line,
                "line_end": class_def.end_line,
                "remediation": {
                    "description": "Consider splitting the class into smaller classes with fewer responsibilities",
                    "effort": "medium"
                }
            }
            issues.append(issue)
            context.add_issue(**issue)
        
        # Check cyclomatic complexity
        cc = calculate_cyclomatic_complexity(content)
        if cc > self.thresholds["cyclomatic_complexity"]["error"]:
            issue = {
                "type": "error",
                "severity": 4,
                "message": f"Class '{class_def.name}' has very high cyclomatic complexity ({cc})",
                "file_path": file_path,
                "symbol_name": class_def.name,
                "line_start": class_def.start_line,
                "line_end": class_def.end_line,
                "remediation": {
                    "description": "Refactor the class to reduce complexity by breaking it into smaller classes and methods",
                    "effort": "high"
                }
            }
            issues.append(issue)
            context.add_issue(**issue)
        elif cc > self.thresholds["cyclomatic_complexity"]["warning"]:
            issue = {
                "type": "warning",
                "severity": 3,
                "message": f"Class '{class_def.name}' has high cyclomatic complexity ({cc})",
                "file_path": file_path,
                "symbol_name": class_def.name,
                "line_start": class_def.start_line,
                "line_end": class_def.end_line,
                "remediation": {
                    "description": "Consider refactoring the class to reduce complexity",
                    "effort": "medium"
                }
            }
            issues.append(issue)
            context.add_issue(**issue)
        
        return issues
    
    async def _detect_code_smells(self, context: AnalysisContext) -> List[Dict[str, Any]]:
        """
        Detect code smells in a codebase.
        
        Args:
            context: The analysis context.
            
        Returns:
            A list of detected code smells.
        """
        codebase = context.codebase
        
        code_smells = []
        
        # Detect duplicate code
        duplicates = await self._detect_duplicate_code(context)
        for duplicate in duplicates:
            issue = {
                "type": "warning",
                "severity": 3,
                "message": f"Duplicate code detected in {len(duplicate['files'])} files",
                "file_path": duplicate["files"][0],
                "remediation": {
                    "description": "Extract the duplicate code into a shared function or class",
                    "effort": "medium"
                }
            }
            code_smells.append(issue)
            context.add_issue(**issue)
        
        # Detect long parameter lists
        for file_path in codebase.get_all_file_paths():
            try:
                source_file = codebase.get_source_file(file_path)
                
                # Skip non-source files
                if not source_file or not source_file.content:
                    continue
                
                # Check functions
                for function in source_file.get_functions():
                    param_count = len(function.parameters)
                    if param_count > 7:
                        issue = {
                            "type": "warning",
                            "severity": 2,
                            "message": f"Function '{function.name}' has a long parameter list ({param_count} parameters)",
                            "file_path": file_path,
                            "symbol_name": function.name,
                            "line_start": function.start_line,
                            "line_end": function.end_line,
                            "remediation": {
                                "description": "Refactor the function to use fewer parameters, possibly by grouping related parameters into objects",
                                "effort": "medium"
                            }
                        }
                        code_smells.append(issue)
                        context.add_issue(**issue)
            except Exception:
                continue
        
        return code_smells
    
    async def _detect_duplicate_code(self, context: AnalysisContext) -> List[Dict[str, Any]]:
        """
        Detect duplicate code in a codebase.
        
        Args:
            context: The analysis context.
            
        Returns:
            A list of detected duplicates.
        """
        codebase = context.codebase
        
        # Simple duplicate code detection based on line count
        min_lines = 5  # Minimum number of lines to consider as duplicate
        
        # Extract code blocks from files
        code_blocks = []
        for file_path in codebase.get_all_file_paths():
            try:
                source_file = codebase.get_source_file(file_path)
                
                # Skip non-source files
                if not source_file or not source_file.content:
                    continue
                
                # Split content into lines
                lines = source_file.content.split('\n')
                
                # Extract blocks of code
                for i in range(len(lines) - min_lines + 1):
                    block = '\n'.join(lines[i:i+min_lines])
                    # Skip blocks with too many empty lines
                    if block.count('\n\n') > 2:
                        continue
                    
                    code_blocks.append({
                        "file": file_path,
                        "start_line": i + 1,
                        "end_line": i + min_lines,
                        "content": block
                    })
            except Exception:
                continue
        
        # Find duplicates
        duplicates = []
        seen_blocks = {}
        
        for block in code_blocks:
            content = block["content"]
            
            if content in seen_blocks:
                seen_blocks[content].append(block)
            else:
                seen_blocks[content] = [block]
        
        # Filter duplicates
        for content, blocks in seen_blocks.items():
            if len(blocks) > 1:
                # Skip blocks with too little content
                if len(content.strip()) < 100:
                    continue
                
                duplicates.append({
                    "files": [block["file"] for block in blocks],
                    "blocks": blocks,
                    "content": content
                })
        
        return duplicates
    
    def _count_comment_lines(self, content: str, file_path: str) -> int:
        """
        Count comment lines in a file.
        
        Args:
            content: The file content.
            file_path: The file path.
            
        Returns:
            The number of comment lines.
        """
        ext = os.path.splitext(file_path)[1].lower()
        
        # Different comment styles for different languages
        if ext in ['.py']:
            # Python comments
            lines = content.split('\n')
            comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
            
            # Count docstrings
            in_docstring = False
            for line in lines:
                line = line.strip()
                if line.startswith('"""') or line.startswith("'''"):
                    if in_docstring:
                        in_docstring = False
                    else:
                        in_docstring = True
                        comment_lines += 1
                elif in_docstring:
                    comment_lines += 1
            
            return comment_lines
        
        elif ext in ['.js', '.jsx', '.ts', '.tsx', '.java', '.c', '.cpp', '.h', '.hpp', '.cs', '.go', '.php', '.swift', '.kt', '.scala']:
            # C-style comments
            lines = content.split('\n')
            comment_lines = sum(1 for line in lines if line.strip().startswith('//'))
            
            # Count block comments
            in_block_comment = False
            for line in lines:
                line = line.strip()
                if not in_block_comment and '/*' in line:
                    in_block_comment = True
                    comment_lines += 1
                elif in_block_comment and '*/' in line:
                    in_block_comment = False
                elif in_block_comment:
                    comment_lines += 1
            
            return comment_lines
        
        elif ext in ['.rb']:
            # Ruby comments
            lines = content.split('\n')
            return sum(1 for line in lines if line.strip().startswith('#'))
        
        elif ext in ['.html', '.xml']:
            # HTML/XML comments
            lines = content.split('\n')
            comment_lines = 0
            in_comment = False
            for line in lines:
                line = line.strip()
                if not in_comment and '<!--' in line:
                    in_comment = True
                    comment_lines += 1
                elif in_comment and '-->' in line:
                    in_comment = False
                elif in_comment:
                    comment_lines += 1
            
            return comment_lines
        
        else:
            # Default: assume no comments
            return 0

