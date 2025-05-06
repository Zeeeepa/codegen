"""
Code integrity analysis module.

This module provides tools for analyzing code integrity, including:
- Finding functions with issues
- Identifying classes with problems
- Detecting parameter usage errors
- Finding incorrect function callback points
- Comparing error counts between branches
- Analyzing code complexity and duplication
- Checking for type hint usage
- Detecting unused imports
"""

from typing import Any, Dict, Optional

from graph_sitter.core.codebase import Codebase

from codegen_on_oss.analysis.code_integrity_analyzer import (
    CodeIntegrityAnalyzer,
    compare_branches,
)
from codegen_on_oss.analysis.code_integrity_main import analyze_code_integrity

__all__ = ["CodeIntegrityAnalyzer", "analyze_code_integrity", "compare_branches"]

