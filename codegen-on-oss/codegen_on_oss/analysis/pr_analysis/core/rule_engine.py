"""
Rule engine for PR analysis.

This module provides the RuleEngine class, which is responsible for
loading and running analysis rules.
"""

import importlib
import logging
from typing import Any, Dict, List, Type

from codegen_on_oss.analysis.pr_analysis.core.analysis_context import AnalysisContext
from codegen_on_oss.analysis.pr_analysis.rules.base_rule import BaseRule

logger = logging.getLogger(__name__)


class RuleEngine:
    """
    Engine for applying analysis rules.

    This class is responsible for loading and running analysis rules.

    Attributes:
        context: Analysis context
        rules: Dictionary of loaded rules
    """

    def __init__(self, context: AnalysisContext):
        """
        Initialize the rule engine.

        Args:
            context: Analysis context
        """
        self.context = context
        self.rules: Dict[str, BaseRule] = {}

    def load_rule(self, rule_class: Type[BaseRule]) -> BaseRule:
        """
        Load a rule.

        Args:
            rule_class: Rule class to load

        Returns:
            Loaded rule instance
        """
        rule = rule_class(self.context)
        self.rules[rule.rule_id] = rule
        return rule

    def load_rule_from_path(self, rule_path: str) -> BaseRule:
        """
        Load a rule from a module path.

        Args:
            rule_path: Module path to the rule class

        Returns:
            Loaded rule instance

        Raises:
            ImportError: If the rule cannot be imported
            ValueError: If the rule is not a BaseRule subclass
        """
        try:
            module_path, class_name = rule_path.rsplit(".", 1)
            module = importlib.import_module(module_path)
            rule_class = getattr(module, class_name)

            if not issubclass(rule_class, BaseRule):
                raise ValueError(f"Rule {rule_path} is not a BaseRule subclass")

            return self.load_rule(rule_class)
        except (ImportError, AttributeError) as e:
            logger.error(f"Failed to load rule {rule_path}: {e}")
            raise ImportError(f"Failed to load rule {rule_path}: {e}")

    def load_rules_from_config(self, rules_config: List[Dict[str, Any]]) -> None:
        """
        Load rules from configuration.

        Args:
            rules_config: List of rule configurations
        """
        for rule_config in rules_config:
            rule_path = rule_config.get("rule_path")
            if not rule_path:
                logger.warning(f"Rule configuration missing rule_path: {rule_config}")
                continue

            try:
                rule = self.load_rule_from_path(rule_path)
                if "config" in rule_config:
                    rule.configure(rule_config["config"])
            except (ImportError, ValueError) as e:
                logger.error(f"Failed to load rule {rule_path}: {e}")

    def run_rule(self, rule_id: str) -> Dict[str, Any]:
        """
        Run a specific rule.

        Args:
            rule_id: ID of the rule to run

        Returns:
            Rule result

        Raises:
            ValueError: If the rule is not loaded
        """
        if rule_id not in self.rules:
            raise ValueError(f"Rule {rule_id} is not loaded")

        rule = self.rules[rule_id]
        logger.info(f"Running rule {rule_id}: {rule.name}")

        try:
            result = rule.run()
            logger.info(f"Rule {rule_id} completed with status: {result['status']}")
            return result
        except Exception as e:
            logger.error(f"Error running rule {rule_id}: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Error running rule: {str(e)}",
                "rule_id": rule_id,
                "rule_name": rule.name,
            }

    def run_all_rules(self) -> Dict[str, Dict[str, Any]]:
        """
        Run all loaded rules.

        Returns:
            Dictionary mapping rule IDs to rule results
        """
        results = {}
        for rule_id in self.rules:
            results[rule_id] = self.run_rule(rule_id)
        return results

