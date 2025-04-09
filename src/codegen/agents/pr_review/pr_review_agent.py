"""
PR Review Agent for reviewing pull requests.

This module provides a PR Review Agent that can analyze and review pull requests.
"""

from typing import Dict, List, Any, Optional, Tuple
import os
import logging
from github import Github
from github.PullRequest import PullRequest

from codegen.agents.base import BaseAgent
from codegen.agents.code.code_agent import CodeAgent
from codegen.tools.planning.manager import PlanManager
from codegen.tools.research.researcher import Researcher
from codegen.tools.reflection.reflector import Reflector
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)

class PRReviewAgent(BaseAgent):
    """Agent for reviewing pull requests."""
    
    def __init__(
        self,
        github_token: Optional[str] = None,
        model_provider: str = "anthropic",
        model_name: str = "claude-3-5-sonnet-latest",
        memory: bool = True,
        temperature: float = 0.2,
        max_tokens: int = 4000,
    ):
        """Initialize a PRReviewAgent.
        
        Args:
            github_token: GitHub token for API access
            model_provider: Provider of the LLM
            model_name: Name of the LLM
            memory: Whether to use memory
            temperature: Temperature for the LLM
            max_tokens: Maximum tokens for the LLM
        """
        super().__init__(
            model_provider=model_provider,
            model_name=model_name,
            memory=memory,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        self.github_token = github_token or os.environ.get("GITHUB_TOKEN")
        if not self.github_token:
            logger.warning("No GitHub token provided. Some functionality may be limited.")
            
        self.github = Github(self.github_token) if self.github_token else None
        self.code_agent = None
        self.plan_manager = PlanManager()
        self.researcher = Researcher()
        self.reflector = Reflector()
        
    def review_pr(self, repo_name: str, pr_number: int) -> Dict[str, Any]:
        """Review a pull request.
        
        Args:
            repo_name: Name of the repository (e.g., "owner/repo")
            pr_number: Number of the pull request
            
        Returns:
            Review results
        """
        if not self.github:
            return {"error": "GitHub token not provided"}
            
        try:
            # Get the repository and PR
            repo = self.github.get_repo(repo_name)
            pr = repo.get_pull(pr_number)
            
            # Initialize a code agent for the repository
            self.code_agent = CodeAgent(
                model_provider=self.model_provider,
                model_name=self.model_name,
            )
            
            # Analyze the PR
            analysis = self._analyze_pr(pr)
            
            # Generate review comments
            review_comments = self._generate_review_comments(pr, analysis)
            
            # Create a summary
            summary = self._create_review_summary(pr, analysis, review_comments)
            
            return {
                "summary": summary,
                "analysis": analysis,
                "review_comments": review_comments,
            }
            
        except Exception as e:
            logger.error(f"Error reviewing PR: {str(e)}")
            return {"error": f"Error reviewing PR: {str(e)}"}
            
    def _analyze_pr(self, pr: PullRequest) -> Dict[str, Any]:
        """Analyze a pull request.
        
        Args:
            pr: Pull request to analyze
            
        Returns:
            Analysis results
        """
        # Get the PR details
        title = pr.title
        body = pr.body or ""
        files_changed = list(pr.get_files())
        commits = list(pr.get_commits())
        
        # Analyze the code changes
        code_analysis = self._analyze_code_changes(files_changed)
        
        # Analyze the commit history
        commit_analysis = self._analyze_commits(commits)
        
        # Use the researcher to gather insights
        research_results = self.researcher.research_code_changes(
            files_changed=[f.filename for f in files_changed],
            code_changes={f.filename: f.patch for f in files_changed if f.patch},
        )
        
        # Use the reflector to reflect on the changes
        reflection_results = self.reflector.reflect_on_changes(
            title=title,
            description=body,
            files_changed=[f.filename for f in files_changed],
            code_changes={f.filename: f.patch for f in files_changed if f.patch},
        )
        
        return {
            "title": title,
            "body": body,
            "files_changed": [f.filename for f in files_changed],
            "commits": [c.sha for c in commits],
            "code_analysis": code_analysis,
            "commit_analysis": commit_analysis,
            "research_results": research_results,
            "reflection_results": reflection_results,
        }
        
    def _analyze_code_changes(self, files_changed: List[Any]) -> Dict[str, Any]:
        """Analyze code changes in a PR.
        
        Args:
            files_changed: List of files changed in the PR
            
        Returns:
            Analysis of code changes
        """
        # Placeholder for code analysis
        return {
            "files_count": len(files_changed),
            "file_types": self._get_file_types(files_changed),
            "lines_added": sum(f.additions for f in files_changed),
            "lines_deleted": sum(f.deletions for f in files_changed),
        }
        
    def _analyze_commits(self, commits: List[Any]) -> Dict[str, Any]:
        """Analyze commits in a PR.
        
        Args:
            commits: List of commits in the PR
            
        Returns:
            Analysis of commits
        """
        # Placeholder for commit analysis
        return {
            "count": len(commits),
            "authors": list(set(c.author.login for c in commits if c.author)),
            "messages": [c.commit.message for c in commits],
        }
        
    def _get_file_types(self, files_changed: List[Any]) -> Dict[str, int]:
        """Get the types of files changed in a PR.
        
        Args:
            files_changed: List of files changed in the PR
            
        Returns:
            Dictionary mapping file extensions to counts
        """
        file_types = {}
        
        for file in files_changed:
            ext = os.path.splitext(file.filename)[1]
            if not ext:
                ext = "no_extension"
                
            if ext in file_types:
                file_types[ext] += 1
            else:
                file_types[ext] = 1
                
        return file_types
        
    def _generate_review_comments(self, pr: PullRequest, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate review comments for a PR.
        
        Args:
            pr: Pull request to generate comments for
            analysis: Analysis of the PR
            
        Returns:
            List of review comments
        """
        # Placeholder for review comments
        comments = []
        
        # Add comments based on the analysis
        if analysis["code_analysis"]["lines_added"] > 500:
            comments.append({
                "type": "warning",
                "message": "This PR adds a large number of lines. Consider breaking it down into smaller PRs.",
            })
            
        if len(analysis["commits"]) == 1:
            comments.append({
                "type": "info",
                "message": "This PR has only one commit. Consider adding more granular commits for better history.",
            })
            
        # Add comments from research results
        if "insights" in analysis["research_results"]:
            for insight in analysis["research_results"]["insights"]:
                comments.append({
                    "type": "suggestion",
                    "message": insight["description"],
                    "file": insight.get("file"),
                    "line": insight.get("line"),
                })
                
        return comments
        
    def _create_review_summary(self, pr: PullRequest, analysis: Dict[str, Any], review_comments: List[Dict[str, Any]]) -> str:
        """Create a summary of the PR review.
        
        Args:
            pr: Pull request being reviewed
            analysis: Analysis of the PR
            review_comments: Review comments
            
        Returns:
            Summary of the review
        """
        # Count comment types
        comment_counts = {}
        for comment in review_comments:
            comment_type = comment["type"]
            if comment_type in comment_counts:
                comment_counts[comment_type] += 1
            else:
                comment_counts[comment_type] = 1
                
        # Create the summary
        summary = f"# PR Review: {pr.title}\n\n"
        
        summary += "## Summary\n\n"
        summary += f"- Files changed: {analysis['code_analysis']['files_count']}\n"
        summary += f"- Lines added: {analysis['code_analysis']['lines_added']}\n"
        summary += f"- Lines deleted: {analysis['code_analysis']['lines_deleted']}\n"
        summary += f"- Commits: {analysis['commit_analysis']['count']}\n"
        
        if comment_counts:
            summary += "\n## Comments\n\n"
            for comment_type, count in comment_counts.items():
                summary += f"- {comment_type.capitalize()}: {count}\n"
                
        if "reflection_results" in analysis and "summary" in analysis["reflection_results"]:
            summary += f"\n## Reflection\n\n{analysis['reflection_results']['summary']}\n"
            
        return summary
