"""
Integration module for the CodeIntegrityAnalyzer with the main CodeAnalyzer class.

This module provides functions to integrate the CodeIntegrityAnalyzer with the
main CodeAnalyzer class, allowing for seamless code integrity analysis.
"""

from typing import Any, Dict, Optional

from graph_sitter.core.codebase import Codebase

from codegen_on_oss.analysis.analysis import CodeAnalyzer
from codegen_on_oss.analysis.code_integrity_analyzer import CodeIntegrityAnalyzer


def analyze_code_integrity(
    codebase: Codebase, config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Analyze code integrity for a codebase.

    Args:
        codebase: The codebase to analyze
        config: Optional configuration options for the analyzer

    Returns:
        A dictionary with analysis results
    """
    analyzer = CodeIntegrityAnalyzer(codebase, config)
    return analyzer.analyze()


# Extend the CodeAnalyzer class with a method to analyze code integrity
def _add_code_integrity_analysis_to_code_analyzer():
    """
    Add code integrity analysis method to the CodeAnalyzer class.
    """

    def analyze_code_integrity_method(
        self, config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze code integrity for the current codebase.

        Args:
            config: Optional configuration options for the analyzer

        Returns:
            A dictionary with analysis results
        """
        self.initialize()
        analyzer = CodeIntegrityAnalyzer(self.codebase, config)
        return analyzer.analyze()

    # Add the method to the CodeAnalyzer class
    CodeAnalyzer.analyze_code_integrity = analyze_code_integrity_method


# Add the code integrity analysis method to the CodeAnalyzer class
_add_code_integrity_analysis_to_code_analyzer()

