"""
Configuration Utilities

Utilities for working with configuration.
"""

import json
import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from a file.

    Args:
        config_path: The path to the configuration file

    Returns:
        A dictionary containing the configuration
    """
    # Default config path
    if not config_path:
        config_path = os.environ.get(
            "PR_ANALYSIS_CONFIG",
            os.path.join(os.path.dirname(__file__), "..", "config", "pr_analysis.json"),
        )

    # Check if config file exists
    if not os.path.exists(config_path):
        logger.warning(f"Config file not found: {config_path}")
        return get_default_config()

    # Load config from file
    try:
        with open(config_path, "r") as f:
            config = json.load(f)

        logger.info(f"Loaded config from {config_path}")
        return config
    except Exception as e:
        logger.exception(f"Error loading config from {config_path}: {e}")
        return get_default_config()


def get_default_config() -> Dict[str, Any]:
    """
    Get the default configuration.

    Returns:
        A dictionary containing the default configuration
    """
    return {
        "github": {
            "post_comments": True,
            "post_summary": True,
            "max_inline_comments": 10,
        },
        "rules": {
            "code_integrity": {"enabled": True, "severity_threshold": "warning"},
            "parameter_validation": {"enabled": True, "severity_threshold": "warning"},
            "implementation_validation": {
                "enabled": True,
                "severity_threshold": "warning",
            },
        },
        "reporting": {"format": "markdown", "include_visualization": False},
    }


def merge_configs(base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge two configurations.

    Args:
        base_config: The base configuration
        override_config: The configuration to override with

    Returns:
        A dictionary containing the merged configuration
    """
    merged_config = base_config.copy()

    for key, value in override_config.items():
        if (
            isinstance(value, dict)
            and key in merged_config
            and isinstance(merged_config[key], dict)
        ):
            # Recursively merge dictionaries
            merged_config[key] = merge_configs(merged_config[key], value)
        else:
            # Override value
            merged_config[key] = value

    return merged_config
