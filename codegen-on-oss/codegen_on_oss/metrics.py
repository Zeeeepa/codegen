import json
import os
import time
import math
from collections.abc import Generator
from contextlib import contextmanager
from importlib.metadata import version
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

import psutil
from codegen import Codebase

from codegen_on_oss.errors import ParseRunError
from codegen_on_oss.outputs.base import BaseOutput
from codegen_on_oss.analysis.analysis import (
    calculate_cyclomatic_complexity,
    calculate_halstead_volume,
    calculate_maintainability_index,
    count_lines,
    get_operators_and_operands,
    cc_rank,
    get_maintainability_rank,
    calculate_doi,
)

if TYPE_CHECKING:
    # Logger only available in type checking context.
    from loguru import Logger  # type: ignore[attr-defined]


codegen_version = str(version("codegen"))


class CodeMetrics:
    """
    A class to calculate and provide code quality metrics for a codebase.
    Integrates with the analysis module for comprehensive code analysis.
    """

    # Constants for threshold values
    COMPLEXITY_THRESHOLD = 10
    MAINTAINABILITY_THRESHOLD = 65
    INHERITANCE_DEPTH_THRESHOLD = 3

    def __init__(self, codebase: Codebase):
        """
        Initialize the CodeMetrics class with a codebase.

        Args:
            codebase: The Codebase object to analyze
        """
        self.codebase = codebase
        self._complexity_metrics = None
        self._line_metrics = None
        self._maintainability_metrics = None
        self._inheritance_metrics = None
        self._halstead_metrics = None

    def calculate_all_metrics(self) -> Dict[str, Any]:
        """
        Calculate all available metrics for the codebase.

        Returns:
            A dictionary containing all metrics categories
        """
        return {
            "complexity": self.complexity_metrics,
            "lines": self.line_metrics,
            "maintainability": self.maintainability_metrics,
            "inheritance": self.inheritance_metrics,
            "halstead": self.halstead_metrics,
        }

    @property
    def complexity_metrics(self) -> Dict[str, Any]:
        """
        Calculate cyclomatic complexity metrics for the codebase.

        Returns:
            A dictionary containing complexity metrics including average,
            rank, and per-function complexity scores
        """
        if self._complexity_metrics is not None:
            return self._complexity_metrics

        callables = self.codebase.functions + [
            m for c in self.codebase.classes for m in c.methods
        ]

        complexities = []
        for func in callables:
            if not hasattr(func, "code_block"):
                continue

            complexity = calculate_cyclomatic_complexity(func)
            complexities.append(
                {
                    "name": func.name,
                    "complexity": complexity,
                    "rank": cc_rank(complexity),
                }
            )

        avg_complexity = (
            sum(item["complexity"] for item in complexities) / len(complexities)
            if complexities
            else 0
        )

        self._complexity_metrics = {
            "average": avg_complexity,
            "rank": cc_rank(avg_complexity),
            "functions": complexities,
        }

        return self._complexity_metrics

    @property
    def line_metrics(self) -> Dict[str, Any]:
        """
        Calculate line-based metrics for the codebase.

        Returns:
            A dictionary containing line metrics including total counts
            and per-file metrics for LOC, LLOC, SLOC, and comments
        """
        if self._line_metrics is not None:
            return self._line_metrics

        total_loc = total_lloc = total_sloc = total_comments = 0
        file_metrics = []

        for file in self.codebase.files:
            loc, lloc, sloc, comments = count_lines(file.source)
            comment_density = (comments / loc * 100) if loc > 0 else 0

            file_metrics.append(
                {
                    "file": file.path,
                    "loc": loc,
                    "lloc": lloc,
                    "sloc": sloc,
                    "comments": comments,
                    "comment_density": comment_density,
                }
            )

            total_loc += loc
            total_lloc += lloc
            total_sloc += sloc
            total_comments += comments

        total_comment_density = total_comments / total_loc * 100 if total_loc > 0 else 0

        self._line_metrics = {
            "total": {
                "loc": total_loc,
                "lloc": total_lloc,
                "sloc": total_sloc,
                "comments": total_comments,
                "comment_density": total_comment_density,
            },
            "files": file_metrics,
        }

        return self._line_metrics

    @property
    def maintainability_metrics(self) -> Dict[str, Any]:
        """
        Calculate maintainability index metrics for the codebase.

        Returns:
            A dictionary containing maintainability metrics including average,
            rank, and per-function maintainability scores
        """
        if self._maintainability_metrics is not None:
            return self._maintainability_metrics

        callables = self.codebase.functions + [
            m for c in self.codebase.classes for m in c.methods
        ]

        mi_scores = []
        for func in callables:
            if not hasattr(func, "code_block"):
                continue

            complexity = calculate_cyclomatic_complexity(func)
            operators, operands = get_operators_and_operands(func)
            volume, _, _, _, _ = calculate_halstead_volume(operators, operands)
            loc = len(func.code_block.source.splitlines())
            mi_score = calculate_maintainability_index(volume, complexity, loc)

            mi_scores.append(
                {
                    "name": func.name,
                    "mi_score": mi_score,
                    "rank": get_maintainability_rank(mi_score),
                }
            )

        avg_mi = (
            sum(item["mi_score"] for item in mi_scores) / len(mi_scores)
            if mi_scores
            else 0
        )

        self._maintainability_metrics = {
            "average": avg_mi,
            "rank": get_maintainability_rank(avg_mi),
            "functions": mi_scores,
        }

        return self._maintainability_metrics

    @property
    def inheritance_metrics(self) -> Dict[str, Any]:
        """
        Calculate inheritance metrics for the codebase.

        Returns:
            A dictionary containing inheritance metrics including average
            depth of inheritance and per-class inheritance depth
        """
        if self._inheritance_metrics is not None:
            return self._inheritance_metrics

        class_metrics = []
        for cls in self.codebase.classes:
            doi = calculate_doi(cls)
            class_metrics.append({"name": cls.name, "doi": doi})

        avg_doi = (
            sum(item["doi"] for item in class_metrics) / len(class_metrics)
            if class_metrics
            else 0
        )

        self._inheritance_metrics = {"average": avg_doi, "classes": class_metrics}

        return self._inheritance_metrics

    @property
    def halstead_metrics(self) -> Dict[str, Any]:
        """
        Calculate Halstead complexity metrics for the codebase.

        Returns:
            A dictionary containing Halstead metrics including volume,
            difficulty, effort, and other Halstead measures
        """
        if self._halstead_metrics is not None:
            return self._halstead_metrics

        callables = self.codebase.functions + [
            m for c in self.codebase.classes for m in c.methods
        ]

        halstead_metrics = []
        for func in callables:
            if not hasattr(func, "code_block"):
                continue

            operators, operands = get_operators_and_operands(func)
            volume, n1, n2, n_operators, n_operands = calculate_halstead_volume(
                operators, operands
            )

            # Calculate additional Halstead metrics
            n = n_operators + n_operands
            N = n1 + n2

            difficulty = (n_operators / 2) * (n2 / n_operands) if n_operands > 0 else 0
            effort = difficulty * volume if volume > 0 else 0
            time_required = effort / 18 if effort > 0 else 0  # Seconds
            bugs_delivered = volume / 3000 if volume > 0 else 0

            halstead_metrics.append(
                {
                    "name": func.name,
                    "volume": volume,
                    "difficulty": difficulty,
                    "effort": effort,
                    "time_required": time_required,  # in seconds
                    "bugs_delivered": bugs_delivered,
                }
            )

        avg_volume = (
            sum(item["volume"] for item in halstead_metrics) / len(halstead_metrics)
            if halstead_metrics
            else 0
        )
        avg_difficulty = (
            sum(item["difficulty"] for item in halstead_metrics) / len(halstead_metrics)
            if halstead_metrics
            else 0
        )
        avg_effort = (
            sum(item["effort"] for item in halstead_metrics) / len(halstead_metrics)
            if halstead_metrics
            else 0
        )

        self._halstead_metrics = {
            "average": {
                "volume": avg_volume,
                "difficulty": avg_difficulty,
                "effort": avg_effort,
            },
            "functions": halstead_metrics,
        }

        return self._halstead_metrics

    def find_complex_functions(
        self, threshold: int = COMPLEXITY_THRESHOLD
    ) -> List[Dict[str, Any]]:
        """
        Find functions with cyclomatic complexity above the threshold.

        Args:
            threshold: The complexity threshold (default: 10)

        Returns:
            A list of functions with complexity above the threshold
        """
        metrics = self.complexity_metrics
        return [func for func in metrics["functions"] if func["complexity"] > threshold]

    def find_low_maintainability_functions(
        self, threshold: int = MAINTAINABILITY_THRESHOLD
    ) -> List[Dict[str, Any]]:
        """
        Find functions with maintainability index below the threshold.

        Args:
            threshold: The maintainability threshold (default: 65)

        Returns:
            A list of functions with maintainability below the threshold
        """
        metrics = self.maintainability_metrics
        return [func for func in metrics["functions"] if func["mi_score"] < threshold]

    def find_deep_inheritance_classes(
        self, threshold: int = INHERITANCE_DEPTH_THRESHOLD
    ) -> List[Dict[str, Any]]:
        """
        Find classes with depth of inheritance above the threshold.

        Args:
            threshold: The inheritance depth threshold (default: 3)

        Returns:
            A list of classes with inheritance depth above the threshold
        """
        metrics = self.inheritance_metrics
        return [cls for cls in metrics["classes"] if cls["doi"] > threshold]

    def find_high_volume_functions(self, threshold: int = 1000) -> List[Dict[str, Any]]:
        """
        Find functions with Halstead volume above the threshold.

        Args:
            threshold: The volume threshold (default: 1000)

        Returns:
            A list of functions with volume above the threshold
        """
        metrics = self.halstead_metrics
        return [func for func in metrics["functions"] if func["volume"] > threshold]

    def find_high_effort_functions(
        self, threshold: int = 50000
    ) -> List[Dict[str, Any]]:
        """
        Find functions with high Halstead effort (difficult to maintain).

        Args:
            threshold: The effort threshold (default: 50000)

        Returns:
            A list of functions with effort above the threshold
        """
        metrics = self.halstead_metrics
        return [func for func in metrics["functions"] if func["effort"] > threshold]

    def find_bug_prone_functions(self, threshold: float = 0.5) -> List[Dict[str, Any]]:
        """
        Find functions with high estimated bug delivery.

        Args:
            threshold: The bugs delivered threshold (default: 0.5)

        Returns:
            A list of functions likely to contain bugs
        """
        metrics = self.halstead_metrics
        return [
            func for func in metrics["functions"] if func["bugs_delivered"] > threshold
        ]

    def get_code_quality_summary(self) -> Dict[str, Any]:
        """
        Generate a comprehensive code quality summary.

        Returns:
            A dictionary with overall code quality metrics and problem areas
        """
        return {
            "overall_metrics": {
                "complexity": self.complexity_metrics["average"],
                "complexity_rank": self.complexity_metrics["rank"],
                "maintainability": self.maintainability_metrics["average"],
                "maintainability_rank": self.maintainability_metrics["rank"],
                "lines_of_code": self.line_metrics["total"]["loc"],
                "comment_density": self.line_metrics["total"]["comment_density"],
                "inheritance_depth": self.inheritance_metrics["average"],
                "halstead_volume": self.halstead_metrics["average"]["volume"],
                "halstead_difficulty": self.halstead_metrics["average"]["difficulty"],
            },
            "problem_areas": {
                "complex_functions": len(self.find_complex_functions()),
                "low_maintainability": len(self.find_low_maintainability_functions()),
                "deep_inheritance": len(self.find_deep_inheritance_classes()),
                "high_volume": len(self.find_high_volume_functions()),
                "high_effort": len(self.find_high_effort_functions()),
                "bug_prone": len(self.find_bug_prone_functions()),
            },
        }


