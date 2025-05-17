import modal
from codegen.extensions.linear.linear_client import LinearClient
from codegen.extensions.events.app import CodegenApp
from codegen.extensions.tools.github.create_pr import create_pr
from codegen.shared.enums.programming_language import ProgrammingLanguage
from codegen.extensions.linear.types import LinearEvent
from helpers import create_codebase, format_linear_message, has_codegen_label, process_update_event
from typing import Dict, Any

# Create a Modal image with the required dependencies
image = modal.Image.debian_slim(python_version="3.13").apt_install("git").pip_install("codegen>=0.26.3")

# Initialize the CodegenApp with a name and the image
app = CodegenApp(name="linear-bot", modal_api_key="", image=image)


# Define a Modal class to handle Linear events
@app.cls(secrets=[modal.Secret.from_dotenv()], keep_warm=1)
class LinearBot:
    """Modal class for handling Linear webhook events and creating GitHub PRs.

    This class defines handlers for Linear Issue events, specifically looking for
    issues labeled with "Codegen" to automatically create GitHub PRs.
    """

    def __enter__(self):
        """Initialize the Linear client when the class is instantiated."""
        self.linear_client = LinearClient()

    @modal.web_endpoint(method="POST")
    @app.linear.webhook_endpoint()
    def webhook(self, event: LinearEvent):
        """Main webhook endpoint that receives all Linear events.

        This endpoint will be triggered for all Linear webhook events.
        """
        return {"status": "success", "message": "Webhook received"}

    @app.linear.event("Issue")
    def handle_issue(self, event: LinearEvent):
        """Handle Linear Issue events, specifically looking for issues labeled with "Codegen".

        When an issue with the "Codegen" label is created or updated, this handler will:
        1. Create a codebase object for the GitHub repository
        2. Run a Codegen agent to analyze the issue and create a PR
        3. Comment on the Linear issue with a link to the PR
        """
        # Only process events for issues with the "Codegen" label
        if not has_codegen_label(event):
            return {"status": "skipped", "message": "Issue does not have the Codegen label"}

        # Process the event based on the action (created, updated, etc.)
        if event.action == "create":
            return self.process_create_event(event)
        elif event.action == "update":
            # Process the update event without passing the linear_client
            return process_update_event(event.data)
        else:
            return {"status": "skipped", "message": f"Unsupported action: {event.action}"}

    def process_create_event(self, event: LinearEvent):
        """Process a Linear Issue create event.

        This method will:
        1. Create a codebase object for the GitHub repository
        2. Run a Codegen agent to analyze the issue and create a PR
        3. Comment on the Linear issue with a link to the PR
        """
        # Create a codebase object for the GitHub repository
        repo_name = "Zeeeepa/codegen"  # Default repository
        codebase = create_codebase(repo_name=repo_name, language=ProgrammingLanguage.PYTHON)

        # Format the issue description for the PR
        issue_title = event.data.title
        issue_description = event.data.description or ""
        pr_title = f"Implement {issue_title}"
        pr_body = format_linear_message(issue_description, event.data.id)

        # Create a PR using the Codegen agent
        pr_url = create_pr(
            codebase=codebase,
            title=pr_title,
            body=pr_body,
            programming_language=ProgrammingLanguage.PYTHON,
        )

        # Comment on the Linear issue with a link to the PR
        self.linear_client.comment_on_issue(
            issue_id=event.data.id,
            body=f"Created PR: {pr_url}",
        )

        return {
            "status": "success",
            "message": "Created PR for Linear issue",
            "issue_id": event.data.id,
            "pr_url": pr_url,
        }


# If running this file directly, this will deploy the app to Modal
if __name__ == "__main__":
    app.serve()

