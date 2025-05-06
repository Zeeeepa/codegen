"""
Rule Engine Module

This module provides the RuleEngine class, which manages and applies analysis rules.
"""

import os
import importlib
import inspect
from typing import Dict, List, Optional, Any, Type, Set, Callable
import logging

# Fix circular import
from .analysis_context import AnalysisContext, AnalysisResult

# Set up logging
logger = logging.getLogger(__name__)


class BaseRule:
    """
    Base class for all analysis rules.
    """
    
    # Class attributes that should be overridden by subclasses
    id: str = "base_rule"
    name: str = "Base Rule"
    description: str = "Base class for all rules"
    category: str = "general"  # "code_integrity", "parameter", "implementation"
    severity: str = "info"  # "error", "warning", "info"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the rule.
        
        Args:
            config: Rule-specific configuration
        """
        self.config = config or {}
    
    def apply(self, context: AnalysisContext) -> List[AnalysisResult]:
        """
        Apply the rule to the analysis context.
        
        Args:
            context: Analysis context
            
        Returns:
            List of analysis results
        """
        raise NotImplementedError("Subclasses must implement apply()")
    
    def is_applicable(self, context: AnalysisContext) -> bool:
        """
        Check if the rule is applicable to the current context.
        
        Args:
            context: Analysis context
            
        Returns:
            True if the rule is applicable, False otherwise
        """
        return True
    
    def create_result(
        self,
        message: str,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
        severity: Optional[str] = None,
        category: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AnalysisResult:
        """
        Create a result object.
        
        Args:
            message: Result message
            file_path: Path to the file
            line_number: Line number
            severity: Severity level (defaults to the rule's severity)
            category: Category (defaults to the rule's category)
            metadata: Additional metadata
            
        Returns:
            Analysis result
        """
        return AnalysisResult(
            rule_id=self.id,
            message=message,
            file_path=file_path,
            line_number=line_number,
            severity=severity or self.severity,
            category=category or self.category,
            metadata=metadata or {}
        )
    
    def get_configuration(self) -> Dict[str, Any]:
        """
        Get rule-specific configuration.
        
        Returns:
            Rule configuration
        """
        return self.config


class RuleEngine:
    """
    Engine for managing and applying analysis rules.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the rule engine.
        
        Args:
            config: Engine configuration
        """
        self.config = config or {}
        self._rules: Dict[str, BaseRule] = {}
        self._rule_categories: Dict[str, List[str]] = {}
        self._rule_priorities: Dict[str, int] = {}
        self._rule_dependencies: Dict[str, List[str]] = {}
    
    def register_rule(self, rule: BaseRule, priority: int = 0, dependencies: Optional[List[str]] = None) -> None:
        """
        Register a rule with the engine.
        
        Args:
            rule: Rule to register
            priority: Rule priority (higher values run first)
            dependencies: List of rule IDs that this rule depends on
        """
        rule_id = rule.id
        
        if rule_id in self._rules:
            logger.warning(f"Rule with ID '{rule_id}' already registered, overwriting")
        
        self._rules[rule_id] = rule
        self._rule_priorities[rule_id] = priority
        self._rule_dependencies[rule_id] = dependencies or []
        
        # Add to category mapping
        category = rule.category
        if category not in self._rule_categories:
            self._rule_categories[category] = []
        if rule_id not in self._rule_categories[category]:
            self._rule_categories[category].append(rule_id)
    
    def load_rules_from_directory(self, directory: str) -> None:
        """
        Load rules from a directory.
        
        Args:
            directory: Directory containing rule modules
        """
        if not os.path.isdir(directory):
            logger.error(f"Directory '{directory}' does not exist")
            return
        
        # Get all Python files in the directory
        for filename in os.listdir(directory):
            if filename.endswith(".py") and not filename.startswith("__"):
                module_path = os.path.join(directory, filename)
                module_name = os.path.splitext(filename)[0]
                
                try:
                    # Import the module
                    spec = importlib.util.spec_from_file_location(module_name, module_path)
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        
                        # Find all rule classes in the module
                        for name, obj in inspect.getmembers(module):
                            if (inspect.isclass(obj) and 
                                issubclass(obj, BaseRule) and 
                                obj is not BaseRule):
                                # Create an instance of the rule and register it
                                rule = obj()
                                self.register_rule(rule)
                                logger.info(f"Loaded rule '{rule.id}' from {filename}")
                except Exception as e:
                    logger.error(f"Error loading rules from {filename}: {e}")
    
    def get_rule(self, rule_id: str) -> Optional[BaseRule]:
        """
        Get a rule by ID.
        
        Args:
            rule_id: Rule ID
            
        Returns:
            Rule or None if not found
        """
        return self._rules.get(rule_id)
    
    def get_rules(self) -> List[BaseRule]:
        """
        Get all registered rules.
        
        Returns:
            List of rules
        """
        return list(self._rules.values())
    
    def get_rules_by_category(self, category: str) -> List[BaseRule]:
        """
        Get rules by category.
        
        Args:
            category: Rule category
            
        Returns:
            List of rules in the specified category
        """
        rule_ids = self._rule_categories.get(category, [])
        return [self._rules[rule_id] for rule_id in rule_ids if rule_id in self._rules]
    
    def _get_sorted_rule_ids(self, rule_ids: List[str]) -> List[str]:
        """
        Sort rule IDs by priority and dependencies.
        
        Args:
            rule_ids: List of rule IDs
            
        Returns:
            Sorted list of rule IDs
        """
        # Create a dependency graph
        graph: Dict[str, Set[str]] = {rule_id: set(self._rule_dependencies.get(rule_id, [])) for rule_id in rule_ids}
        
        # Topological sort
        sorted_ids: List[str] = []
        visited: Set[str] = set()
        temp_visited: Set[str] = set()
        
        def visit(rule_id: str) -> None:
            if rule_id in temp_visited:
                # Circular dependency detected
                logger.warning(f"Circular dependency detected for rule '{rule_id}'")
                return
            if rule_id in visited:
                return
            
            temp_visited.add(rule_id)
            
            # Visit dependencies
            for dep_id in graph.get(rule_id, set()):
                if dep_id in rule_ids:  # Only consider dependencies that are in the current set
                    visit(dep_id)
            
            temp_visited.remove(rule_id)
            visited.add(rule_id)
            sorted_ids.append(rule_id)
        
        # Sort by priority first (higher priority first)
        priority_sorted = sorted(rule_ids, key=lambda r: self._rule_priorities.get(r, 0), reverse=True)
        
        # Then apply topological sort for dependencies
        for rule_id in priority_sorted:
            if rule_id not in visited:
                visit(rule_id)
        
        return sorted_ids
    
    def apply_rules(self, context: AnalysisContext) -> List[AnalysisResult]:
        """
        Apply all rules to the analysis context.
        
        Args:
            context: Analysis context
            
        Returns:
            List of analysis results
        """
        results: List[AnalysisResult] = []
        
        # Get all rule IDs
        rule_ids = list(self._rules.keys())
        
        # Sort rules by priority and dependencies
        sorted_rule_ids = self._get_sorted_rule_ids(rule_ids)
        
        # Apply each rule
        for rule_id in sorted_rule_ids:
            rule = self._rules[rule_id]
            
            # Check if the rule is applicable
            if rule.is_applicable(context):
                try:
                    # Apply the rule
                    rule_results = rule.apply(context)
                    
                    # Add results to the context and the result list
                    for result in rule_results:
                        context.add_result(result)
                        results.append(result)
                except Exception as e:
                    logger.error(f"Error applying rule '{rule_id}': {e}")
                    # Create an error result
                    error_result = AnalysisResult(
                        rule_id="rule_engine",
                        message=f"Error applying rule '{rule_id}': {e}",
                        severity="error",
                        category="rule_engine"
                    )
                    context.add_result(error_result)
                    results.append(error_result)
        
        return results
    
    def apply_rule_category(self, category: str, context: AnalysisContext) -> List[AnalysisResult]:
        """
        Apply rules of a specific category.
        
        Args:
            category: Rule category
            context: Analysis context
            
        Returns:
            List of analysis results
        """
        results: List[AnalysisResult] = []
        
        # Get rule IDs for the category
        rule_ids = self._rule_categories.get(category, [])
        
        # Sort rules by priority and dependencies
        sorted_rule_ids = self._get_sorted_rule_ids(rule_ids)
        
        # Apply each rule
        for rule_id in sorted_rule_ids:
            if rule_id in self._rules:
                rule = self._rules[rule_id]
                
                # Check if the rule is applicable
                if rule.is_applicable(context):
                    try:
                        # Apply the rule
                        rule_results = rule.apply(context)
                        
                        # Add results to the context and the result list
                        for result in rule_results:
                            context.add_result(result)
                            results.append(result)
                    except Exception as e:
                        logger.error(f"Error applying rule '{rule_id}': {e}")
                        # Create an error result
                        error_result = AnalysisResult(
                            rule_id="rule_engine",
                            message=f"Error applying rule '{rule_id}': {e}",
                            severity="error",
                            category="rule_engine"
                        )
                        context.add_result(error_result)
                        results.append(error_result)
        
        return results
    
    def apply_single_rule(self, rule_id: str, context: AnalysisContext) -> List[AnalysisResult]:
        """
        Apply a single rule.
        
        Args:
            rule_id: Rule ID
            context: Analysis context
            
        Returns:
            List of analysis results
        """
        results: List[AnalysisResult] = []
        
        if rule_id in self._rules:
            rule = self._rules[rule_id]
            
            # Check if the rule is applicable
            if rule.is_applicable(context):
                try:
                    # Apply the rule
                    rule_results = rule.apply(context)
                    
                    # Add results to the context and the result list
                    for result in rule_results:
                        context.add_result(result)
                        results.append(result)
                except Exception as e:
                    logger.error(f"Error applying rule '{rule_id}': {e}")
                    # Create an error result
                    error_result = AnalysisResult(
                        rule_id="rule_engine",
                        message=f"Error applying rule '{rule_id}': {e}",
                        severity="error",
                        category="rule_engine"
                    )
                    context.add_result(error_result)
                    results.append(error_result)
        else:
            logger.error(f"Rule '{rule_id}' not found")
            # Create an error result
            error_result = AnalysisResult(
                rule_id="rule_engine",
                message=f"Rule '{rule_id}' not found",
                severity="error",
                category="rule_engine"
            )
            context.add_result(error_result)
            results.append(error_result)
        
        return results
    
    def get_results(self, context: AnalysisContext) -> List[AnalysisResult]:
        """
        Get all rule application results.
        
        Args:
            context: Analysis context
            
        Returns:
            List of analysis results
        """
        return context.get_results()
    
    def get_results_by_severity(self, context: AnalysisContext, severity: str) -> List[AnalysisResult]:
        """
        Get results filtered by severity.
        
        Args:
            context: Analysis context
            severity: Severity level
            
        Returns:
            List of analysis results with the specified severity
        """
        return context.get_results_by_severity(severity)
    
    def get_results_by_category(self, context: AnalysisContext, category: str) -> List[AnalysisResult]:
        """
        Get results filtered by category.
        
        Args:
            context: Analysis context
            category: Result category
            
        Returns:
            List of analysis results in the specified category
        """
        return context.get_results_by_category(category)
