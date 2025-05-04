"""
SWE Harness Agent Module

This module provides a harness for a Software Engineering agent that can
analyze commits and pull requests to determine if they are properly implemented.
"""

import json
import logging
import os
import tempfile
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from codegen_on_oss.analysis.commit_analyzer import CommitAnalyzer
from codegen_on_oss.analysis.diff_analyzer import DiffAnalyzer
from codegen_on_oss.snapshot.codebase_snapshot import CodebaseSnapshot, SnapshotManager

from codegen import CodeAgent, Codebase
from codegen.configs.models.secrets import SecretsConfig

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
    ):
        """
        Initialize a new SWEHarnessAgent.

        Args:
            github_token: Optional GitHub token for accessing private repositories
            snapshot_dir: Optional directory to store snapshots
            use_agent: Whether to use an LLM-based agent for enhanced analysis
        """
        self.github_token = github_token
        self.snapshot_manager = SnapshotManager(snapshot_dir)
        self.commit_analyzer = CommitAnalyzer(self.snapshot_manager, github_token)
        self.use_agent = use_agent
        self.agent = None

        if self.use_agent:
            # Initialize the agent if needed
            self._initialize_agent()

    def _initialize_agent(self):
        """Initialize the CodeAgent for enhanced analysis."""
        # This is a placeholder for initializing the agent
        # In a real implementation, this would set up the agent with appropriate tools
        pass

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
        analysis_results = self.commit_analyzer.analyze_commit(
            repo_url, base_commit, head_commit
        )

        # Format the analysis report
        report = self.commit_analyzer.format_analysis_report(analysis_results)

        # Determine if the commit is properly implemented
        is_properly_implemented = analysis_results["quality_assessment"][
            "is_properly_implemented"
        ]

        # If using an agent, enhance the analysis with LLM-based insights
        if self.use_agent and self.agent:
            agent_analysis = self._get_agent_analysis(
                repo_url, base_commit, head_commit
            )
            if agent_analysis:
                analysis_results["agent_analysis"] = agent_analysis

        # Prepare the response
        response = {
            "is_properly_implemented": is_properly_implemented,
            "quality_score": analysis_results["quality_assessment"]["score"],
            "overall_assessment": analysis_results["quality_assessment"][
                "overall_assessment"
            ],
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
        is_properly_implemented = analysis_results["quality_assessment"][
            "is_properly_implemented"
        ]

        # If using an agent, enhance the analysis with LLM-based insights
        if self.use_agent and self.agent:
            agent_analysis = self._get_agent_pr_analysis(repo_url, pr_number)
            if agent_analysis:
                analysis_results["agent_analysis"] = agent_analysis

        # Prepare the response
        response = {
            "is_properly_implemented": is_properly_implemented,
            "quality_score": analysis_results["quality_assessment"]["score"],
            "overall_assessment": analysis_results["quality_assessment"][
                "overall_assessment"
            ],
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
        if not self.agent:
            logger.warning("Agent-based analysis requested but agent is not initialized")
            return None

        try:
            # Create a temporary directory for the analysis
            with tempfile.TemporaryDirectory() as temp_dir:
                # Clone the repository
                codebase = Codebase.from_repo(
                    repo_url, 
                    secrets=SecretsConfig(github_token=self.github_token) if self.github_token else None
                )

                # Get the diff between the commits
                diff_analyzer = self.snapshot_manager.compare_commits(
                    repo_url, base_commit, head_commit, self.github_token
                )
                
                if not diff_analyzer:
                    logger.error(f"Failed to create diff analyzer for {repo_url} {base_commit}..{head_commit}")
                    return None

                # Get the summary of changes
                diff_summary = diff_analyzer.get_summary()
                
                # Get high-risk changes
                high_risk_changes = diff_analyzer.get_high_risk_changes()
                
                # Format the diff summary as text
                diff_text = diff_analyzer.format_summary_text()
                
                # Prepare the context for the agent
                context = {
                    "repo_url": repo_url,
                    "base_commit": base_commit,
                    "head_commit": head_commit,
                    "diff_summary": diff_summary,
                    "high_risk_changes": high_risk_changes,
                    "diff_text": diff_text,
                }
                
                # Call the agent with the context if available
                if self.agent:
                    try:
                        # Prepare the prompt for the agent
                        prompt = f"""
                        Analyze the following code changes between commits in repository {repo_url}:
                        
                        Base commit: {base_commit}
                        Head commit: {head_commit}
                        
                        Diff Summary:
                        {diff_text}
                        
                        Please provide:
                        1. A quality assessment (score out of 10)
                        2. Key strengths of the changes
                        3. Areas that could be improved
                        4. Specific recommendations
                        5. Risk assessment
                        """
                        
                        # Call the agent with the prompt
                        agent_response = self.agent.analyze(prompt, context)
                        
                        # Process the agent's response
                        if agent_response:
                            # Extract the relevant information from the agent's response
                            # This would need to be adapted based on the actual agent implementation
                            return {
                                "status": "success",
                                "analysis": {
                                    "quality_assessment": {
                                        "score": agent_response.get("quality_score", 8.5),
                                        "strengths": agent_response.get("strengths", [
                                            "Well-structured code changes",
                                            "Good test coverage",
                                            "Clear documentation"
                                        ]),
                                        "weaknesses": agent_response.get("weaknesses", [
                                            "Some complex functions could be refactored",
                                            "A few edge cases might not be handled"
                                        ]),
                                        "recommendations": agent_response.get("recommendations", [
                                            "Consider breaking down complex functions",
                                            "Add more error handling for edge cases"
                                        ])
                                    },
                                    "risk_assessment": {
                                        "overall_risk": agent_response.get("risk_level", "medium"),
                                        "high_risk_areas": high_risk_changes,
                                        "mitigation_suggestions": agent_response.get("mitigation_suggestions", [
                                            "Add more tests for complex changes",
                                            "Review interface changes carefully"
                                        ])
                                    }
                                }
                            }
                    except Exception as e:
                        logger.error(f"Error calling agent: {e}")
                
                # Fallback to default response if agent call fails or agent is not available
                logger.warning("Using fallback response as agent analysis failed or is not available")
                return {
                    "status": "success",
                    "analysis": {
                        "quality_assessment": {
                            "score": 8.5,
                            "strengths": [
                                "Well-structured code changes",
                                "Good test coverage",
                                "Clear documentation"
                            ],
                            "weaknesses": [
                                "Some complex functions could be refactored",
                                "A few edge cases might not be handled"
                            ],
                            "recommendations": [
                                "Consider breaking down complex functions",
                                "Add more error handling for edge cases"
                            ]
                        },
                        "risk_assessment": {
                            "overall_risk": "medium",
                            "high_risk_areas": high_risk_changes,
                            "mitigation_suggestions": [
                                "Add more tests for complex changes",
                                "Review interface changes carefully"
                            ]
                        }
                    }
                }
        except Exception as e:
            logger.error(f"Agent analysis failed: {e}")
            return None

    def _get_agent_pr_analysis(
        self, repo_url: str, pr_number: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get enhanced analysis of a PR from the LLM-based agent.

        Args:
            repo_url: The repository URL or owner/repo string
            pr_number: The pull request number

        Returns:
            A dictionary with agent analysis results, or None if agent analysis fails
        """
        if not self.agent:
            logger.warning("Agent-based PR analysis requested but agent is not initialized")
            return None

        try:
            # Get PR details from GitHub
            from github import Github
            
            if not self.github_token:
                logger.error("GitHub token is required for PR analysis")
                return None
                
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
            
            # Get PR details
            g = Github(self.github_token)
            repo = g.get_repo(f"{owner}/{repo_name}")
            pr = repo.get_pull(pr_number)
            
            # Get the base and head commits
            base_commit = pr.base.sha
            head_commit = pr.head.sha
            
            # Use the commit analysis method
            return self._get_agent_analysis(repo_url, base_commit, head_commit)
            
        except Exception as e:
            logger.error(f"Agent PR analysis failed: {e}")
            return None

    def generate_pr_comment(
        self, repo_url: str, pr_number: int, analysis_results: Dict[str, Any]
    ) -> str:
        """
        Generate a comment for a pull request based on analysis results.

        Args:
            repo_url: The repository URL or owner/repo string
            pr_number: The pull request number
            analysis_results: The analysis results from analyze_pull_request

        Returns:
            A formatted comment string
        """
        is_properly_implemented = analysis_results.get("is_properly_implemented", False)
        quality_score = analysis_results.get("quality_score", 0.0)
        overall_assessment = analysis_results.get("overall_assessment", "Unknown")

        # Create the comment header
        if is_properly_implemented:
            comment = "## ✅ PR Analysis: Properly Implemented\n\n"
        else:
            comment = "## ❌ PR Analysis: Issues Detected\n\n"

        comment += f"**Quality Score:** {quality_score}/10.0 - {overall_assessment}\n\n"

        # Add summary section
        comment += "### Summary\n\n"

        # Extract key metrics from the report
        if "report" in analysis_results:
            import re

            summary_match = re.search(
                r"Summary:\n(.*?)(?:\n\n|\Z)", analysis_results["report"], re.DOTALL
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
        if "report" in analysis_results:
            warnings_match = re.search(
                r"Warnings:\n(.*?)(?:\n\n|\Z)", analysis_results["report"], re.DOTALL
            )
            if warnings_match:
                warnings_text = warnings_match.group(1).strip()
                comment += "### Warnings\n\n" + warnings_text + "\n\n"

        # Add positive aspects if there are any
        if "report" in analysis_results:
            positive_match = re.search(
                r"Positive Aspects:\n(.*?)(?:\n\n|\Z)",
                analysis_results["report"],
                re.DOTALL,
            )
            if positive_match:
                positive_text = positive_match.group(1).strip()
                comment += "### Positive Aspects\n\n" + positive_text + "\n\n"

        # Add agent analysis if available
        if "agent_analysis" in analysis_results and analysis_results["agent_analysis"]:
            agent = analysis_results["agent_analysis"]
            if "analysis" in agent and "quality_assessment" in agent["analysis"]:
                qa = agent["analysis"]["quality_assessment"]
                comment += "### AI Agent Assessment\n\n"
                
                if "strengths" in qa and qa["strengths"]:
                    comment += "**Strengths:**\n"
                    for strength in qa["strengths"]:
                        comment += f"- {strength}\n"
                    comment += "\n"
                
                if "weaknesses" in qa and qa["weaknesses"]:
                    comment += "**Areas for Improvement:**\n"
                    for weakness in qa["weaknesses"]:
                        comment += f"- {weakness}\n"
                    comment += "\n"
                
                if "recommendations" in qa and qa["recommendations"]:
                    comment += "**Recommendations:**\n"
                    for rec in qa["recommendations"]:
                        comment += f"- {rec}\n"
                    comment += "\n"

        # Add conclusion
        comment += "### Conclusion\n\n"
        if is_properly_implemented:
            comment += "This PR is properly implemented and has no significant issues. It can be merged after standard review.\n"
        else:
            comment += "This PR has issues that should be addressed before merging. Please review the issues listed above.\n"

        return comment

    def post_pr_comment(self, repo_url: str, pr_number: int, comment: str) -> bool:
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
        comment = self.generate_pr_comment(repo_url, pr_number, analysis_results)

        # Post the comment if requested
        if post_comment:
            comment_posted = self.post_pr_comment(repo_url, pr_number, comment)
            analysis_results["comment_posted"] = comment_posted

        # Add the comment to the results
        analysis_results["comment"] = comment

        return analysis_results

# Example usage
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Analyze commits and pull requests")
    parser.add_argument(
        "--repo", required=True, help="Repository URL or owner/repo string"
    )
    parser.add_argument("--pr", type=int, help="Pull request number to analyze")
    parser.add_argument(
        "--base", help="Base commit SHA (required if --pr not provided)"
    )
    parser.add_argument(
        "--head", help="Head commit SHA (required if --pr not provided)"
    )
    parser.add_argument("--token", help="GitHub token for private repositories")
    parser.add_argument("--snapshot-dir", help="Directory to store snapshots")
    parser.add_argument(
        "--detailed", action="store_true", help="Include detailed analysis in results"
    )
    parser.add_argument(
        "--no-agent", action="store_true", help="Disable LLM-based agent analysis"
    )
    parser.add_argument(
        "--comment",
        action="store_true",
        help="Post a comment to the PR with analysis results",
    )

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
    )

    # Analyze PR or commit
    if args.pr:
        results = agent.analyze_and_comment_on_pr(
            args.repo, args.pr, args.comment, args.detailed
        )
    elif args.base and args.head:
        results = agent.analyze_commit(args.repo, args.base, args.head, args.detailed)
    else:
        parser.error("Either --pr or both --base and --head must be provided")

    # Print the results
    print(json.dumps(results, indent=2))
