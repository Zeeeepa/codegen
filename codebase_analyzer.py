#!/usr/bin/env python3
"""Comprehensive Codebase Analyzer

This module provides a complete static code analysis system using the Codegen SDK.
It analyzes a codebase and provides extensive information about its structure,
dependencies, code quality, and more.
"""

import logging
import sys
from typing import Any

try:
    from codegen.sdk.codebase.codebase_analysis import (
        analyze_codebase_quality,
        get_codebase_summary,
    )
    from codegen.sdk.codebase.codebase_context import CodebaseContext
    from codegen.sdk.core.codebase import Codebase
except ImportError:
    print("Codegen SDK not found. Please install it first.")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)


class CodebaseAnalyzer:
    """Comprehensive codebase analyzer using the Codegen SDK."""

    def __init__(self, codebase_path: str):
        """Initialize the codebase analyzer.

        Args:
            codebase_path: Path to the codebase to analyze.
        """
        self.codebase_path = codebase_path
        self.codebase = Codebase(codebase_path)
        self.context = CodebaseContext(self.codebase)
        logger.info(f"Initialized CodebaseAnalyzer for {codebase_path}")

    def get_codebase_summary(self) -> dict[str, Any]:
        """Get a summary of the codebase.

        Returns:
            A dictionary containing codebase summary information.
        """
        try:
            return get_codebase_summary(self.codebase)
        except Exception as e:
            return {"error": str(e)}

    def analyze_code_quality(self) -> dict[str, Any]:
        """Analyze the code quality of the codebase.

        Returns:
            A dictionary containing code quality analysis results.
        """
        try:
            return analyze_codebase_quality(self.codebase)
        except Exception as e:
            return {"error": str(e)}
