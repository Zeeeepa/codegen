"""
Diff Utilities

Utilities for working with diffs.
"""

import difflib
import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


def parse_diff(diff_text: str) -> Dict[str, Any]:
    """
    Parse a diff text into a structured format.

    Args:
        diff_text: The diff text to parse

    Returns:
        A dictionary containing the parsed diff
    """
    if not diff_text:
        return {"chunks": []}

    chunks = []
    current_chunk = None

    for line in diff_text.split("\n"):
        if line.startswith("@@"):
            # New chunk
            if current_chunk:
                chunks.append(current_chunk)

            # Parse chunk header
            header_parts = line.split(" ")
            if len(header_parts) >= 3:
                old_range = header_parts[1]
                new_range = header_parts[2]

                old_start, old_count = _parse_range(old_range)
                new_start, new_count = _parse_range(new_range)

                current_chunk = {
                    "header": line,
                    "old_start": old_start,
                    "old_count": old_count,
                    "new_start": new_start,
                    "new_count": new_count,
                    "lines": [],
                }
        elif current_chunk is not None:
            # Add line to current chunk
            current_chunk["lines"].append(line)

    # Add the last chunk
    if current_chunk:
        chunks.append(current_chunk)

    return {"chunks": chunks}


def _parse_range(range_str: str) -> Tuple[int, int]:
    """
    Parse a range string from a diff header.

    Args:
        range_str: The range string to parse (e.g., "-1,5" or "+2,10")

    Returns:
        A tuple of (start_line, line_count)
    """
    # Remove the +/- prefix
    range_str = range_str[1:]

    # Split by comma
    parts = range_str.split(",")

    # Parse start line
    start_line = int(parts[0])

    # Parse line count (default to 1 if not specified)
    line_count = int(parts[1]) if len(parts) > 1 else 1

    return start_line, line_count


def get_changed_lines(diff_text: str) -> Dict[int, str]:
    """
    Get the changed lines from a diff.

    Args:
        diff_text: The diff text to parse

    Returns:
        A dictionary mapping line numbers to line types ("added" or "removed")
    """
    parsed_diff = parse_diff(diff_text)
    changed_lines = {}

    for chunk in parsed_diff["chunks"]:
        new_line = chunk["new_start"]

        for line in chunk["lines"]:
            if line.startswith("+"):
                changed_lines[new_line] = "added"
                new_line += 1
            elif line.startswith("-"):
                # Removed lines don't affect the new line number
                pass
            else:
                new_line += 1

    return changed_lines


def get_context_lines(file_content: str, line_number: int, context_lines: int = 3) -> str:
    """
    Get context lines around a specific line in a file.

    Args:
        file_content: The content of the file
        line_number: The line number to get context for
        context_lines: The number of context lines to include

    Returns:
        A string containing the context lines
    """
    lines = file_content.split("\n")

    start_line = max(0, line_number - context_lines - 1)
    end_line = min(len(lines), line_number + context_lines)

    context = lines[start_line:end_line]

    return "\n".join(context)
