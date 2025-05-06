"""
Diff Utilities Module

This module provides utilities for diff analysis.
"""

import difflib
import logging
from typing import Dict, List, Any, Tuple

logger = logging.getLogger(__name__)


def parse_diff(diff_text: str) -> Dict[str, Any]:
    """
    Parse a diff text into a structured format.
    
    Args:
        diff_text: Diff text to parse
        
    Returns:
        Parsed diff as a dictionary
    """
    result = {}
    current_file = None
    current_hunks = []
    
    lines = diff_text.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # New file
        if line.startswith('diff --git'):
            if current_file is not None:
                result[current_file] = {
                    'hunks': current_hunks
                }
            
            # Extract file name
            parts = line.split(' ')
            current_file = parts[2][2:]  # Remove 'a/'
            current_hunks = []
        
        # Hunk header
        elif line.startswith('@@'):
            hunk_header = line
            hunk_lines = []
            
            # Extract line numbers
            parts = hunk_header.split(' ')
            old_start = int(parts[1].split(',')[0][1:])
            new_start = int(parts[2].split(',')[0][1:])
            
            # Skip the hunk header
            i += 1
            
            # Parse hunk lines
            while i < len(lines) and not (lines[i].startswith('diff --git') or lines[i].startswith('@@')):
                hunk_lines.append(lines[i])
                i += 1
            
            # Add the hunk
            current_hunks.append({
                'header': hunk_header,
                'old_start': old_start,
                'new_start': new_start,
                'lines': hunk_lines
            })
            
            # Continue without incrementing i
            continue
        
        i += 1
    
    # Add the last file
    if current_file is not None:
        result[current_file] = {
            'hunks': current_hunks
        }
    
    return result


def get_changed_lines(diff: Dict[str, Any]) -> Dict[str, List[int]]:
    """
    Get lines changed in a diff.
    
    Args:
        diff: Parsed diff
        
    Returns:
        Dictionary mapping file paths to lists of changed line numbers
    """
    result = {}
    
    for file_path, file_diff in diff.items():
        changed_lines = []
        
        for hunk in file_diff['hunks']:
            new_line = hunk['new_start']
            
            for line in hunk['lines']:
                if line.startswith('+'):
                    changed_lines.append(new_line)
                
                if not line.startswith('-'):
                    new_line += 1
        
        result[file_path] = changed_lines
    
    return result


def compute_diff(base_content: str, head_content: str) -> str:
    """
    Compute the diff between two strings.
    
    Args:
        base_content: Base content
        head_content: Head content
        
    Returns:
        Diff as a string
    """
    base_lines = base_content.splitlines()
    head_lines = head_content.splitlines()
    
    diff = difflib.unified_diff(
        base_lines,
        head_lines,
        fromfile='base',
        tofile='head',
        lineterm=''
    )
    
    return '\n'.join(diff)


def get_line_changes(base_content: str, head_content: str) -> Tuple[List[int], List[int], List[int]]:
    """
    Get line changes between two strings.
    
    Args:
        base_content: Base content
        head_content: Head content
        
    Returns:
        Tuple of (added_lines, deleted_lines, modified_lines)
    """
    base_lines = base_content.splitlines()
    head_lines = head_content.splitlines()
    
    matcher = difflib.SequenceMatcher(None, base_lines, head_lines)
    
    added_lines = []
    deleted_lines = []
    modified_lines = []
    
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'insert':
            added_lines.extend(range(j1, j2))
        elif tag == 'delete':
            deleted_lines.extend(range(i1, i2))
        elif tag == 'replace':
            modified_lines.extend(range(j1, j2))
    
    return added_lines, deleted_lines, modified_lines


def highlight_diff(base_content: str, head_content: str) -> str:
    """
    Generate an HTML diff with highlighted changes.
    
    Args:
        base_content: Base content
        head_content: Head content
        
    Returns:
        HTML diff with highlighted changes
    """
    base_lines = base_content.splitlines()
    head_lines = head_content.splitlines()
    
    diff = difflib.HtmlDiff()
    return diff.make_file(base_lines, head_lines, fromdesc='Base', todesc='Head')

