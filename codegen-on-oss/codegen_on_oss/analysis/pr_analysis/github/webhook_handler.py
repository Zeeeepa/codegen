"""
Webhook Handler

Handler for GitHub webhooks related to pull requests.
"""

import json
import logging
from typing import Dict, Any, Optional

from graph_sitter.git.models.pull_request_context import PullRequestContext
from codegen_on_oss.analysis.pr_analysis.core.pr_analyzer import PRAnalyzer

logger = logging.getLogger(__name__)


class WebhookHandler:
    """
    Handler for GitHub webhooks related to pull requests.
    
    This class processes webhook events from GitHub and triggers
    the appropriate analysis based on the event type.
    """
    
    def __init__(self, pr_analyzer: Optional[PRAnalyzer] = None):
        """
        Initialize the webhook handler.
        
        Args:
            pr_analyzer: The PR analyzer to use for processing PRs
        """
        self.pr_analyzer = pr_analyzer or PRAnalyzer()
    
    def handle_webhook(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a webhook event from GitHub.
        
        Args:
            event_type: The type of event (e.g., "pull_request")
            payload: The webhook payload
            
        Returns:
            A dictionary containing the result of handling the webhook
        """
        logger.info(f"Received webhook event: {event_type}")
        
        if event_type == "pull_request":
            return self._handle_pull_request_event(payload)
        elif event_type == "pull_request_review":
            return self._handle_pull_request_review_event(payload)
        else:
            logger.warning(f"Unsupported event type: {event_type}")
            return {"status": "ignored", "reason": f"Unsupported event type: {event_type}"}
    
    def _handle_pull_request_event(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a pull_request event.
        
        Args:
            payload: The webhook payload
            
        Returns:
            A dictionary containing the result of handling the event
        """
        action = payload.get("action")
        logger.info(f"Handling pull_request event with action: {action}")
        
        # Only analyze on open or synchronize (push to PR branch)
        if action not in ["opened", "reopened", "synchronize"]:
            return {"status": "ignored", "reason": f"Ignored pull_request action: {action}"}
        
        # Create PR context
        pr_context = PullRequestContext.from_payload(payload)
        
        # Analyze PR
        try:
            result = self.pr_analyzer.analyze_pr(pr_context)
            return {
                "status": "success",
                "pr_number": pr_context.number,
                "result": result
            }
        except Exception as e:
            logger.exception(f"Error analyzing PR #{pr_context.number}: {e}")
            return {
                "status": "error",
                "pr_number": pr_context.number,
                "error": str(e)
            }
    
    def _handle_pull_request_review_event(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a pull_request_review event.
        
        Args:
            payload: The webhook payload
            
        Returns:
            A dictionary containing the result of handling the event
        """
        action = payload.get("action")
        logger.info(f"Handling pull_request_review event with action: {action}")
        
        # Only analyze on review submission
        if action != "submitted":
            return {"status": "ignored", "reason": f"Ignored pull_request_review action: {action}"}
        
        # Create PR context
        pr_context = PullRequestContext.from_payload(payload)
        
        # Analyze PR
        try:
            result = self.pr_analyzer.analyze_pr(pr_context)
            return {
                "status": "success",
                "pr_number": pr_context.number,
                "result": result
            }
        except Exception as e:
            logger.exception(f"Error analyzing PR #{pr_context.number}: {e}")
            return {
                "status": "error",
                "pr_number": pr_context.number,
                "error": str(e)
            }

