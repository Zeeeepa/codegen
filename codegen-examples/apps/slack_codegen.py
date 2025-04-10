"""
Slack Codegen Integration

This module provides a comprehensive Slack integration for Codegen, allowing users to interact
with Codegen's capabilities through Slack. It combines functionality from various Codegen
components including event handling, codebase operations, and agent interactions.
"""

import os
import logging
from typing import Any, Dict, Optional

import modal
from fastapi import FastAPI, Request
from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler
from openai import OpenAI

# Updated imports to use proper module paths
from codegen.agents.code.code_agent import CodeAgent
from codegen.sdk.core.codebase import Codebase
from codegen.extensions.events.codegen_app import CodegenApp
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

########################################################################################################################
# Core Slack Bot Logic
########################################################################################################################

def format_response(answer: str, context: Optional[list[tuple[str, int]]] = None) -> str:
    """Format the response for Slack with file links if context is provided."""
    if not context:
        return answer
    
    response = f"*Answer:*\n{answer}\n\n*Relevant Files:*\n"
    for filename, score in context:
        if "#chunk" in filename:
            filename = filename.split("#chunk")[0]
        github_link = f"https://github.com/codegen-sh/codegen/blob/main/{filename}"
        response += f"• <{github_link}|{filename}>\n"
    return response


def process_codebase_query(codebase: Codebase, query: str) -> tuple[str, list[tuple[str, int]]]:
    """Process a query about the codebase using the CodeAgent."""
    # Initialize code agent
    agent = CodeAgent(codebase=codebase)
    
    # Run the agent with the query
    response = agent.run(query)
    
    # For now, we don't have context scores, so we'll return an empty list
    # In a real implementation, you might want to use VectorIndex to get relevant files
    return response, []


########################################################################################################################
# Modal App Setup
########################################################################################################################

# Create the base image with dependencies
base_image = (
    modal.Image.debian_slim(python_version="3.13")
    .apt_install("git")
    .pip_install(
        # =====[ Codegen ]=====
        "codegen>=0.42.1",
        # =====[ Rest ]=====
        "openai>=1.1.0",
        "fastapi[standard]",
        "slack_bolt>=1.18.0",
        "slack_sdk",
        "langchain-core>=0.1.0",  # Added langchain-core dependency
    )
)

# Create Modal app
slack_codegen_app = modal.App("slack-codegen")


@slack_codegen_app.cls(
    image=base_image, 
    secrets=[modal.Secret.from_dotenv()], 
    enable_memory_snapshot=True,
    container_idle_timeout=300
)
class SlackCodegenAPI(CodebaseEventsApp):
    """Slack Codegen API that handles Slack events and integrates with Codegen."""
    
    # Parameters for the codebase
    commit: str = modal.parameter(default="main")
    repo_org: str = modal.parameter(default="codegen-sh")
    repo_name: str = modal.parameter(default="codegen")
    snapshot_index_id: str = SNAPSHOT_DICT_ID
    
    def setup_handlers(self, cg: CodegenApp):
        """Set up event handlers for the Codegen app."""
        
        @cg.slack.event("app_mention")
        async def handle_mention(event: SlackEvent):
            """Handle mentions of the bot in Slack channels."""
            logger.info("[APP_MENTION] Received app_mention event")
            
            # Get the codebase
            logger.info("[CODEBASE] Initializing codebase")
            codebase = cg.get_codebase()
            
            # Extract the query from the message (remove the bot mention)
            query = event.text.split(">", 1)[1].strip() if ">" in event.text else event.text
            
            if not query:
                cg.slack.client.chat_postMessage(
                    channel=event.channel,
                    text="Please ask a question about the codebase!",
                    thread_ts=event.ts
                )
                return {"message": "Empty query", "received_text": event.text}
            
            try:
                # Add typing indicator
                cg.slack.client.reactions_add(
                    channel=event.channel,
                    timestamp=event.ts,
                    name="writing_hand"
                )
                
                # Process the query
                response, context = process_codebase_query(codebase, query)
                
                # Format and send the response
                formatted_response = format_response(response, context)
                cg.slack.client.chat_postMessage(
                    channel=event.channel,
                    text=formatted_response,
                    thread_ts=event.ts
                )
                
                return {
                    "message": "Mentioned",
                    "received_text": event.text,
                    "response": response
                }
                
            except Exception as e:
                logger.exception(f"Error processing query: {e}")
                cg.slack.client.chat_postMessage(
                    channel=event.channel,
                    text=f"Error processing your request: {str(e)}",
                    thread_ts=event.ts
                )
                return {"error": str(e)}
        
        @cg.github.event("pull_request:labeled")
        def handle_pr(event: PullRequestLabeledEvent):
            """Handle PR labeled events."""
            logger.info("PR labeled")
            logger.info(f"PR head sha: {event.pull_request.head.sha}")
            
            codebase = cg.get_codebase()
            logger.info(f"Codebase: {codebase.name} codebase.repo: {codebase.repo_path}")
            
            # Check out the commit
            logger.info("> Checking out commit")
            codebase.checkout(commit=event.pull_request.head.sha)
            
            # Get the README file
            logger.info("> Getting README file")
            file = codebase.get_file("README.md")
            
            # Create a PR comment with the README content
            codebase._op.create_pr_comment(
                event.pull_request.number,
                f"Codegen Slack Bot has analyzed this PR.\n\nREADME content:\n```markdown\n{file.content[:500]}...\n```"
            )
            
            return {
                "message": "PR event handled",
                "num_files": len(codebase.files),
                "num_functions": len(codebase.functions)
            }
        
        @cg.linear.event("Issue")
        def handle_issue(event: LinearEvent):
            """Handle Linear issue events."""
            logger.info(f"Issue created: {event}")
            codebase = cg.get_codebase()
            return {
                "message": "Linear Issue event",
                "num_files": len(codebase.files),
                "num_functions": len(codebase.functions)
            }