class MetricsProfiler:
    """
    A helper to record performance metrics across multiple profiles and write them to a CSV.

    Usage:

        metrics_profiler = MetricsProfiler(output_path="metrics.csv")

        with metrics_profiler.start_profiler(name="profile_1", language="python") as profile:
            # Some code block...
            profile.measure("step 1")
            # More code...
            profile.measure("step 2")

        # The CSV "metrics.csv" now contains the measurements for profile_1.
    """

    def __init__(self, output: BaseOutput):
        self.output = output

    @contextmanager
    def start_profiler(
        self, name: str, revision: str, language: Optional[str], logger: "Logger"
    ) -> Generator["MetricsProfile", None, None]:
        """
        Starts a new profiling session for a given profile name.
        Returns a MetricsProfile instance that you can use to mark measurements.
        """
        profile = MetricsProfile(name, revision, language or "", logger, self.output)
        try:
            yield profile
        finally:
            profile.finish()


class MetricsProfile:
    """
    Context-managed profile that records measurements at each call to `measure()`.
    It tracks the wall-clock duration, CPU time, and memory usage (with delta)
    at the time of the call. Upon exiting the context, it also writes all collected
    metrics, including the total time, to a CSV file.
    """

    if TYPE_CHECKING:
        logger: "Logger"
        measurements: list[dict[str, Any]]

    def __init__(
        self,
        name: str,
        revision: str,
        language: str,
        output: BaseOutput,
        logger: "Logger",
    ):
        self.name = name
        self.revision = revision
        self.language = language
        self.output = output
        self.logger = logger

        # Capture initial metrics.
        self.start_time = time.perf_counter()
        self.start_cpu = time.process_time()
        self.start_mem = int(
            psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
        )

        # For delta calculations, store the last measurement values.
        self.last_measure_time = self.start_time
        self.last_measure_mem = self.start_mem

    def reset_checkpoint(self):
        # Update last measurement time and memory for the next delta.
        self.last_measure_time = time.perf_counter()
        self.last_measure_mem = self.start_mem

    def measure(self, action_name: str):
        """
        Records a measurement for the given step. The measurement includes:
          - Delta wall-clock time since the last measurement or the start,
          - Cumulative wall-clock time since the start,
          - The current CPU usage of the process (using time.process_time()),
          - The current memory usage (RSS in bytes),
          - The memory delta (difference from the previous measurement).
        """
        current_time = time.perf_counter()
        current_cpu = float(time.process_time())
        current_mem = int(psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024))

        # Calculate time deltas.
        delta_time = current_time - self.last_measure_time
        cumulative_time = current_time - self.start_time

        # Calculate memory delta.
        memory_delta = current_mem - self.last_measure_mem

        # Record the measurement.
        measurement = {
            "repo": self.name,
            "revision": self.revision,
            "codegen_version": codegen_version,
            "action": action_name,
            "language": self.language,
            "delta_time": delta_time,
            "cumulative_time": cumulative_time,
            "cpu_time": current_cpu,  # CPU usage at this point.
            "memory_usage": current_mem,
            "memory_delta": memory_delta,
            "error": None,
        }
        self.write_output(measurement)

        # Update last measurement time and memory for the next delta.
        self.last_measure_time = current_time
        self.last_measure_mem = current_mem

    def finish(self):
        """
        Called automatically when the profiling context is exited.
        This method records a final measurement (for the total duration) and
        writes all collected metrics to the CSV file.
        """
        finish_time = time.perf_counter()
        finish_cpu = float(time.process_time())
        finish_mem = int(psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024))

        total_duration = finish_time - self.start_time

        # Calculate final memory delta.
        memory_delta = finish_mem - self.last_measure_mem

        # Record the overall profile measurement.
        self.write_output(
            {
                "repo": self.name,
                "revision": self.revision,
                "codegen_version": codegen_version,
                "language": self.language,
                "action": "total_parse",
                "delta_time": total_duration,
                "cumulative_time": total_duration,
                "cpu_time": finish_cpu,
                "memory_usage": finish_mem,
                "memory_delta": memory_delta,
                "error": None,
            }
        )

    def write_output(self, measurement: dict[str, Any]):
        """
        Writes all measurements to the CSV file using CSVOutput.
        """
        self.logger.info(json.dumps(measurement, indent=4))
        self.output.write_output(measurement)
