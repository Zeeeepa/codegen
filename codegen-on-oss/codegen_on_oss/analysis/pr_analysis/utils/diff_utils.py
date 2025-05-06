"""
Utilities for diff analysis.

This module provides utility functions for analyzing diffs, including
parsing diffs, extracting changed lines, and getting file diffs.
"""

import logging
import re
from typing import Dict, List, Optional, Any, Tuple, Set


logger = logging.getLogger(__name__)


def parse_diff(diff: str) -> Dict[str, Dict[str, Any]]:
    """
    Parse a Git diff.
    
    Args:
        diff: Git diff string
        
    Returns:
        Dictionary of file diffs by filename
    """
    logger.debug("Parsing diff")
    
    file_diffs = {}
    current_file = None
    current_hunks = []
    
    # Split diff into lines
    lines = diff.splitlines()
    
    # Parse diff
    for line in lines:
        # Check for file header
        file_header_match = re.match(r'^diff --git a/(.*) b/(.*)$', line)
        if file_header_match:
            # Save previous file diff
            if current_file:
                file_diffs[current_file] = {
                    'hunks': current_hunks,
                    'binary': False,
                }
            
            # Start new file diff
            current_file = file_header_match.group(1)
            current_hunks = []
            continue
        
        # Check for binary file
        if line.startswith('Binary files '):
            if current_file:
                file_diffs[current_file] = {
                    'hunks': [],
                    'binary': True,
                }
            continue
        
        # Check for hunk header
        hunk_header_match = re.match(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', line)
        if hunk_header_match:
            old_start = int(hunk_header_match.group(1))
            old_count = int(hunk_header_match.group(2) or 1)
            new_start = int(hunk_header_match.group(3))
            new_count = int(hunk_header_match.group(4) or 1)
            
            current_hunks.append({
                'old_start': old_start,
                'old_count': old_count,
                'new_start': new_start,
                'new_count': new_count,
                'lines': [],
            })
            continue
        
        # Add line to current hunk
        if current_hunks:
            current_hunks[-1]['lines'].append(line)
    
    # Save last file diff
    if current_file:
        file_diffs[current_file] = {
            'hunks': current_hunks,
            'binary': False,
        }
    
    return file_diffs


def get_changed_lines(diff: str) -> Dict[str, Dict[str, Set[int]]]:
    """
    Get changed lines from a Git diff.
    
    Args:
        diff: Git diff string
        
    Returns:
        Dictionary of changed lines by filename
    """
    logger.debug("Getting changed lines from diff")
    
    changed_lines = {}
    
    # Parse diff
    file_diffs = parse_diff(diff)
    
    # Extract changed lines
    for filename, file_diff in file_diffs.items():
        if file_diff['binary']:
            continue
        
        added_lines = set()
        removed_lines = set()
        
        for hunk in file_diff['hunks']:
            old_line = hunk['old_start']
            new_line = hunk['new_start']
            
            for line in hunk['lines']:
                if line.startswith('+'):
                    added_lines.add(new_line)
                    new_line += 1
                elif line.startswith('-'):
                    removed_lines.add(old_line)
                    old_line += 1
                else:
                    old_line += 1
                    new_line += 1
        
        changed_lines[filename] = {
            'added': added_lines,
            'removed': removed_lines,
        }
    
    return changed_lines


def get_file_diff(diff: str, filename: str) -> Optional[str]:
    """
    Get the diff for a specific file.
    
    Args:
        diff: Git diff string
        filename: Filename to get diff for
        
    Returns:
        File diff or None if not found
    """
    logger.debug(f"Getting diff for file: {filename}")
    
    # Split diff into file diffs
    file_diffs = diff.split('diff --git ')
    
    # Find the diff for the specified file
    for file_diff in file_diffs:
        if not file_diff:
            continue
        
        # Check if this is the diff for the specified file
        file_match = re.match(r'^a/(.*) b/(.*)$', file_diff.splitlines()[0])
        if file_match and (file_match.group(1) == filename or file_match.group(2) == filename):
            return 'diff --git ' + file_diff
    
    return None


def get_line_ranges_from_diff(diff: str) -> Dict[str, List[Tuple[int, int]]]:
    """
    Get line ranges from a Git diff.
    
    Args:
        diff: Git diff string
        
    Returns:
        Dictionary of line ranges by filename
    """
    logger.debug("Getting line ranges from diff")
    
    line_ranges = {}
    
    # Parse diff
    file_diffs = parse_diff(diff)
    
    # Extract line ranges
    for filename, file_diff in file_diffs.items():
        if file_diff['binary']:
            continue
        
        ranges = []
        
        for hunk in file_diff['hunks']:
            new_start = hunk['new_start']
            new_count = hunk['new_count']
            
            if new_count > 0:
                ranges.append((new_start, new_start + new_count - 1))
        
        line_ranges[filename] = ranges
    
    return line_ranges


def get_context_lines(content: str, line_number: int, context_lines: int = 3) -> Tuple[int, int, List[str]]:
    """
    Get context lines around a specific line.
    
    Args:
        content: File content
        line_number: Line number to get context for
        context_lines: Number of context lines before and after
        
    Returns:
        Tuple of (start_line, end_line, context_lines)
    """
    logger.debug(f"Getting context lines for line {line_number}")
    
    lines = content.splitlines()
    
    start_line = max(1, line_number - context_lines)
    end_line = min(len(lines), line_number + context_lines)
    
    context = lines[start_line - 1:end_line]
    
    return start_line, end_line, context

