#!/usr/bin/env python3
"""
Script to analyze and report errors in a codebase.

This script provides comprehensive error analysis for a codebase, including:
- Syntax errors
- Import errors
- Type errors
- Unused imports
- Undefined variables
- Code style issues
- Security vulnerabilities
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add the parent directory to the path so we can import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from codegen_on_oss.analysis.wsl_client import WSLClient


class ErrorAnalyzer:
    """
    Analyzer for detecting and reporting errors in a codebase.
    """

    def __init__(
        self,
        repo_path: str,
        output_file: Optional[str] = None,
        output_format: str = "json",
        github_token: Optional[str] = None,
    ):
        """
        Initialize a new ErrorAnalyzer.

        Args:
            repo_path: Path to the repository
            output_file: Optional file to write the results to
            output_format: Output format (json or markdown)
            github_token: GitHub token for authentication
        """
        self.repo_path = repo_path
        self.output_file = output_file
        self.output_format = output_format
        self.github_token = github_token
        self.errors: List[Dict[str, Any]] = []
        self.summary: Dict[str, Any] = {
            "total_errors": 0,
            "error_types": {},
            "files_with_errors": set(),
        }

    def run_analysis(self) -> Dict[str, Any]:
        """
        Run all error analysis checks.

        Returns:
            Analysis results
        """
        logger.info(f"Analyzing repository: {self.repo_path}")

        # Run syntax check
        self._check_syntax()

        # Run import check
        self._check_imports()

        # Run type check
        self._check_types()

        # Run style check
        self._check_style()

        # Run security check
        self._check_security()

        # Prepare summary
        self.summary["total_errors"] = len(self.errors)
        self.summary["files_with_errors"] = list(self.summary["files_with_errors"])

        # Prepare results
        results = {
            "repo_path": self.repo_path,
            "errors": self.errors,
            "summary": self.summary,
        }

        # Save results to file if requested
        if self.output_file:
            self._save_results(results)

        return results

    def _check_syntax(self) -> None:
        """Check for syntax errors using Python's built-in parser."""
        logger.info("Checking for syntax errors")

        # Find all Python files
        python_files = self._find_python_files()

        for file_path in python_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    source = f.read()
                
                # Try to compile the source code
                try:
                    compile(source, file_path, "exec")
                except SyntaxError as e:
                    self._add_error(
                        file_path=file_path,
                        line=e.lineno or 0,
                        error_type="syntax_error",
                        message=str(e),
                        severity="error",
                    )
            except Exception as e:
                logger.warning(f"Error reading file {file_path}: {str(e)}")

    def _check_imports(self) -> None:
        """Check for import errors using a custom import checker."""
        logger.info("Checking for import errors")

        # Find all Python files
        python_files = self._find_python_files()

        for file_path in python_files:
            try:
                # Run a separate process to check imports
                result = subprocess.run(
                    [
                        sys.executable,
                        "-c",
                        f"import sys; sys.path.insert(0, '{os.path.dirname(file_path)}'); "
                        f"try: import {os.path.splitext(os.path.basename(file_path))[0]}; "
                        f"except ImportError as e: print(str(e)); sys.exit(1)",
                    ],
                    capture_output=True,
                    text=True,
                )

                if result.returncode != 0:
                    self._add_error(
                        file_path=file_path,
                        line=1,
                        error_type="import_error",
                        message=result.stdout.strip() or result.stderr.strip() or "Unknown import error",
                        severity="error",
                    )
            except Exception as e:
                logger.warning(f"Error checking imports for {file_path}: {str(e)}")

    def _check_types(self) -> None:
        """Check for type errors using mypy."""
        logger.info("Checking for type errors")

        try:
            # Check if mypy is installed
            subprocess.run(
                [sys.executable, "-m", "pip", "show", "mypy"],
                capture_output=True,
                check=True,
            )
        except subprocess.CalledProcessError:
            logger.warning("mypy is not installed, skipping type checking")
            return

        # Find all Python files
        python_files = self._find_python_files()

        for file_path in python_files:
            try:
                # Run mypy on the file
                result = subprocess.run(
                    [sys.executable, "-m", "mypy", file_path],
                    capture_output=True,
                    text=True,
                )

                if result.returncode != 0:
                    # Parse mypy output
                    for line in result.stdout.splitlines():
                        if ":" in line:
                            parts = line.split(":", 2)
                            if len(parts) >= 3:
                                try:
                                    line_num = int(parts[1])
                                    message = parts[2].strip()
                                    self._add_error(
                                        file_path=file_path,
                                        line=line_num,
                                        error_type="type_error",
                                        message=message,
                                        severity="warning",
                                    )
                                except ValueError:
                                    pass
            except Exception as e:
                logger.warning(f"Error checking types for {file_path}: {str(e)}")

    def _check_style(self) -> None:
        """Check for style issues using flake8."""
        logger.info("Checking for style issues")

        try:
            # Check if flake8 is installed
            subprocess.run(
                [sys.executable, "-m", "pip", "show", "flake8"],
                capture_output=True,
                check=True,
            )
        except subprocess.CalledProcessError:
            logger.warning("flake8 is not installed, skipping style checking")
            return

        # Find all Python files
        python_files = self._find_python_files()

        for file_path in python_files:
            try:
                # Run flake8 on the file
                result = subprocess.run(
                    [sys.executable, "-m", "flake8", file_path],
                    capture_output=True,
                    text=True,
                )

                if result.returncode != 0:
                    # Parse flake8 output
                    for line in result.stdout.splitlines():
                        if ":" in line:
                            parts = line.split(":", 2)
                            if len(parts) >= 3:
                                try:
                                    line_num = int(parts[1])
                                    message = parts[2].strip()
                                    self._add_error(
                                        file_path=file_path,
                                        line=line_num,
                                        error_type="style_issue",
                                        message=message,
                                        severity="info",
                                    )
                                except ValueError:
                                    pass
            except Exception as e:
                logger.warning(f"Error checking style for {file_path}: {str(e)}")

    def _check_security(self) -> None:
        """Check for security vulnerabilities using bandit."""
        logger.info("Checking for security vulnerabilities")

        try:
            # Check if bandit is installed
            subprocess.run(
                [sys.executable, "-m", "pip", "show", "bandit"],
                capture_output=True,
                check=True,
            )
        except subprocess.CalledProcessError:
            logger.warning("bandit is not installed, skipping security checking")
            return

        # Find all Python files
        python_files = self._find_python_files()

        for file_path in python_files:
            try:
                # Run bandit on the file
                result = subprocess.run(
                    [sys.executable, "-m", "bandit", "-f", "json", file_path],
                    capture_output=True,
                    text=True,
                )

                if result.returncode != 0:
                    # Parse bandit output
                    try:
                        bandit_results = json.loads(result.stdout)
                        for issue in bandit_results.get("results", []):
                            self._add_error(
                                file_path=file_path,
                                line=issue.get("line_number", 0),
                                error_type="security_vulnerability",
                                message=f"{issue.get('issue_text', '')} (Confidence: {issue.get('issue_confidence', '')})",
                                severity="error" if issue.get("issue_severity") == "HIGH" else "warning",
                            )
                    except json.JSONDecodeError:
                        logger.warning(f"Error parsing bandit output for {file_path}")
            except Exception as e:
                logger.warning(f"Error checking security for {file_path}: {str(e)}")

    def _find_python_files(self) -> List[str]:
        """
        Find all Python files in the repository.

        Returns:
            List of Python file paths
        """
        python_files = []
        for root, _, files in os.walk(self.repo_path):
            for file in files:
                if file.endswith(".py"):
                    python_files.append(os.path.join(root, file))
        return python_files

    def _add_error(
        self,
        file_path: str,
        line: int,
        error_type: str,
        message: str,
        severity: str = "error",
    ) -> None:
        """
        Add an error to the list of errors.

        Args:
            file_path: Path to the file with the error
            line: Line number of the error
            error_type: Type of error
            message: Error message
            severity: Error severity (error, warning, info)
        """
        # Make file path relative to repo path
        rel_path = os.path.relpath(file_path, self.repo_path)

        error = {
            "filepath": rel_path,
            "line": line,
            "error_type": error_type,
            "message": message,
            "severity": severity,
        }

        self.errors.append(error)
        self.summary["files_with_errors"].add(rel_path)

        # Update error type count
        if error_type not in self.summary["error_types"]:
            self.summary["error_types"][error_type] = 0
        self.summary["error_types"][error_type] += 1

    def _save_results(self, results: Dict[str, Any]) -> None:
        """
        Save results to a file.

        Args:
            results: Results to save
        """
        # Convert set to list for JSON serialization
        results_copy = results.copy()
        results_copy["summary"] = results_copy["summary"].copy()
        results_copy["summary"]["files_with_errors"] = list(results_copy["summary"]["files_with_errors"])

        if self.output_format.lower() == "markdown":
            with open(self.output_file, "w") as f:
                f.write(self._format_markdown(results_copy))
        else:
            with open(self.output_file, "w") as f:
                json.dump(results_copy, f, indent=2)

        logger.info(f"Results saved to {self.output_file}")

    def _format_markdown(self, results: Dict[str, Any]) -> str:
        """
        Format results as Markdown.

        Args:
            results: Results to format

        Returns:
            Markdown-formatted string
        """
        markdown = f"# Error Analysis Results: {results['repo_path']}\n\n"
        markdown += "## Summary\n\n"
        markdown += f"- **Total Errors**: {results['summary']['total_errors']}\n"
        markdown += f"- **Files with Errors**: {len(results['summary']['files_with_errors'])}\n\n"

        markdown += "### Error Types\n\n"
        for error_type, count in results['summary']['error_types'].items():
            markdown += f"- **{error_type.replace('_', ' ').title()}**: {count}\n"
        markdown += "\n"

        markdown += "## Errors\n\n"
        for error in results['errors']:
            severity_icon = "🔴" if error['severity'] == "error" else "🟠" if error['severity'] == "warning" else "🔵"
            markdown += f"### {severity_icon} {error['error_type'].replace('_', ' ').title()}\n\n"
            markdown += f"- **File**: {error['filepath']}\n"
            markdown += f"- **Line**: {error['line']}\n"
            markdown += f"- **Message**: {error['message']}\n"
            markdown += f"- **Severity**: {error['severity']}\n\n"

        return markdown


