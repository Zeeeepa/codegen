"""Rule for detecting code smells.

This module provides a rule for detecting common code smells.
"""

import ast
import logging
from typing import Any

from pr_static_analysis.rules.base import RuleResult, RuleSeverity
from pr_static_analysis.rules.code_integrity import BaseCodeIntegrityRule

logger = logging.getLogger(__name__)


class CodeSmellRule(BaseCodeIntegrityRule):
    """Rule for detecting common code smells.

    This rule checks for various code smells, such as:
    - Long functions
    - Deeply nested code
    - Magic numbers
    - Duplicate code
    - Empty catch blocks
    """

    @property
    def id(self) -> str:
        """Get the unique identifier for the rule."""
        return "code-smell"

    @property
    def name(self) -> str:
        """Get the human-readable name for the rule."""
        return "Code Smell Detection"

    @property
    def description(self) -> str:
        """Get the detailed description of what the rule checks for."""
        return "Detects common code smells, such as long functions, deeply nested code, magic numbers, duplicate code, and empty catch blocks."

    @property
    def severity(self) -> RuleSeverity:
        """Get the default severity level for issues found by this rule."""
        return RuleSeverity.WARNING

    def get_default_config(self) -> dict[str, Any]:
        """Get the default configuration options for the rule.

        Returns:
            A dictionary of configuration options
        """
        return {
            "max_function_length": 100,
            "max_nesting_depth": 4,
            "ignore_magic_numbers": [-1, 0, 1, 2, 100],
            "min_duplicate_lines": 5,
        }

    def analyze(self, context: dict[str, Any]) -> list[RuleResult]:
        """Analyze the PR for code smells.

        Args:
            context: Context information for the analysis

        Returns:
            A list of RuleResult objects representing issues found
        """
        results = []

        # Get the files from the context
        files = context.get("files", [])

        for file_info in files:
            filepath = file_info.get("filepath")
            content = file_info.get("content")

            # Skip non-Python files
            if not filepath.endswith(".py"):
                continue

            # Skip empty files
            if not content:
                continue

            # Parse the file
            try:
                tree = ast.parse(content)

                # Check for long functions
                results.extend(self._check_long_functions(tree, filepath, content))

                # Check for deeply nested code
                results.extend(self._check_nesting_depth(tree, filepath, content))

                # Check for magic numbers
                results.extend(self._check_magic_numbers(tree, filepath, content))

                # Check for empty catch blocks
                results.extend(self._check_empty_catch_blocks(tree, filepath, content))

            except SyntaxError:
                # Skip files with syntax errors (they will be caught by the syntax error rule)
                continue

        # Check for duplicate code across files
        results.extend(self._check_duplicate_code(files))

        return results

    def _check_long_functions(self, tree: ast.AST, filepath: str, content: str) -> list[RuleResult]:
        """Check for long functions.

        Args:
            tree: AST of the file
            filepath: Path to the file
            content: Content of the file

        Returns:
            A list of RuleResult objects representing issues found
        """
        results = []
        max_length = self.config.get("max_function_length", 100)

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Count the number of lines in the function
                if hasattr(node, "end_lineno") and node.end_lineno is not None:
                    function_length = node.end_lineno - node.lineno + 1
                else:
                    # Fallback for older Python versions
                    function_lines = ast.get_source_segment(content, node)
                    if function_lines:
                        function_length = len(function_lines.split("\n"))
                    else:
                        continue

                if function_length > max_length:
                    results.append(
                        RuleResult(
                            rule_id=self.id,
                            severity=self.severity,
                            message=(f"Function '{node.name}' is too long ({function_length} lines, max {max_length})"),
                            filepath=filepath,
                            line=node.lineno,
                            code_snippet=ast.get_source_segment(content, node),
                            fix_suggestions=[
                                "Break the function into smaller, more focused functions",
                                "Extract complex logic into helper functions",
                                "Consider using a class to organize related functionality",
                            ],
                        )
                    )

        return results

    def _check_nesting_depth(self, tree: ast.AST, filepath: str, content: str) -> list[RuleResult]:
        """Check for deeply nested code.

        Args:
            tree: AST of the file
            filepath: Path to the file
            content: Content of the file

        Returns:
            A list of RuleResult objects representing issues found
        """
        results = []
        max_depth = self.config.get("max_nesting_depth", 4)

        class NestingVisitor(ast.NodeVisitor):
            def __init__(self):
                self.current_depth = 0
                self.max_depth_seen = 0
                self.max_depth_node = None

            def generic_visit(self, node):
                # Only count certain types of nodes for nesting depth
                if isinstance(
                    node,
                    (
                        ast.If,
                        ast.For,
                        ast.While,
                        ast.Try,
                        ast.With,
                        ast.FunctionDef,
                        ast.AsyncFunctionDef,
                        ast.ClassDef,
                    ),
                ):
                    self.current_depth += 1
                    if self.current_depth > self.max_depth_seen:
                        self.max_depth_seen = self.current_depth
                        self.max_depth_node = node

                    # Visit children
                    super().generic_visit(node)

                    self.current_depth -= 1
                else:
                    # Visit children without increasing depth
                    super().generic_visit(node)

        visitor = NestingVisitor()
        visitor.visit(tree)

        if visitor.max_depth_seen > max_depth and visitor.max_depth_node:
            results.append(
                RuleResult(
                    rule_id=self.id,
                    severity=self.severity,
                    message=(f"Code is too deeply nested (depth {visitor.max_depth_seen}, max {max_depth})"),
                    filepath=filepath,
                    line=visitor.max_depth_node.lineno,
                    code_snippet=ast.get_source_segment(content, visitor.max_depth_node),
                    fix_suggestions=[
                        "Extract nested code into separate functions",
                        "Use early returns to reduce nesting",
                        "Consider using guard clauses",
                        "Refactor complex conditionals",
                    ],
                )
            )

        return results

    def _check_magic_numbers(self, tree: ast.AST, filepath: str, content: str) -> list[RuleResult]:
        """Check for magic numbers.

        Args:
            tree: AST of the file
            filepath: Path to the file
            content: Content of the file

        Returns:
            A list of RuleResult objects representing issues found
        """
        results = []
        ignore_numbers = set(self.config.get("ignore_magic_numbers", [-1, 0, 1, 2, 100]))

        class MagicNumberVisitor(ast.NodeVisitor):
            def __init__(self):
                self.magic_numbers = []

            def visit_Num(self, node):
                # For Python < 3.8
                if hasattr(node, "n") and isinstance(node.n, (int, float)):
                    if node.n not in ignore_numbers:
                        self.magic_numbers.append((node, node.n))

            def visit_Constant(self, node):
                # For Python >= 3.8
                if hasattr(node, "value") and isinstance(node.value, (int, float)):
                    if node.value not in ignore_numbers:
                        self.magic_numbers.append((node, node.value))

        visitor = MagicNumberVisitor()
        visitor.visit(tree)

        for node, value in visitor.magic_numbers:
            results.append(
                RuleResult(
                    rule_id=self.id,
                    severity=RuleSeverity.INFO,  # Lower severity for magic numbers
                    message=f"Magic number: {value}",
                    filepath=filepath,
                    line=node.lineno if hasattr(node, "lineno") else None,
                    code_snippet=ast.get_source_segment(content, node),
                    fix_suggestions=[
                        "Define the number as a named constant",
                        "Use an enum for related constants",
                        "Add a comment explaining the significance of the number",
                    ],
                )
            )

        return results

    def _check_empty_catch_blocks(self, tree: ast.AST, filepath: str, content: str) -> list[RuleResult]:
        """Check for empty catch blocks.

        Args:
            tree: AST of the file
            filepath: Path to the file
            content: Content of the file

        Returns:
            A list of RuleResult objects representing issues found
        """
        results = []

        class EmptyCatchVisitor(ast.NodeVisitor):
            def __init__(self):
                self.empty_catches = []

            def visit_ExceptHandler(self, node):
                # Check if the except block is empty or only contains a pass statement
                if (
                    not node.body
                    or (len(node.body) == 1 and isinstance(node.body[0], ast.Pass))
                    or (len(node.body) == 1 and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant) and node.body[0].value.value in (None, ""))
                ):
                    self.empty_catches.append(node)

                self.generic_visit(node)

        visitor = EmptyCatchVisitor()
        visitor.visit(tree)

        for node in visitor.empty_catches:
            exception_name = f"Exception {node.name}" if node.name else "Exception"
            exception_type = ast.get_source_segment(content, node.type) if node.type else "all exceptions"

            results.append(
                RuleResult(
                    rule_id=self.id,
                    severity=self.severity,
                    message=f"Empty catch block for {exception_type}",
                    filepath=filepath,
                    line=node.lineno,
                    code_snippet=ast.get_source_segment(content, node),
                    fix_suggestions=[
                        "Add logging to the catch block",
                        "Re-raise the exception if it can't be handled",
                        "Add a comment explaining why the exception is being ignored",
                        "Consider using a more specific exception type",
                    ],
                )
            )

        return results

    def _check_duplicate_code(self, files: list[dict[str, Any]]) -> list[RuleResult]:
        """Check for duplicate code across files.

        Args:
            files: List of file information dictionaries

        Returns:
            A list of RuleResult objects representing issues found
        """
        results = []
        min_duplicate_lines = self.config.get("min_duplicate_lines", 5)

        # Extract Python files
        python_files = [file_info for file_info in files if file_info.get("filepath", "").endswith(".py")]

        # Skip if there are not enough files
        if len(python_files) < 2:
            return results

        # Compare each file with every other file
        for i, file1 in enumerate(python_files):
            filepath1 = file1.get("filepath", "")
            content1 = file1.get("content", "")

            # Skip empty files
            if not content1 or not filepath1:
                continue

            lines1 = content1.split("\n")

            for j in range(i + 1, len(python_files)):
                file2 = python_files[j]
                filepath2 = file2.get("filepath", "")
                content2 = file2.get("content", "")

                # Skip empty files
                if not content2 or not filepath2:
                    continue

                lines2 = content2.split("\n")

                # Find duplicate blocks
                duplicate_blocks = self._find_duplicate_blocks(lines1, lines2, min_duplicate_lines)

                # Report duplicate blocks
                for block in duplicate_blocks:
                    start_line1, end_line1, start_line2, end_line2 = block

                    # Create a result for the first file
                    results.append(
                        RuleResult(
                            rule_id=self.id,
                            severity=self.severity,
                            message=(f"Duplicate code block found in {filepath2} (lines {start_line2 + 1}-{end_line2 + 1})"),
                            filepath=filepath1,
                            line=start_line1 + 1,
                            code_snippet="\n".join(lines1[start_line1 : end_line1 + 1]),
                            fix_suggestions=[
                                "Extract the duplicate code into a shared function or class",
                                "Use inheritance or composition to share common functionality",
                                "Consider using a design pattern to eliminate duplication",
                            ],
                        )
                    )

        return results

    def _find_duplicate_blocks(self, lines1: list[str], lines2: list[str], min_length: int) -> list[tuple[int, int, int, int]]:
        """Find duplicate blocks of code between two lists of lines.

        Args:
            lines1: First list of lines
            lines2: Second list of lines
            min_length: Minimum length of duplicate blocks to report

        Returns:
            List of tuples (start1, end1, start2, end2) representing duplicate blocks
        """
        duplicates = []

        for i in range(len(lines1) - min_length + 1):
            for j in range(len(lines2) - min_length + 1):
                # Check if the current block of min_length lines is identical
                if all(lines1[i + k] == lines2[j + k] for k in range(min_length)):
                    # Found a duplicate block, extend it as far as possible
                    end1 = i + min_length
                    end2 = j + min_length

                    while end1 < len(lines1) and end2 < len(lines2) and lines1[end1] == lines2[end2]:
                        end1 += 1
                        end2 += 1

                    # Add the duplicate block to the list
                    duplicates.append((i, end1, j, end2))

                    # Skip ahead to avoid reporting overlapping blocks
                    i = end1 - 1
                    break

        return duplicates
