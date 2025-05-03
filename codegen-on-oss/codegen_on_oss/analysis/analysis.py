"""Unified Analysis Module for Codegen-on-OSS

This module serves as a central hub for all code analysis functionality, integrating
various specialized analysis components into a cohesive system.
"""

# Import from codegen SDK
# Import from existing analysis modules
from codegen_on_oss.analysis.codebase_analysis import get_codebase_summary, get_file_summary

from codegen import Codebase


class CodeAnalyzer:
    """Central class for code analysis that integrates all analysis components.

    This class serves as the main entry point for all code analysis functionality,
    providing a unified interface to access various analysis capabilities.
    """

    def __init__(self, codebase: Codebase):
        """Initialize the CodeAnalyzer with a codebase.

        Args:
            codebase: The Codebase object to analyze
        """
        self.codebase = codebase
        self._context = None
        self._initialized = False

    def get_codebase_summary(self) -> str:
        """Get a comprehensive summary of the codebase.

        Returns:
            A string containing summary information about the codebase
        """
        return get_codebase_summary(self.codebase)

    def get_file_summary(self, file_path: str) -> str:
        """Get a summary of a specific file.

        Args:
            file_path: Path to the file to analyze

        Returns:
            A string containing summary information about the file
        """
        file = self.codebase.get_file(file_path)
        if file is None:
            return f"File not found: {file_path}"
        return get_file_summary(file)
