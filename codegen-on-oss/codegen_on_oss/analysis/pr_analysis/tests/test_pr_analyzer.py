"""
Test PR Analyzer

This module demonstrates how to use the PR analyzer.
"""

import os
import sys
import logging
from typing import List

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Fix imports to use absolute imports
from codegen_on_oss.analysis.pr_analysis.core.pr_analyzer import PRAnalyzer
from codegen_on_oss.analysis.pr_analysis.core.analysis_context import AnalysisContext, AnalysisResult
from codegen_on_oss.analysis.pr_analysis.core.rule_engine import BaseRule

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SampleRule(BaseRule):
    """
    A sample rule for testing.
    """
    
    id = "sample_rule"
    name = "Sample Rule"
    description = "A sample rule for testing"
    category = "test"
    severity = "info"
    
    def apply(self, context: AnalysisContext) -> List[AnalysisResult]:
        """
        Apply the rule to the analysis context.
        
        Args:
            context: Analysis context
            
        Returns:
            List of analysis results
        """
        results = []
        
        # Create a sample result
        result = self.create_result(
            message="This is a sample result",
            file_path="sample.py",
            line_number=42
        )
        results.append(result)
        
        return results


def test_pr_analyzer():
    """
    Test the PR analyzer.
    """
    logger.info("Testing PR analyzer")
    
    # Create a PR analyzer
    analyzer = PRAnalyzer()
    
    # Register a sample rule
    analyzer.register_rule(SampleRule())
    
    # Analyze a PR
    context = analyzer.analyze_pr(
        pr_number=123,
        repo="test/repo"
    )
    
    # Get the results
    results = analyzer.get_results(context)
    
    # Print the results
    logger.info(f"Found {len(results)} results:")
    for result in results:
        logger.info(f"  {result.rule_id}: {result.message} ({result.severity})")
    
    # Check if there are any errors or warnings
    if analyzer.has_errors(context):
        logger.warning(f"Found {analyzer.get_error_count(context)} errors")
    if analyzer.has_warnings(context):
        logger.warning(f"Found {analyzer.get_warning_count(context)} warnings")
    
    logger.info("PR analyzer test completed")


if __name__ == "__main__":
    test_pr_analyzer()
