"""Rule registry for PR static analysis.

This module provides a registry for managing available rules.
"""

import importlib
import inspect
import logging
import os
import pkgutil
from typing import Optional

from pr_static_analysis.rules.base.base_rule import BaseRule, RuleCategory

logger = logging.getLogger(__name__)


class RuleRegistry:
    """Registry for managing available rules.

    This class provides methods for registering, discovering, and retrieving rules.

    Attributes:
        rules (Dict[str, Type[BaseRule]]): Dictionary mapping rule IDs to rule classes
    """

    def __init__(self):
        """Initialize the rule registry."""
        self.rules: dict[str, type[BaseRule]] = {}

    def register(self, rule_class: type[BaseRule]) -> None:
        """Register a rule class.

        Args:
            rule_class: The rule class to register

        Raises:
            ValueError: If a rule with the same ID is already registered
        """
        rule_id = rule_class.id.__get__(None, rule_class)  # Get the property value without an instance
        if rule_id in self.rules:
            msg = f"Rule with ID '{rule_id}' is already registered"
            raise ValueError(msg)

        self.rules[rule_id] = rule_class
        logger.debug(f"Registered rule: {rule_id}")

    def get_rule(self, rule_id: str) -> Optional[type[BaseRule]]:
        """Get a rule class by ID.

        Args:
            rule_id: The ID of the rule to get

        Returns:
            The rule class, or None if not found
        """
        return self.rules.get(rule_id)

    def get_all_rules(self) -> dict[str, type[BaseRule]]:
        """Get all registered rules.

        Returns:
            Dictionary mapping rule IDs to rule classes
        """
        return self.rules.copy()

    def get_rules_by_category(self, category: RuleCategory) -> dict[str, type[BaseRule]]:
        """Get all rules in a specific category.

        Args:
            category: The category to filter by

        Returns:
            Dictionary mapping rule IDs to rule classes
        """
        return {rule_id: rule_class for rule_id, rule_class in self.rules.items() if rule_class.category == category}

    def get_enabled_rules(self) -> dict[str, type[BaseRule]]:
        """Get all enabled rules.

        Returns:
            Dictionary mapping rule IDs to rule classes
        """
        return {
            rule_id: rule_class
            for rule_id, rule_class in self.rules.items()
            if rule_class.enabled.__get__(None, rule_class)  # Get the property value without an instance
        }

    def discover_rules(self, package_name: str) -> None:
        """Discover and register rules from a package.

        This method recursively searches for rule classes in the specified package
        and registers them.

        Args:
            package_name: The name of the package to search
        """
        package = importlib.import_module(package_name)
        package_path = os.path.dirname(package.__file__ or "")

        for _, module_name, is_pkg in pkgutil.iter_modules([package_path]):
            full_module_name = f"{package_name}.{module_name}"

            if is_pkg:
                # Recursively discover rules in subpackages
                self.discover_rules(full_module_name)
            else:
                try:
                    module = importlib.import_module(full_module_name)

                    # Find all rule classes in the module
                    for name, obj in inspect.getmembers(module):
                        if inspect.isclass(obj) and issubclass(obj, BaseRule) and obj != BaseRule and not inspect.isabstract(obj):
                            self.register(obj)

                except (ImportError, AttributeError) as e:
                    logger.warning(f"Error importing module {full_module_name}: {e}")

    def resolve_dependencies(self, rule_ids: list[str]) -> list[str]:
        """Resolve dependencies for a list of rules.

        This method returns a list of rule IDs in the order they should be executed,
        ensuring that dependencies are executed before the rules that depend on them.

        Args:
            rule_ids: List of rule IDs to resolve dependencies for

        Returns:
            List of rule IDs in dependency order

        Raises:
            ValueError: If there is a circular dependency
        """
        # Build dependency graph
        graph: dict[str, set[str]] = {}
        for rule_id in rule_ids:
            rule_class = self.get_rule(rule_id)
            if rule_class:
                # Get the dependencies property value without an instance
                deps = rule_class.dependencies.__get__(None, rule_class)
                graph[rule_id] = deps

        # Topological sort
        result = []
        temp_marks = set()
        perm_marks = set()

        def visit(node: str) -> None:
            if node in perm_marks:
                return
            if node in temp_marks:
                msg = f"Circular dependency detected involving rule '{node}'"
                raise ValueError(msg)

            temp_marks.add(node)

            for dep in graph.get(node, set()):
                if dep in graph:
                    visit(dep)

            temp_marks.remove(node)
            perm_marks.add(node)
            result.append(node)

        for node in graph:
            if node not in perm_marks:
                visit(node)

        return result


# Create a global rule registry instance
rule_registry = RuleRegistry()
