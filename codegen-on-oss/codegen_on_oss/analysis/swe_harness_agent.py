"""
SWE Harness Agent Module

This module provides a harness for a Software Engineering agent that can
analyze commits and pull requests to determine if they are properly implemented.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple

import requests
from github import Github, GithubException

from codegen_on_oss.analysis.commit_analyzer import CommitAnalyzer
from codegen_on_oss.snapshot.codebase_snapshot import SnapshotManager

logger = logging.getLogger(__name__)


class SWEHarnessAgent:
    """
    A harness for a Software Engineering agent that can analyze commits
    and pull requests to determine if they are properly implemented.
    """

    def __init__(
        self,
        github_token: Optional[str] = None,
        snapshot_dir: Optional[str] = None,
        use_agent: bool = True,
        agent_api_key: Optional[str] = None,
        agent_api_url: Optional[str] = None,
    ):
        """
        Initialize a new SWEHarnessAgent.

        Args:
            github_token: Optional GitHub token for accessing private repositories
            snapshot_dir: Optional directory to store snapshots
            use_agent: Whether to use an LLM-based agent for enhanced analysis
            agent_api_key: API key for the LLM-based agent service
            agent_api_url: URL for the LLM-based agent service
        """
        self.github_token = github_token
        self.snapshot_manager = SnapshotManager(snapshot_dir)
        self.commit_analyzer = CommitAnalyzer(self.snapshot_manager, github_token)
        self.use_agent = use_agent
        self.agent_api_key = agent_api_key
        self.agent_api_url = agent_api_url or "https://api.codegen.sh/agent"
        self.agent = None

        if self.use_agent:
            # Initialize the agent if needed
            self._initialize_agent()

    def _initialize_agent(self):
        """Initialize the CodeAgent for enhanced analysis."""
        # Check if we have the necessary credentials
        if self.use_agent and not self.agent_api_key:
            # Try to get the API key from environment variables
            self.agent_api_key = os.environ.get("CODEGEN_API_KEY")
            
        if self.use_agent and not self.agent_api_key:
            logger.warning("Agent-based analysis requested but no API key provided")
            logger.warning("Set CODEGEN_API_KEY environment variable or pass agent_api_key")
            self.use_agent = False
        
        # Initialize the agent client if we have credentials
        if self.use_agent and self.agent_api_key:
            try:
                # Test the connection to the agent API
                headers = {"Authorization": f"Bearer {self.agent_api_key}"}
                response = requests.get(f"{self.agent_api_url}/health", headers=headers)
                if response.status_code == 200:
                    logger.info("Successfully connected to agent API")
                    self.agent = True
                else:
                    logger.warning(f"Failed to connect to agent API: {response.status_code}")
                    self.use_agent = False
            except Exception as e:
                logger.warning(f"Error connecting to agent API: {e}")
                self.use_agent = False

    def analyze_commit(
        self, repo_url: str, base_commit: str, head_commit: str, detailed: bool = False
    ) -> Dict[str, Any]:
        """
        Analyze a commit to determine if it's properly implemented.

        Args:
            repo_url: The repository URL or owner/repo string
            base_commit: The base commit SHA (before the changes)
            head_commit: The head commit SHA (after the changes)
            detailed: Whether to include detailed analysis in the results

        Returns:
            A dictionary with analysis results
        """
        # Use the commit analyzer to get basic analysis
        analysis_results = self.commit_analyzer.analyze_commit(repo_url, base_commit, head_commit)

        # Format the analysis report
        report = self.commit_analyzer.format_analysis_report(analysis_results)

        # Determine if the commit is properly implemented
        is_properly_implemented = analysis_results["quality_assessment"]["is_properly_implemented"]

        # If using an agent, enhance the analysis with LLM-based insights
        if self.use_agent and self.agent:
            agent_analysis = self._get_agent_analysis(repo_url, base_commit, head_commit)
            if agent_analysis:
                analysis_results["agent_analysis"] = agent_analysis

        # Prepare the response
        response = {
            "is_properly_implemented": is_properly_implemented,
            "quality_score": analysis_results["quality_assessment"]["score"],
            "overall_assessment": analysis_results["quality_assessment"]["overall_assessment"],
            "report": report,
        }

        # Include issues if there are any
        if analysis_results["quality_assessment"]["issues"]:
            response["issues"] = analysis_results["quality_assessment"]["issues"]

        # Include detailed analysis if requested
        if detailed:
            response["detailed_analysis"] = analysis_results

        return response

    def analyze_pull_request(
        self, repo_url: str, pr_number: int, detailed: bool = False
    ) -> Dict[str, Any]:
        """
        Analyze a pull request to determine if it's properly implemented.

        Args:
            repo_url: The repository URL or owner/repo string
            pr_number: The pull request number
            detailed: Whether to include detailed analysis in the results

        Returns:
            A dictionary with analysis results
        """
        # Use the commit analyzer to get PR analysis
        analysis_results = self.commit_analyzer.analyze_pull_request(
            repo_url, pr_number, self.github_token
        )

        # Format the analysis report
        report = self.commit_analyzer.format_analysis_report(analysis_results)

        # Determine if the PR is properly implemented
        is_properly_implemented = analysis_results["quality_assessment"]["is_properly_implemented"]

        # If using an agent, enhance the analysis with LLM-based insights
        if self.use_agent and self.agent:
            agent_analysis = self._get_agent_pr_analysis(repo_url, pr_number)
            if agent_analysis:
                analysis_results["agent_analysis"] = agent_analysis

        # Prepare the response
        response = {
            "is_properly_implemented": is_properly_implemented,
            "quality_score": analysis_results["quality_assessment"]["score"],
            "overall_assessment": analysis_results["quality_assessment"]["overall_assessment"],
            "report": report,
        }

        # Include issues if there are any
        if analysis_results["quality_assessment"]["issues"]:
            response["issues"] = analysis_results["quality_assessment"]["issues"]

        # Include detailed analysis if requested
        if detailed:
            response["detailed_analysis"] = analysis_results

        return response

    def _get_agent_analysis(
        self, repo_url: str, base_commit: str, head_commit: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get enhanced analysis from the LLM-based agent.

        Args:
            repo_url: The repository URL or owner/repo string
            base_commit: The base commit SHA
            head_commit: The head commit SHA

        Returns:
            A dictionary with agent analysis results, or None if agent analysis fails
        """
        if not self.agent or not self.agent_api_key:
            logger.info("Agent-based commit analysis requested but agent is not initialized")
            return {
                "status": "not_initialized",
                "message": "Agent-based analysis is not initialized",
                "fallback": "Using standard analysis methods instead",
            }
            
        try:
            # Get the diff between the two commits
            diff = self._get_commit_diff(repo_url, base_commit, head_commit)
            
            # Get the commit message
            commit_message = self._get_commit_message(repo_url, head_commit)
            
            # Prepare the request to the agent API
            headers = {
                "Authorization": f"Bearer {self.agent_api_key}",
                "Content-Type": "application/json",
            }
            
            payload = {
                "repo_url": repo_url,
                "base_commit": base_commit,
                "head_commit": head_commit,
                "diff": diff,
                "commit_message": commit_message,
                "analysis_type": "commit",
            }
            
            # Send the request to the agent API
            response = requests.post(
                f"{self.agent_api_url}/analyze",
                headers=headers,
                json=payload,
            )
            
            # Check if the request was successful
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Agent API returned status code {response.status_code}")
                logger.warning(f"Response: {response.text}")
                return {
                    "status": "api_error",
                    "message": f"Agent API returned status code {response.status_code}",
                    "fallback": "Using standard analysis methods instead",
                }
                
        except Exception as e:
            logger.exception(f"Error during agent-based commit analysis: {e}")
            return {
                "status": "error",
                "message": f"Error during agent-based analysis: {str(e)}",
                "fallback": "Using standard analysis methods instead",
            }

    def _get_agent_pr_analysis(self, repo_url: str, pr_number: int) -> Optional[Dict[str, Any]]:
        """
        Get enhanced analysis of a PR from the LLM-based agent.

        Args:
            repo_url: The repository URL or owner/repo string
            pr_number: The pull request number

        Returns:
            A dictionary with agent analysis results, or None if agent analysis fails
        """
        if not self.agent or not self.agent_api_key:
            logger.info("Agent-based PR analysis requested but agent is not initialized")
            return {
                "status": "not_initialized",
                "message": "Agent-based analysis is not initialized",
                "fallback": "Using standard analysis methods instead",
            }
            
        try:
            # Parse the repo URL to get owner and repo name
            if "/" in repo_url and "github.com" not in repo_url:
                owner, repo_name = repo_url.split("/")
            else:
                # Extract owner/repo from a full GitHub URL
                parts = repo_url.rstrip("/").split("/")
                owner = parts[-2]
                repo_name = parts[-1]
                if repo_name.endswith(".git"):
                    repo_name = repo_name[:-4]
            
            # Get the PR from GitHub
            g = Github(self.github_token) if self.github_token else Github()
            repo = g.get_repo(f"{owner}/{repo_name}")
            pr = repo.get_pull(pr_number)
            
            # Get PR details
            pr_title = pr.title
            pr_description = pr.body or ""
            pr_files = [file.filename for file in pr.get_files()]
            
            # Get the diff
            diff = pr.diff_url
            diff_content = requests.get(diff).text if diff else ""
            
            # Prepare the request to the agent API
            headers = {
                "Authorization": f"Bearer {self.agent_api_key}",
                "Content-Type": "application/json",
            }
            
            payload = {
                "repo_url": repo_url,
                "pr_number": pr_number,
                "pr_title": pr_title,
                "pr_description": pr_description,
                "pr_files": pr_files,
                "diff": diff_content,
                "analysis_type": "pull_request",
            }
            
            # Send the request to the agent API
            response = requests.post(
                f"{self.agent_api_url}/analyze",
                headers=headers,
                json=payload,
            )
            
            # Check if the request was successful
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Agent API returned status code {response.status_code}")
                logger.warning(f"Response: {response.text}")
                return {
                    "status": "api_error",
                    "message": f"Agent API returned status code {response.status_code}",
                    "fallback": "Using standard analysis methods instead",
                }
                
        except Exception as e:
            logger.exception(f"Error during agent-based PR analysis: {e}")
            return {
                "status": "error",
                "message": f"Error during agent-based analysis: {str(e)}",
                "fallback": "Using standard analysis methods instead",
            }

    def _get_commit_diff(self, repo_url: str, base_commit: str, head_commit: str) -> str:
        """
        Get the diff between two commits.
        
        Args:
            repo_url: The repository URL or owner/repo string
            base_commit: The base commit SHA
            head_commit: The head commit SHA
            
        Returns:
            The diff as a string
        """
        try:
            # Parse the repo URL to get owner and repo name
            if "/" in repo_url and "github.com" not in repo_url:
                owner, repo_name = repo_url.split("/")
            else:
                # Extract owner/repo from a full GitHub URL
                parts = repo_url.rstrip("/").split("/")
                owner = parts[-2]
                repo_name = parts[-1]
                if repo_name.endswith(".git"):
                    repo_name = repo_name[:-4]
            
            # Get the diff from GitHub
            diff_url = f"https://github.com/{owner}/{repo_name}/compare/{base_commit}...{head_commit}.diff"
            response = requests.get(diff_url)
            
            if response.status_code == 200:
                return response.text
            else:
                logger.warning(f"Failed to get diff: {response.status_code}")
                return ""
                
        except Exception as e:
            logger.exception(f"Error getting commit diff: {e}")
            return ""
            
    def _get_commit_message(self, repo_url: str, commit_hash: str) -> str:
        """
        Get the commit message for a commit.
        
        Args:
            repo_url: The repository URL or owner/repo string
            commit_hash: The commit hash
            
        Returns:
            The commit message as a string
        """
        try:
            # Parse the repo URL to get owner and repo name
            if "/" in repo_url and "github.com" not in repo_url:
                owner, repo_name = repo_url.split("/")
            else:
                # Extract owner/repo from a full GitHub URL
                parts = repo_url.rstrip("/").split("/")
                owner = parts[-2]
                repo_name = parts[-1]
                if repo_name.endswith(".git"):
                    repo_name = repo_name[:-4]
            
            # Get the commit from GitHub
            g = Github(self.github_token) if self.github_token else Github()
            repo = g.get_repo(f"{owner}/{repo_name}")
            commit = repo.get_commit(commit_hash)
            
            return commit.commit.message
                
        except Exception as e:
            logger.exception(f"Error getting commit message: {e}")
            return ""

    def create_comment_for_pr(
        self, repo_url: str, pr_number: int, analysis_results: Dict[str, Any]
    ) -> str:
        """
        Create a comment for a pull request based on analysis results.

        Args:
            repo_url: The repository URL or owner/repo string
            pr_number: The pull request number
            analysis_results: The analysis results from analyze_pull_request

        Returns:
            A formatted comment string
        """
        is_properly_implemented = analysis_results["is_properly_implemented"]
        quality_score = analysis_results["quality_score"]
        overall_assessment = analysis_results["overall_assessment"]

        # Create the comment header
        if is_properly_implemented:
            comment = "## ✅ PR Analysis: Properly Implemented\n\n"
        else:
            comment = "## ❌ PR Analysis: Issues Detected\n\n"

        comment += f"**Quality Score:** {quality_score}/10.0 - {overall_assessment}\n\n"

        # Add summary section
        comment += "### Summary\n\n"

        # Extract key metrics from the report
        import re

        summary_match = re.search(
            r"Summary:\\n(.*?)(?:\\n\\n|\\Z)", analysis_results["report"], re.DOTALL
        )
        if summary_match:
            summary_text = summary_match.group(1).strip()
            comment += summary_text + "\n\n"

        # Add issues if there are any
        if "issues" in analysis_results and analysis_results["issues"]:
            comment += "### Issues\n\n"
            for issue in analysis_results["issues"]:
                comment += f"- {issue}\n"
            comment += "\n"

        # Add warnings if there are any
        warnings_match = re.search(
            r"Warnings:\\n(.*?)(?:\\n\\n|\\Z)", analysis_results["report"], re.DOTALL
        )
        if warnings_match:
            warnings_text = warnings_match.group(1).strip()
            comment += "### Warnings\n\n" + warnings_text + "\n\n"

        # Add positive aspects if there are any
        positive_match = re.search(
            r"Positive Aspects:\\n(.*?)(?:\\n\\n|\\Z)",
            analysis_results["report"],
            re.DOTALL,
        )
        if positive_match:
            positive_text = positive_match.group(1).strip()
            comment += "### Positive Aspects\n\n" + positive_text + "\n\n"

        # Add agent analysis if available
        if "agent_analysis" in analysis_results and analysis_results["agent_analysis"]:
            agent_analysis = analysis_results["agent_analysis"]
            if "insights" in agent_analysis:
                comment += "### AI-Enhanced Analysis\n\n"
                for insight in agent_analysis["insights"]:
                    comment += f"- {insight}\n"
                comment += "\n"
            
            if "recommendations" in agent_analysis:
                comment += "### Recommendations\n\n"
                for recommendation in agent_analysis["recommendations"]:
                    comment += f"- {recommendation}\n"
                comment += "\n"

        # Add conclusion
        comment += "### Conclusion\n\n"
        if is_properly_implemented:
            comment += "This PR is properly implemented and has no significant issues. It can be merged after standard review.\n"
        else:
            comment += "This PR has issues that should be addressed before merging. Please review the issues listed above.\n"

        return comment

    def post_comment_to_pr(self, repo_url: str, pr_number: int, comment: str) -> bool:
        """
        Post a comment to a pull request.

        Args:
            repo_url: The repository URL or owner/repo string
            pr_number: The pull request number
            comment: The comment to post

        Returns:
            True if the comment was posted successfully, False otherwise
        """
        from github import Github

        if not self.github_token:
            logger.error("GitHub token is required to post comments")
            return False

        try:
            # Parse the repo URL to get owner and repo name
            if "/" in repo_url and "github.com" not in repo_url:
                owner, repo_name = repo_url.split("/")
            else:
                # Extract owner/repo from a full GitHub URL
                parts = repo_url.rstrip("/").split("/")
                owner = parts[-2]
                repo_name = parts[-1]
                if repo_name.endswith(".git"):
                    repo_name = repo_name[:-4]

            # Post the comment to GitHub
            g = Github(self.github_token)
            repo = g.get_repo(f"{owner}/{repo_name}")
            pr = repo.get_pull(pr_number)
            pr.create_issue_comment(comment)

            return True
        except Exception as e:
            logger.error(f"Failed to post comment to PR: {e}")
            return False

    def post_pr_comment(self, repo: str, pr_number: int, comment: str) -> bool:
        """
        Post a comment on a pull request.

        Args:
            repo: Repository in the format "owner/repo"
            pr_number: PR number
            comment: Comment text

        Returns:
            True if successful, False otherwise
        """
        from github import Github

        if not self.github_token:
            logger.error("GitHub token is required to post comments")
            return False

        try:
            # Parse repository owner and name
            owner, repo_name = repo.split("/")

            # Initialize GitHub client
            g = Github(self.github_token)
            repo_obj = g.get_repo(f"{owner}/{repo_name}")
            pr = repo_obj.get_pull(pr_number)

            # Post the comment to GitHub
            pr.create_issue_comment(comment)

            return True
        except Exception as e:
            logger.error(f"Failed to post comment to PR: {e}")
            return False

    def analyze_and_comment_on_pr(
        self,
        repo_url: str,
        pr_number: int,
        post_comment: bool = True,
        detailed: bool = False,
    ) -> Dict[str, Any]:
        """
        Analyze a pull request and optionally post a comment with the results.

        Args:
            repo_url: The repository URL or owner/repo string
            pr_number: The pull request number
            post_comment: Whether to post a comment to the PR with the analysis results
            detailed: Whether to include detailed analysis in the results

        Returns:
            A dictionary with analysis results
        """
        # Analyze the PR
        analysis_results = self.analyze_pull_request(repo_url, pr_number, detailed)

        # Create a comment for the PR
        comment = self.create_comment_for_pr(repo_url, pr_number, analysis_results)

        # Post the comment if requested
        if post_comment:
            comment_posted = self.post_comment_to_pr(repo_url, pr_number, comment)
            analysis_results["comment_posted"] = comment_posted

        # Add the comment to the results
        analysis_results["comment"] = comment
        
        return analysis_results

    def get_pr_file_content(self, repo: str, pr_number: int) -> Dict[str, str]:
        """
        Get the content of files changed in a pull request.
        
        Args:
            repo: Repository in the format "owner/repo"
            pr_number: PR number
            
        Returns:
            A dictionary mapping file paths to their content
        """
        try:
            from github import Github, GithubException
            
            if not self.github_token:
                logger.error("GitHub token is required to get PR file content")
                return {}
                
            owner, repo_name = repo.split('/')
            g = Github(self.github_token)
            repo_obj = g.get_repo(f"{owner}/{repo_name}")
            pr = repo_obj.get_pull(pr_number)
            files = pr.get_files()
            
            file_content = {}
            for file in files:
                try:
                    content = repo_obj.get_contents(file.filename, ref=pr.head.ref).decoded_content.decode('utf-8')
                    file_content[file.filename] = content
                except GithubException as e:
                    logger.warning(f"GitHub API error for {file.filename}: {e.data.get('message', str(e))}")
                except UnicodeDecodeError as e:
                    logger.warning(f"Unicode decode error for {file.filename}: {str(e)}")
                except Exception as e:
                    logger.warning(f"Unexpected error for {file.filename}: {str(e)}")
            return file_content
        
        except ValueError as e:
            logger.error(f"Invalid repository format: {str(e)}")
        except GithubException as e:
            logger.error(f"GitHub API error: {e.data.get('message', str(e))}")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
        return {}


