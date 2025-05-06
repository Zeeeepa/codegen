"""
Rule engine for PR analysis.

This module provides the RuleEngine class, which is responsible for loading,
configuring, and applying analysis rules to pull requests.
"""

import importlib
import logging
from typing import Dict, List, Optional, Type, Any

from codegen_on_oss.analysis.pr_analysis.core.analysis_context import AnalysisContext
from codegen_on_oss.analysis.pr_analysis.rules.base_rule import BaseRule


logger = logging.getLogger(__name__)


class RuleEngine:
    """
    Engine for applying analysis rules to pull requests.
    
    This class is responsible for loading, configuring, and applying analysis rules
    to pull requests. It manages the rule lifecycle and provides methods for
    running rules and collecting results.
    
    Attributes:
        rules: Dictionary of rule instances by rule ID
        context: Analysis context
    """
    
    def __init__(self, context: AnalysisContext):
        """
        Initialize the rule engine.
        
        Args:
            context: Analysis context
        """
        self.rules: Dict[str, BaseRule] = {}
        self.context = context
    
    def load_rule(self, rule_class: Type[BaseRule]) -> BaseRule:
        """
        Load a rule into the engine.
        
        Args:
            rule_class: Rule class to load
            
        Returns:
            Loaded rule instance
            
        Raises:
            ValueError: If a rule with the same ID is already loaded
        """
        rule = rule_class(self.context)
        if rule.rule_id in self.rules:
            raise ValueError(f"Rule with ID '{rule.rule_id}' is already loaded")
        
        self.rules[rule.rule_id] = rule
        return rule
    
    def load_rule_by_name(self, rule_path: str) -> BaseRule:
        """
        Load a rule by its module path and class name.
        
        Args:
            rule_path: Full path to the rule class (e.g., 'module.submodule.RuleClass')
            
        Returns:
            Loaded rule instance
            
        Raises:
            ImportError: If the rule module cannot be imported
            AttributeError: If the rule class cannot be found in the module
        """
        module_path, class_name = rule_path.rsplit('.', 1)
        try:
            module = importlib.import_module(module_path)
            rule_class = getattr(module, class_name)
            return self.load_rule(rule_class)
        except ImportError:
            logger.error(f"Failed to import rule module: {module_path}")
            raise
        except AttributeError:
            logger.error(f"Failed to find rule class '{class_name}' in module '{module_path}'")
            raise
    
    def load_rules_from_config(self, rules_config: List[Dict[str, Any]]) -> List[BaseRule]:
        """
        Load rules from configuration.
        
        Args:
            rules_config: List of rule configurations
            
        Returns:
            List of loaded rule instances
        """
        loaded_rules = []
        for rule_config in rules_config:
            rule_path = rule_config.get('rule_path')
            if not rule_path:
                logger.warning(f"Skipping rule with missing 'rule_path': {rule_config}")
                continue
            
            try:
                rule = self.load_rule_by_name(rule_path)
                rule.configure(rule_config.get('config', {}))
                loaded_rules.append(rule)
            except (ImportError, AttributeError) as e:
                logger.error(f"Failed to load rule '{rule_path}': {e}")
        
        return loaded_rules
    
    def get_rule(self, rule_id: str) -> Optional[BaseRule]:
        """
        Get a rule by its ID.
        
        Args:
            rule_id: Rule ID
            
        Returns:
            Rule instance or None if not found
        """
        return self.rules.get(rule_id)
    
    def run_rule(self, rule_id: str) -> Dict[str, Any]:
        """
        Run a specific rule.
        
        Args:
            rule_id: Rule ID
            
        Returns:
            Rule results
            
        Raises:
            ValueError: If the rule is not found
        """
        rule = self.get_rule(rule_id)
        if not rule:
            raise ValueError(f"Rule with ID '{rule_id}' not found")
        
        logger.info(f"Running rule: {rule_id}")
        return rule.run()
    
    def run_all_rules(self) -> Dict[str, Dict[str, Any]]:
        """
        Run all loaded rules.
        
        Returns:
            Dictionary of rule results by rule ID
        """
        results = {}
        for rule_id, rule in self.rules.items():
            try:
                results[rule_id] = rule.run()
            except Exception as e:
                logger.error(f"Error running rule '{rule_id}': {e}", exc_info=True)
                results[rule_id] = {'error': str(e)}
        
        return results

