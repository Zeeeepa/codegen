"""
CodebaseAnalysisHarness: Integration of the harness.py functionality from swebench.
Provides comprehensive codebase analysis, diff generation, and context management.
"""

import json
import pprint
import random
import subprocess
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from loguru import logger

from codegen import Codebase
from codegen.agents.code_agent import CodeAgent
from codegen.configs.models.codebase import CodebaseConfig
from codegen_on_oss.bucket_store import BucketStore


class CodebaseAnalysisHarness:
    """
    A harness for analyzing codebases, generating diffs, and tracking file changes.
    Integrates functionality from the swebench harness.py.
    """

    def __init__(
        self,
        codebase: Codebase,
        base_commit: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the CodebaseAnalysisHarness.

        Args:
            codebase: The Codebase object to analyze
            base_commit: Optional base commit to compare against
            metadata: Optional metadata to associate with the analysis
        """
        self.codebase = codebase
        self.base_commit = base_commit or codebase.commit
        self.metadata = metadata or {}
        self.analysis_results: Dict[str, Any] = {}
        self.run_id = str(uuid.uuid4())

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
            commit: Optional commit to checkout
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

    def analyze_codebase(self) -> Dict[str, Any]:
        """
        Analyze the codebase and return the results.

        Returns:
            A dictionary containing the analysis results
        """
        logger.info(f"Analyzing codebase: {self.codebase.repo_full_name}")
        
        # Get basic repository information
        repo_info = {
            "repo_name": self.codebase.repo_full_name,
            "commit": self.codebase.commit,
            "base_commit": self.base_commit,
            "run_id": self.run_id,
        }
        
        # Get file statistics
        file_stats = self._get_file_stats()
        
        # Combine all results
        self.analysis_results = {
            "repo_info": repo_info,
            "file_stats": file_stats,
            "metadata": self.metadata,
        }
        
        return self.analysis_results

    def _get_file_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the files in the codebase.

        Returns:
            A dictionary containing file statistics
        """
        file_count = len(self.codebase.files)
        file_types = {}
        
        for file in self.codebase.files:
            ext = Path(file.path).suffix
            if ext in file_types:
                file_types[ext] += 1
            else:
                file_types[ext] = 1
        
        return {
            "file_count": file_count,
            "file_types": file_types,
        }

    def get_diff(self, base: Optional[str] = None) -> str:
        """
        Get the diff between the current state and a base commit.

        Args:
            base: The base commit to compare against (defaults to self.base_commit)

        Returns:
            The diff as a string
        """
        base_commit = base or self.base_commit
        return self.codebase.get_diff(base=base_commit)

    def diff_versus_commit(self, commit: Optional[str] = None) -> str:
        """
        Take a diff of the current contents versus a commit.

        Args:
            commit: The commit to compare against (defaults to self.base_commit)

        Returns:
            The diff output as a string
        """
        commit_to_use = commit or self.base_commit
        git_dname = self.codebase.repo_path
        diff_cmd = f"git -C {git_dname} diff {commit_to_use}"
        diff_output = subprocess.check_output(diff_cmd.split()).decode()
        return diff_output

    def files_in_patch(self, patch: str) -> List[str]:
        """
        Extract the list of modified files from a unified diff patch string.

        Args:
            patch: The unified diff patch string

        Returns:
            A list of modified files
        """
        files = []
        for line in patch.split("\n"):
            if line.startswith("--- a/") or line.startswith("+++ b/"):
                fname = line.split("/", 1)[1]
                if fname not in files:
                    files.append(fname)
        return files

    def run_agent(self, prompt: str, model: Optional[str] = None) -> Dict[str, Any]:
        """
        Run an agent on the codebase with the given prompt.

        Args:
            prompt: The prompt to send to the agent
            model: Optional model to use for the agent

        Returns:
            The result of the agent run
        """
        metadata = {
            "run_id": self.run_id,
            **self.metadata,
        }
        tags = [str(value) for value in metadata.values()]
        agent = CodeAgent(codebase=self.codebase, tags=tags, metadata=metadata)

        try:
            result = agent.run(prompt=prompt)
        except Exception as agent_error:
            logger.error(f"Agent run terminated with error: {agent_error}")
            raise agent_error

        # Get the diff between the current state and the original commit
        model_patch = self.get_diff(base=self.base_commit)
        
        # Record the results
        edited_files = self.files_in_patch(model_patch)
        
        return {
            "agent_result": result,
            "model_patch": model_patch,
            "edited_files": edited_files,
        }

    def save_results(self, bucket_store: BucketStore, path: str) -> str:
        """
        Save the analysis results to a bucket store.

        Args:
            bucket_store: The BucketStore to save to
            path: The path to save to

        Returns:
            The key of the saved file
        """
        if not self.analysis_results:
            self.analyze_codebase()
            
        # Save to a temporary file
        temp_file = Path(f"/tmp/{self.run_id}_analysis.json")
        with open(temp_file, "w") as f:
            json.dump(self.analysis_results, f)
            
        # Upload to bucket store
        key = bucket_store.upload_file(str(temp_file), path)
        
        # Clean up
        temp_file.unlink()
        
        return key

