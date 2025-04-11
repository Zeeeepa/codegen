"""
PR Review Controller for PR Review Agent.
This module provides the main controller for coordinating the PR review process.
"""
import os
import logging
import traceback
from typing import Dict, List, Any, Optional, Tuple
from github import Github, PullRequest, Repository
from ..validators.documentation_service import DocumentationValidationService
from ..utils.github_client import GitHubClient
from ..utils.slack_notifier import SlackNotifier
from ..utils.storage_manager import StorageManager
from ..utils.ai_service import AIService
logger = logging.getLogger(__name__)
class PRReviewController:
    """
    Controller for coordinating the PR review process.
    
    Handles the workflow for reviewing PRs, validating them against requirements,
    and providing feedback.
    """
    
    def __init__(self, config: Dict[str, Any], repo_path: str):
        """
        Initialize the PR review controller.
        
        Args:
            config: Configuration dictionary
            repo_path: Path to the repository
        """
        self.config = config
        self.repo_path = repo_path
        
        # Initialize GitHub client
        github_token = config["github"]["token"]
        self.github_client = GitHubClient(github_token)
        
        # Initialize documentation validation service
        self.doc_validation_service = DocumentationValidationService(config, repo_path)
        
        # Initialize Slack notifier
        slack_enabled = config["notification"]["slack"]["enabled"]
        slack_token = config["notification"]["slack"]["token"]
        slack_channel = config["notification"]["slack"]["channel"]
        
        self.slack_notifier = SlackNotifier(
            enabled=slack_enabled,
            token=slack_token,
            default_channel=slack_channel
        )
        
        # Initialize storage manager
        storage_type = config["storage"]["type"]
        storage_path = config["storage"]["path"]
        
        self.storage_manager = StorageManager(
            storage_type=storage_type,
            storage_path=storage_path
        )
        
        # Initialize AI service
        ai_provider = config["ai"]["provider"]
        ai_model = config["ai"]["model"]
        ai_api_key = config["ai"]["api_key"]
        
        self.ai_service = AIService(
            provider=ai_provider,
            model=ai_model,
            api_key=ai_api_key,
            temperature=config["ai"]["temperature"],
            max_tokens=config["ai"]["max_tokens"]
        )
    
    def handle_pr_event(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a PR event from GitHub webhook.
        
        Args:
            event_type: Type of event (opened, synchronize, etc.)
            payload: Event payload
            
        Returns:
            Result of handling the event
        """
        try:
            # Extract PR details
            repo_name = payload["repository"]["full_name"]
            pr_number = payload["pull_request"]["number"]
            
            logger.info(f"Handling {event_type} event for PR #{pr_number} in {repo_name}")
            
            # Check if auto-review is enabled
            if not self.config["github"]["auto_review"]:
                logger.info("Auto-review is disabled, skipping")
                return {
                    "status": "skipped",
                    "message": "Auto-review is disabled"
                }
            
            # Check if PR has the review label
            if self.config["github"]["review_label"]:
                review_label = self.config["github"]["review_label"]
                labels = [label["name"] for label in payload["pull_request"]["labels"]]
                
                if review_label not in labels:
                    logger.info(f"PR does not have the review label '{review_label}', skipping")
                    return {
                        "status": "skipped",
                        "message": f"PR does not have the review label '{review_label}'"
                    }
            
            # Review the PR
            return self.review_pr(repo_name, pr_number)
        
        except Exception as e:
            logger.error(f"Error handling PR event: {e}")
            logger.error(traceback.format_exc())
            
            return {
                "status": "error",
                "message": f"Error handling PR event: {str(e)}"
            }
    
    def review_pr(self, repo_name: str, pr_number: int) -> Dict[str, Any]:
        """
        Review a pull request.
        
        Args:
            repo_name: Repository name (owner/repo)
            pr_number: Pull request number
            
        Returns:
            Result of the review
        """
        try:
            logger.info(f"Reviewing PR #{pr_number} in {repo_name}")
            
            # Get PR details
            pr = self.github_client.get_pull_request(repo_name, pr_number)
            
            # Create a comment to indicate that review is in progress
            comment_id = self.github_client.create_pr_comment(
                repo_name=repo_name,
                pr_number=pr_number,
                body="🔍 PR Review Agent is reviewing this PR. Please wait..."
            )
            
            # Validate PR against documentation
            doc_validation_results = self.doc_validation_service.validate_pr(repo_name, pr_number)
            
            # Generate AI-powered review
            ai_review = self._generate_ai_review(repo_name, pr_number)
            
            # Combine results
            review_results = {
                "pr_number": pr_number,
                "repo_name": repo_name,
                "documentation_validation": doc_validation_results,
                "ai_review": ai_review,
                "passed": doc_validation_results.get("passed", False) and ai_review.get("passed", False)
            }
            
            # Generate review comment
            review_comment = self._generate_review_comment(review_results)
            
            # Update the comment with review results
            if comment_id:
                self.github_client.update_pr_comment(
                    repo_name=repo_name,
                    comment_id=comment_id,
                    body=review_comment
                )
            else:
                # Create a new comment if update failed
                self.github_client.create_pr_comment(
                    repo_name=repo_name,
                    pr_number=pr_number,
                    body=review_comment
                )
            
            # Submit formal review
            self._submit_formal_review(repo_name, pr_number, review_results)
            
            # Send notification
            self._send_notification(repo_name, pr_number, review_results)
            
            # Save review results
            if not review_results["passed"]:
                self._save_review_results(repo_name, pr_number, review_results)
            
            # Auto-merge if enabled and review passed
            if self.config["github"]["auto_merge"] and review_results["passed"]:
                self._auto_merge_pr(repo_name, pr_number)
            
            return {
                "status": "success",
                "message": "PR review completed",
                "results": review_results
            }
        
        except Exception as e:
            logger.error(f"Error reviewing PR: {e}")
            logger.error(traceback.format_exc())
            
            # Create error comment
            self.github_client.create_pr_comment(
                repo_name=repo_name,
                pr_number=pr_number,
                body=f"❌ Error reviewing PR: {str(e)}"
            )
            
            return {
                "status": "error",
                "message": f"Error reviewing PR: {str(e)}"
            }
    
    def _generate_ai_review(self, repo_name: str, pr_number: int) -> Dict[str, Any]:
        """
        Generate an AI-powered review of the PR.
        
        Args:
            repo_name: Repository name (owner/repo)
            pr_number: Pull request number
            
        Returns:
            AI review results
        """
        try:
            # Get PR details
            pr = self.github_client.get_pull_request(repo_name, pr_number)
            pr_files = self.github_client.get_pr_files(repo_name, pr_number)
            pr_diff = self.github_client.get_pr_diff(repo_name, pr_number)
            
            # Prepare prompt for AI
            prompt = f"""
            You are a code reviewer reviewing a pull request. Please analyze the following PR and provide feedback.
            
            Repository: {repo_name}
            PR Number: {pr_number}
            PR Title: {pr.title}
            PR Description: {pr.body or "No description provided"}
            
            Files changed:
            {', '.join([f.filename for f in pr_files])}
            
            PR Diff:
            ```diff
            {pr_diff}
            ```
            
            Please provide a detailed review of this PR, including:
            1. Overall assessment
            2. Code quality issues
            3. Potential bugs or issues
            4. Suggestions for improvement
            5. Whether the PR should be approved or needs changes
            
            Format your response as a JSON object with the following structure:
            {
                "passed": true/false,
                "overall_assessment": "Your overall assessment",
                "issues": [
                    {"type": "code_quality", "message": "Issue description", "file": "file_path", "line": line_number},
                    ...
                ],
                "suggestions": [
                    {"description": "Suggestion description", "file": "file_path", "line": line_number},
                    ...
                ],
                "approval_recommendation": "approve" or "request_changes",
                "review_comment": "Your detailed review comment"
            }
            """
            
            # Generate AI review
            ai_response = self.ai_service.generate(prompt)
            
            # Parse AI response
            import json
            import re
            
            # Try to extract JSON from the response
            json_match = re.search(r'```json\s*(.*?)\s*```', ai_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_match = re.search(r'({.*})', ai_response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    logger.error("Could not extract JSON from AI response")
                    return {
                        "passed": False,
                        "overall_assessment": "Failed to generate AI review",
                        "issues": [],
                        "suggestions": [],
                        "approval_recommendation": "request_changes",
                        "review_comment": "Failed to generate AI review"
                    }
            
            try:
                ai_review = json.loads(json_str)
                return ai_review
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing AI response: {e}")
                return {
                    "passed": False,
                    "overall_assessment": "Failed to parse AI review",
                    "issues": [],
                    "suggestions": [],
                    "approval_recommendation": "request_changes",
                    "review_comment": "Failed to parse AI review"
                }
        
        except Exception as e:
            logger.error(f"Error generating AI review: {e}")
            logger.error(traceback.format_exc())
            
            return {
                "passed": False,
                "overall_assessment": f"Error generating AI review: {str(e)}",
                "issues": [],
                "suggestions": [],
                "approval_recommendation": "request_changes",
                "review_comment": f"Error generating AI review: {str(e)}"
            }
    
    def _generate_review_comment(self, review_results: Dict[str, Any]) -> str:
        """
        Generate a review comment based on review results.
        
        Args:
            review_results: Review results
            
        Returns:
            Review comment as a string
        """
        passed = review_results.get("passed", False)
        
        comment = []
        comment.append("# PR Review Agent Results\n")
        
        if passed:
            comment.append("## ✅ Review Passed\n")
            comment.append("This PR has passed all validation checks and is ready to be merged.\n")
        else:
            comment.append("## ❌ Review Failed\n")
            comment.append("This PR has failed one or more validation checks and needs changes.\n")
        
        # Add documentation validation results
        doc_validation = review_results.get("documentation_validation", {})
        doc_validation_report = self.doc_validation_service.generate_validation_report(doc_validation)
        comment.append("\n## Documentation Validation\n")
        comment.append(doc_validation_report)
        
        # Add AI review results
        ai_review = review_results.get("ai_review", {})
        comment.append("\n## AI Review\n")
        
        if ai_review.get("passed", False):
            comment.append("### ✅ AI Review Passed\n")
        else:
            comment.append("### ❌ AI Review Failed\n")
        
        comment.append(ai_review.get("overall_assessment", "No assessment provided.") + "\n")
        
        # Add issues
        issues = ai_review.get("issues", [])
        if issues:
            comment.append("\n### Issues\n")
            for i, issue in enumerate(issues, 1):
                issue_type = issue.get("type", "issue")
                message = issue.get("message", "No description")
                file = issue.get("file", "")
                line = issue.get("line", "")
                
                if file and line:
                    comment.append(f"{i}. **{issue_type.upper()}**: {message} (in `{file}` at line {line})")
                elif file:
                    comment.append(f"{i}. **{issue_type.upper()}**: {message} (in `{file}`)")
                else:
                    comment.append(f"{i}. **{issue_type.upper()}**: {message}")
            comment.append("")
        
        # Add suggestions
        suggestions = ai_review.get("suggestions", [])
        if suggestions:
            comment.append("\n### Suggestions\n")
            for i, suggestion in enumerate(suggestions, 1):
                description = suggestion.get("description", "No description")
                file = suggestion.get("file", "")
                line = suggestion.get("line", "")
                
                if file and line:
                    comment.append(f"{i}. {description} (in `{file}` at line {line})")
                elif file:
                    comment.append(f"{i}. {description} (in `{file}`)")
                else:
                    comment.append(f"{i}. {description}")
            comment.append("")
        
        # Add detailed review comment
        review_comment = ai_review.get("review_comment", "")
        if review_comment:
            comment.append("\n### Detailed Review\n")
            comment.append(review_comment)
        
        return "\n".join(comment)
    
    def _submit_formal_review(self, repo_name: str, pr_number: int, review_results: Dict[str, Any]) -> None:
        """
        Submit a formal review on the PR.
        
        Args:
            repo_name: Repository name (owner/repo)
            pr_number: Pull request number
            review_results: Review results
        """
        passed = review_results.get("passed", False)
        ai_review = review_results.get("ai_review", {})
        
        # Determine review state
        if passed:
            review_state = "APPROVE"
            review_body = "✅ This PR has passed all validation checks and is ready to be merged."
        else:
            review_state = "REQUEST_CHANGES"
            review_body = "❌ This PR has failed one or more validation checks and needs changes."
        
        # Add AI review comment
        if ai_review:
            review_body += "\n\n" + ai_review.get("overall_assessment", "")
        
        # Submit review
        self.github_client.submit_pr_review(
            repo_name=repo_name,
            pr_number=pr_number,
            body=review_body,
            event=review_state
        )
    
    def _send_notification(self, repo_name: str, pr_number: int, review_results: Dict[str, Any]) -> None:
        """
        Send a notification about the PR review.
        
        Args:
            repo_name: Repository name (owner/repo)
            pr_number: Pull request number
            review_results: Review results
        """
        passed = review_results.get("passed", False)
        
        # Get PR details
        pr = self.github_client.get_pull_request(repo_name, pr_number)
        
        # Prepare notification message
        if passed:
            title = f"✅ PR #{pr_number} Review Passed"
            message = f"PR #{pr_number}: {pr.title} has passed all validation checks and is ready to be merged."
        else:
            title = f"❌ PR #{pr_number} Review Failed"
            message = f"PR #{pr_number}: {pr.title} has failed one or more validation checks and needs changes."
        
        # Add PR link
        pr_url = f"https://github.com/{repo_name}/pull/{pr_number}"
        message += f"\n\nView PR: {pr_url}"
        
        # Send notification
        self.slack_notifier.send_notification(
            title=title,
            message=message,
            pr_url=pr_url,
            status="success" if passed else "failure"
        )
    
    def _save_review_results(self, repo_name: str, pr_number: int, review_results: Dict[str, Any]) -> None:
        """
        Save review results for failed validations.
        
        Args:
            repo_name: Repository name (owner/repo)
            pr_number: Pull request number
            review_results: Review results
        """
        # Save review results
        self.storage_manager.save_review_results(
            repo_name=repo_name,
            pr_number=pr_number,
            review_results=review_results
        )
        
        # Save documentation validation results
        doc_validation = review_results.get("documentation_validation", {})
        if not doc_validation.get("passed", False):
            self.doc_validation_service.save_validation_results(
                validation_results=doc_validation,
                output_dir=os.path.join(self.config["storage"]["path"], "insights")
            )
    
    def _auto_merge_pr(self, repo_name: str, pr_number: int) -> None:
        """
        Auto-merge a PR if it passes all validation checks.
        
        Args:
            repo_name: Repository name (owner/repo)
            pr_number: Pull request number
        """
        try:
            # Get PR details
            pr = self.github_client.get_pull_request(repo_name, pr_number)
            
            # Check if PR is mergeable
            if not pr.mergeable:
                logger.warning(f"PR #{pr_number} is not mergeable")
                return
            
            # Merge the PR
            self.github_client.merge_pr(
                repo_name=repo_name,
                pr_number=pr_number,
                commit_title=f"Merge PR #{pr_number}: {pr.title}",
                commit_message=f"Automatically merged PR #{pr_number} after passing validation checks.",
                merge_method="merge"
            )
            
            logger.info(f"PR #{pr_number} automatically merged")
            
            # Send notification
            self.slack_notifier.send_notification(
                title=f"🔄 PR #{pr_number} Automatically Merged",
                message=f"PR #{pr_number}: {pr.title} has been automatically merged after passing validation checks.",
                pr_url=f"https://github.com/{repo_name}/pull/{pr_number}",
                status="success"
            )
        
        except Exception as e:
            logger.error(f"Error auto-merging PR: {e}")
            logger.error(traceback.format_exc())
