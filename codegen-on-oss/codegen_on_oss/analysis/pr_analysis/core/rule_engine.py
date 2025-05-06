"""
Rule Engine

Engine for applying analysis rules to pull requests.
"""

import logging
from typing import Dict, List, Optional, Any, Type

from codegen_on_oss.analysis.pr_analysis.core.analysis_context import AnalysisContext
from codegen_on_oss.analysis.pr_analysis.rules.base_rule import BaseRule

logger = logging.getLogger(__name__)


class RuleEngine:
    """
    Engine for applying analysis rules to pull requests.
    
    This class manages the registration, configuration, and execution of
    analysis rules on pull requests.
    """
    
    def __init__(self):
        """Initialize the rule engine."""
        self.rules: List[BaseRule] = []
        self.rule_registry: Dict[str, Type[BaseRule]] = {}
    
    def register_rule(self, rule_class: Type[BaseRule]) -> None:
        """
        Register a rule class with the engine.
        
        Args:
            rule_class: The rule class to register
        """
        rule_id = rule_class.rule_id
        if rule_id in self.rule_registry:
            logger.warning(f"Rule with ID '{rule_id}' already registered. Overwriting.")
        
        self.rule_registry[rule_id] = rule_class
        logger.debug(f"Registered rule: {rule_id}")
    
    def create_rule_instance(self, rule_id: str, config: Optional[Dict[str, Any]] = None) -> BaseRule:
        """
        Create an instance of a rule with the given ID and configuration.
        
        Args:
            rule_id: The ID of the rule to create
            config: Optional configuration for the rule
            
        Returns:
            An instance of the rule
            
        Raises:
            ValueError: If the rule ID is not registered
        """
        if rule_id not in self.rule_registry:
            raise ValueError(f"Rule with ID '{rule_id}' not registered")
        
        rule_class = self.rule_registry[rule_id]
        return rule_class(config or {})
    
    def add_rule(self, rule: BaseRule) -> None:
        """
        Add a rule instance to the engine.
        
        Args:
            rule: The rule instance to add
        """
        self.rules.append(rule)
        logger.debug(f"Added rule instance: {rule.rule_id}")
    
    def configure_rules(self, rules_config: Dict[str, Dict[str, Any]]) -> None:
        """
        Configure rules based on the provided configuration.
        
        Args:
            rules_config: A dictionary mapping rule IDs to their configurations
        """
        self.rules = []
        
        for rule_id, config in rules_config.items():
            try:
                rule = self.create_rule_instance(rule_id, config)
                self.add_rule(rule)
            except ValueError as e:
                logger.warning(f"Skipping rule '{rule_id}': {e}")
    
    def run_rules(self, context: AnalysisContext) -> Dict[str, Any]:
        """
        Run all registered rules on the given context.
        
        Args:
            context: The analysis context to run rules on
            
        Returns:
            A dictionary containing the results of all rules
        """
        results = {}
        
        for rule in self.rules:
            try:
                logger.info(f"Running rule: {rule.rule_id}")
                rule_result = rule.analyze(context)
                results[rule.rule_id] = rule_result
                logger.info(f"Rule {rule.rule_id} completed with {len(rule_result.get('issues', []))} issues")
            except Exception as e:
                logger.exception(f"Error running rule {rule.rule_id}: {e}")
                results[rule.rule_id] = {
                    "error": str(e),
                    "issues": []
                }
        
        return results

