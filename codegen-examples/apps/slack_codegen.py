"""
Slack Codegen Integration

This module provides a comprehensive Slack integration for Codegen, allowing users to interact
with Codegen's capabilities through Slack. It combines functionality from various Codegen
components including event handling, codebase operations, and agent interactions.
"""

import os
import logging
from typing import Any, Dict, Optional, List, TYPE_CHECKING
import json

import modal
from fastapi import FastAPI, Request
from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler
from openai import OpenAI

from codegen.sdk.core.codebase import Codebase
from codegen.agents.code.code_agent import CodeAgent
from codegen import CodegenApp
from codegen.extensions.events.modal.base import CodebaseEventsApp
from codegen.extensions.slack.types import SlackEvent
from codegen.extensions.github.types.events.pull_request import PullRequestLabeledEvent
from codegen.extensions.linear.types import LinearEvent
from langchain_core.tools import BaseTool

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
SNAPSHOT_DICT_ID = "codegen-slack-codebase-snapshots"

# Initialize Modal app
app = modal.App("slack-codegen")
fastapi_app = FastAPI()

# Initialize Slack app
slack_app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
)
slack_handler = SlackRequestHandler(slack_app)

# Initialize Codegen components
codegen_app = CodegenApp()
events_app = CodebaseEventsApp()

# Create a volume to store codebase snapshots
volume = modal.Volume.from_name(SNAPSHOT_DICT_ID, create_if_missing=True)

