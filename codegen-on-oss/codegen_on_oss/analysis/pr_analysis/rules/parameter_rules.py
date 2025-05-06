"""
Parameter Rules

Rules for validating parameter usage in pull requests.
"""

import logging
import re
from typing import Any, Dict, List, Optional

from codegen_on_oss.analysis.pr_analysis.core.analysis_context import AnalysisContext
from codegen_on_oss.analysis.pr_analysis.rules.base_rule import BaseRule

logger = logging.getLogger(__name__)


class ParameterValidationRule(BaseRule):
    """
    Rule for validating parameter usage in pull requests.

    This rule checks for issues such as:
    - Missing parameter validation
    - Inconsistent parameter types
    - Unused parameters
    """

    rule_id: str = "parameter_validation"
    rule_name: str = "Parameter Validation"
    rule_description: str = "Checks for proper parameter validation and usage."

    def analyze(self, context: AnalysisContext) -> Dict[str, Any]:
        """
        Analyze the PR for parameter validation issues.

        Args:
            context: The analysis context containing PR and codebase information

        Returns:
            A dictionary containing the analysis results
        """
        logger.info("Running parameter validation analysis")

        # Get changed files
        changed_files = context.get_changed_files()

        # Analyze each changed file
        issues = []
        for file_path, file_info in changed_files.items():
            # Skip deleted files
            if file_info.get("status") == "deleted":
                continue

            # Get file content
            file_content = context.get_file_content(file_path, "head")
            if not file_content:
                continue

            # Analyze file
            try:
                file_issues = self._analyze_file_parameters(file_content, file_path)
                issues.extend(file_issues)
            except Exception as e:
                logger.exception(f"Error analyzing parameters in file {file_path}: {e}")
                issues.append(
                    self.create_issue(
                        file_path=file_path,
                        message=f"Error analyzing parameters: {str(e)}",
                        severity="error",
                    )
                )

        return {
            "issues": issues,
            "summary": {
                "total_issues": len(issues),
                "error_count": sum(1 for issue in issues if issue["severity"] == "error"),
                "warning_count": sum(1 for issue in issues if issue["severity"] == "warning"),
                "info_count": sum(1 for issue in issues if issue["severity"] == "info"),
            },
        }

    def _analyze_file_parameters(self, file_content: str, file_path: str) -> List[Dict[str, Any]]:
        """
        Analyze parameter usage in a file.

        Args:
            file_content: The content of the file to analyze
            file_path: The path of the file

        Returns:
            A list of issues found in the file
        """
        issues = []

        # Check for Python function definitions
        if file_path.endswith(".py"):
            # Simple regex to find function definitions
            func_pattern = r"def\s+(\w+)\s*\(([^)]*)\)(?:\s*->\s*([^:]+))?\s*:"
            for match in re.finditer(func_pattern, file_content):
                func_name = match.group(1)
                params_str = match.group(2)
                return_type = match.group(3)

                # Get line number
                line_number = file_content[: match.start()].count("\n") + 1

                # Check for parameters
                if params_str.strip() and "self" not in params_str:
                    # Check if there's parameter validation in the function body
                    func_body = self._get_function_body(file_content, match.end())
                    if not self._has_parameter_validation(func_body, params_str):
                        issues.append(
                            self.create_issue(
                                file_path=file_path,
                                line_number=line_number,
                                message=f"Function '{func_name}' has parameters but no validation",
                                severity="warning",
                                code=match.group(0),
                                suggestion="Add parameter validation to ensure correct input types and values.",
                            )
                        )

        # Check for JavaScript/TypeScript function definitions
        elif file_path.endswith((".js", ".ts", ".jsx", ".tsx")):
            # Simple regex to find function definitions
            func_pattern = r"(function|const|let|var)\s+(\w+)\s*=?\s*(?:function)?\s*\(([^)]*)\)"
            for match in re.finditer(func_pattern, file_content):
                func_type = match.group(1)
                func_name = match.group(2)
                params_str = match.group(3)

                # Get line number
                line_number = file_content[: match.start()].count("\n") + 1

                # Check for parameters
                if params_str.strip():
                    # Check if there's parameter validation in the function body
                    func_body = self._get_function_body(file_content, match.end())
                    if not self._has_parameter_validation(func_body, params_str):
                        issues.append(
                            self.create_issue(
                                file_path=file_path,
                                line_number=line_number,
                                message=f"Function '{func_name}' has parameters but no validation",
                                severity="warning",
                                code=match.group(0),
                                suggestion="Add parameter validation to ensure correct input types and values.",
                            )
                        )

        return issues

    def _get_function_body(self, file_content: str, start_pos: int) -> str:
        """
        Extract the function body from the file content.

        Args:
            file_content: The content of the file
            start_pos: The position where the function definition ends

        Returns:
            The function body
        """
        # This is a simplified implementation that assumes the function body
        # is indented and ends when the indentation level decreases
        lines = file_content[start_pos:].split("\n")
        body_lines = []

        # Skip the first line (it's the function definition)
        for line in lines[1:]:
            if line.strip() and not line.startswith(" ") and not line.startswith("\t"):
                break
            body_lines.append(line)

        return "\n".join(body_lines)

    def _has_parameter_validation(self, func_body: str, params_str: str) -> bool:
        """
        Check if the function body contains parameter validation.

        Args:
            func_body: The function body to check
            params_str: The parameter string from the function definition

        Returns:
            True if the function body contains parameter validation, False otherwise
        """
        # Extract parameter names
        params = []
        for param in params_str.split(","):
            param = param.strip()
            if param:
                # Handle default values and type annotations
                param_name = param.split("=")[0].split(":")[0].strip()
                if param_name and param_name != "self":
                    params.append(param_name)

        # Check for common validation patterns
        for param in params:
            # Check for type checking
            if re.search(rf"isinstance\(\s*{param}\s*,", func_body):
                return True

            # Check for null/undefined checking
            if re.search(rf"if\s+{param}\s+is\s+None", func_body):
                return True
            if re.search(rf"if\s+{param}\s+==\s+None", func_body):
                return True
            if re.search(rf"if\s+not\s+{param}", func_body):
                return True

            # Check for value validation
            if re.search(rf"if\s+{param}\s+[<>=!]", func_body):
                return True

        return False
