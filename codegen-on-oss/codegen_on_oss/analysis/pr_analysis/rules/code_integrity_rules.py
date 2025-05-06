"""
Code integrity rules for PR analysis.

This module provides rules for analyzing code integrity in pull requests,
including code style, test coverage, and security vulnerabilities.
"""

import logging
import os
import re
from typing import Any, Dict, List

from codegen_on_oss.analysis.pr_analysis.git.models import File, FileStatus
from codegen_on_oss.analysis.pr_analysis.rules.base_rule import BaseRule

logger = logging.getLogger(__name__)


class CodeStyleRule(BaseRule):
    """
    Rule for checking code style.

    This rule checks for code style issues in the pull request, including
    formatting, naming conventions, and other style guidelines.
    """

    rule_id = "code_style"
    name = "Code Style"
    description = "Checks for code style issues in the pull request"

    def run(self) -> Dict[str, Any]:
        """
        Run the code style rule.

        Returns:
            Rule results
        """
        logger.info(f"Running code style rule for PR #{self.context.pull_request.number}")

        # Get files changed in the PR
        files = self.context.pull_request.files

        # Filter files based on configuration
        include_patterns = self.get_config("include_patterns", [r".*\.(py|js|ts|tsx|jsx)$"])
        exclude_patterns = self.get_config("exclude_patterns", [r".*\.(json|md|txt|csv|yml|yaml)$"])

        filtered_files = []
        for file in files:
            # Skip deleted files
            if file.status == FileStatus.REMOVED:
                continue

            # Check if file matches include patterns
            included = any(re.match(pattern, file.filename) for pattern in include_patterns)

            # Check if file matches exclude patterns
            excluded = any(re.match(pattern, file.filename) for pattern in exclude_patterns)

            if included and not excluded:
                filtered_files.append(file)

        # If no files to check, return success
        if not filtered_files:
            return self.success("No files to check for code style issues")

        # Check code style for each file
        issues = []
        for file in filtered_files:
            file_issues = self._check_file_style(file)
            issues.extend(file_issues)

        # Return results
        if not issues:
            return self.success("No code style issues found")
        elif len(issues) <= self.get_config("warning_threshold", 5):
            return self.warning(f"Found {len(issues)} code style issues", {"issues": issues})
        else:
            return self.error(f"Found {len(issues)} code style issues", {"issues": issues})

    def _check_file_style(self, file: File) -> List[Dict[str, Any]]:
        """
        Check code style for a file.

        Args:
            file: File to check

        Returns:
            List of style issues
        """
        # Get file content
        try:
            content = self.context.cache.get(f"file_content_{file.filename}")
            if content is None:
                repo_operator = self.context.cache.get("repo_operator")
                if repo_operator:
                    content = repo_operator.get_file_content(file.filename)
                    self.context.cache[f"file_content_{file.filename}"] = content
        except Exception as e:
            logger.error(f"Failed to get content of file '{file.filename}': {e}")
            return [
                {"file": file.filename, "line": 0, "message": f"Failed to check file: {str(e)}"}
            ]

        if content is None:
            return [{"file": file.filename, "line": 0, "message": "Failed to get file content"}]

        # Check file style
        issues = []

        # Example: Check line length
        max_line_length = self.get_config("max_line_length", 100)
        for i, line in enumerate(content.splitlines(), 1):
            if len(line) > max_line_length:
                issues.append(
                    {
                        "file": file.filename,
                        "line": i,
                        "message": f"Line too long ({len(line)} > {max_line_length})",
                    }
                )

        # Example: Check trailing whitespace
        if self.get_config("check_trailing_whitespace", True):
            for i, line in enumerate(content.splitlines(), 1):
                if line.rstrip() != line:
                    issues.append(
                        {
                            "file": file.filename,
                            "line": i,
                            "message": "Line has trailing whitespace",
                        }
                    )

        # Example: Check file ends with newline
        if self.get_config("check_final_newline", True):
            if content and not content.endswith("\n"):
                issues.append(
                    {
                        "file": file.filename,
                        "line": len(content.splitlines()),
                        "message": "File does not end with a newline",
                    }
                )

        return issues


