"""
Codegen SDK Codebase Module

This module provides functionality for accessing the Codegen SDK codebase for analysis.
It includes functions for getting SDK subdirectories and creating a Codebase instance
specifically for the SDK.
"""

import os.path

from codegen.configs.models.codebase import CodebaseConfig
from codegen.configs.models.secrets import SecretsConfig
from codegen.sdk.core.codebase import Codebase
from codegen.shared.enums.programming_language import ProgrammingLanguage
from codegen.shared.logging.get_logger import get_logger

from codegen_on_oss.analyzers.current_code_codebase import (
    get_repo_path,
    get_selected_codebase,
)

logger = get_logger(__name__)


def get_codegen_sdk_base_path() -> str:
    """
    Returns the base directory path of the Codegen SDK.
    
    Returns:
        str: The base path of the Codegen SDK
    """
    repo_path = get_repo_path()
    # Check common locations for the SDK
    potential_paths = [
        os.path.join(repo_path, "src"),
        os.path.join(repo_path, "codegen"),
        repo_path,
    ]
    
    for path in potential_paths:
        sdk_path = os.path.join(path, "codegen", "sdk")
        if os.path.exists(sdk_path) and os.path.isdir(sdk_path):
            logger.info(f"Found Codegen SDK at: {sdk_path}")
            return path
    
    # If not found, default to repo path and log a warning
    logger.warning(
        f"Could not find Codegen SDK directory, defaulting to repo path: {repo_path}"
    )
    return repo_path


def get_codegen_sdk_subdirectories() -> list[str]:
    """
    Returns a list of subdirectories that contain the Codegen SDK code.
    
    Returns:
        list[str]: A list of directory paths containing the SDK code
    """
    base = get_codegen_sdk_base_path()
    sdk_path = os.path.join(base, "codegen", "sdk")
    codemods_path = os.path.join(base, "codemods")
    
    subdirs = []
    
    if os.path.exists(sdk_path) and os.path.isdir(sdk_path):
        subdirs.append(sdk_path)
    else:
        logger.warning(f"SDK directory not found at: {sdk_path}")
    
    if os.path.exists(codemods_path) and os.path.isdir(codemods_path):
        subdirs.append(codemods_path)
    else:
        logger.debug(f"Codemods directory not found at: {codemods_path}")
    
    if not subdirs:
        logger.warning("No SDK subdirectories found. Analysis may be incomplete.")
    
    return subdirs


def get_codegen_sdk_codebase(
    config: CodebaseConfig | None = None,
    secrets: SecretsConfig | None = None,
    programming_language: ProgrammingLanguage | None = None,
) -> Codebase:
    """
    Creates a Codebase instance specifically for the Codegen SDK.
    
    This function is responsible for figuring out where the SDK is located
    (either in Modal or local environment) and creating a properly configured
    Codebase instance for it.
    
    Parameters:
        config: Optional CodebaseConfig instance for customizing codebase behavior
        secrets: Optional SecretsConfig for any credentials needed
        programming_language: Optional programming language specification
        
    Returns:
        Codebase: A Codebase instance configured for the Codegen SDK
    """
    # Default to Python if not specified
    if not programming_language:
        programming_language = ProgrammingLanguage.PYTHON
    
    # Get the SDK subdirectories
    subdirectories = get_codegen_sdk_subdirectories()
    
    # Get the repo path
    repo_path = get_repo_path()
    
    # Get the base path
    base_path = get_codegen_sdk_base_path()
    if base_path == repo_path:
        # If base_path is the same as repo_path, use empty string
        # to avoid duplication in paths
        base_path = ""
    
    logger.info(f"Creating Codegen SDK codebase with subdirectories: {subdirectories}")
    
    # Create and return the codebase
    codebase = get_selected_codebase(
        repo_path=repo_path,
        base_path=base_path,
        config=config,
        secrets=secrets,
        subdirectories=subdirectories,
        programming_language=programming_language,
    )
    
    return codebase
