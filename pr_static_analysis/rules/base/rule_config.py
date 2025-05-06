"""
Configuration system for PR static analysis rules.

This module provides utilities for loading and managing rule configurations.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional, Set, Type

import yaml

from pr_static_analysis.rules.base.base_rule import BaseRule, RuleCategory, RuleSeverity
from pr_static_analysis.rules.base.rule_registry import rule_registry

logger = logging.getLogger(__name__)


class RuleConfig:
    """
    Configuration manager for PR static analysis rules.
    
    This class provides methods for loading and managing rule configurations.
    
    Attributes:
        global_config (Dict[str, Any]): Global configuration options
        rule_configs (Dict[str, Dict[str, Any]]): Configuration options for each rule
        enabled_rules (Set[str]): Set of enabled rule IDs
        disabled_rules (Set[str]): Set of disabled rule IDs
    """
    
    def __init__(self):
        """Initialize the rule configuration manager."""
        self.global_config: Dict[str, Any] = {}
        self.rule_configs: Dict[str, Dict[str, Any]] = {}
        self.enabled_rules: Set[str] = set()
        self.disabled_rules: Set[str] = set()
    
    def load_config_file(self, config_file: str) -> None:
        """
        Load configuration from a file.
        
        Args:
            config_file: Path to the configuration file (YAML or JSON)
        
        Raises:
            ValueError: If the configuration file is invalid
        """
        if not os.path.exists(config_file):
            raise ValueError(f"Configuration file '{config_file}' does not exist")
        
        try:
            with open(config_file, "r") as f:
                if config_file.endswith(".yaml") or config_file.endswith(".yml"):
                    config = yaml.safe_load(f)
                elif config_file.endswith(".json"):
                    config = json.load(f)
                else:
                    raise ValueError(
                        f"Unsupported configuration file format: {config_file}"
                    )
            
            self.load_config(config)
        
        except (yaml.YAMLError, json.JSONDecodeError) as e:
            raise ValueError(f"Error parsing configuration file '{config_file}': {e}")
    
    def load_config(self, config: Dict[str, Any]) -> None:
        """
        Load configuration from a dictionary.
        
        Args:
            config: Configuration dictionary
        """
        # Load global configuration
        self.global_config = config.get("global", {})
        
        # Load rule configurations
        rule_configs = config.get("rules", {})
        for rule_id, rule_config in rule_configs.items():
            self.rule_configs[rule_id] = rule_config
            
            # Track enabled/disabled rules
            if rule_config.get("enabled") is True:
                self.enabled_rules.add(rule_id)
            elif rule_config.get("enabled") is False:
                self.disabled_rules.add(rule_id)
        
        # Load enabled/disabled rule lists
        self.enabled_rules.update(config.get("enabled_rules", []))
        self.disabled_rules.update(config.get("disabled_rules", []))
        
        logger.info(f"Loaded configuration with {len(self.rule_configs)} rule configs")
    
    def is_rule_enabled(self, rule_id: str) -> bool:
        """
        Check if a rule is enabled.
        
        Args:
            rule_id: The ID of the rule to check
        
        Returns:
            True if the rule is enabled, False otherwise
        """
        if rule_id in self.disabled_rules:
            return False
        if rule_id in self.enabled_rules:
            return True
        
        # Fall back to the rule's default enabled state
        rule_class = rule_registry.get_rule(rule_id)
        return rule_class.enabled if rule_class else False
    
    def get_rule_config(self, rule_id: str) -> Dict[str, Any]:
        """
        Get the configuration for a rule.
        
        Args:
            rule_id: The ID of the rule to get configuration for
        
        Returns:
            Configuration dictionary for the rule
        """
        return self.rule_configs.get(rule_id, {})
    
    def get_enabled_rule_ids(self) -> List[str]:
        """
        Get the IDs of all enabled rules.
        
        Returns:
            List of enabled rule IDs
        """
        return [
            rule_id
            for rule_id in rule_registry.get_all_rules().keys()
            if self.is_rule_enabled(rule_id)
        ]
    
    def create_rule_instance(self, rule_id: str) -> Optional[BaseRule]:
        """
        Create an instance of a rule with its configuration.
        
        Args:
            rule_id: The ID of the rule to create
        
        Returns:
            An instance of the rule, or None if the rule is not found or disabled
        """
        if not self.is_rule_enabled(rule_id):
            return None
        
        rule_class = rule_registry.get_rule(rule_id)
        if not rule_class:
            return None
        
        rule_config = self.get_rule_config(rule_id)
        return rule_class(rule_config)
    
    def create_all_enabled_rule_instances(self) -> Dict[str, BaseRule]:
        """
        Create instances of all enabled rules.
        
        Returns:
            Dictionary mapping rule IDs to rule instances
        """
        rule_instances = {}
        
        for rule_id in self.get_enabled_rule_ids():
            rule_instance = self.create_rule_instance(rule_id)
            if rule_instance:
                rule_instances[rule_id] = rule_instance
        
        return rule_instances


# Create a global rule configuration instance
rule_config = RuleConfig()

