#!/usr/bin/env python3
"""
Resolution Manager Module

This module provides functionality for resolving code issues identified
during codebase analysis. It integrates with the analyzer modules to
apply automated fixes and track issue resolution.
"""

import logging
import os
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class ResolutionStrategy(str, Enum):
    """Strategies for resolving issues."""

    AUTO_FIX = "auto_fix"
    SUGGESTION = "suggestion"
    MANUAL = "manual"
    IGNORE = "ignore"


class ResolutionStatus(str, Enum):
    """Status of resolution attempts."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    FAILED = "failed"
    IGNORED = "ignored"


class ResolutionManager:
    """
    Manager for resolving code issues identified during analysis.

    This class provides functionality to track, apply, and validate
    resolutions for issues found in the codebase.
    """

    def __init__(
        self,
        analyzer=None,
        codebase=None,
        context=None,
        auto_apply: bool = False,
        strategies: dict[str, ResolutionStrategy] | None = None,
    ):
        """
        Initialize the ResolutionManager.

        Args:
            analyzer: Optional analyzer with analysis results
            codebase: Optional codebase to resolve issues for
            context: Optional context providing graph representation
            auto_apply: Whether to automatically apply resolutions
            strategies: Dictionary mapping issue types to resolution strategies
        """
        self.analyzer = analyzer
        self.codebase = codebase or (analyzer.base_codebase if analyzer else None)
        self.context = context or (analyzer.base_context if analyzer else None)
        self.auto_apply = auto_apply
        self.strategies = strategies or {}
        self.resolutions = {}
        self.resolution_history = []

        # Initialize strategies if not provided
        if not self.strategies:
            self._init_default_strategies()

    def _init_default_strategies(self):
        """Initialize default resolution strategies for common issue types."""
        self.strategies = {
            "unused_import": ResolutionStrategy.AUTO_FIX,
            "unused_variable": ResolutionStrategy.AUTO_FIX,
            "unused_function": ResolutionStrategy.SUGGESTION,
            "missing_return_type": ResolutionStrategy.AUTO_FIX,
            "parameter_type_mismatch": ResolutionStrategy.SUGGESTION,
            "circular_dependency": ResolutionStrategy.MANUAL,
            "complex_function": ResolutionStrategy.SUGGESTION,
            "dead_code": ResolutionStrategy.SUGGESTION,
            "security_issue": ResolutionStrategy.MANUAL,
        }

    def load_issues(self):
        """
        Load issues from the analyzer.

        Returns:
            List of issues
        """
        if not self.analyzer:
            logger.error("No analyzer available")
            return []

        if not hasattr(self.analyzer, "results") or not self.analyzer.results:
            logger.error("No analysis results available")
            return []

        if "issues" not in self.analyzer.results:
            logger.error("No issues found in analysis results")
            return []

        issues = self.analyzer.results["issues"]

        # Initialize resolutions tracking
        for issue in issues:
            issue_id = issue.get("id")
            if not issue_id:
                continue

            self.resolutions[issue_id] = {
                "issue": issue,
                "status": ResolutionStatus.PENDING,
                "strategy": self.strategies.get(
                    issue.get("type"), ResolutionStrategy.MANUAL
                ),
                "resolution_data": None,
                "applied": False,
                "validation_result": None,
            }

        return issues

    def get_resolution_candidates(
        self, filter_strategy: ResolutionStrategy | None = None
    ):
        """
        Get issues that can be resolved with the specified strategy.

        Args:
            filter_strategy: Optional strategy to filter issues by

        Returns:
            List of issues that can be resolved with the specified strategy
        """
        candidates = []

        for _issue_id, resolution in self.resolutions.items():
            if filter_strategy and resolution["strategy"] != filter_strategy:
                continue

            if resolution["status"] == ResolutionStatus.PENDING:
                candidates.append(resolution["issue"])

        return candidates

    def generate_resolutions(self):
        """
        Generate resolutions for all pending issues.

        Returns:
            Number of resolutions generated
        """
        count = 0

        # Process auto-fix issues first
        auto_fix_candidates = self.get_resolution_candidates(
            ResolutionStrategy.AUTO_FIX
        )
        for issue in auto_fix_candidates:
            if self._generate_resolution(issue):
                count += 1

        # Process suggestion issues next
        suggestion_candidates = self.get_resolution_candidates(
            ResolutionStrategy.SUGGESTION
        )
        for issue in suggestion_candidates:
            if self._generate_resolution(issue):
                count += 1

        # Skip manual issues as they require human intervention

        return count

    def _generate_resolution(self, issue):
        """
        Generate a resolution for a specific issue.

        Args:
            issue: Issue to generate a resolution for

        Returns:
            True if a resolution was generated, False otherwise
        """
        issue_id = issue.get("id")
        if not issue_id or issue_id not in self.resolutions:
            return False

        resolution = self.resolutions[issue_id]
        resolution["status"] = ResolutionStatus.IN_PROGRESS

        try:
            # Generate resolution based on issue type
            issue_type = issue.get("type")
            issue.get("file")
            issue.get("line")

            # Special handling for common issue types
            if issue_type == "unused_import":
                resolution_data = self._resolve_unused_import(issue)
            elif issue_type == "unused_variable":
                resolution_data = self._resolve_unused_variable(issue)
            elif issue_type == "unused_function":
                resolution_data = self._resolve_unused_function(issue)
            elif issue_type == "missing_return_type":
                resolution_data = self._resolve_missing_return_type(issue)
            elif issue_type == "parameter_type_mismatch":
                resolution_data = self._resolve_parameter_type_mismatch(issue)
            elif issue_type == "circular_dependency":
                resolution_data = self._resolve_circular_dependency(issue)
            elif issue_type == "complex_function":
                resolution_data = self._resolve_complex_function(issue)
            elif issue_type == "dead_code":
                resolution_data = self._resolve_dead_code(issue)
            else:
                # No specific handler for this issue type
                resolution["status"] = ResolutionStatus.PENDING
                return False

            if not resolution_data:
                resolution["status"] = ResolutionStatus.FAILED
                return False

            resolution["resolution_data"] = resolution_data
            resolution["status"] = ResolutionStatus.RESOLVED

            # Auto-apply if configured
            if (
                self.auto_apply
                and resolution["strategy"] == ResolutionStrategy.AUTO_FIX
            ):
                self.apply_resolution(issue_id)

            return True
        except Exception as e:
            logger.exception(f"Error generating resolution for issue {issue_id}: {e!s}")
            resolution["status"] = ResolutionStatus.FAILED
            return False

    def apply_resolution(self, issue_id):
        """
        Apply a resolution to the codebase.

        Args:
            issue_id: ID of the issue to apply the resolution for

        Returns:
            True if the resolution was applied, False otherwise
        """
        if issue_id not in self.resolutions:
            logger.error(f"Issue {issue_id} not found")
            return False

        resolution = self.resolutions[issue_id]
        if resolution["status"] != ResolutionStatus.RESOLVED:
            logger.error(f"Resolution for issue {issue_id} is not ready to apply")
            return False

        if resolution["applied"]:
            logger.warning(f"Resolution for issue {issue_id} already applied")
            return True

        try:
            # Apply the resolution
            issue = resolution["issue"]
            resolution_data = resolution["resolution_data"]

            issue_type = issue.get("type")
            issue_file = issue.get("file")

            if not issue_file or not os.path.isfile(issue_file):
                logger.error(f"Issue file not found: {issue_file}")
                return False

            # Special handling based on issue type
            if (
                (
                    issue_type == "unused_import"
                    or issue_type == "unused_variable"
                    or issue_type == "unused_function"
                )
                or issue_type == "missing_return_type"
                or issue_type == "parameter_type_mismatch"
            ):
                if "code_changes" in resolution_data:
                    self._apply_code_changes(
                        issue_file, resolution_data["code_changes"]
                    )
            elif issue_type == "circular_dependency":
                if "code_changes" in resolution_data:
                    for file_path, changes in resolution_data["code_changes"].items():
                        self._apply_code_changes(file_path, changes)
            else:
                logger.warning(
                    f"No implementation for applying resolution of type {issue_type}"
                )
                return False

            # Record the application
            resolution["applied"] = True
            self.resolution_history.append({
                "issue_id": issue_id,
                "timestamp": datetime.now().isoformat(),
                "action": "apply",
                "success": True,
            })

            return True
        except Exception as e:
            logger.exception(f"Error applying resolution for issue {issue_id}: {e!s}")
            self.resolution_history.append({
                "issue_id": issue_id,
                "timestamp": datetime.now().isoformat(),
                "action": "apply",
                "success": False,
                "error": str(e),
            })
            return False

    def validate_resolution(self, issue_id):
        """
        Validate a resolution after it has been applied.

        Args:
            issue_id: ID of the issue to validate the resolution for

        Returns:
            True if the resolution is valid, False otherwise
        """
        if issue_id not in self.resolutions:
            logger.error(f"Issue {issue_id} not found")
            return False

        resolution = self.resolutions[issue_id]
        if not resolution["applied"]:
            logger.error(f"Resolution for issue {issue_id} has not been applied")
            return False

        try:
            # Validate the resolution
            resolution["issue"]
            resolution["resolution_data"]

            # Rerun the analyzer to check if the issue is fixed
            if self.analyzer:
                self.analyzer.analyze()

                # Check if the issue still exists
                if "issues" in self.analyzer.results:
                    for current_issue in self.analyzer.results["issues"]:
                        if current_issue.get("id") == issue_id:
                            # Issue still exists, resolution is invalid
                            resolution["validation_result"] = {
                                "valid": False,
                                "reason": "Issue still exists after resolution",
                            }
                            return False

                # Issue no longer exists, resolution is valid
                resolution["validation_result"] = {"valid": True}
                return True
            else:
                logger.warning("No analyzer available for validation")
                return True
        except Exception as e:
            logger.exception(f"Error validating resolution for issue {issue_id}: {e!s}")
            resolution["validation_result"] = {
                "valid": False,
                "reason": f"Error during validation: {e!s}",
            }
            return False

    def rollback_resolution(self, issue_id):
        """
        Rollback a resolution that has been applied.

        Args:
            issue_id: ID of the issue to rollback the resolution for

        Returns:
            True if the resolution was rolled back, False otherwise
        """
        if issue_id not in self.resolutions:
            logger.error(f"Issue {issue_id} not found")
            return False

        resolution = self.resolutions[issue_id]
        if not resolution["applied"]:
            logger.error(f"Resolution for issue {issue_id} has not been applied")
            return False

        try:
            # Rollback the resolution
            issue = resolution["issue"]
            resolution_data = resolution["resolution_data"]

            if "original_code" in resolution_data:
                issue_file = issue.get("file")
                with open(issue_file, "w") as f:
                    f.write(resolution_data["original_code"])

            # Record the rollback
            resolution["applied"] = False
            resolution["validation_result"] = None
            self.resolution_history.append({
                "issue_id": issue_id,
                "timestamp": datetime.now().isoformat(),
                "action": "rollback",
                "success": True,
            })

            return True
        except Exception as e:
            logger.exception(
                f"Error rolling back resolution for issue {issue_id}: {e!s}"
            )
            self.resolution_history.append({
                "issue_id": issue_id,
                "timestamp": datetime.now().isoformat(),
                "action": "rollback",
                "success": False,
                "error": str(e),
            })
            return False

    def ignore_issue(self, issue_id, reason: str = ""):
        """
        Mark an issue as ignored.

        Args:
            issue_id: ID of the issue to ignore
            reason: Reason for ignoring the issue

        Returns:
            True if the issue was marked as ignored, False otherwise
        """
        if issue_id not in self.resolutions:
            logger.error(f"Issue {issue_id} not found")
            return False

        resolution = self.resolutions[issue_id]
        resolution["status"] = ResolutionStatus.IGNORED
        resolution["resolution_data"] = {
            "reason": reason,
            "timestamp": datetime.now().isoformat(),
        }

        self.resolution_history.append({
            "issue_id": issue_id,
            "timestamp": datetime.now().isoformat(),
            "action": "ignore",
            "reason": reason,
        })

        return True

    def get_resolution_status(self, issue_id=None):
        """
        Get the status of resolutions.

        Args:
            issue_id: Optional ID of the issue to get the status for

        Returns:
            Resolution status information
        """
        if issue_id:
            if issue_id not in self.resolutions:
                logger.error(f"Issue {issue_id} not found")
                return None

            return self.resolutions[issue_id]
        else:
            # Get summary of all resolutions
            summary = {
                "total": len(self.resolutions),
                "pending": 0,
                "in_progress": 0,
                "resolved": 0,
                "applied": 0,
                "failed": 0,
                "ignored": 0,
                "valid": 0,
                "invalid": 0,
            }

            for resolution in self.resolutions.values():
                if resolution["status"] == ResolutionStatus.PENDING:
                    summary["pending"] += 1
                elif resolution["status"] == ResolutionStatus.IN_PROGRESS:
                    summary["in_progress"] += 1
                elif resolution["status"] == ResolutionStatus.RESOLVED:
                    summary["resolved"] += 1
                    if resolution["applied"]:
                        summary["applied"] += 1
                        if resolution["validation_result"] and resolution[
                            "validation_result"
                        ].get("valid"):
                            summary["valid"] += 1
                        elif resolution["validation_result"]:
                            summary["invalid"] += 1
                elif resolution["status"] == ResolutionStatus.FAILED:
                    summary["failed"] += 1
                elif resolution["status"] == ResolutionStatus.IGNORED:
                    summary["ignored"] += 1

            return summary

    def _apply_code_changes(self, file_path, changes):
        """
        Apply code changes to a file.

        Args:
            file_path: Path to the file to apply changes to
            changes: List of changes to apply

        Returns:
            True if changes were applied, False otherwise
        """
        try:
            # Read the file
            with open(file_path) as f:
                lines = f.readlines()

            # Apply the changes
            for change in changes:
                if "line" in change and "action" in change:
                    line_idx = change["line"] - 1  # Convert to 0-indexed

                    if change["action"] == "remove":
                        if 0 <= line_idx < len(lines):
                            lines[line_idx] = ""
                    elif change["action"] == "replace" and "new_text" in change:
                        if 0 <= line_idx < len(lines):
                            lines[line_idx] = change["new_text"] + "\n"
                    elif change["action"] == "insert" and "new_text" in change:
                        if 0 <= line_idx <= len(lines):
                            lines.insert(line_idx, change["new_text"] + "\n")

            # Write the changes back to the file
            with open(file_path, "w") as f:
                f.writelines(lines)

            return True
        except Exception as e:
            logger.exception(f"Error applying code changes to {file_path}: {e!s}")
            return False

    # Resolution generators for specific issue types
    def _resolve_unused_import(self, issue):
        """
        Generate a resolution for an unused import issue.

        Args:
            issue: Issue to generate a resolution for

        Returns:
            Resolution data or None if no resolution could be generated
        """
        try:
            issue_file = issue.get("file")
            issue_line = issue.get("line")
            import_name = issue.get("symbol")

            if (
                not issue_file
                or not os.path.isfile(issue_file)
                or not issue_line
                or not import_name
            ):
                return None

            # Read the file
            with open(issue_file) as f:
                lines = f.readlines()
                original_code = "".join(lines)

            # Find the import line
            if 0 <= issue_line - 1 < len(lines):
                import_line = lines[issue_line - 1]

                # Check if it's a single import or part of a multi-import
                if f"import {import_name}" in import_line or (
                    "from " in import_line and f" import {import_name}" in import_line
                ):
                    # Generate change
                    return {
                        "original_code": original_code,
                        "code_changes": [{"line": issue_line, "action": "remove"}],
                    }

            return None
        except Exception as e:
            logger.exception(f"Error resolving unused import: {e!s}")
            return None

    def _resolve_unused_variable(self, issue):
        """Resolution generator for unused variable issues."""
        try:
            issue_file = issue.get("file")
            issue_line = issue.get("line")
            var_name = issue.get("symbol")

            if (
                not issue_file
                or not os.path.isfile(issue_file)
                or not issue_line
                or not var_name
            ):
                return None

            # Read the file
            with open(issue_file) as f:
                lines = f.readlines()
                original_code = "".join(lines)

            # Find the variable declaration line
            if 0 <= issue_line - 1 < len(lines):
                var_line = lines[issue_line - 1]

                # Check if it's a variable assignment
                if f"{var_name} =" in var_line or f"{var_name}=" in var_line:
                    # Generate change
                    return {
                        "original_code": original_code,
                        "code_changes": [{"line": issue_line, "action": "remove"}],
                    }

            return None
        except Exception as e:
            logger.exception(f"Error resolving unused variable: {e!s}")
            return None

    def _resolve_unused_function(self, issue):
        """Resolution generator for unused function issues."""
        try:
            issue_file = issue.get("file")
            issue_line = issue.get("line")
            func_name = issue.get("symbol")

            if (
                not issue_file
                or not os.path.isfile(issue_file)
                or not issue_line
                or not func_name
            ):
                return None

            # Read the file
            with open(issue_file) as f:
                lines = f.readlines()
                original_code = "".join(lines)

            # Find the function declaration line
            if 0 <= issue_line - 1 < len(lines):
                func_line = lines[issue_line - 1]

                # Check if it's a function declaration
                if f"def {func_name}" in func_line:
                    # Find the end of the function
                    end_line = issue_line
                    indent_level = None

                    # Get indentation level of the function
                    for i, char in enumerate(func_line):
                        if char != " " and char != "\t":
                            indent_level = i
                            break

                    if indent_level is None:
                        return None

                    # Find all lines of the function
                    function_lines = []
                    for i in range(issue_line - 1, len(lines)):
                        # Skip empty lines
                        if not lines[i].strip():
                            continue

                        # Check indentation
                        current_indent = 0
                        for j, char in enumerate(lines[i]):
                            if char != " " and char != "\t":
                                current_indent = j
                                break

                        # If indentation is less than function, we've reached the end
                        if current_indent <= indent_level and i > issue_line - 1:
                            end_line = i
                            break

                        function_lines.append(lines[i])

                    # Generate change
                    changes = []
                    for i in range(issue_line - 1, end_line):
                        changes.append({"line": i + 1, "action": "remove"})

                    return {
                        "original_code": original_code,
                        "code_changes": changes,
                        "function_text": "".join(function_lines),
                    }

            return None
        except Exception as e:
            logger.exception(f"Error resolving unused function: {e!s}")
            return None

    def _resolve_missing_return_type(self, issue):
        """Resolution generator for missing return type issues."""
        try:
            issue_file = issue.get("file")
            issue_line = issue.get("line")
            func_name = issue.get("symbol")
            suggested_type = issue.get("suggested_type", "Any")

            if (
                not issue_file
                or not os.path.isfile(issue_file)
                or not issue_line
                or not func_name
            ):
                return None

            # Read the file
            with open(issue_file) as f:
                lines = f.readlines()
                original_code = "".join(lines)

            # Find the function declaration line
            if 0 <= issue_line - 1 < len(lines):
                func_line = lines[issue_line - 1]

                # Check if it's a function declaration and doesn't have a return type
                if f"def {func_name}" in func_line and "->" not in func_line:
                    # Find the closing parenthesis
                    close_paren_idx = func_line.rfind(")")
                    colon_idx = func_line.rfind(":")

                    if (
                        close_paren_idx != -1
                        and colon_idx != -1
                        and close_paren_idx < colon_idx
                    ):
                        # Insert return type
                        new_line = (
                            func_line[: close_paren_idx + 1]
                            + f" -> {suggested_type}"
                            + func_line[close_paren_idx + 1 :]
                        )

                        # Generate change
                        return {
                            "original_code": original_code,
                            "code_changes": [
                                {
                                    "line": issue_line,
                                    "action": "replace",
                                    "new_text": new_line.rstrip(),
                                }
                            ],
                        }

            return None
        except Exception as e:
            logger.exception(f"Error resolving missing return type: {e!s}")
            return None

    def _resolve_parameter_type_mismatch(self, issue):
        """Resolution generator for parameter type mismatch issues."""
        # Implementation would depend on the specific issue structure
        return None

    def _resolve_circular_dependency(self, issue):
        """Resolution generator for circular dependency issues."""
        # Implementation would involve analyzing the dependency graph
        # and suggesting module reorganization
        return None

    def _resolve_complex_function(self, issue):
        """Resolution generator for complex function issues."""
        # Implementation would involve suggesting function refactoring
        return None

    def _resolve_dead_code(self, issue):
        """Resolution generator for dead code issues."""
        # Similar to unused function resolution
        return None
