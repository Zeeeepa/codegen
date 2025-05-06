"""PR static analysis engine.

This module provides the main engine for analyzing PRs using the rule system.
"""

import logging
from typing import Any, Optional

from pr_static_analysis.rules.base import (
    RuleResult,
    RuleSeverity,
    rule_config,
    rule_registry,
)

logger = logging.getLogger(__name__)


class PRStaticAnalyzer:
    """Engine for analyzing PRs using the rule system.

    This class provides methods for analyzing PRs and generating reports.

    Attributes:
        rules (Dict[str, BaseRule]): Dictionary mapping rule IDs to rule instances
    """

    def __init__(self, config_file: Optional[str] = None):
        """Initialize the PR static analyzer.

        Args:
            config_file: Optional path to a configuration file
        """
        # Load configuration if provided
        if config_file:
            rule_config.load_config_file(config_file)

        # Create rule instances
        self.rules = rule_config.create_all_enabled_rule_instances()
        logger.info(f"Initialized PR static analyzer with {len(self.rules)} rules")

    def analyze(self, context: dict[str, Any]) -> list[RuleResult]:
        """Analyze a PR for issues.

        Args:
            context: Context information for the analysis, including:
                - codebase: The codebase object
                - pr: The PR object
                - files: List of files in the PR
                - diff: The diff of the PR
                - config: Global configuration options

        Returns:
            A list of RuleResult objects representing issues found
        """
        # Get the order in which to execute rules based on dependencies
        rule_ids = rule_registry.resolve_dependencies(list(self.rules.keys()))

        # Execute rules in dependency order
        results: list[RuleResult] = []
        rule_results: dict[str, list[RuleResult]] = {}

        for rule_id in rule_ids:
            rule = self.rules.get(rule_id)
            if not rule:
                continue

            # Check if the rule is applicable to this context
            if not rule.is_applicable(context):
                logger.debug(f"Rule '{rule_id}' is not applicable to this context")
                continue

            # Add results from dependent rules to the context
            context["results"] = rule_results

            # Execute the rule
            logger.debug(f"Executing rule '{rule_id}'")
            try:
                rule_result = rule.analyze(context)
                results.extend(rule_result)
                rule_results[rule_id] = rule_result
            except Exception as e:
                logger.exception(f"Error executing rule '{rule_id}': {e}")

        return results

    def generate_report(self, results: list[RuleResult]) -> dict[str, Any]:
        """Generate a report from the analysis results.

        Args:
            results: List of RuleResult objects

        Returns:
            A dictionary containing the report data
        """
        # Group results by severity
        results_by_severity: dict[RuleSeverity, list[RuleResult]] = {}
        for result in results:
            if result.severity not in results_by_severity:
                results_by_severity[result.severity] = []
            results_by_severity[result.severity].append(result)

        # Group results by rule
        results_by_rule: dict[str, list[RuleResult]] = {}
        for result in results:
            if result.rule_id not in results_by_rule:
                results_by_rule[result.rule_id] = []
            results_by_rule[result.rule_id].append(result)

        # Group results by file
        results_by_file: dict[str, list[RuleResult]] = {}
        for result in results:
            if result.filepath not in results_by_file:
                results_by_file[result.filepath] = []
            results_by_file[result.filepath].append(result)

        # Create summary
        summary = {
            "total_issues": len(results),
            "issues_by_severity": {severity: len(issues) for severity, issues in results_by_severity.items() if issues},
            "issues_by_rule": {rule_id: len(issues) for rule_id, issues in results_by_rule.items()},
            "issues_by_file": {filepath: len(issues) for filepath, issues in results_by_file.items()},
        }

        # Create report
        report = {
            "summary": summary,
            "results_by_severity": results_by_severity,
            "results_by_rule": results_by_rule,
            "results_by_file": results_by_file,
            "all_results": [result.to_dict() for result in results],
        }

        return report