@app.function(
    image=modal.Image.debian_slim().pip_install(
        ["slack_bolt", "slack_sdk", "openai", "codegen"]
    ),
    volumes={"/snapshots": volume},
    secrets=[
        modal.Secret.from_name("slack-secrets"),
        modal.Secret.from_name("github-secrets"),
        modal.Secret.from_name("openai-secrets"),
    ],
)
def handle_slack_event(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle incoming Slack events.
    
    Args:
        payload: The Slack event payload
        
    Returns:
        Response dictionary
    """
    try:
        # Process the Slack event
        event = SlackEvent.from_dict(payload)
        
        # Handle different event types
        if event.type == "app_mention":
            return handle_app_mention(event)
        elif event.type == "message":
            return handle_message(event)
        else:
            logger.info(f"Unhandled event type: {event.type}")
            return {"status": "ignored", "reason": f"Unhandled event type: {event.type}"}
    
    except Exception as e:
        logger.error(f"Error handling Slack event: {str(e)}")
        return {"status": "error", "error": str(e)}

def handle_app_mention(event: SlackEvent) -> Dict[str, Any]:
    """
    Handle app mention events.
    
    Args:
        event: The Slack event
        
    Returns:
        Response dictionary
    """
    try:
        # Extract the message text
        text = event.text.replace(f"<@{event.bot_id}>", "").strip()
        
        # Get or create a codebase instance
        codebase = get_or_create_codebase(event.channel)
        
        # Create a code agent
        agent = CodeAgent(
            codebase=codebase,
            model_provider=os.environ.get("CODEGEN_MODEL_PROVIDER", "anthropic"),
            model_name=os.environ.get("CODEGEN_MODEL_NAME", "claude-3-sonnet-20240229"),
        )
        
        # Process the message with the agent
        response = agent.chat(text)
        
        # Send the response back to Slack
        slack_app.client.chat_postMessage(
            channel=event.channel,
            thread_ts=event.thread_ts or event.ts,
            text=response,
        )
        
        return {"status": "success", "response": response}
    
    except Exception as e:
        logger.error(f"Error handling app mention: {str(e)}")
        slack_app.client.chat_postMessage(
            channel=event.channel,
            thread_ts=event.thread_ts or event.ts,
            text=f"Error processing your request: {str(e)}",
        )
        return {"status": "error", "error": str(e)}

def handle_message(event: SlackEvent) -> Dict[str, Any]:
    """
    Handle regular message events.
    
    Args:
        event: The Slack event
        
    Returns:
        Response dictionary
    """
    # Only process messages in threads where the bot was previously mentioned
    if event.thread_ts and is_bot_in_thread(event.channel, event.thread_ts):
        try:
            # Get or create a codebase instance
            codebase = get_or_create_codebase(event.channel)
            
            # Create a code agent
            agent = CodeAgent(
                codebase=codebase,
                model_provider=os.environ.get("CODEGEN_MODEL_PROVIDER", "anthropic"),
                model_name=os.environ.get("CODEGEN_MODEL_NAME", "claude-3-sonnet-20240229"),
            )
            
            # Process the message with the agent
            response = agent.chat(event.text)
            
            # Send the response back to Slack
            slack_app.client.chat_postMessage(
                channel=event.channel,
                thread_ts=event.thread_ts,
                text=response,
            )
            
            return {"status": "success", "response": response}
        
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            slack_app.client.chat_postMessage(
                channel=event.channel,
                thread_ts=event.thread_ts,
                text=f"Error processing your request: {str(e)}",
            )
            return {"status": "error", "error": str(e)}
    
    return {"status": "ignored", "reason": "Not in a thread with the bot"}

def is_bot_in_thread(channel: str, thread_ts: str) -> bool:
    """
    Check if the bot is part of a thread.
    
    Args:
        channel: The Slack channel ID
        thread_ts: The thread timestamp
        
    Returns:
        True if the bot is in the thread, False otherwise
    """
    try:
        # Get the replies in the thread
        response = slack_app.client.conversations_replies(
            channel=channel,
            ts=thread_ts,
        )
        
        # Check if any message in the thread is from the bot
        bot_id = slack_app.client.auth_test()["bot_id"]
        for message in response["messages"]:
            if message.get("bot_id") == bot_id:
                return True
        
        return False
    
    except Exception as e:
        logger.error(f"Error checking if bot is in thread: {str(e)}")
        return False

def get_or_create_codebase(channel_id: str) -> Codebase:
    """
    Get or create a codebase instance for a channel.
    
    Args:
        channel_id: The Slack channel ID
        
    Returns:
        A Codebase instance
    """
    # Create a unique ID for the codebase based on the channel
    codebase_id = f"slack-{channel_id}"
    
    # Check if a snapshot exists for this channel
    snapshot_path = f"/snapshots/{codebase_id}.json"
    if os.path.exists(snapshot_path):
        # Load the codebase from the snapshot
        with open(snapshot_path, "r") as f:
            snapshot_data = json.load(f)
        
        # Create a codebase from the snapshot
        return Codebase.from_snapshot(snapshot_data)
    
    # Create a new codebase
    repo_url = os.environ.get("CODEGEN_DEFAULT_REPO", "")
    if not repo_url:
        raise ValueError("CODEGEN_DEFAULT_REPO environment variable is not set")
    
    # Create a new codebase
    codebase = Codebase.from_github_url(repo_url)
    
    # Save the codebase snapshot
    snapshot = codebase.to_snapshot()
    with open(snapshot_path, "w") as f:
        json.dump(snapshot, f)
    
    return codebase

@app.function(
    image=modal.Image.debian_slim().pip_install(
        ["fastapi", "slack_bolt", "slack_sdk", "uvicorn"]
    ),
    secrets=[modal.Secret.from_name("slack-secrets")],
)
@modal.asgi_app()
def fastapi_endpoint() -> FastAPI:
    """
    Create a FastAPI endpoint for handling Slack events.
    
    Returns:
        FastAPI app
    """
    @fastapi_app.post("/slack/events")
    async def slack_events(request: Request) -> Dict[str, Any]:
        """Handle Slack events."""
        return await slack_handler.handle(request)
    
    @fastapi_app.get("/health")
    async def health_check() -> Dict[str, str]:
        """Health check endpoint."""
        return {"status": "healthy"}
    
    return fastapi_app

if __name__ == "__main__":
    # For local development
    import uvicorn
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run the FastAPI app
    uvicorn.run(fastapi_endpoint, host="0.0.0.0", port=8000)
