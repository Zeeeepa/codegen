"""
Rule Engine Module

This module provides the engine for applying analysis rules.
"""

import logging
from typing import List, Dict, Any, Optional

from ..rules.base_rule import BaseRule, AnalysisResult

logger = logging.getLogger(__name__)


class RuleEngine:
    """Engine for applying analysis rules."""
    
    def __init__(self, rules: Optional[List[BaseRule]] = None):
        """
        Initialize a new rule engine.
        
        Args:
            rules: List of rules to apply
        """
        self.rules = rules or []
        
    def register_rule(self, rule: BaseRule) -> None:
        """
        Register a new rule.
        
        Args:
            rule: Rule to register
        """
        self.rules.append(rule)
        
    def apply_rules(self, context) -> List[AnalysisResult]:
        """
        Apply all rules to the context and return results.
        
        Args:
            context: Context to apply rules to
            
        Returns:
            List of rule results
        """
        results = []
        
        # Apply each rule
        for rule in self.rules:
            try:
                logger.info(f"Applying rule: {rule.rule_id}")
                rule_results = rule.apply(context)
                results.extend(rule_results)
                logger.info(f"Rule {rule.rule_id} produced {len(rule_results)} results")
            except Exception as e:
                # Log the error and continue with the next rule
                logger.error(f"Error applying rule {rule.rule_id}: {e}", exc_info=True)
                
                # Add an error result
                results.append(
                    AnalysisResult(
                        rule_id=rule.rule_id,
                        severity="error",
                        message=f"Error applying rule: {e}",
                    )
                )
        
        return results
    
    def get_rule_by_id(self, rule_id: str) -> Optional[BaseRule]:
        """
        Get a rule by its ID.
        
        Args:
            rule_id: ID of the rule to get
            
        Returns:
            Rule with the given ID, or None if not found
        """
        for rule in self.rules:
            if rule.rule_id == rule_id:
                return rule
        return None
    
    def get_rules_by_category(self, category: str) -> List[BaseRule]:
        """
        Get rules by category.
        
        Args:
            category: Category of rules to get
            
        Returns:
            List of rules in the given category
        """
        return [rule for rule in self.rules if rule.category == category]
    
    def get_all_rules(self) -> List[BaseRule]:
        """
        Get all registered rules.
        
        Returns:
            List of all rules
        """
        return self.rules
    
    def get_rule_categories(self) -> List[str]:
        """
        Get all rule categories.
        
        Returns:
            List of all rule categories
        """
        categories = set()
        for rule in self.rules:
            categories.add(rule.category)
        return list(categories)
    
    def get_rule_documentation(self) -> List[Dict[str, str]]:
        """
        Get documentation for all rules.
        
        Returns:
            List of rule documentation dictionaries
        """
        return [rule.get_documentation() for rule in self.rules]