class TestCoverageRule(BaseRule):
    """
    Rule for checking test coverage.

    This rule checks for test coverage of code changes in the pull request,
    ensuring that new or modified code is adequately tested.
    """

    rule_id = "test_coverage"
    name = "Test Coverage"
    description = "Checks for test coverage of code changes in the pull request"

    def run(self) -> Dict[str, Any]:
        """
        Run the test coverage rule.

        Returns:
            Rule results
        """
        logger.info(f"Running test coverage rule for PR #{self.context.pull_request.number}")

        # Get files changed in the PR
        files = self.context.pull_request.files

        # Filter for code files (not tests)
        code_files = []
        test_files = []

        code_patterns = self.get_config("code_patterns", [r".*\.(py|js|ts|tsx|jsx)$"])
        test_patterns = self.get_config(
            "test_patterns", [r".*_test\.py$", r".*\.test\.(js|ts|tsx|jsx)$", r"test_.*\.py$"]
        )

        for file in files:
            # Skip deleted files
            if file.status == FileStatus.REMOVED:
                continue

            # Check if file is a test file
            is_test = any(re.match(pattern, file.filename) for pattern in test_patterns)
            if is_test:
                test_files.append(file)
                continue

            # Check if file is a code file
            is_code = any(re.match(pattern, file.filename) for pattern in code_patterns)
            if is_code:
                code_files.append(file)

        # If no code files, return success
        if not code_files:
            return self.success("No code files to check for test coverage")

        # Check if there are any test files
        if not test_files:
            return self.warning(
                "No test files found in the pull request",
                {"code_files": [f.filename for f in code_files]},
            )

        # Check test coverage for each code file
        uncovered_files = []
        for code_file in code_files:
            if not self._has_test_coverage(code_file, test_files):
                uncovered_files.append(code_file.filename)

        # Return results
        if not uncovered_files:
            return self.success("All code files have test coverage")
        elif len(uncovered_files) <= self.get_config("warning_threshold", 2):
            return self.warning(
                f"Found {len(uncovered_files)} files without test coverage",
                {"uncovered_files": uncovered_files},
            )
        else:
            return self.error(
                f"Found {len(uncovered_files)} files without test coverage",
                {"uncovered_files": uncovered_files},
            )

    def _has_test_coverage(self, code_file: File, test_files: List[File]) -> bool:
        """
        Check if a code file has test coverage.

        Args:
            code_file: Code file to check
            test_files: List of test files

        Returns:
            True if the code file has test coverage, False otherwise
        """
        # This is a simplified implementation that checks if there's a test file
        # with a similar name to the code file. In a real implementation, you would
        # use a more sophisticated approach, such as analyzing imports or running
        # a coverage tool.

        # Get the base name of the code file (without extension)
        code_file_base = os.path.splitext(os.path.basename(code_file.filename))[0]

        # Check if there's a test file with a similar name
        for test_file in test_files:
            test_file_base = os.path.splitext(os.path.basename(test_file.filename))[0]

            # Check for common test file naming patterns
            if test_file_base == f"test_{code_file_base}":
                return True
            if test_file_base == f"{code_file_base}_test":
                return True
            if test_file_base == code_file_base and "test" in test_file.filename:
                return True

        return False


