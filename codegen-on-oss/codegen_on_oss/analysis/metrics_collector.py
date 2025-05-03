"""
Metrics Collector for Codegen-on-OSS

This module provides a metrics collector that collects code quality metrics
for repositories, files, and symbols.
"""

import logging
import os
import math
from typing import Dict, List, Optional, Any, Union, Set, Tuple

from codegen import Codebase
from codegen.sdk.core.file import SourceFile
from codegen.sdk.core.function import Function
from codegen.sdk.core.class_definition import Class
from codegen.sdk.core.symbol import Symbol

from codegen_on_oss.database import get_db_session, MetricRepository
from codegen_on_oss.analysis.coordinator import AnalysisContext
from codegen_on_oss.analysis.analysis import (
    calculate_cyclomatic_complexity,
    calculate_halstead_volume,
    calculate_maintainability_index,
    count_lines,
    get_operators_and_operands,
    cc_rank,
    get_maintainability_rank,
    calculate_doi
)

logger = logging.getLogger(__name__)

class MetricsCollector:
    """
    Metrics collector for collecting code quality metrics.
    
    This class collects code quality metrics for repositories, files, and symbols,
    such as cyclomatic complexity, maintainability index, and lines of code.
    """
    
    def __init__(self):
        """Initialize the metrics collector."""
        self.metric_repo = MetricRepository()
        
        # Metric thresholds
        self.thresholds = {
            "cyclomatic_complexity": 10,
            "maintainability_index": 65,
            "halstead_volume": 1000,
            "loc": 500,
            "comment_ratio": 0.1
        }
    
    async def collect(self, context: AnalysisContext) -> Dict[str, Any]:
        """
        Collect metrics for a codebase.
        
        Args:
            context: The analysis context.
            
        Returns:
            Collected metrics.
        """
        logger.info(f"Collecting metrics for repository: {context.repo_url}")
        
        codebase = context.codebase
        
        # Collect repository-level metrics
        repo_metrics = await self._collect_repository_metrics(context)
        
        # Collect file-level metrics
        file_metrics = {}
        for file_path in codebase.get_all_file_paths():
            try:
                source_file = codebase.get_source_file(file_path)
                
                # Skip non-source files
                if not source_file or not source_file.content:
                    continue
                
                # Collect file metrics
                file_metrics[file_path] = await self._collect_file_metrics(context, source_file)
            except Exception as e:
                logger.warning(f"Error collecting metrics for file {file_path}: {e}")
                continue
        
        # Collect symbol-level metrics
        symbol_metrics = {}
        for file_path, metrics in file_metrics.items():
            try:
                source_file = codebase.get_source_file(file_path)
                
                # Collect function metrics
                for function in source_file.get_functions():
                    symbol_id = f"{file_path}:{function.name}:{function.start_line}"
                    symbol_metrics[symbol_id] = await self._collect_function_metrics(context, function)
                
                # Collect class metrics
                for class_def in source_file.get_classes():
                    symbol_id = f"{file_path}:{class_def.name}:{class_def.start_line}"
                    symbol_metrics[symbol_id] = await self._collect_class_metrics(context, class_def)
            except Exception as e:
                logger.warning(f"Error collecting metrics for symbols in {file_path}: {e}")
                continue
        
        # Aggregate metrics
        all_metrics = {
            "repository": repo_metrics,
            "files": file_metrics,
            "symbols": symbol_metrics
        }
        
        # Add metrics to context
        context.add_result("metrics", all_metrics)
        
        return all_metrics
    
    async def _collect_repository_metrics(self, context: AnalysisContext) -> Dict[str, Any]:
        """
        Collect repository-level metrics.
        
        Args:
            context: The analysis context.
            
        Returns:
            Repository metrics.
        """
        codebase = context.codebase
        
        # Count files by language
        language_counts = {}
        for file_path in codebase.get_all_file_paths():
            ext = os.path.splitext(file_path)[1].lower()
            language = self._get_language_from_extension(ext)
            if language:
                language_counts[language] = language_counts.get(language, 0) + 1
        
        # Calculate total lines of code
        total_loc = 0
        total_files = 0
        for file_path in codebase.get_all_file_paths():
            try:
                source_file = codebase.get_source_file(file_path)
                
                # Skip non-source files
                if not source_file or not source_file.content:
                    continue
                
                # Count lines
                loc = count_lines(source_file.content)
                total_loc += loc
                total_files += 1
                
                # Add metric to context
                context.add_metric(
                    name="loc",
                    value=loc,
                    file_path=file_path,
                    threshold=self.thresholds["loc"]
                )
            except Exception:
                continue
        
        # Calculate average lines of code per file
        avg_loc = total_loc / total_files if total_files > 0 else 0
        
        # Add metrics to context
        context.add_metric(
            name="total_loc",
            value=total_loc
        )
        
        context.add_metric(
            name="avg_loc_per_file",
            value=avg_loc
        )
        
        context.add_metric(
            name="total_files",
            value=total_files
        )
        
        # Return metrics
        return {
            "total_loc": total_loc,
            "avg_loc_per_file": avg_loc,
            "total_files": total_files,
            "language_counts": language_counts
        }
    
    async def _collect_file_metrics(self, context: AnalysisContext, source_file: SourceFile) -> Dict[str, Any]:
        """
        Collect file-level metrics.
        
        Args:
            context: The analysis context.
            source_file: The source file.
            
        Returns:
            File metrics.
        """
        file_path = source_file.path
        content = source_file.content
        
        # Count lines
        loc = count_lines(content)
        
        # Count comment lines
        comment_lines = self._count_comment_lines(content, file_path)
        
        # Calculate comment ratio
        comment_ratio = comment_lines / loc if loc > 0 else 0
        
        # Calculate cyclomatic complexity
        cc = calculate_cyclomatic_complexity(content)
        
        # Calculate Halstead volume
        operators, operands = get_operators_and_operands(content)
        halstead_volume = calculate_halstead_volume(operators, operands)
        
        # Calculate maintainability index
        mi = calculate_maintainability_index(content, cc, halstead_volume)
        
        # Calculate ranks
        cc_ranking = cc_rank(cc)
        mi_ranking = get_maintainability_rank(mi)
        
        # Add metrics to context
        context.add_metric(
            name="loc",
            value=loc,
            file_path=file_path,
            threshold=self.thresholds["loc"]
        )
        
        context.add_metric(
            name="comment_ratio",
            value=comment_ratio,
            file_path=file_path,
            threshold=self.thresholds["comment_ratio"]
        )
        
        context.add_metric(
            name="cyclomatic_complexity",
            value=cc,
            file_path=file_path,
            threshold=self.thresholds["cyclomatic_complexity"]
        )
        
        context.add_metric(
            name="halstead_volume",
            value=halstead_volume,
            file_path=file_path,
            threshold=self.thresholds["halstead_volume"]
        )
        
        context.add_metric(
            name="maintainability_index",
            value=mi,
            file_path=file_path,
            threshold=self.thresholds["maintainability_index"]
        )
        
        # Return metrics
        return {
            "loc": loc,
            "comment_lines": comment_lines,
            "comment_ratio": comment_ratio,
            "cyclomatic_complexity": cc,
            "cc_ranking": cc_ranking,
            "halstead_volume": halstead_volume,
            "maintainability_index": mi,
            "mi_ranking": mi_ranking
        }
    
    async def _collect_function_metrics(self, context: AnalysisContext, function: Function) -> Dict[str, Any]:
        """
        Collect function-level metrics.
        
        Args:
            context: The analysis context.
            function: The function.
            
        Returns:
            Function metrics.
        """
        file_path = function.source_file.path
        content = function.content
        
        # Count lines
        loc = count_lines(content)
        
        # Count comment lines
        comment_lines = self._count_comment_lines(content, file_path)
        
        # Calculate comment ratio
        comment_ratio = comment_lines / loc if loc > 0 else 0
        
        # Calculate cyclomatic complexity
        cc = calculate_cyclomatic_complexity(content)
        
        # Calculate Halstead volume
        operators, operands = get_operators_and_operands(content)
        halstead_volume = calculate_halstead_volume(operators, operands)
        
        # Calculate maintainability index
        mi = calculate_maintainability_index(content, cc, halstead_volume)
        
        # Calculate ranks
        cc_ranking = cc_rank(cc)
        mi_ranking = get_maintainability_rank(mi)
        
        # Calculate degree of interest
        doi = calculate_doi(cc, halstead_volume, loc)
        
        # Add metrics to context
        context.add_metric(
            name="loc",
            value=loc,
            file_path=file_path,
            symbol_name=function.name,
            threshold=self.thresholds["loc"]
        )
        
        context.add_metric(
            name="comment_ratio",
            value=comment_ratio,
            file_path=file_path,
            symbol_name=function.name,
            threshold=self.thresholds["comment_ratio"]
        )
        
        context.add_metric(
            name="cyclomatic_complexity",
            value=cc,
            file_path=file_path,
            symbol_name=function.name,
            threshold=self.thresholds["cyclomatic_complexity"]
        )
        
        context.add_metric(
            name="halstead_volume",
            value=halstead_volume,
            file_path=file_path,
            symbol_name=function.name,
            threshold=self.thresholds["halstead_volume"]
        )
        
        context.add_metric(
            name="maintainability_index",
            value=mi,
            file_path=file_path,
            symbol_name=function.name,
            threshold=self.thresholds["maintainability_index"]
        )
        
        context.add_metric(
            name="degree_of_interest",
            value=doi,
            file_path=file_path,
            symbol_name=function.name
        )
        
        # Return metrics
        return {
            "loc": loc,
            "comment_lines": comment_lines,
            "comment_ratio": comment_ratio,
            "cyclomatic_complexity": cc,
            "cc_ranking": cc_ranking,
            "halstead_volume": halstead_volume,
            "maintainability_index": mi,
            "mi_ranking": mi_ranking,
            "degree_of_interest": doi
        }
    
    async def _collect_class_metrics(self, context: AnalysisContext, class_def: Class) -> Dict[str, Any]:
        """
        Collect class-level metrics.
        
        Args:
            context: The analysis context.
            class_def: The class definition.
            
        Returns:
            Class metrics.
        """
        file_path = class_def.source_file.path
        content = class_def.content
        
        # Count lines
        loc = count_lines(content)
        
        # Count comment lines
        comment_lines = self._count_comment_lines(content, file_path)
        
        # Calculate comment ratio
        comment_ratio = comment_lines / loc if loc > 0 else 0
        
        # Count methods
        method_count = len(class_def.get_methods())
        
        # Calculate average method complexity
        total_cc = 0
        for method in class_def.get_methods():
            total_cc += calculate_cyclomatic_complexity(method.content)
        
        avg_method_cc = total_cc / method_count if method_count > 0 else 0
        
        # Calculate cyclomatic complexity
        cc = calculate_cyclomatic_complexity(content)
        
        # Calculate Halstead volume
        operators, operands = get_operators_and_operands(content)
        halstead_volume = calculate_halstead_volume(operators, operands)
        
        # Calculate maintainability index
        mi = calculate_maintainability_index(content, cc, halstead_volume)
        
        # Calculate ranks
        cc_ranking = cc_rank(cc)
        mi_ranking = get_maintainability_rank(mi)
        
        # Calculate degree of interest
        doi = calculate_doi(cc, halstead_volume, loc)
        
        # Add metrics to context
        context.add_metric(
            name="loc",
            value=loc,
            file_path=file_path,
            symbol_name=class_def.name,
            threshold=self.thresholds["loc"]
        )
        
        context.add_metric(
            name="comment_ratio",
            value=comment_ratio,
            file_path=file_path,
            symbol_name=class_def.name,
            threshold=self.thresholds["comment_ratio"]
        )
        
        context.add_metric(
            name="cyclomatic_complexity",
            value=cc,
            file_path=file_path,
            symbol_name=class_def.name,
            threshold=self.thresholds["cyclomatic_complexity"]
        )
        
        context.add_metric(
            name="halstead_volume",
            value=halstead_volume,
            file_path=file_path,
            symbol_name=class_def.name,
            threshold=self.thresholds["halstead_volume"]
        )
        
        context.add_metric(
            name="maintainability_index",
            value=mi,
            file_path=file_path,
            symbol_name=class_def.name,
            threshold=self.thresholds["maintainability_index"]
        )
        
        context.add_metric(
            name="method_count",
            value=method_count,
            file_path=file_path,
            symbol_name=class_def.name
        )
        
        context.add_metric(
            name="avg_method_cc",
            value=avg_method_cc,
            file_path=file_path,
            symbol_name=class_def.name
        )
        
        context.add_metric(
            name="degree_of_interest",
            value=doi,
            file_path=file_path,
            symbol_name=class_def.name
        )
        
        # Return metrics
        return {
            "loc": loc,
            "comment_lines": comment_lines,
            "comment_ratio": comment_ratio,
            "method_count": method_count,
            "avg_method_cc": avg_method_cc,
            "cyclomatic_complexity": cc,
            "cc_ranking": cc_ranking,
            "halstead_volume": halstead_volume,
            "maintainability_index": mi,
            "mi_ranking": mi_ranking,
            "degree_of_interest": doi
        }
    
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
    
    def _get_language_from_extension(self, ext: str) -> Optional[str]:
        """
        Get the programming language from a file extension.
        
        Args:
            ext: The file extension.
            
        Returns:
            The programming language or None if unknown.
        """
        # Map of file extensions to languages
        extension_map = {
            ".py": "Python",
            ".js": "JavaScript",
            ".jsx": "JavaScript",
            ".ts": "TypeScript",
            ".tsx": "TypeScript",
            ".java": "Java",
            ".c": "C",
            ".cpp": "C++",
            ".h": "C/C++",
            ".hpp": "C++",
            ".cs": "C#",
            ".go": "Go",
            ".rb": "Ruby",
            ".php": "PHP",
            ".swift": "Swift",
            ".kt": "Kotlin",
            ".rs": "Rust",
            ".scala": "Scala",
            ".html": "HTML",
            ".css": "CSS",
            ".scss": "SCSS",
            ".sass": "SASS",
            ".less": "LESS",
            ".json": "JSON",
            ".xml": "XML",
            ".yaml": "YAML",
            ".yml": "YAML",
            ".md": "Markdown",
            ".sh": "Shell",
            ".bat": "Batch",
            ".ps1": "PowerShell",
            ".sql": "SQL",
            ".r": "R",
            ".dart": "Dart",
            ".lua": "Lua",
            ".pl": "Perl",
            ".pm": "Perl",
            ".t": "Perl",
            ".ex": "Elixir",
            ".exs": "Elixir",
            ".erl": "Erlang",
            ".hrl": "Erlang",
            ".clj": "Clojure",
            ".groovy": "Groovy",
            ".hs": "Haskell",
            ".lhs": "Haskell",
            ".fs": "F#",
            ".fsx": "F#",
            ".ml": "OCaml",
            ".mli": "OCaml",
        }
        
        return extension_map.get(ext)

