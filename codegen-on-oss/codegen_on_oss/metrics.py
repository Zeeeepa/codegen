"""
Metrics module for codegen-on-oss.

This module provides tools for measuring and profiling code metrics,
including complexity, performance, and other quality indicators.
"""

import csv
import os
import resource
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, TextIO, Union

from codegen import Codebase
from loguru import logger


@dataclass
class MetricsProfile:
    """
    Represents a profiling session for a specific repository.

    This class records step-by-step metrics (clock duration, CPU time, memory usage)
    and can write them to a CSV file.
    """

    profile_name: str
    language: Optional[str] = None
    revision: Optional[str] = None
    _start_time: float = field(default_factory=time.perf_counter, repr=False)
    _start_cpu_time: float = field(default_factory=lambda: resource.getrusage(resource.RUSAGE_SELF).ru_utime, repr=False)
    _start_memory: int = field(default_factory=lambda: resource.getrusage(resource.RUSAGE_SELF).ru_maxrss, repr=False)
    _checkpoint_time: float = field(default=0.0, repr=False)
    _checkpoint_cpu_time: float = field(default=0.0, repr=False)
    _checkpoint_memory: int = field(default=0, repr=False)
    _steps: List[Dict[str, Any]] = field(default_factory=list, repr=False)

    def __post_init__(self):
        """Initialize the profile with the starting checkpoint."""
        self._checkpoint_time = self._start_time
        self._checkpoint_cpu_time = self._start_cpu_time
        self._checkpoint_memory = self._start_memory

    def reset_checkpoint(self):
        """Reset the checkpoint to the current time and memory usage."""
        self._checkpoint_time = time.perf_counter()
        self._checkpoint_cpu_time = resource.getrusage(resource.RUSAGE_SELF).ru_utime
        self._checkpoint_memory = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

    def measure(self, step: str, error: Optional[str] = None):
        """
        Measure the time and memory usage since the last checkpoint.

        Args:
            step: The name of the step being measured
            error: Optional error message if the step failed
        """
        current_time = time.perf_counter()
        current_cpu_time = resource.getrusage(resource.RUSAGE_SELF).ru_utime
        current_memory = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

        delta_time = current_time - self._checkpoint_time
        delta_cpu_time = current_cpu_time - self._checkpoint_cpu_time
        delta_memory = current_memory - self._checkpoint_memory

        cumulative_time = current_time - self._start_time

        step_data = {
            "profile_name": self.profile_name,
            "step": step,
            "delta_time": delta_time,
            "cumulative_time": cumulative_time,
            "cpu_time": current_cpu_time,
            "memory_usage": current_memory,
            "memory_delta": delta_memory,
            "error": error,
        }

        self._steps.append(step_data)
        logger.info(step_data)

        self._checkpoint_time = current_time
        self._checkpoint_cpu_time = current_cpu_time
        self._checkpoint_memory = current_memory

        return step_data

    def write_to_csv(self, output_path: Union[str, Path, TextIO]):
        """
        Write the profile data to a CSV file.

        Args:
            output_path: Path to the output CSV file or a file-like object
        """
        if not self._steps:
            return

        # Determine if we're writing to a file or a file-like object
        close_file = False
        if isinstance(output_path, (str, Path)):
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            f = open(output_path, "a", newline="")
            close_file = True
        else:
            f = output_path

        try:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "profile_name",
                    "step",
                    "delta_time",
                    "cumulative_time",
                    "cpu_time",
                    "memory_usage",
                    "memory_delta",
                    "error",
                ],
            )

            # Write header if the file is empty
            if isinstance(output_path, (str, Path)) and os.path.getsize(output_path) == 0:
                writer.writeheader()

            # Write the steps
            writer.writerows(self._steps)
        finally:
            if close_file:
                f.close()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the profile to a dictionary.

        Returns:
            Dict containing the profile data
        """
        return {
            "profile_name": self.profile_name,
            "language": self.language,
            "revision": self.revision,
            "timestamp": datetime.now().isoformat(),
            "steps": self._steps,
        }


class MetricsProfiler:
    """
    A context manager that creates a profiling session.

    This class provides a convenient way to profile code execution
    and record metrics at key steps.
    """

    def __init__(self, output_path: Optional[Union[str, Path, TextIO]] = None):
        """
        Initialize the profiler.

        Args:
            output_path: Optional path to the output CSV file or a file-like object
        """
        self.output_path = output_path

    @contextmanager
    def start_profiler(
        self,
        name: str,
        language: Optional[str] = None,
        revision: Optional[str] = None,
        logger=None,
    ):
        """
        Start a profiling session.

        Args:
            name: Name of the profile (usually the repository name)
            language: Optional language of the repository
            revision: Optional revision (commit hash) of the repository
            logger: Optional logger to use for logging

        Yields:
            MetricsProfile instance
        """
        profile = MetricsProfile(profile_name=name, language=language, revision=revision)
        try:
            yield profile
            profile.measure("TOTAL")
        except Exception as e:
            if logger:
                logger.exception(f"Error in profiling session: {e}")
            profile.measure("TOTAL", error=str(e))
            raise
        finally:
            if self.output_path:
                profile.write_to_csv(self.output_path)


class CodeMetrics:
    """
    Calculate code metrics for a codebase.

    This class provides methods for calculating various code metrics,
    including complexity, maintainability, and other quality indicators.
    """

    def __init__(self, codebase: Codebase):
        """
        Initialize the CodeMetrics.

        Args:
            codebase: The codebase to analyze
        """
        self.codebase = codebase

    def calculate_metrics(self) -> Dict[str, Any]:
        """
        Calculate all metrics for the codebase.

        Returns:
            Dict containing all metrics
        """
        return {
            "complexity": self.calculate_complexity_metrics(),
            "size": self.calculate_size_metrics(),
            "maintainability": self.calculate_maintainability_metrics(),
            "dependencies": self.calculate_dependency_metrics(),
        }

    def calculate_complexity_metrics(self) -> Dict[str, Any]:
        """
        Calculate complexity metrics for the codebase.

        Returns:
            Dict containing complexity metrics
        """
        functions = list(self.codebase.functions)
        if not functions:
            return {
                "average_complexity": 0,
                "max_complexity": 0,
                "complexity_distribution": {
                    "low": 0,
                    "moderate": 0,
                    "high": 0,
                    "very_high": 0,
                },
                "most_complex_functions": [],
            }

        # Calculate cyclomatic complexity for each function
        complexities = []
        for func in functions:
            try:
                complexity = self._calculate_cyclomatic_complexity(func)
                complexities.append((func, complexity))
            except Exception:
                # Skip functions that can't be analyzed
                pass

        if not complexities:
            return {
                "average_complexity": 0,
                "max_complexity": 0,
                "complexity_distribution": {
                    "low": 0,
                    "moderate": 0,
                    "high": 0,
                    "very_high": 0,
                },
                "most_complex_functions": [],
            }

        # Calculate metrics
        total_complexity = sum(c for _, c in complexities)
        average_complexity = total_complexity / len(complexities)
        max_complexity = max(c for _, c in complexities)

        # Categorize complexity
        complexity_distribution = {
            "low": 0,  # 1-5
            "moderate": 0,  # 6-10
            "high": 0,  # 11-20
            "very_high": 0,  # 21+
        }

        for _, complexity in complexities:
            if complexity <= 5:
                complexity_distribution["low"] += 1
            elif complexity <= 10:
                complexity_distribution["moderate"] += 1
            elif complexity <= 20:
                complexity_distribution["high"] += 1
            else:
                complexity_distribution["very_high"] += 1

        # Get the most complex functions
        most_complex = sorted(complexities, key=lambda x: x[1], reverse=True)[:10]
        most_complex_functions = [
            {
                "name": func.name,
                "file": func.file.file_path if hasattr(func, "file") else "Unknown",
                "complexity": complexity,
            }
            for func, complexity in most_complex
        ]

        return {
            "average_complexity": average_complexity,
            "max_complexity": max_complexity,
            "complexity_distribution": complexity_distribution,
            "most_complex_functions": most_complex_functions,
        }

    def calculate_size_metrics(self) -> Dict[str, Any]:
        """
        Calculate size metrics for the codebase.

        Returns:
            Dict containing size metrics
        """
        files = list(self.codebase.files)
        functions = list(self.codebase.functions)
        classes = list(self.codebase.classes)

        # Calculate file size metrics
        file_sizes = []
        total_lines = 0
        for file in files:
            try:
                size = len(file.source.splitlines())
                file_sizes.append((file, size))
                total_lines += size
            except Exception:
                # Skip files that can't be analyzed
                pass

        if not file_sizes:
            return {
                "total_files": len(files),
                "total_functions": len(functions),
                "total_classes": len(classes),
                "total_lines": 0,
                "average_file_size": 0,
                "largest_files": [],
            }

        # Calculate metrics
        average_file_size = total_lines / len(file_sizes)

        # Get the largest files
        largest_files = sorted(file_sizes, key=lambda x: x[1], reverse=True)[:10]
        largest_files_info = [
            {
                "file": file.file_path,
                "size": size,
            }
            for file, size in largest_files
        ]

        return {
            "total_files": len(files),
            "total_functions": len(functions),
            "total_classes": len(classes),
            "total_lines": total_lines,
            "average_file_size": average_file_size,
            "largest_files": largest_files_info,
        }

    def calculate_maintainability_metrics(self) -> Dict[str, Any]:
        """
        Calculate maintainability metrics for the codebase.

        Returns:
            Dict containing maintainability metrics
        """
        functions = list(self.codebase.functions)
        if not functions:
            return {
                "average_maintainability_index": 0,
                "maintainability_distribution": {
                    "excellent": 0,
                    "good": 0,
                    "fair": 0,
                    "poor": 0,
                },
                "least_maintainable_functions": [],
            }

        # Calculate maintainability index for each function
        maintainability_indices = []
        for func in functions:
            try:
                index = self._calculate_maintainability_index(func)
                maintainability_indices.append((func, index))
            except Exception:
                # Skip functions that can't be analyzed
                pass

        if not maintainability_indices:
            return {
                "average_maintainability_index": 0,
                "maintainability_distribution": {
                    "excellent": 0,
                    "good": 0,
                    "fair": 0,
                    "poor": 0,
                },
                "least_maintainable_functions": [],
            }

        # Calculate metrics
        total_index = sum(i for _, i in maintainability_indices)
        average_index = total_index / len(maintainability_indices)

        # Categorize maintainability
        maintainability_distribution = {
            "excellent": 0,  # 85-100
            "good": 0,  # 65-84
            "fair": 0,  # 40-64
            "poor": 0,  # 0-39
        }

        for _, index in maintainability_indices:
            if index >= 85:
                maintainability_distribution["excellent"] += 1
            elif index >= 65:
                maintainability_distribution["good"] += 1
            elif index >= 40:
                maintainability_distribution["fair"] += 1
            else:
                maintainability_distribution["poor"] += 1

        # Get the least maintainable functions
        least_maintainable = sorted(maintainability_indices, key=lambda x: x[1])[:10]
        least_maintainable_functions = [
            {
                "name": func.name,
                "file": func.file.file_path if hasattr(func, "file") else "Unknown",
                "maintainability_index": index,
            }
            for func, index in least_maintainable
        ]

        return {
            "average_maintainability_index": average_index,
            "maintainability_distribution": maintainability_distribution,
            "least_maintainable_functions": least_maintainable_functions,
        }

    def calculate_dependency_metrics(self) -> Dict[str, Any]:
        """
        Calculate dependency metrics for the codebase.

        Returns:
            Dict containing dependency metrics
        """
        imports = list(self.codebase.imports)
        if not imports:
            return {
                "total_imports": 0,
                "external_imports": 0,
                "internal_imports": 0,
                "most_imported_modules": [],
            }

        # Count imports by module
        import_counts = {}
        external_imports = 0
        internal_imports = 0

        for imp in imports:
            module = imp.module_name
            if module not in import_counts:
                import_counts[module] = 0
            import_counts[module] += 1

            # Determine if the import is external or internal
            if hasattr(imp, "is_external") and imp.is_external:
                external_imports += 1
            else:
                internal_imports += 1

        # Get the most imported modules
        most_imported = sorted(import_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        most_imported_modules = [
            {
                "module": module,
                "count": count,
            }
            for module, count in most_imported
        ]

        return {
            "total_imports": len(imports),
            "external_imports": external_imports,
            "internal_imports": internal_imports,
            "most_imported_modules": most_imported_modules,
        }

    def _calculate_cyclomatic_complexity(self, func) -> int:
        """
        Calculate the cyclomatic complexity of a function.

        Args:
            func: The function to analyze

        Returns:
            Cyclomatic complexity value
        """
        # This is a simplified calculation
        # A more accurate calculation would parse the AST and count decision points
        source = func.source
        complexity = 1  # Base complexity

        # Count decision points
        complexity += source.count("if ")
        complexity += source.count("elif ")
        complexity += source.count("for ")
        complexity += source.count("while ")
        complexity += source.count("except")
        complexity += source.count("case ")
        complexity += source.count(" and ")
        complexity += source.count(" or ")
        complexity += source.count("?")  # Ternary operator

        return complexity

    def _calculate_maintainability_index(self, func) -> float:
        """
        Calculate the maintainability index of a function.

        Args:
            func: The function to analyze

        Returns:
            Maintainability index value
        """
        # This is a simplified calculation
        # The maintainability index is a weighted combination of:
        # - Cyclomatic complexity
        # - Halstead volume
        # - Lines of code
        # - Comment percentage
        import math

        source = func.source
        lines = source.splitlines()
        line_count = len(lines)
        if line_count == 0:
            return 100  # Perfect maintainability for empty functions

        # Calculate cyclomatic complexity
        complexity = self._calculate_cyclomatic_complexity(func)

        # Calculate Halstead volume (simplified)
        operators = len([c for c in source if c in "+-*/=<>!&|^~"])
        operands = len([word for line in lines for word in line.split() if word.isalnum()])
        if operators == 0 or operands == 0:
            volume = 0
        else:
            volume = (operators + operands) * math.log2(operators + operands)

        # Calculate comment percentage (simplified)
        comment_lines = sum(1 for line in lines if line.strip().startswith(("#", "//", "/*", "*", "*/")))
        comment_percentage = comment_lines / line_count if line_count > 0 else 0

        # Calculate maintainability index
        # MI = 171 - 5.2 * ln(volume) - 0.23 * complexity - 16.2 * ln(line_count) + 50 * sin(sqrt(2.4 * comment_percentage))
        mi = 171
        if volume > 0:
            mi -= 5.2 * math.log(volume)
        mi -= 0.23 * complexity
        if line_count > 0:
            mi -= 16.2 * math.log(line_count)
        mi += 50 * math.sin(math.sqrt(2.4 * comment_percentage))

        # Normalize to 0-100 scale
        mi = max(0, min(100, mi))

        return mi