def analyze_errors(
    repo_path: str,
    output_file: Optional[str] = None,
    output_format: str = "json",
    github_token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Analyze errors in a repository.

    Args:
        repo_path: Path to the repository
        output_file: Optional file to write the results to
        output_format: Output format (json or markdown)
        github_token: GitHub token for authentication

    Returns:
        Analysis results
    """
    analyzer = ErrorAnalyzer(
        repo_path=repo_path,
        output_file=output_file,
        output_format=output_format,
        github_token=github_token,
    )
    return analyzer.run_analysis()


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Analyze errors in a repository")

    parser.add_argument("repo_path", help="Path to the repository")
    parser.add_argument("--output", help="Output file to save results to")
    parser.add_argument(
        "--format",
        choices=["json", "markdown"],
        default="json",
        help="Output format",
    )
    parser.add_argument("--github-token", help="GitHub token for authentication")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Analyze errors
    results = analyze_errors(
        repo_path=args.repo_path,
        output_file=args.output,
        output_format=args.format,
        github_token=args.github_token,
    )

    # Print summary
    if args.format == "markdown":
        print(f"# Error Analysis Summary\n\n")
        print(f"- **Total Errors**: {results['summary']['total_errors']}\n")
        print(f"- **Files with Errors**: {len(results['summary']['files_with_errors'])}\n\n")
        
        print("### Error Types\n\n")
        for error_type, count in results['summary']['error_types'].items():
            print(f"- **{error_type.replace('_', ' ').title()}**: {count}\n")
    else:
        print(json.dumps(results["summary"], indent=2))


if __name__ == "__main__":
    main()

