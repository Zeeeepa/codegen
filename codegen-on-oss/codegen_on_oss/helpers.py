"""
Helper functions for the codegen-on-oss package.

This module provides helper functions for common tasks.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional, Union

from codegen import Codebase

from codegen_on_oss.api import CodegenOnOSS


def setup_logging(level: str = "INFO") -> logging.Logger:
    """
    Set up logging for the codegen-on-oss package.
    
    Args:
        level: The logging level (default: INFO)
        
    Returns:
        A configured logger
    """
    # Convert string level to logging level
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {level}")
    
    # Configure logging
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    # Create and return a logger
    logger = logging.getLogger("codegen-on-oss")
    logger.setLevel(numeric_level)
    
    return logger


def save_results(results: Dict[str, Any], output_path: str) -> None:
    """
    Save analysis results to a file.
    
    Args:
        results: The results to save
        output_path: The path to save the results to
    """
    # Create the directory if it doesn't exist
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    # Save the results
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)


def analyze_repository(
    repo_url: str,
    output_path: Optional[str] = None,
    include_integrity: bool = False,
    branch: Optional[str] = None,
    github_token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Analyze a repository and return the results.
    
    Args:
        repo_url: The URL of the repository to analyze
        output_path: Optional path to save the results to
        include_integrity: Whether to include code integrity analysis
        branch: Optional branch to analyze
        github_token: Optional GitHub token for accessing private repositories
        
    Returns:
        A dictionary containing the analysis results
    """
    # Create an API instance
    api = CodegenOnOSS(github_token=github_token)
    
    # Parse the repository
    repo_data = api.parse_repository(repo_url, branch=branch)
    
    # Analyze the codebase
    analysis = api.analyze_codebase(repo_data, analysis_type="full")
    
    # Add integrity analysis if requested
    if include_integrity:
        integrity = api.analyze_code_integrity(repo_data)
        analysis["integrity"] = integrity
    
    # Save the results if requested
    if output_path:
        save_results(analysis, output_path)
    
    return analysis


def batch_analyze_repositories(
    repo_urls: List[str],
    output_dir: Optional[str] = None,
    include_integrity: bool = False,
    github_token: Optional[str] = None,
) -> Dict[str, Dict[str, Any]]:
    """
    Analyze multiple repositories and return the results.
    
    Args:
        repo_urls: The URLs of the repositories to analyze
        output_dir: Optional directory to save the results to
        include_integrity: Whether to include code integrity analysis
        github_token: Optional GitHub token for accessing private repositories
        
    Returns:
        A dictionary mapping repository URLs to analysis results
    """
    # Create an API instance
    api = CodegenOnOSS(github_token=github_token)
    
    # Analyze each repository
    results = {}
    for repo_url in repo_urls:
        # Generate a filename for the results
        repo_name = repo_url.split("/")[-1].split(".")[0]
        output_path = None
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"{repo_name}.json")
        
        # Analyze the repository
        try:
            results[repo_url] = analyze_repository(
                repo_url=repo_url,
                output_path=output_path,
                include_integrity=include_integrity,
                github_token=github_token,
            )
        except Exception as e:
            results[repo_url] = {"error": str(e)}
    
    return results

