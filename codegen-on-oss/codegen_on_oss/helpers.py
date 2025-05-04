"""
Helper functions for common tasks in codegen-on-oss.

This module provides utility functions that simplify common operations
when working with the codegen-on-oss component.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Union, Any, Callable

from codegen_on_oss.api import (
    CodegenOnOSS,
    parse_repository,
    analyze_codebase,
    analyze_code_integrity,
)


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    format_string: Optional[str] = None,
) -> logging.Logger:
    """Set up logging for codegen-on-oss.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Optional file path to write logs to.
        format_string: Optional custom format string for log messages.
        
    Returns:
        Configured logger instance.
    """
    log_level = getattr(logging, level.upper())
    logger = logging.getLogger("codegen_on_oss")
    logger.setLevel(log_level)
    
    # Default format
    if not format_string:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    formatter = logging.Formatter(format_string)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from a JSON file.
    
    Args:
        config_path: Path to the configuration file.
        
    Returns:
        Configuration dictionary.
        
    Raises:
        FileNotFoundError: If the configuration file doesn't exist.
        json.JSONDecodeError: If the configuration file is not valid JSON.
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, "r") as f:
        return json.load(f)


def save_results(
    results: Dict[str, Any],
    output_path: str,
    pretty_print: bool = True,
) -> None:
    """Save analysis results to a JSON file.
    
    Args:
        results: Analysis results to save.
        output_path: Path to save the results to.
        pretty_print: Whether to format the JSON for readability.
        
    Raises:
        IOError: If the output file cannot be written.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    with open(output_path, "w") as f:
        if pretty_print:
            json.dump(results, f, indent=2, sort_keys=True)
        else:
            json.dump(results, f)


def analyze_repository(
    repo_url: str,
    output_path: Optional[str] = None,
    analysis_type: str = "full",
    include_integrity: bool = False,
    branch: Optional[str] = None,
) -> Dict[str, Any]:
    """Analyze a repository in a single function call.
    
    This is a convenience function that combines repository parsing and analysis.
    
    Args:
        repo_url: URL of the repository to analyze.
        output_path: Optional path to save the results to.
        analysis_type: Type of analysis to perform.
        include_integrity: Whether to include code integrity analysis.
        branch: Optional branch to analyze.
        
    Returns:
        Dictionary containing analysis results.
    """
    # Initialize the API
    api = CodegenOnOSS()
    
    # Parse the repository
    repo_data = api.parse_repository(repo_url, branch=branch)
    
    # Analyze the codebase
    results = api.analyze_codebase(repo_data, analysis_type=analysis_type)
    
    # Add integrity analysis if requested
    if include_integrity:
        integrity_results = api.analyze_code_integrity(repo_data)
        results["integrity"] = integrity_results
    
    # Save results if output path is provided
    if output_path:
        save_results(results, output_path)
    
    return results


def batch_analyze_repositories(
    repo_urls: List[str],
    output_dir: str,
    analysis_type: str = "full",
    include_integrity: bool = False,
) -> Dict[str, str]:
    """Analyze multiple repositories and save results to separate files.
    
    Args:
        repo_urls: List of repository URLs to analyze.
        output_dir: Directory to save the results to.
        analysis_type: Type of analysis to perform.
        include_integrity: Whether to include code integrity analysis.
        
    Returns:
        Dictionary mapping repository URLs to output file paths.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    results = {}
    for repo_url in repo_urls:
        # Extract repo name from URL for the filename
        repo_name = repo_url.rstrip("/").split("/")[-1]
        if repo_name.endswith(".git"):
            repo_name = repo_name[:-4]
        
        output_path = os.path.join(output_dir, f"{repo_name}_analysis.json")
        
        try:
            analyze_repository(
                repo_url,
                output_path=output_path,
                analysis_type=analysis_type,
                include_integrity=include_integrity,
            )
            results[repo_url] = output_path
        except Exception as e:
            logging.error(f"Error analyzing {repo_url}: {str(e)}")
            results[repo_url] = f"ERROR: {str(e)}"
    
    return results


def compare_repositories(
    repo_url_1: str,
    repo_url_2: str,
    output_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Compare two repositories and identify differences.
    
    Args:
        repo_url_1: URL of the first repository.
        repo_url_2: URL of the second repository.
        output_path: Optional path to save the comparison results to.
        
    Returns:
        Dictionary containing comparison results.
    """
    # Initialize the API
    api = CodegenOnOSS()
    
    # Parse both repositories
    repo_data_1 = api.parse_repository(repo_url_1)
    repo_data_2 = api.parse_repository(repo_url_2)
    
    # Create snapshots
    snapshot_id_1 = api.create_snapshot(repo_data_1)
    snapshot_id_2 = api.create_snapshot(repo_data_2)
    
    # Compare snapshots
    comparison = api.compare_snapshots(snapshot_id_1, snapshot_id_2)
    
    # Save results if output path is provided
    if output_path:
        save_results(comparison, output_path)
    
    return comparison

