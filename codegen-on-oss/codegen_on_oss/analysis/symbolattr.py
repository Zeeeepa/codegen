"""
Module for attributing symbols to authors.
"""

from typing import Dict, List, Union

from codegen import Codebase
from codegen.sdk.core.symbol import Symbol


def get_symbol_attribution(symbol: Symbol) -> Dict[str, Union[str, int]]:
    """
    Get attribution information for a symbol.

    Args:
        symbol: The symbol to get attribution for

    Returns:
        A dictionary with attribution information
    """
    # Get the file path for the symbol
    file_path = symbol.filepath

    # Get the line range for the symbol
    start_line = symbol.line_number
    end_line = symbol.end_line_number if hasattr(symbol, "end_line_number") else start_line + 10

    # Use git blame to get the author information
    blame_info = _get_git_blame_info(file_path, start_line, end_line)

    # Process the blame info to get attribution
    attribution = _process_blame_info(blame_info)

    # Add symbol information
    attribution["symbol_name"] = symbol.name
    attribution["symbol_type"] = symbol.type
    attribution["file_path"] = file_path
    attribution["line_range"] = f"{start_line}-{end_line}"

    return attribution


def get_file_attribution(
    file_path: str,
) -> Dict[str, Union[str, int, List[Dict[str, Union[str, int]]]]]:
    """
    Get attribution information for a file.

    Args:
        file_path: Path to the file to get attribution for

    Returns:
        A dictionary with attribution information
    """
    # Get the number of lines in the file
    num_lines = _get_file_line_count(file_path)

    # Use git blame to get the author information
    blame_info = _get_git_blame_info(file_path, 1, num_lines)

    # Process the blame info to get attribution
    attribution = _process_blame_info(blame_info)

    # Add file information
    attribution["file_path"] = file_path
    attribution["line_count"] = num_lines

    # Get per-author breakdown
    author_breakdown: List[Dict[str, Union[str, int]]] = _get_author_breakdown(blame_info)
    attribution["author_breakdown"] = author_breakdown

    return attribution


def _get_git_blame_info(file_path: str, start_line: int, end_line: int) -> List[Dict[str, str]]:
    """
    Get git blame information for a file.

    Args:
        file_path: Path to the file
        start_line: Start line number
        end_line: End line number

    Returns:
        A list of dictionaries with blame information
    """
    # This is a placeholder for actual git blame implementation
    # In a real implementation, you would run git blame and parse the output
    return [
        {
            "author": "John Doe",
            "email": "john@example.com",
            "date": "2023-01-01",
            "line": i,
        }
        for i in range(start_line, end_line + 1)
    ]


def _process_blame_info(blame_info: List[Dict[str, str]]) -> Dict[str, Union[str, int]]:
    """
    Process git blame information to get attribution.

    Args:
        blame_info: List of dictionaries with blame information

    Returns:
        A dictionary with processed attribution information
    """
    # Count the number of lines per author
    author_counts = {}
    for info in blame_info:
        author = info["author"]
        author_counts[author] = author_counts.get(author, 0) + 1

    # Find the primary author (the one with the most lines)
    primary_author = max(author_counts.items(), key=lambda x: x[1]) if author_counts else (None, 0)

    # Calculate the percentage of lines by the primary author
    total_lines = len(blame_info)
    primary_percentage = (primary_author[1] / total_lines) * 100 if total_lines > 0 else 0

    return {
        "primary_author": primary_author[0],
        "primary_author_lines": primary_author[1],
        "primary_author_percentage": primary_percentage,
        "total_lines": total_lines,
    }


def _get_author_breakdown(blame_info: List[Dict[str, str]]) -> List[Dict[str, Union[str, int]]]:
    """
    Get a breakdown of lines by author.

    Args:
        blame_info: List of dictionaries with blame information

    Returns:
        A list of dictionaries with author breakdown information
    """
    # Count the number of lines per author
    author_counts = {}
    for info in blame_info:
        author = info["author"]
        author_counts[author] = author_counts.get(author, 0) + 1

    # Calculate the percentage of lines by each author
    total_lines = len(blame_info)
    author_breakdown = []
    for author, count in author_counts.items():
        percentage = (count / total_lines) * 100 if total_lines > 0 else 0
        author_breakdown.append(
            {
                "author": author,
                "lines": count,
                "percentage": percentage,
            }
        )

    # Sort by number of lines (descending)
    author_breakdown.sort(key=lambda x: x["lines"], reverse=True)

    return author_breakdown


def _get_file_line_count(file_path: str) -> int:
    """
    Get the number of lines in a file.

    Args:
        file_path: Path to the file

    Returns:
        The number of lines in the file
    """
    # This is a placeholder for actual line counting
    # In a real implementation, you would read the file and count the lines
    return 100


def print_symbol_attribution(codebase: Codebase) -> None:
    """
    Print attribution information for all symbols in a codebase.

    Args:
        codebase: The codebase to analyze
    """
    for symbol in codebase.symbols:
        attribution = get_symbol_attribution(symbol)
        print(f"Symbol: {attribution['symbol_name']} ({attribution['symbol_type']})")
        print(f"File: {attribution['file_path']}")
        print(f"Lines: {attribution['line_range']}")
        print(
            f"Primary Author: {attribution['primary_author']} ({attribution['primary_author_percentage']:.2f}%)"
        )
        print(f"Total Lines: {attribution['total_lines']}")
        print()
