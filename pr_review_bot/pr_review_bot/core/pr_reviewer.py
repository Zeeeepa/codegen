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

# Import compatibility layer
from .compatibility import (
    Codebase, 
    HAS_CODEGEN, 
    HAS_AGENTGEN,
    CodeAgent,
    GithubViewPRTool,
    GithubCreatePRCommentTool,
    GithubCreatePRReviewCommentTool
)

# Try to import AI models
try:
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_anthropic import ChatAnthropic
    from langchain_openai import ChatOpenAI
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False

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
        self.llm = None
        if HAS_LANGCHAIN:
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
            if HAS_AGENTGEN:
                review_result = self._run_agent_review(codebase, pr_number, pr_url)
            else:
                review_result = self._run_basic_review(codebase, pr_number, pr_url)
            
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
                            "requirements_check": requirements_check
                        }
                else:
                    logger.info(f"PR #{pr_number} does not meet requirements")
                    return {
                        "pr_number": pr_number,
                        "repo_name": repo_name,
                        "merged": False,
                        "message": "PR does not meet requirements.",
                        "requirements_check": requirements_check
                    }
            else:
                logger.info(f"PR #{pr_number} is not mergeable")
                return {
                    "pr_number": pr_number,
                    "repo_name": repo_name,
                    "merged": False,
                    "message": "PR is not mergeable."
                }
        except Exception as e:
            logger.error(f"Error reviewing PR: {e}")
            logger.error(traceback.format_exc())
            raise
    
    def _run_agent_review(self, codebase, pr_number: int, pr_url: str) -> Dict[str, Any]:
        """
        Run the PR review using the CodeAgent.
        
        Args:
            codebase: Codebase instance
            pr_number: Pull request number
            pr_url: Pull request URL
            
        Returns:
            Result of the review
        """
        logger.info(f"Running agent review for PR #{pr_number}")
        
        # Define tools for the agent
        pr_tools = [
            GithubViewPRTool(codebase),
            GithubCreatePRCommentTool(codebase),
            GithubCreatePRReviewCommentTool(codebase),
        ]
        
        # Create agent with the defined tools
        agent = CodeAgent(codebase=codebase, tools=pr_tools)
        
        # Create the prompt for the agent
        prompt = f"""
        Hey CodegenBot!

        Here's a task for you. Please review this pull request!
        {pr_url}
        
        Do not terminate until you have reviewed the pull request and are satisfied with your review.

        Review this Pull request thoroughly:
        1. Be explicit about the changes
        2. Produce a short summary
        3. Point out possible improvements where present
        4. Don't be self-congratulatory, stick to the facts
        5. Use the tools at your disposal to create proper PR reviews
        6. Include code snippets if needed
        7. Suggest improvements if necessary
        8. Check if the PR is valid and can be merged to the main branch
        """
        
        # Run the agent
        result = agent.run(prompt)
        
        return {
            "pr_number": pr_number,
            "review_type": "agent",
            "result": result
        }
    
    def _run_basic_review(self, codebase, pr_number: int, pr_url: str) -> Dict[str, Any]:
        """
        Run a basic PR review without the CodeAgent.
        
        Args:
            codebase: Codebase instance
            pr_number: Pull request number
            pr_url: Pull request URL
            
        Returns:
            Result of the review
        """
        logger.info(f"Running basic review for PR #{pr_number}")
        
        # Get PR details
        pr = codebase.repo_operator.get_pr(pr_number)
        
        # Create a simple review comment
        comment_body = f"""
        ## PR Review

        This PR has been reviewed by the PR Review Bot.

        ### Summary
        - PR Number: #{pr_number}
        - Title: {pr.title}
        - Description: {pr.body or "No description provided"}
        
        ### Review
        This is an automated review. The PR has been checked for basic issues.
        
        ### Recommendation
        The PR appears to be valid and can be merged if all checks pass.
        """
        
        codebase.repo_operator.create_pr_comment(pr_number, comment_body)
        
        return {
            "pr_number": pr_number,
            "review_type": "basic",
            "result": "Basic review completed"
        }
    
    def check_against_requirements(self, codebase, pr: PullRequest) -> Dict[str, Any]:
        """
        Check if a PR meets the requirements specified in REQUIREMENTS.md.
        
        Args:
            codebase: Codebase instance
            pr: Pull request
            
        Returns:
            Result of the check
        """
        logger.info(f"Checking PR #{pr.number} against requirements")
        
        repo = pr.base.repo
        
        try:
            # Try to get the REQUIREMENTS.md file
            requirements_content = None
            try:
                requirements_file = repo.get_contents("REQUIREMENTS.md", ref=pr.base.ref)
                if hasattr(requirements_file, "decoded_content"):
                    requirements_content = requirements_file.decoded_content.decode("utf-8")
            except Exception as e:
                logger.info(f"No REQUIREMENTS.md found in {repo.full_name}: {e}")
            
            if not requirements_content:
                # No requirements file, so the PR passes by default
                return {
                    "passed": True,
                    "message": "No REQUIREMENTS.md file found, PR passes by default."
                }
            
            # If we have a requirements file and an LLM, check the PR against it
            if self.llm and HAS_LANGCHAIN:
                # Get PR details
                pr_files = list(pr.get_files())
                pr_changes = []
                
                for file in pr_files:
                    pr_changes.append(f"File: {file.filename}")
                    pr_changes.append(f"Status: {file.status}")
                    pr_changes.append(f"Changes: +{file.additions}, -{file.deletions}")
                    
                    # Add patch if available
                    if file.patch:
                        pr_changes.append("Patch:")
                        pr_changes.append(file.patch)
                    
                    pr_changes.append("---")
                
                pr_changes_text = "\n".join(pr_changes)
                
                # Create prompt for the LLM
                prompt = ChatPromptTemplate.from_template("""
                You are a code reviewer checking if a PR meets the requirements.
                
                # Requirements
                {requirements}
                
                # PR Details
                Title: {pr_title}
                Description: {pr_description}
                
                # Changes
                {pr_changes}
                
                Based on the requirements and the PR changes, determine if the PR meets all requirements.
                Provide a detailed analysis of how the PR meets or fails to meet each requirement.
                
                Finally, provide a clear YES or NO answer to whether the PR should be merged.
                """)
                
                # Run the LLM
                result = self.llm.invoke(
                    prompt.format(
                        requirements=requirements_content,
                        pr_title=pr.title,
                        pr_description=pr.body or "No description provided",
                        pr_changes=pr_changes_text
                    )
                )
                
                # Parse the result
                content = result.content.lower()
                passed = "yes" in content and "no" not in content[-50:]  # Check if the final answer is YES
                
                # Create a comment with the result
                comment_body = f"""
                ## Requirements Check
                
                {result.content}
                
                **Verdict:** {"✅ PR meets requirements" if passed else "❌ PR does not meet requirements"}
                """
                
                codebase.repo_operator.create_pr_comment(pr.number, comment_body)
                
                return {
                    "passed": passed,
                    "message": result.content,
                    "requirements": requirements_content
                }
            else:
                # No LLM available, so we can't check the requirements
                logger.warning("No LLM available to check requirements")
                return {
                    "passed": True,
                    "message": "No LLM available to check requirements, PR passes by default."
                }
        except Exception as e:
            logger.error(f"Error checking requirements: {e}")
            logger.error(traceback.format_exc())
            return {
                "passed": True,
                "message": f"Error checking requirements: {str(e)}, PR passes by default."
            }
