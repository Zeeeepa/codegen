"""
CodebaseAnalysisHarness - Integration of the harness.py functionality from swebench.

This module provides comprehensive codebase analysis capabilities by integrating
the core functionality from the swebench harness.py module.
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Set, Union

from loguru import logger

from codegen import Codebase
from codegen.configs.models.codebase import CodebaseConfig


class CodebaseAnalysisHarness:
    """
    A harness for comprehensive codebase analysis, integrating functionality
    from the swebench harness.py module.
    """

    def __init__(
        self,
        codebase: Codebase,
        metadata: Optional[Dict] = None,
        tags: Optional[List[str]] = None,
    ):
        """
        Initialize the CodebaseAnalysisHarness with a codebase.

        Args:
            codebase: The Codebase object to analyze
            metadata: Optional metadata to associate with the analysis
            tags: Optional tags to categorize the analysis
        """
        self.codebase = codebase
        self.metadata = metadata or {}
        self.tags = tags or []
        self.analysis_results = {}

    @classmethod
    def from_repo(
        cls,
        repo_full_name: str,
        commit: Optional[str] = None,
        language: str = "python",
        disable_file_parse: bool = False,
    ) -> "CodebaseAnalysisHarness":
        """
        Create a CodebaseAnalysisHarness from a repository.

        Args:
            repo_full_name: The full name of the repository (e.g., "owner/repo")
            commit: Optional commit hash to checkout
            language: The primary language of the codebase
            disable_file_parse: Whether to disable file parsing

        Returns:
            A new CodebaseAnalysisHarness instance
        """
        config = CodebaseConfig(
            disable_file_parse=disable_file_parse,
        )
        codebase = Codebase.from_repo(
            repo_full_name=repo_full_name,
            commit=commit,
            language=language,
            config=config,
        )
        return cls(codebase=codebase)

    def analyze_codebase(self) -> Dict:
        """
        Perform comprehensive analysis of the codebase.

        Returns:
            A dictionary containing analysis results
        """
        logger.info(f"Analyzing codebase: {self.codebase.repo_name}")

        # Collect basic codebase statistics
        stats = {
            "repo_name": self.codebase.repo_name,
            "language": self.codebase.language,
            "file_count": len(self.codebase.files),
            "metadata": self.metadata,
            "tags": self.tags,
        }

        # Get file structure
        file_structure = self._get_file_structure()
        stats["file_structure"] = file_structure

        # Store the results
        self.analysis_results = stats
        return stats

    def _get_file_structure(self) -> Dict:
        """
        Get the file structure of the codebase.

        Returns:
            A dictionary representing the file structure
        """
        structure = {}
        for file_path in self.codebase.files:
            parts = file_path.split("/")
            current = structure
            for i, part in enumerate(parts):
                if i == len(parts) - 1:  # This is a file
                    current.setdefault("files", []).append(part)
                else:  # This is a directory
                    current.setdefault("dirs", {}).setdefault(part, {})
                    current = current["dirs"][part]
        return structure

    def diff_versus_commit(self, commit: str) -> str:
        """
        Take a diff of current contents versus the specified commit.

        Args:
            commit: The commit hash to diff against

        Returns:
            The diff output as a string
        """
        return self.codebase.get_diff(base=commit)

    def files_in_patch(self, patch: str) -> List[str]:
        """
        Extract the list of modified files from a unified diff patch string.

        Args:
            patch: The unified diff patch string

        Returns:
            A list of modified file paths
        """
        files = []
        for line in patch.split("\n"):
            if line.startswith("--- a/") or line.startswith("+++ b/"):
                fname = line.split("/", 1)[1]
                if fname not in files:
                    files.append(fname)
        return files

    def save_analysis_results(self, output_path: Union[str, Path]) -> None:
        """
        Save the analysis results to a JSON file.

        Args:
            output_path: The path to save the results to
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w") as f:
            json.dump(self.analysis_results, f, indent=2)
        
        logger.info(f"Analysis results saved to {output_path}")

