"""
File system utilities for Serena tools integration.

Contains scan_directory function for directory traversal and file listing.
"""

import os
from pathlib import Path
from typing import Callable, List, Tuple


def scan_directory(
    path: str,
    relative_to: str = "",
    recursive: bool = True,
    is_ignored_dir: Callable[[str], bool] = None,
    is_ignored_file: Callable[[str], bool] = None,
) -> Tuple[List[str], List[str]]:
    """
    Scan a directory and return lists of directories and files.

    :param path: Absolute path to the directory to scan
    :param relative_to: Base path to make results relative to (optional)
    :param recursive: Whether to scan subdirectories recursively
    :param is_ignored_dir: Function to check if a directory should be ignored
    :param is_ignored_file: Function to check if a file should be ignored
    :return: Tuple of (directories, files) as lists of relative paths
    """
    dirs = []
    files = []
    
    if is_ignored_dir is None:
        is_ignored_dir = lambda x: False
    if is_ignored_file is None:
        is_ignored_file = lambda x: False
    
    try:
        path_obj = Path(path)
        if not path_obj.exists() or not path_obj.is_dir():
            return dirs, files
        
        base_path = Path(relative_to) if relative_to else Path.cwd()
        
        if recursive:
            # Recursive scan
            for root, dirnames, filenames in os.walk(path):
                root_path = Path(root)
                
                # Filter directories in-place to control os.walk recursion
                dirnames[:] = [
                    d for d in dirnames 
                    if not is_ignored_dir(str(root_path / d))
                ]
                
                # Process directories
                for dirname in dirnames:
                    dir_path = root_path / dirname
                    if not is_ignored_dir(str(dir_path)):
                        try:
                            relative_path = str(dir_path.relative_to(base_path))
                            dirs.append(relative_path)
                        except ValueError:
                            # Path is not relative to base_path, use as-is
                            dirs.append(str(dir_path))
                
                # Process files
                for filename in filenames:
                    file_path = root_path / filename
                    if not is_ignored_file(str(file_path)):
                        try:
                            relative_path = str(file_path.relative_to(base_path))
                            files.append(relative_path)
                        except ValueError:
                            # Path is not relative to base_path, use as-is
                            files.append(str(file_path))
        else:
            # Non-recursive scan
            for item in path_obj.iterdir():
                if item.is_dir():
                    if not is_ignored_dir(str(item)):
                        try:
                            relative_path = str(item.relative_to(base_path))
                            dirs.append(relative_path)
                        except ValueError:
                            dirs.append(str(item))
                elif item.is_file():
                    if not is_ignored_file(str(item)):
                        try:
                            relative_path = str(item.relative_to(base_path))
                            files.append(relative_path)
                        except ValueError:
                            files.append(str(item))
    
    except Exception as e:
        # Log error but don't fail completely
        import logging
        log = logging.getLogger(__name__)
        log.warning(f"Error scanning directory {path}: {e}")
    
    # Sort results for consistent output
    dirs.sort()
    files.sort()
    
    return dirs, files


def is_common_ignored_path(path: str) -> bool:
    """
    Check if a path matches common ignore patterns.
    
    :param path: Path to check
    :return: True if path should be ignored
    """
    path_obj = Path(path)
    ignore_patterns = [
        '.git', '__pycache__', '.pytest_cache', 'node_modules', 
        '.venv', 'venv', '.env', 'dist', 'build', '.DS_Store',
        '.mypy_cache', '.tox', '.coverage', 'htmlcov',
        '.idea', '.vscode', '*.egg-info'
    ]
    
    # Check if any part of the path matches ignore patterns
    for part in path_obj.parts:
        for pattern in ignore_patterns:
            if pattern.startswith('*') and part.endswith(pattern[1:]):
                return True
            elif part == pattern:
                return True
    
    return False


def find_files_by_extension(
    directory: str,
    extensions: List[str],
    recursive: bool = True,
    relative_to: str = ""
) -> List[str]:
    """
    Find files with specific extensions in a directory.
    
    :param directory: Directory to search in
    :param extensions: List of file extensions (e.g., ['.py', '.js'])
    :param recursive: Whether to search recursively
    :param relative_to: Base path to make results relative to
    :return: List of file paths
    """
    def is_ignored_file(path: str) -> bool:
        if is_common_ignored_path(path):
            return True
        return Path(path).suffix.lower() not in [ext.lower() for ext in extensions]
    
    _, files = scan_directory(
        directory,
        relative_to=relative_to,
        recursive=recursive,
        is_ignored_dir=is_common_ignored_path,
        is_ignored_file=is_ignored_file
    )
    
    return files


def get_file_info(file_path: str) -> dict:
    """
    Get information about a file.
    
    :param file_path: Path to the file
    :return: Dictionary with file information
    """
    try:
        path_obj = Path(file_path)
        if not path_obj.exists():
            return {"error": "File not found"}
        
        stat = path_obj.stat()
        return {
            "path": str(path_obj),
            "name": path_obj.name,
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "is_file": path_obj.is_file(),
            "is_dir": path_obj.is_dir(),
            "extension": path_obj.suffix,
            "parent": str(path_obj.parent)
        }
    except Exception as e:
        return {"error": str(e)}
