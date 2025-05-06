"""
Diff utilities for PR analysis.

This module provides utilities for analyzing code diffs.
"""

import difflib
import logging
from typing import Dict, List, Tuple, Any, Optional

logger = logging.getLogger(__name__)


def parse_diff(diff_text: str) -> Dict[str, Dict[str, Any]]:
    """
    Parse a diff text into a structured format.

    Args:
        diff_text: Diff text

    Returns:
        Dictionary mapping file paths to diff information
    """
    result = {}
    current_file = None
    current_hunks = []
    current_hunk = None
    current_hunk_lines = []

    for line in diff_text.splitlines():
        if line.startswith("diff --git"):
            # Start of a new file
            if current_file:
                # Save the previous file
                result[current_file]["hunks"] = current_hunks
                current_hunks = []

            # Extract the file path
            parts = line.split(" ")
            a_file = parts[2][2:]  # Remove "a/"
            b_file = parts[3][2:]  # Remove "b/"
            current_file = b_file

            result[current_file] = {
                "a_file": a_file,
                "b_file": b_file,
                "hunks": [],
            }
        elif line.startswith("@@"):
            # Start of a new hunk
            if current_hunk:
                # Save the previous hunk
                current_hunk["lines"] = current_hunk_lines
                current_hunks.append(current_hunk)
                current_hunk_lines = []

            # Parse the hunk header
            parts = line.split(" ")
            a_range = parts[1]
            b_range = parts[2]

            a_start = int(a_range.split(",")[0][1:])
            a_count = int(a_range.split(",")[1]) if "," in a_range else 1

            b_start = int(b_range.split(",")[0][1:])
            b_count = int(b_range.split(",")[1]) if "," in b_range else 1

            current_hunk = {
                "a_start": a_start,
                "a_count": a_count,
                "b_start": b_start,
                "b_count": b_count,
                "lines": [],
            }
        elif current_hunk is not None:
            # Add the line to the current hunk
            current_hunk_lines.append(line)

    # Save the last file and hunk
    if current_file and current_hunk:
        current_hunk["lines"] = current_hunk_lines
        current_hunks.append(current_hunk)
        result[current_file]["hunks"] = current_hunks

    return result


def get_changed_lines(diff_info: Dict[str, Dict[str, Any]]) -> Dict[str, List[int]]:
    """
    Get the lines that were changed in a diff.

    Args:
        diff_info: Diff information from parse_diff

    Returns:
        Dictionary mapping file paths to lists of changed line numbers
    """
    result = {}

    for file_path, file_diff in diff_info.items():
        changed_lines = []

        for hunk in file_diff["hunks"]:
            b_line = hunk["b_start"]

            for line in hunk["lines"]:
                if line.startswith("+"):
                    changed_lines.append(b_line)
                    b_line += 1
                elif line.startswith("-"):
                    # Line was removed, don't increment b_line
                    pass
                else:
                    b_line += 1

        result[file_path] = changed_lines

    return result


def get_diff_stats(diff_info: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
    """
    Get statistics for a diff.

    Args:
        diff_info: Diff information from parse_diff

    Returns:
        Dictionary mapping file paths to diff statistics
    """
    result = {}

    for file_path, file_diff in diff_info.items():
        additions = 0
        deletions = 0

        for hunk in file_diff["hunks"]:
            for line in hunk["lines"]:
                if line.startswith("+"):
                    additions += 1
                elif line.startswith("-"):
                    deletions += 1

        result[file_path] = {
            "additions": additions,
            "deletions": deletions,
            "changes": additions + deletions,
        }

    return result


def generate_diff(original_text: str, modified_text: str, context_lines: int = 3) -> str:
    """
    Generate a diff between two texts.

    Args:
        original_text: Original text
        modified_text: Modified text
        context_lines: Number of context lines to include

    Returns:
        Diff text
    """
    original_lines = original_text.splitlines()
    modified_lines = modified_text.splitlines()

    diff = difflib.unified_diff(
        original_lines,
        modified_lines,
        n=context_lines,
        lineterm="",
    )

    return "\n".join(diff)