# Example usage
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Analyze commits and pull requests")
    parser.add_argument("--repo", required=True, help="Repository URL or owner/repo string")
    parser.add_argument("--pr", type=int, help="Pull request number to analyze")
    parser.add_argument("--base", help="Base commit SHA (required if --pr not provided)")
    parser.add_argument("--head", help="Head commit SHA (required if --pr not provided)")
    parser.add_argument("--token", help="GitHub token for private repositories")
    parser.add_argument("--snapshot-dir", help="Directory to store snapshots")
    parser.add_argument(
        "--detailed", action="store_true", help="Include detailed analysis in results"
    )
    parser.add_argument("--no-agent", action="store_true", help="Disable LLM-based agent analysis")
    parser.add_argument(
        "--comment",
        action="store_true",
        help="Post a comment to the PR with analysis results",
    )
    parser.add_argument("--agent-api-key", help="API key for the LLM-based agent service")
    parser.add_argument("--agent-api-url", help="URL for the LLM-based agent service")

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Create the agent
    agent = SWEHarnessAgent(
        github_token=args.token,
        snapshot_dir=args.snapshot_dir,
        use_agent=not args.no_agent,
        agent_api_key=args.agent_api_key,
        agent_api_url=args.agent_api_url,
    )

    # Analyze PR or commit
    if args.pr:
        results = agent.analyze_and_comment_on_pr(args.repo, args.pr, args.comment, args.detailed)
    elif args.base and args.head:
        results = agent.analyze_commit(args.repo, args.base, args.head, args.detailed)
    else:
        parser.error("Either --pr or both --base and --head must be provided")

    # Print the results
    print(json.dumps(results, indent=2))
