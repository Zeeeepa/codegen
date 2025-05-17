from codegen import Codebase, CodeAgent
from codegen.extensions.linear.linear_client import LinearClient
from codegen.extensions.events.app import CodegenApp
from codegen.extensions.tools.github.create_pr import create_pr
from codegen.shared.enums.programming_language import ProgrammingLanguage
from codegen.extensions.linear.types import LinearEvent, LinearIssue, LinearComment, LinearUser
from helpers import create_codebase, format_linear_message, has_codegen_label, process_update_event

from fastapi import Request

import os
import modal
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a Modal image with the necessary dependencies
image = modal.Image.debian_slim(python_version="3.13").apt_install("git").pip_install("fastapi[standard]", "codegen>=v0.26.3")

# Initialize the CodegenApp with a name and the image
app = CodegenApp("linear-bot", image=image, modal_api_key="")


@app.cls(secrets=[modal.Secret.from_dotenv()], keep_warm=1)
class LinearApp:
    codebase: Codebase

    @modal.enter()
    def run_this_on_container_startup(self):
        """Initialize the codebase and subscribe to Linear webhook handlers"""
        self.codebase = create_codebase("codegen-sh/codegen-sdk", ProgrammingLanguage.PYTHON)

        # Subscribe web endpoints as linear webhook callbacks
        app.linear.subscribe_all_handlers()

    @modal.exit()
    def run_this_on_container_exit(self):
        """Unsubscribe from Linear webhook handlers when the app stops"""
        app.linear.unsubscribe_all_handlers()

    @modal.web_endpoint(method="POST")
    @app.linear.event("Issue", should_handle=has_codegen_label)
    def handle_webhook(self, event: LinearEvent, request: Request):
        """Handle incoming webhook events from Linear"""
        linear_client = LinearClient(access_token=os.environ["LINEAR_ACCESS_TOKEN"])

        # Process the event data
        update_event = process_update_event(event.data)
        linear_client.comment_on_issue(update_event.issue_id, "I'm on it 👍")

        # Format the query for the agent
        query = format_linear_message(update_event.title, update_event.description)
        agent = CodeAgent(self.codebase)

        # Run the agent with the query
        agent.run(query)

        # Create a PR with the agent's changes
        pr_title = f"[{update_event.identifier}] " + update_event.title
        pr_body = "Codegen generated PR for issue: " + update_event.issue_url
        create_pr_result = create_pr(self.codebase, pr_title, pr_body)

        logger.info(f"PR created: {create_pr_result.model_dump_json()}")

        # Comment on the Linear issue with the PR link
        linear_client.comment_on_issue(
            update_event.issue_id, 
            f"I've finished running, please review the PR: {create_pr_result.url}"
        )
        
        # Reset the codebase for the next request
        self.codebase.reset()

        return {"status": "success"}

# If running this file directly, this will deploy the app to Modal
if __name__ == "__main__":
    app.serve()

