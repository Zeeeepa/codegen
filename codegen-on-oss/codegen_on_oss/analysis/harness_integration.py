"""
CodebaseAnalysisHarness - Integration of harness.py functionality for comprehensive codebase analysis.
"""

import json
from pathlib import Path
from typing import Any

from codegen import Codebase
from codegen.agents.code_agent import CodeAgent
from codegen.configs.models.codebase import CodebaseConfig
from loguru import logger


class CodebaseAnalysisHarness:
    """
    A comprehensive harness for analyzing codebases, generating diffs, and tracking file changes.
    Integrates core functionality from the original harness.py with enhanced analysis capabilities.
    """

    def __init__(
        self,
        codebase: Codebase,
        base_commit: str | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """
        Initialize the CodebaseAnalysisHarness with a codebase.

        Args:
            codebase: The Codebase object to analyze
            base_commit: Optional base commit to compare against
            metadata: Optional metadata to associate with the analysis
        """
        self.codebase = codebase
        self.base_commit = base_commit
        self.metadata = metadata or {}
        self.analysis_results: dict[str, Any] = {}

    @classmethod
    def from_repo(
        cls,
        repo_full_name: str,
        commit: str | None = None,
        language: str = "python",
        disable_file_parse: bool = False,
    ) -> "CodebaseAnalysisHarness":
        """
        Create a CodebaseAnalysisHarness from a repository.

        Args:
            repo_full_name: The full name of the repository (e.g., "owner/repo")
            commit: Optional commit hash to checkout
            language: The primary language of the repository
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
        return cls(codebase=codebase, base_commit=commit)

    def analyze_codebase(self) -> dict[str, Any]:
        """
        Perform comprehensive analysis of the codebase.

        Returns:
            A dictionary containing analysis results
        """
        logger.info(f"Analyzing codebase: {self.codebase.repo_name}")

        # Collect basic repository information
        repo_info = {
            "repo_name": self.codebase.repo_name,
            "language": self.codebase.language,
            "base_commit": self.base_commit,
        }

        # Get file statistics
        file_stats = self._get_file_statistics()

        # Combine all results
        self.analysis_results = {
            "repo_info": repo_info,
            "file_stats": file_stats,
            "metadata": self.metadata,
        }

        return self.analysis_results

    def _get_file_statistics(self) -> dict[str, Any]:
        """
        Get statistics about files in the codebase.

        Returns:
            A dictionary containing file statistics
        """
        file_count = len(self.codebase.files)
        file_extensions = {}

        for file in self.codebase.files:
            ext = Path(file.path).suffix
            if ext in file_extensions:
                file_extensions[ext] += 1
            else:
                file_extensions[ext] = 1

        return {
            "file_count": file_count,
            "file_extensions": file_extensions,
        }

    def get_diff(self, base: str | None = None) -> str:
        """
        Get the diff between the current state and a base commit.

        Args:
            base: The base commit to compare against (defaults to self.base_commit)

        Returns:
            A string containing the diff
        """
        base_commit = base or self.base_commit
        if not base_commit:
            logger.warning("No base commit specified for diff generation")
            return ""

        return self.codebase.get_diff(base=base_commit)

    def files_in_patch(self, patch: str) -> list[str]:
        """
        Extract the list of modified files from a unified diff patch string.

        Args:
            patch: A unified diff patch string

        Returns:
            A list of modified file paths
        """
        files: set[str] = set()
        for line in patch.split("\n"):
            if line.startswith("--- a/") or line.startswith("+++ b/"):
                fname = line.split("/", 1)[1]
                files.add(fname)

        return list(files)

    def run_agent(self, prompt: str, model: str | None = None) -> dict[str, Any]:
        """
        Run a CodeAgent on the codebase with the given prompt.

        Args:
            prompt: The prompt to send to the agent
            model: Optional model to use for the agent

        Returns:
            The result of the agent run
        """
        tags = [str(value) for value in self.metadata.values() if value]
        agent = CodeAgent(codebase=self.codebase, tags=tags, metadata=self.metadata)

        try:
            result = agent.run(prompt=prompt)

            # Get the diff between the current state and the original commit
            model_patch = self.get_diff(base=self.base_commit)
            edited_files = self.files_in_patch(model_patch)

            return {
                "result": result,
                "model_patch": model_patch,
                "edited_files": edited_files,
            }
        except Exception as agent_error:
            logger.error(f"Agent run failed with error: {agent_error}")
            raise

    def save_analysis_results(self, output_path: str | Path) -> Path:
        """
        Save the analysis results to a JSON file.

        Args:
            output_path: The path to save the results to

        Returns:
            The path where the results were saved
        """
        if not self.analysis_results:
            logger.warning("No analysis results to save. Run analyze_codebase() first.")
            self.analyze_codebase()

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(self.analysis_results, f, indent=2)

        logger.info(f"Analysis results saved to {output_path}")
        return output_path
