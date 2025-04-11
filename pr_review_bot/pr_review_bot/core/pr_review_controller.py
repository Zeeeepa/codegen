"""
PR Review Controller for the PR Review Bot.
This module provides functionality for coordinating the PR review process.
"""

import os
import json
import logging
import traceback
from typing import Dict, List, Any, Optional, Tuple
from github import Github, PullRequest, Repository
from ..validator.documentation_service import DocumentationValidationService
from .github_client import GitHubClient
from ..utils.slack_notifier import SlackNotifier
from ..utils.storage_manager import StorageManager
from ..utils.ai_service import AIService

logger = logging.getLogger(__name__)

class PRReviewController:
    """
    Controller for coordinating the PR review process.
    
    Coordinates the workflow between different components of the PR Review Bot.
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
        
        # Get GitHub token
        github_token = config["github"]["token"]
        
        # Initialize GitHub client
        self.github_client = GitHubClient(github_token)
        
        # Initialize documentation validation service
        self.doc_validation_service = DocumentationValidationService(config, repo_path)
        
        # Initialize Slack notifier
        slack_enabled = config["notification"]["slack"]["enabled"]
        slack_token = config["notification"]["slack"]["token"]
        slack_channel = config["notification"]["slack"]["channel"]
        
        self.slack_notifier = SlackNotifier(
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
            
            # Get repository
            repo = self.github_client.get_repository(repo_name)
            
            # Get PR details
            pr = self.github_client.get_pull_request(repo, pr_number)
            
            # Create a comment to indicate that review is in progress
            comment_body = "🔍 PR Review Bot is reviewing this PR. Please wait..."
            comment = pr.create_issue_comment(comment_body)
            comment_id = comment.id if comment else None
            
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
                try:
                    comment.edit(review_comment)
                    logger.info(f"Updated comment {comment_id} with review results")
                except Exception as e:
                    logger.error(f"Error updating comment: {e}")
                    # Create a new comment if update failed
                    pr.create_issue_comment(review_comment)
                    logger.info("Created new comment with review results")
            else:
                # Create a new comment if update failed
                pr.create_issue_comment(review_comment)
                logger.info("Created new comment with review results")
            
            # Submit formal review
            self._submit_formal_review(repo, pr, review_results)
            
            # Send notification
            self._send_notification(repo_name, pr_number, review_results)
            
            # Save review results
            if not review_results["passed"]:
                self._save_review_results(repo_name, pr_number, review_results)
            
            # Auto-merge if enabled and review passed
            if self.config["github"]["auto_merge"] and review_results["passed"]:
                self._auto_merge_pr(repo, pr)
            
            return {
                "status": "success",
                "message": "PR review completed",
                "results": review_results
            }
        
        except Exception as e:
            logger.error(f"Error reviewing PR: {e}")
            logger.error(traceback.format_exc())
            
            # Create error comment
            try:
                repo = self.github_client.get_repository(repo_name)
                pr = self.github_client.get_pull_request(repo, pr_number)
                pr.create_issue_comment(f"❌ Error reviewing PR: {str(e)}")
            except Exception as comment_error:
                logger.error(f"Error creating error comment: {comment_error}")
            
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
            # Get repository
            repo = self.github_client.get_repository(repo_name)
            
            # Get PR details
            pr = self.github_client.get_pull_request(repo, pr_number)
            pr_title = pr.title
            pr_body = pr.body or ""
            
            # Get PR files
            pr_files = list(pr.get_files())
            pr_files_list = [f.filename for f in pr_files]
            
            # Get PR diff
            pr_diff = ""
            for file in pr_files:
                if file.patch:
                    pr_diff += f"File: {file.filename}\n"
                    pr_diff += f"Status: {file.status}\n"
                    pr_diff += f"Changes: +{file.additions}, -{file.deletions}\n"
                    pr_diff += "```diff\n"
                    pr_diff += file.patch
                    pr_diff += "\n```\n\n"
            
            # Prepare PR details for AI analysis
            pr_details = {
                "repo_name": repo_name,
                "number": pr_number,
                "title": pr_title,
                "body": pr_body,
                "files": pr_files_list
            }
            
            # Use AI service to analyze PR
            return self.ai_service.analyze_pr(pr_details, pr_diff)
        
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
        comment.append("# PR Review Bot Results\n")
        
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
    
    def _submit_formal_review(self, repo: Repository, pr: PullRequest, review_results: Dict[str, Any]) -> None:
        """
        Submit a formal review on the PR.
        
        Args:
            repo: Repository object
            pr: Pull request object
            review_results: Review results
        """
        passed = review_results.get("passed", False)
        ai_review = review_results.get("ai_review", {})
        
        try:
            # Determine review state
            if passed:
                review_state = "APPROVE"
                review_message = "PR Review Bot approves this PR."
            else:
                review_state = "REQUEST_CHANGES"
                review_message = "PR Review Bot requests changes to this PR."
            
            # Add AI review comment if available
            if ai_review.get("review_comment"):
                review_message += "\n\n" + ai_review.get("review_comment")
            
            # Submit review
            pr.create_review(
                body=review_message,
                event=review_state
            )
            
            logger.info(f"Submitted formal review for PR #{pr.number} with state {review_state}")
        except Exception as e:
            logger.error(f"Error submitting formal review: {e}")
            logger.error(traceback.format_exc())
    
    def _send_notification(self, repo_name: str, pr_number: int, review_results: Dict[str, Any]) -> None:
        """
        Send a notification about the PR review.
        
        Args:
            repo_name: Repository name
            pr_number: Pull request number
            review_results: Review results
        """
        if not self.config["notification"]["slack"]["enabled"]:
            logger.info("Slack notifications are disabled, skipping")
            return
        
        try:
            passed = review_results.get("passed", False)
            
            # Get PR details
            repo = self.github_client.get_repository(repo_name)
            pr = self.github_client.get_pull_request(repo, pr_number)
            
            # Create message
            if passed:
                message = f"✅ PR #{pr_number} in {repo_name} has passed review"
            else:
                message = f"❌ PR #{pr_number} in {repo_name} has failed review"
            
            # Create attachments
            attachments = [
                {
                    "color": "#36a64f" if passed else "#ff0000",
                    "title": f"{repo_name}: {pr.title}",
                    "title_link": pr.html_url,
                    "fields": [
                        {
                            "title": "Repository",
                            "value": repo_name,
                            "short": True
                        },
                        {
                            "title": "PR Number",
                            "value": f"#{pr_number}",
                            "short": True
                        },
                        {
                            "title": "Author",
                            "value": pr.user.login,
                            "short": True
                        },
                        {
                            "title": "Status",
                            "value": "Passed" if passed else "Failed",
                            "short": True
                        }
                    ],
                    "footer": "PR Review Bot",
                    "footer_icon": "https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png"
                }
            ]
            
            # Send notification
            self.slack_notifier.send_message(message, attachments=attachments)
            
            logger.info(f"Sent Slack notification for PR #{pr_number}")
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            logger.error(traceback.format_exc())
    
    def _save_review_results(self, repo_name: str, pr_number: int, review_results: Dict[str, Any]) -> None:
        """
        Save review results for failed validations.
        
        Args:
            repo_name: Repository name
            pr_number: Pull request number
            review_results: Review results
        """
        try:
            # Save review results
            self.storage_manager.save_review_results(repo_name, pr_number, review_results)
            
            # Save documentation validation insights
            doc_validation = review_results.get("documentation_validation", {})
            if not doc_validation.get("passed", False):
                self.storage_manager.save_insights(
                    repo_name=repo_name,
                    pr_number=pr_number,
                    insights=doc_validation,
                    insight_type="documentation"
                )
            
            # Save AI review insights
            ai_review = review_results.get("ai_review", {})
            if not ai_review.get("passed", False):
                self.storage_manager.save_insights(
                    repo_name=repo_name,
                    pr_number=pr_number,
                    insights=ai_review,
                    insight_type="ai"
                )
            
            logger.info(f"Saved review results for PR #{pr_number}")
        except Exception as e:
            logger.error(f"Error saving review results: {e}")
            logger.error(traceback.format_exc())
    
    def _auto_merge_pr(self, repo: Repository, pr: PullRequest) -> None:
        """
        Auto-merge a PR if it passes all checks.
        
        Args:
            repo: Repository object
            pr: Pull request object
        """
        try:
            # Check if PR is mergeable
            if not pr.mergeable:
                logger.warning(f"PR #{pr.number} is not mergeable, skipping auto-merge")
                return
            
            # Check if PR has any merge conflicts
            if pr.mergeable_state == "dirty":
                logger.warning(f"PR #{pr.number} has merge conflicts, skipping auto-merge")
                return
            
            # Check if all required checks have passed
            if pr.mergeable_state == "blocked":
                logger.warning(f"PR #{pr.number} is blocked by required checks, skipping auto-merge")
                return
            
            # Merge the PR
            merge_result = self.github_client.merge_pull_request(
                pr=pr,
                commit_message=f"Auto-merge PR #{pr.number}: {pr.title}"
            )
            
            if merge_result:
                logger.info(f"Auto-merged PR #{pr.number}")
                
                # Send notification
                if self.config["notification"]["slack"]["enabled"]:
                    self.slack_notifier.notify_pr_merged(
                        repo_name=repo.full_name,
                        pr_number=pr.number,
                        pr_title=pr.title,
                        pr_url=pr.html_url,
                        author=pr.user.login
                    )
            else:
                logger.warning(f"Failed to auto-merge PR #{pr.number}")
        except Exception as e:
            logger.error(f"Error auto-merging PR: {e}")
            logger.error(traceback.format_exc())
