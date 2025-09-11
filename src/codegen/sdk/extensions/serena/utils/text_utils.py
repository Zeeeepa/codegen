"""
Text utilities for Serena tools integration.

Contains search_files function for pattern matching in files.
"""

import fnmatch
import logging
import os
import re
from collections.abc import Callable
from typing import List

from codegen.sdk.extensions.solidlsp.utils.text_utils import MatchedConsecutiveLines, TextLine, LineType

log = logging.getLogger(__name__)


def default_file_reader(file_path: str) -> str:
    """Reads using utf-8 encoding."""
    with open(file_path, encoding="utf-8") as f:
        return f.read()


def glob_match(pattern: str, path: str) -> bool:
    """
    Match a file path against a glob pattern.

    Supports standard glob patterns:
    - * matches any number of characters except /
    - ** matches any number of directories (zero or more)
    - ? matches a single character except /
    - [seq] matches any character in seq

    :param pattern: Glob pattern (e.g., 'src/**/*.py', '**agent.py')
    :param path: File path to match against
    :return: True if path matches pattern
    """
    pattern = pattern.replace("\\", "/")  # Normalize backslashes to forward slashes
    path = path.replace("\\", "/")  # Normalize path backslashes to forward slashes

    # Handle ** patterns that should match zero or more directories
    if "**" in pattern:
        # Method 1: Standard fnmatch (matches one or more directories)
        regex1 = fnmatch.translate(pattern)
        if re.match(regex1, path):
            return True

        # Method 2: Handle zero-directory case by removing /** entirely
        # Convert "src/**/test.py" to "src/test.py"
        if "/**/" in pattern:
            zero_dir_pattern = pattern.replace("/**/", "/")
            regex2 = fnmatch.translate(zero_dir_pattern)
            if re.match(regex2, path):
                return True

        # Method 3: Handle leading ** case by removing **/
        # Convert "**/test.py" to "test.py"
        if pattern.startswith("**/"):
            zero_dir_pattern = pattern[3:]  # Remove "**/"
            regex3 = fnmatch.translate(zero_dir_pattern)
            if re.match(regex3, path):
                return True

        return False
    else:
        # Simple pattern without **, use fnmatch directly
        return fnmatch.fnmatch(path, pattern)


def search_files(
    relative_file_paths: List[str],
    pattern: str,
    root_path: str = "",
    file_reader: Callable[[str], str] = default_file_reader,
    context_lines_before: int = 0,
    context_lines_after: int = 0,
    paths_include_glob: str | None = None,
    paths_exclude_glob: str | None = None,
) -> List[MatchedConsecutiveLines]:
    """
    Search for a pattern in multiple files and return matches with context.

    :param relative_file_paths: List of relative file paths to search in
    :param pattern: Regular expression pattern to search for
    :param root_path: Root path for resolving relative file paths
    :param file_reader: Function to read file contents
    :param context_lines_before: Number of context lines before each match
    :param context_lines_after: Number of context lines after each match
    :param paths_include_glob: Optional glob pattern to include files
    :param paths_exclude_glob: Optional glob pattern to exclude files
    :return: List of MatchedConsecutiveLines objects
    """
    matches = []
    
    for relative_path in relative_file_paths:
        # Apply glob filters if specified
        if paths_include_glob and not glob_match(paths_include_glob, relative_path):
            continue
        if paths_exclude_glob and glob_match(paths_exclude_glob, relative_path):
            continue
        
        try:
            abs_path = os.path.join(root_path, relative_path) if root_path else relative_path
            content = file_reader(abs_path)
            
            # Search for pattern in file content
            file_matches = search_in_text(
                content,
                pattern,
                context_lines_before=context_lines_before,
                context_lines_after=context_lines_after,
                source_file_path=relative_path
            )
            matches.extend(file_matches)
            
        except Exception as e:
            log.warning(f"Error searching in file {relative_path}: {e}")
            continue
    
    return matches


def search_in_text(
    text: str,
    pattern: str,
    context_lines_before: int = 0,
    context_lines_after: int = 0,
    source_file_path: str | None = None,
    multiline: bool = True
) -> List[MatchedConsecutiveLines]:
    """
    Search for a pattern in text and return matches with context.

    :param text: Text content to search in
    :param pattern: Regular expression pattern to search for
    :param context_lines_before: Number of context lines before each match
    :param context_lines_after: Number of context lines after each match
    :param source_file_path: Optional source file path for metadata
    :param multiline: Whether to enable multiline matching
    :return: List of MatchedConsecutiveLines objects
    """
    matches = []
    lines = text.splitlines()
    total_lines = len(lines)
    
    if multiline:
        # Search across multiple lines with DOTALL flag
        compiled_pattern = re.compile(pattern, re.DOTALL | re.MULTILINE)
        for match in compiled_pattern.finditer(text):
            # Find which lines the match spans
            start_pos = match.start()
            end_pos = match.end()
            
            # Convert character positions to line numbers
            start_line_num = text[:start_pos].count('\n')
            end_line_num = text[:end_pos].count('\n')
            
            # Calculate context range
            context_start = max(0, start_line_num - context_lines_before)
            context_end = min(total_lines - 1, end_line_num + context_lines_after)
            
            # Create TextLine objects for the context
            context_lines = []
            for i in range(context_start, context_end + 1):
                line_num = i + 1  # 1-based line numbers
                if i < start_line_num:
                    match_type = LineType.BEFORE_MATCH
                elif i > end_line_num:
                    match_type = LineType.AFTER_MATCH
                else:
                    match_type = LineType.MATCH

                context_lines.append(TextLine(
                    line_number=line_num, 
                    line_content=lines[i], 
                    match_type=match_type
                ))

            matches.append(MatchedConsecutiveLines(
                lines=context_lines, 
                source_file_path=source_file_path
            ))
    else:
        # Search line by line
        compiled_pattern = re.compile(pattern)
        for i, line in enumerate(lines):
            line_num = i + 1
            if compiled_pattern.search(line):
                # Calculate the range of lines to include in the context
                context_start = max(0, i - context_lines_before)
                context_end = min(total_lines - 1, i + context_lines_after)

                # Create TextLine objects for the context
                context_lines = []
                for j in range(context_start, context_end + 1):
                    context_line_num = j + 1
                    if j < i:
                        match_type = LineType.BEFORE_MATCH
                    elif j > i:
                        match_type = LineType.AFTER_MATCH
                    else:
                        match_type = LineType.MATCH

                    context_lines.append(TextLine(
                        line_number=context_line_num, 
                        line_content=lines[j], 
                        match_type=match_type
                    ))

                matches.append(MatchedConsecutiveLines(
                    lines=context_lines, 
                    source_file_path=source_file_path
                ))

    return matches
