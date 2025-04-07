"""
Slack notifier module for the PR Review Bot.
Provides functionality for sending notifications to Slack.
"""

import os
import logging
from typing import Dict, Any, Optional
import json
import requests

# Configure logging
logger = logging.getLogger(__name__)

class SlackNotifier:
    """
    Notifier for sending messages to Slack.
    Provides methods for sending notifications about PR events.
    """
    
    def __init__(self, webhook_url: Optional[str] = None, token: Optional[str] = None, default_channel: Optional[str] = None):
        """
        Initialize the Slack notifier.
        
        Args:
            webhook_url: Slack webhook URL (for incoming webhooks)
            token: Slack API token (for bot users)
            default_channel: Default channel to send messages to
        """
        self.webhook_url = webhook_url or os.environ.get("SLACK_WEBHOOK_URL")
        self.token = token or os.environ.get("SLACK_TOKEN")
        self.default_channel = default_channel or os.environ.get("SLACK_DEFAULT_CHANNEL")
        
        if not self.webhook_url and not self.token:
            logger.warning("No Slack webhook URL or token provided, notifications will be disabled")
    
    def send_message(self, message: str, channel: Optional[str] = None, attachments: Optional[list] = None) -> bool:
        """
        Send a message to Slack.
        
        Args:
            message: Message text
            channel: Channel to send the message to (overrides default)
            attachments: Optional list of attachments
            
        Returns:
            True if message was sent successfully, False otherwise
        """
        if not self.webhook_url and not self.token:
            logger.warning("Cannot send Slack message: No webhook URL or token provided")
            return False
        
        target_channel = channel or self.default_channel
        
        try:
            if self.webhook_url:
                return self._send_via_webhook(message, attachments)
            elif self.token:
                return self._send_via_api(message, target_channel, attachments)
            else:
                return False
        except Exception as e:
            logger.error(f"Error sending Slack message: {e}")
            return False
    
    def _send_via_webhook(self, message: str, attachments: Optional[list] = None) -> bool:
        """
        Send a message via Slack webhook.
        
        Args:
            message: Message text
            attachments: Optional list of attachments
            
        Returns:
            True if message was sent successfully, False otherwise
        """
        payload = {
            "text": message
        }
        
        if attachments:
            payload["attachments"] = attachments
        
        response = requests.post(
            self.webhook_url,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            logger.info("Slack message sent successfully via webhook")
            return True
        else:
            logger.error(f"Error sending Slack message via webhook: {response.status_code} - {response.text}")
            return False
    
    def _send_via_api(self, message: str, channel: str, attachments: Optional[list] = None) -> bool:
        """
        Send a message via Slack API.
        
        Args:
            message: Message text
            channel: Channel to send the message to
            attachments: Optional list of attachments
            
        Returns:
            True if message was sent successfully, False otherwise
        """
        payload = {
            "token": self.token,
            "channel": channel,
            "text": message
        }
        
        if attachments:
            payload["attachments"] = json.dumps(attachments)
        
        response = requests.post(
            "https://slack.com/api/chat.postMessage",
            data=payload
        )
        
        response_data = response.json()
        
        if response_data.get("ok"):
            logger.info(f"Slack message sent successfully to {channel}")
            return True
        else:
            logger.error(f"Error sending Slack message via API: {response_data.get('error')}")
            return False
    
    def notify_pr_merged(self, repo_name: str, pr_number: int, pr_title: str, pr_url: str, author: str) -> bool:
        """
        Send a notification about a merged PR.
        
        Args:
            repo_name: Repository name
            pr_number: PR number
            pr_title: PR title
            pr_url: PR URL
            author: PR author
            
        Returns:
            True if notification was sent successfully, False otherwise
        """
        message = f"🎉 *PR #{pr_number} has been merged*\n"
        
        attachments = [
            {
                "color": "#36a64f",
                "title": f"{repo_name}: {pr_title}",
                "title_link": pr_url,
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
                        "value": author,
                        "short": True
                    }
                ],
                "footer": "PR Review Bot",
                "footer_icon": "https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png"
            }
        ]
        
        return self.send_message(message, attachments=attachments)