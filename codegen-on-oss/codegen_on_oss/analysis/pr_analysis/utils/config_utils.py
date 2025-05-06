"""
Utilities for configuration management.

This module provides utility functions for managing configuration,
including loading, saving, and merging configurations.
"""

import logging
import os
import json
import yaml
from typing import Dict, List, Optional, Any, Union


logger = logging.getLogger(__name__)


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from a file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
        
    Raises:
        FileNotFoundError: If the configuration file does not exist
        ValueError: If the configuration file format is invalid
    """
    logger.info(f"Loading configuration from {config_path}")
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    # Determine file format from extension
    _, ext = os.path.splitext(config_path)
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            if ext.lower() == '.json':
                config = json.load(f)
            elif ext.lower() in ('.yaml', '.yml'):
                config = yaml.safe_load(f)
            else:
                raise ValueError(f"Unsupported configuration file format: {ext}")
    except (json.JSONDecodeError, yaml.YAMLError) as e:
        raise ValueError(f"Invalid configuration file format: {e}")
    
    return config


def save_config(config: Dict[str, Any], config_path: str) -> None:
    """
    Save configuration to a file.
    
    Args:
        config: Configuration dictionary
        config_path: Path to configuration file
        
    Raises:
        ValueError: If the configuration file format is invalid
    """
    logger.info(f"Saving configuration to {config_path}")
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(os.path.abspath(config_path)), exist_ok=True)
    
    # Determine file format from extension
    _, ext = os.path.splitext(config_path)
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            if ext.lower() == '.json':
                json.dump(config, f, indent=2)
            elif ext.lower() in ('.yaml', '.yml'):
                yaml.safe_dump(config, f, default_flow_style=False)
            else:
                raise ValueError(f"Unsupported configuration file format: {ext}")
    except (TypeError, ValueError) as e:
        raise ValueError(f"Failed to save configuration: {e}")


def merge_configs(base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge two configurations.
    
    Args:
        base_config: Base configuration
        override_config: Override configuration
        
    Returns:
        Merged configuration
    """
    logger.debug("Merging configurations")
    
    merged_config = base_config.copy()
    
    for key, value in override_config.items():
        if key in merged_config and isinstance(merged_config[key], dict) and isinstance(value, dict):
            merged_config[key] = merge_configs(merged_config[key], value)
        else:
            merged_config[key] = value
    
    return merged_config


def get_config_from_env(prefix: str = 'PR_ANALYSIS_') -> Dict[str, Any]:
    """
    Get configuration from environment variables.
    
    Args:
        prefix: Environment variable prefix
        
    Returns:
        Configuration dictionary
    """
    logger.debug(f"Getting configuration from environment variables with prefix {prefix}")
    
    config = {}
    
    for key, value in os.environ.items():
        if key.startswith(prefix):
            # Remove prefix and convert to lowercase
            config_key = key[len(prefix):].lower()
            
            # Convert value to appropriate type
            if value.lower() in ('true', 'yes', '1'):
                config_value = True
            elif value.lower() in ('false', 'no', '0'):
                config_value = False
            elif value.isdigit():
                config_value = int(value)
            elif value.replace('.', '', 1).isdigit() and value.count('.') == 1:
                config_value = float(value)
            else:
                config_value = value
            
            # Set config value
            config[config_key] = config_value
    
    return config


def get_default_config() -> Dict[str, Any]:
    """
    Get default configuration.
    
    Returns:
        Default configuration dictionary
    """
    logger.debug("Getting default configuration")
    
    return {
        'github': {
            'api_url': 'https://api.github.com',
            'token': None,
        },
        'git': {
            'repo_path': None,
        },
        'rules': [
            {
                'rule_path': 'codegen_on_oss.analysis.pr_analysis.rules.code_integrity_rules.CodeStyleRule',
                'config': {
                    'severity': 'medium',
                    'include_patterns': [r'.*\.(py|js|ts|tsx|jsx)$'],
                    'exclude_patterns': [r'.*\.(json|md|txt|csv|yml|yaml)$'],
                    'max_line_length': 100,
                    'check_trailing_whitespace': True,
                    'check_final_newline': True,
                    'warning_threshold': 5,
                },
            },
            {
                'rule_path': 'codegen_on_oss.analysis.pr_analysis.rules.code_integrity_rules.TestCoverageRule',
                'config': {
                    'severity': 'medium',
                    'code_patterns': [r'.*\.(py|js|ts|tsx|jsx)$'],
                    'test_patterns': [r'.*_test\.py$', r'.*\.test\.(js|ts|tsx|jsx)$', r'test_.*\.py$'],
                    'warning_threshold': 2,
                },
            },
            {
                'rule_path': 'codegen_on_oss.analysis.pr_analysis.rules.code_integrity_rules.SecurityVulnerabilityRule',
                'config': {
                    'severity': 'high',
                    'include_patterns': [r'.*\.(py|js|ts|tsx|jsx)$'],
                    'exclude_patterns': [r'.*\.(json|md|txt|csv|yml|yaml)$'],
                    'secret_patterns': [
                        r'password\s*=\s*[\'"][^\'"]+[\'"]',
                        r'secret\s*=\s*[\'"][^\'"]+[\'"]',
                        r'api_key\s*=\s*[\'"][^\'"]+[\'"]',
                        r'token\s*=\s*[\'"][^\'"]+[\'"]',
                    ],
                },
            },
            {
                'rule_path': 'codegen_on_oss.analysis.pr_analysis.rules.parameter_rules.ParameterTypeRule',
                'config': {
                    'severity': 'medium',
                    'check_return_types': True,
                    'warning_threshold': 5,
                },
            },
            {
                'rule_path': 'codegen_on_oss.analysis.pr_analysis.rules.parameter_rules.ParameterValidationRule',
                'config': {
                    'severity': 'medium',
                    'warning_threshold': 5,
                },
            },
            {
                'rule_path': 'codegen_on_oss.analysis.pr_analysis.rules.implementation_rules.PerformanceRule',
                'config': {
                    'severity': 'medium',
                    'warning_threshold': 3,
                },
            },
            {
                'rule_path': 'codegen_on_oss.analysis.pr_analysis.rules.implementation_rules.ErrorHandlingRule',
                'config': {
                    'severity': 'medium',
                    'warning_threshold': 3,
                },
            },
            {
                'rule_path': 'codegen_on_oss.analysis.pr_analysis.rules.implementation_rules.DocumentationRule',
                'config': {
                    'severity': 'low',
                    'warning_threshold': 5,
                },
            },
        ],
        'reporting': {
            'format': 'markdown',
            'output_file': None,
            'post_to_github': True,
        },
        'performance': {
            'timeout': 300,
            'concurrency': 4,
        },
    }

