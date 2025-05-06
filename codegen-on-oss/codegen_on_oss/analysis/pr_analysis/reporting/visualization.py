"""
Visualization

Components for visualizing analysis results.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class Visualization:
    """
    Components for visualizing analysis results.

    This class provides methods for generating visualizations of analysis results.
    """

    def generate_issue_chart_data(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate data for an issue chart.

        Args:
            results: The analysis results

        Returns:
            A dictionary containing chart data
        """
        # Count issues by rule and severity
        rule_counts = {}
        severity_counts = {"error": 0, "warning": 0, "info": 0}

        for rule_id, rule_result in results.items():
            rule_issues = rule_result.get("issues", [])
            if not rule_issues:
                continue

            # Get the rule name from the first issue
            rule_name = rule_issues[0].get("rule_name", rule_id) if rule_issues else rule_id

            # Count issues by rule
            rule_counts[rule_name] = len(rule_issues)

            # Count issues by severity
            for issue in rule_issues:
                severity = issue.get("severity", "info")
                severity_counts[severity] = severity_counts.get(severity, 0) + 1

        return {"rule_counts": rule_counts, "severity_counts": severity_counts}

    def generate_file_heatmap_data(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate data for a file heatmap.

        Args:
            results: The analysis results

        Returns:
            A dictionary containing heatmap data
        """
        # Count issues by file
        file_counts = {}

        for rule_id, rule_result in results.items():
            for issue in rule_result.get("issues", []):
                file_path = issue.get("file_path")
                if not file_path:
                    continue

                severity = issue.get("severity", "info")

                if file_path not in file_counts:
                    file_counts[file_path] = {
                        "error": 0,
                        "warning": 0,
                        "info": 0,
                        "total": 0,
                    }

                file_counts[file_path][severity] = file_counts[file_path].get(severity, 0) + 1
                file_counts[file_path]["total"] += 1

        return {"file_counts": file_counts}

    def generate_trend_data(
        self,
        current_results: Dict[str, Any],
        previous_results: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate data for a trend chart.

        Args:
            current_results: The current analysis results
            previous_results: The previous analysis results

        Returns:
            A dictionary containing trend data
        """
        # Count current issues by severity
        current_counts = {"error": 0, "warning": 0, "info": 0, "total": 0}

        for rule_id, rule_result in current_results.items():
            for issue in rule_result.get("issues", []):
                severity = issue.get("severity", "info")
                current_counts[severity] = current_counts.get(severity, 0) + 1
                current_counts["total"] += 1

        # Count previous issues by severity
        previous_counts = {"error": 0, "warning": 0, "info": 0, "total": 0}

        if previous_results:
            for rule_id, rule_result in previous_results.items():
                for issue in rule_result.get("issues", []):
                    severity = issue.get("severity", "info")
                    previous_counts[severity] = previous_counts.get(severity, 0) + 1
                    previous_counts["total"] += 1

        # Calculate changes
        changes = {
            "error": current_counts["error"] - previous_counts["error"],
            "warning": current_counts["warning"] - previous_counts["warning"],
            "info": current_counts["info"] - previous_counts["info"],
            "total": current_counts["total"] - previous_counts["total"],
        }

        return {
            "current": current_counts,
            "previous": previous_counts,
            "changes": changes,
        }
