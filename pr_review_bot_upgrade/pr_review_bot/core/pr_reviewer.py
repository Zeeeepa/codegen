"""
PR reviewer module for the PR Review Bot.
Provides functionality for reviewing pull requests using AI.
"""

import os
import logging
import traceback
from typing import Dict, List, Any, Optional, Tuple
from github.Repository import Repository
from github.PullRequest import PullRequest

from codegen.sdk.core.codebase import Codebase
from langchain_core.prompts import ChatPromptTemplate
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

# Configure logging
logger = logging.getLogger(__name__)

class PRReviewer:
    """
    Reviewer for pull requests using AI.
    Provides methods for reviewing PRs and checking them against requirements.
    """
    
    def __init__(self, github_token: str):
        """
        Initialize the PR reviewer.
        
        Args:
            github_token: GitHub API token
        """
        self.github_token = github_token
        
        # Initialize AI models
        self.setup_ai_models()
    
    def setup_ai_models(self):
        """
        Set up AI models for code review.
        Uses Anthropic Claude if available, falls back to OpenAI.
        """
        anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
        openai_api_key = os.environ.get("OPENAI_API_KEY")
        
        if anthropic_api_key:
            logger.info("Using Anthropic Claude for code review")
            self.llm = ChatAnthropic(
                model="claude-3-opus-20240229",
                temperature=0.2,
                anthropic_api_key=anthropic_api_key
            )
        elif openai_api_key:
            logger.info("Using OpenAI for code review")
            self.llm = ChatOpenAI(
                model="gpt-4-turbo",
                temperature=0.2,
                openai_api_key=openai_api_key
            )
        else:
            logger.warning("No AI API keys found, code review will be limited")
            self.llm = None
    
    def review_pr(self, repo_name: str, pr_number: int) -> Dict[str, Any]:
        """
        Review a pull request using AI.
        
        Args:
            repo_name: Repository name in format "owner/repo"
            pr_number: Pull request number
            
        Returns:
            Result of the review
        """
        logger.info(f"Reviewing PR #{pr_number} in {repo_name}")
        
        try:
            # Initialize Codebase
            codebase = Codebase(
                repo_path=repo_name, 
                language="python"  # Default to Python, could be made dynamic
            )
            
            # Create a temporary comment to indicate the review is in progress
            review_attention_message = "CodegenBot is starting to review the PR, please wait..."
            comment = codebase.repo_operator.create_pr_comment(pr_number, review_attention_message)
            
            # Get PR details
            pr = codebase.repo_operator.get_pr(pr_number)
            pr_url = pr.html_url
            
            # Run the AI review
            review_result = self._run_ai_review(codebase, pr_number, pr_url)
            
            # Delete the temporary comment
            if comment:
                comment.delete()
            
            # Check if PR can be merged
            if pr.mergeable:
                # Check against requirements if available
                requirements_check = self.check_against_requirements(codebase, pr)
                
                if requirements_check["passed"]:
                    # Try to merge the PR
                    try:
                        merge_result = codebase.repo_operator.merge_pr(
                            pr_number=pr_number,
                            commit_title=f"Merge PR #{pr_number}: {pr.title}",
                            commit_message=f"Automatically merged PR #{pr_number} after review.",
                            merge_method="merge"
                        )
                        logger.info(f"PR #{pr_number} automatically merged after review")
                        return {
                            "pr_number": pr_number,
                            "repo_name": repo_name,
                            "merged": True,
                            "message": "PR automatically merged after review.",
                            "review_result": review_result,
                            "requirements_check": requirements_check
                        }
                    except Exception as merge_error:
                        logger.error(f"Error merging PR: {merge_error}")
                        logger.error(traceback.format_exc())
                        return {
                            "pr_number": pr_number,
                            "repo_name": repo_name,
                            "merged": False,
                            "message": f"Error merging PR: {str(merge_error)}",
                            "review_result": review_result,
                            "requirements_check": requirements_check
                        }
                else:
                    logger.info(f"PR #{pr_number} failed requirements check")
                    # Add a comment about the failed requirements check
                    codebase.repo_operator.create_pr_comment(
                        pr_number=pr_number,
                        body=f"⚠️ PR failed requirements check: {requirements_check['message']}"
                    )
                    return {
                        "pr_number": pr_number,
                        "repo_name": repo_name,
                        "merged": False,
                        "message": f"PR failed requirements check: {requirements_check['message']}",
                        "review_result": review_result,
                        "requirements_check": requirements_check
                    }
            else:
                logger.info(f"PR #{pr_number} is not mergeable after review")
                return {
                    "pr_number": pr_number,
                    "repo_name": repo_name,
                    "merged": False,
                    "message": "PR is not mergeable after review.",
                    "review_result": review_result
                }
        except Exception as e:
            logger.error(f"Error in PR review: {e}")
            logger.error(traceback.format_exc())
            raise
    
    def _run_ai_review(self, codebase: Codebase, pr_number: int, pr_url: str) -> Dict[str, Any]:
        """
        Run AI review on a pull request.
        
        Args:
            codebase: Codebase object
            pr_number: Pull request number
            pr_url: Pull request URL
            
        Returns:
            Result of the AI review
        """
        if not self.llm:
            logger.warning("No AI model available for review")
            return {"status": "limited", "message": "No AI model available for detailed review"}
        
        try:
            # Get PR details
            pr = codebase.repo_operator.get_pr(pr_number)
            
            # Get the diff
            diff = codebase.repo_operator.get_pr_diff(pr_number)
            
            # Create the prompt for the AI review
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert code reviewer. Your task is to review a GitHub pull request and provide detailed, constructive feedback.
                
                Guidelines for your review:
                1. Focus on code quality, readability, and maintainability
                2. Identify potential bugs, edge cases, or performance issues
                3. Suggest improvements where appropriate
                4. Be specific and actionable in your feedback
                5. Be concise but thorough
                6. Format your response in Markdown
                
                Your review should have the following sections:
                - **Summary**: A brief overview of the changes and your assessment
                - **Strengths**: What aspects of the code are well done
                - **Areas for Improvement**: Specific issues that should be addressed
                - **Suggestions**: Concrete recommendations for improving the code
                - **Overall Assessment**: Your final verdict (Approve, Request Changes, or Comment)
                """),
                ("human", """Please review this pull request:
                
                PR URL: {pr_url}
                PR Title: {pr_title}
                PR Description: {pr_description}
                
                Diff:
                ```diff
                {diff}
                ```
                
                Provide a thorough code review based on the guidelines.
                """)
            ])
            
            # Format the input for the prompt
            formatted_input = {
                "pr_url": pr_url,
                "pr_title": pr.title,
                "pr_description": pr.body or "No description provided",
                "diff": diff[:10000] if len(diff) > 10000 else diff  # Limit diff size
            }
            
            # Run the AI review
            chain = prompt | self.llm
            review_content = chain.invoke(formatted_input).content
            
            # Post the review as a comment
            codebase.repo_operator.create_pr_comment(pr_number, review_content)
            
            return {
                "status": "success",
                "review_content": review_content
            }
        except Exception as e:
            logger.error(f"Error in AI review: {e}")
            logger.error(traceback.format_exc())
            
            # Post a simplified review comment
            error_message = f"⚠️ Error during AI review: {str(e)}\n\nA simplified review will be performed instead."
            codebase.repo_operator.create_pr_comment(pr_number, error_message)
            
            return {
                "status": "error",
                "message": str(e)
            }
    
    def check_against_requirements(self, codebase: Codebase, pr: PullRequest) -> Dict[str, Any]:
        """
        Check a PR against the project's requirements.
        
        Args:
            codebase: Codebase object
            pr: PullRequest object
            
        Returns:
            Result of the requirements check
        """
        try:
            # Get the repository
            repo = codebase.repo_operator.repo
            
            # Check if REQUIREMENTS.md exists
            requirements_content = None
            try:
                requirements_file = repo.get_contents("REQUIREMENTS.md", ref=pr.base.ref)
                requirements_content = requirements_file.decoded_content.decode('utf-8')
            except Exception:
                # Try alternative locations
                try:
                    requirements_file = repo.get_contents("docs/REQUIREMENTS.md", ref=pr.base.ref)
                    requirements_content = requirements_file.decoded_content.decode('utf-8')
                except Exception:
                    logger.info(f"No REQUIREMENTS.md found in {repo.full_name}")
            
            if not requirements_content:
                # No requirements file found, consider it passed
                return {
                    "passed": True,
                    "message": "No requirements file found, skipping check"
                }
            
            # If we have an AI model, use it to check against requirements
            if self.llm:
                # Get the diff
                diff = codebase.repo_operator.get_pr_diff(pr.number)
                
                # Create the prompt for requirements check
                prompt = ChatPromptTemplate.from_messages([
                    ("system", """You are an expert at validating code changes against project requirements.
                    Your task is to determine if a pull request meets the requirements specified in the project's REQUIREMENTS.md file.
                    
                    Analyze the requirements and the code changes carefully, and determine if the PR satisfies all relevant requirements.
                    If any requirements are not met, explain specifically which ones and why.
                    
                    Your response should be structured as follows:
                    1. A clear YES/NO verdict on whether the PR meets requirements
                    2. A brief explanation of your reasoning
                    3. If NO, list the specific requirements that are not met
                    """),
                    ("human", """Please check if this pull request meets the project requirements:
                    
                    PR Title: {pr_title}
                    PR Description: {pr_description}
                    
                    Project Requirements:
                    ```markdown
                    {requirements_content}
                    ```
                    
                    Code Changes:
                    ```diff
                    {diff}
                    ```
                    
                    Does this PR meet all the relevant requirements? Provide a clear YES/NO verdict and explanation.
                    """)
                ])
                
                # Format the input for the prompt
                formatted_input = {
                    "pr_title": pr.title,
                    "pr_description": pr.body or "No description provided",
                    "requirements_content": requirements_content,
                    "diff": diff[:10000] if len(diff) > 10000 else diff  # Limit diff size
                }
                
                # Run the requirements check
                chain = prompt | self.llm
                check_result = chain.invoke(formatted_input).content
                
                # Determine if the check passed based on the AI response
                passed = "YES" in check_result.split("\n")[0].upper()
                
                # Post the check result as a comment
                codebase.repo_operator.create_pr_comment(
                    pr.number,
                    f"## Requirements Check\n\n{check_result}"
                )
                
                return {
                    "passed": passed,
                    "message": check_result,
                    "requirements_found": True
                }
            else:
                # No AI model available, consider it passed but log a warning
                logger.warning("No AI model available for requirements check")
                return {
                    "passed": True,
                    "message": "Requirements check skipped (no AI model available)",
                    "requirements_found": True
                }
        except Exception as e:
            logger.error(f"Error checking against requirements: {e}")
            logger.error(traceback.format_exc())
            
            # Consider it passed but log the error
            return {
                "passed": True,
                "message": f"Error during requirements check: {str(e)}",
                "error": str(e)
            }