########################################################################################################################
# FastAPI Integration
########################################################################################################################

@slack_codegen_app.function(
    image=base_image,
    secrets=[modal.Secret.from_dotenv()],
    timeout=3600,
)
@modal.asgi_app()
def fastapi_app():
    """Create a FastAPI app with Slack handlers."""
    # Initialize Slack app with secrets from environment
    slack_app = App(
        token=os.environ["SLACK_BOT_TOKEN"],
        signing_secret=os.environ["SLACK_SIGNING_SECRET"],
    )
    
    # Create FastAPI app
    web_app = FastAPI(title="Slack Codegen Integration")
    handler = SlackRequestHandler(slack_app)
    
    # Store responded messages to avoid duplicates
    responded = {}
    
    @slack_app.event("app_mention")
    def handle_mention(event: Dict[str, Any], say: Any) -> None:
        """Handle mentions of the bot in channels."""
        logger.info("Received Slack mention event")
        
        # Skip if we've already answered this question
        if event["ts"] in responded:
            return
        responded[event["ts"]] = True
        
        # Get message text without the bot mention
        query = event["text"].split(">", 1)[1].strip() if ">" in event["text"] else event["text"]
        if not query:
            say("Please ask a question about the codebase!")
            return
        
        try:
            # Add typing indicator emoji
            slack_app.client.reactions_add(
                channel=event["channel"],
                timestamp=event["ts"],
                name="writing_hand",
            )
            
            # Initialize the Codegen app and codebase
            cg = CodegenApp(name="slack-codegen", repo="codegen-sh/codegen")
            codebase = cg.get_codebase()
            
            # Initialize code agent
            agent = CodeAgent(codebase=codebase)
            
            # Run the agent with the query
            response = agent.run(query)
            
            # Send the response in the thread
            say(text=response, thread_ts=event["ts"])
            
        except Exception as e:
            # Send error message in thread
            say(text=f"Error: {str(e)}", thread_ts=event["ts"])
    
    @web_app.post("/slack/events")
    async def endpoint(request: Request):
        """Handle Slack events and verify requests."""
        return await handler.handle(request)
    
    @web_app.post("/slack/verify")
    async def verify(request: Request):
        """Handle Slack URL verification challenge."""
        data = await request.json()
        if data["type"] == "url_verification":
            return {"challenge": data["challenge"]}
        return await handler.handle(request)
    
    return web_app


########################################################################################################################
# Cron Job for Repository Snapshots
########################################################################################################################

@slack_codegen_app.function(
    schedule=modal.Cron("*/30 * * * *"),  # Run every 30 minutes
    image=base_image,
    secrets=[modal.Secret.from_dotenv()]
)
def refresh_repository_snapshots():
    """Refresh the repository snapshots periodically."""
    logger.info("Refreshing repository snapshots")
    api = SlackCodegenAPI()
    api.refresh_repository_snapshots(snapshot_index_id=SNAPSHOT_DICT_ID)


# For local development and testing
if __name__ == "__main__":
    import uvicorn
    
    # Create a Codegen app
    cg = CodegenApp(name="slack-codegen", repo="codegen-sh/codegen")
    
    # Run the FastAPI app
    uvicorn.run(cg.app, host="0.0.0.0", port=8000)