class SecurityVulnerabilityRule(BaseRule):
    """
    Rule for checking security vulnerabilities.

    This rule checks for security vulnerabilities in the pull request,
    including common security issues and potential vulnerabilities.
    """

    rule_id = "security_vulnerability"
    name = "Security Vulnerability"
    description = "Checks for security vulnerabilities in the pull request"

    def run(self) -> Dict[str, Any]:
        """
        Run the security vulnerability rule.

        Returns:
            Rule results
        """
        logger.info(
            f"Running security vulnerability rule for PR #{self.context.pull_request.number}"
        )

        # Get files changed in the PR
        files = self.context.pull_request.files

        # Filter files based on configuration
        include_patterns = self.get_config("include_patterns", [r".*\.(py|js|ts|tsx|jsx)$"])
        exclude_patterns = self.get_config("exclude_patterns", [r".*\.(json|md|txt|csv|yml|yaml)$"])

        filtered_files = []
        for file in files:
            # Skip deleted files
            if file.status == FileStatus.REMOVED:
                continue

            # Check if file matches include patterns
            included = any(re.match(pattern, file.filename) for pattern in include_patterns)

            # Check if file matches exclude patterns
            excluded = any(re.match(pattern, file.filename) for pattern in exclude_patterns)

            if included and not excluded:
                filtered_files.append(file)

        # If no files to check, return success
        if not filtered_files:
            return self.success("No files to check for security vulnerabilities")

        # Check security vulnerabilities for each file
        vulnerabilities = []
        for file in filtered_files:
            file_vulnerabilities = self._check_file_security(file)
            vulnerabilities.extend(file_vulnerabilities)

        # Return results
        if not vulnerabilities:
            return self.success("No security vulnerabilities found")
        else:
            return self.error(
                f"Found {len(vulnerabilities)} security vulnerabilities",
                {"vulnerabilities": vulnerabilities},
            )

    def _check_file_security(self, file: File) -> List[Dict[str, Any]]:
        """
        Check security vulnerabilities for a file.

        Args:
            file: File to check

        Returns:
            List of security vulnerabilities
        """
        # Get file content
        try:
            content = self.context.cache.get(f"file_content_{file.filename}")
            if content is None:
                repo_operator = self.context.cache.get("repo_operator")
                if repo_operator:
                    content = repo_operator.get_file_content(file.filename)
                    self.context.cache[f"file_content_{file.filename}"] = content
        except Exception as e:
            logger.error(f"Failed to get content of file '{file.filename}': {e}")
            return [
                {
                    "file": file.filename,
                    "line": 0,
                    "severity": "high",
                    "message": f"Failed to check file: {str(e)}",
                }
            ]

        if content is None:
            return [
                {
                    "file": file.filename,
                    "line": 0,
                    "severity": "high",
                    "message": "Failed to get file content",
                }
            ]

        # Check file security
        vulnerabilities = []

        # Example: Check for hardcoded secrets
        secret_patterns = self.get_config(
            "secret_patterns",
            [
                r'password\s*=\s*[\'"][^\'"]+[\'"]',
                r'secret\s*=\s*[\'"][^\'"]+[\'"]',
                r'api_key\s*=\s*[\'"][^\'"]+[\'"]',
                r'token\s*=\s*[\'"][^\'"]+[\'"]',
            ],
        )

        for i, line in enumerate(content.splitlines(), 1):
            for pattern in secret_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    vulnerabilities.append(
                        {
                            "file": file.filename,
                            "line": i,
                            "severity": "high",
                            "message": "Potential hardcoded secret found",
                        }
                    )

        # Example: Check for SQL injection vulnerabilities
        if file.filename.endswith(".py"):
            sql_injection_patterns = [
                r'execute\s*\(\s*[f"\']+.*\{.*\}.*["\']',
                r'executemany\s*\(\s*[f"\']+.*\{.*\}.*["\']',
                r'raw\s*\(\s*[f"\']+.*\{.*\}.*["\']',
            ]

            for i, line in enumerate(content.splitlines(), 1):
                for pattern in sql_injection_patterns:
                    if re.search(pattern, line):
                        vulnerabilities.append(
                            {
                                "file": file.filename,
                                "line": i,
                                "severity": "high",
                                "message": "Potential SQL injection vulnerability",
                            }
                        )

        # Example: Check for XSS vulnerabilities
        if file.filename.endswith((".js", ".ts", ".tsx", ".jsx")):
            xss_patterns = [
                r"innerHTML\s*=",
                r"dangerouslySetInnerHTML\s*=",
                r"document\.write\s*\(",
            ]

            for i, line in enumerate(content.splitlines(), 1):
                for pattern in xss_patterns:
                    if re.search(pattern, line):
                        vulnerabilities.append(
                            {
                                "file": file.filename,
                                "line": i,
                                "severity": "medium",
                                "message": "Potential XSS vulnerability",
                            }
                        )

        return vulnerabilities
