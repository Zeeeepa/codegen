"""
Configuration utilities for PR analysis.

This module provides utilities for loading and managing configuration.
"""

import json
import logging
import os
from typing import Dict, Any, Optional

import yaml

logger = logging.getLogger(__name__)


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from a file.

    Args:
        config_path: Path to configuration file

    Returns:
        Configuration dictionary

    Raises:
        FileNotFoundError: If the configuration file cannot be found
        ValueError: If the configuration file cannot be parsed
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    try:
        with open(config_path, "r") as f:
            if config_path.endswith(".json"):
                config = json.load(f)
            elif config_path.endswith((".yaml", ".yml")):
                config = yaml.safe_load(f)
            else:
                raise ValueError(f"Unsupported configuration file format: {config_path}")
    except Exception as e:
        logger.error(f"Failed to load configuration from {config_path}: {e}")
        raise ValueError(f"Failed to load configuration from {config_path}: {e}")

    # Merge with environment variables
    config = merge_configs(config, get_config_from_env())

    return config


def get_default_config() -> Dict[str, Any]:
    """
    Get default configuration.

    Returns:
        Default configuration dictionary
    """
    return {
        "github": {
            "token": None,
            "api_url": "https://api.github.com",
        },
        "git": {
            "repo_path": None,
        },
        "rules": [],
        "reporting": {
            "format": "markdown",
            "post_to_github": True,
        },
        "performance": {
            "timeout": 300,
            "concurrency": 4,
        },
    }


def get_config_from_env() -> Dict[str, Any]:
    """
    Get configuration from environment variables.

    Returns:
        Configuration dictionary from environment variables
    """
    config = {}

    # GitHub configuration
    if "GITHUB_TOKEN" in os.environ:
        config.setdefault("github", {})["token"] = os.environ["GITHUB_TOKEN"]

    if "GITHUB_API_URL" in os.environ:
        config.setdefault("github", {})["api_url"] = os.environ["GITHUB_API_URL"]

    # Git configuration
    if "GIT_REPO_PATH" in os.environ:
        config.setdefault("git", {})["repo_path"] = os.environ["GIT_REPO_PATH"]

    # Reporting configuration
    if "REPORTING_FORMAT" in os.environ:
        config.setdefault("reporting", {})["format"] = os.environ["REPORTING_FORMAT"]

    if "REPORTING_POST_TO_GITHUB" in os.environ:
        config.setdefault("reporting", {})["post_to_github"] = os.environ["REPORTING_POST_TO_GITHUB"].lower() in ("true", "1", "yes")

    # Performance configuration
    if "PERFORMANCE_TIMEOUT" in os.environ:
        config.setdefault("performance", {})["timeout"] = int(os.environ["PERFORMANCE_TIMEOUT"])

    if "PERFORMANCE_CONCURRENCY" in os.environ:
        config.setdefault("performance", {})["concurrency"] = int(os.environ["PERFORMANCE_CONCURRENCY"])

    return config


def merge_configs(base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge two configuration dictionaries.

    Args:
        base_config: Base configuration
        override_config: Override configuration

    Returns:
        Merged configuration
    """
    result = base_config.copy()

    for key, value in override_config.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_configs(result[key], value)
        else:
            result[key] = value

    return result

