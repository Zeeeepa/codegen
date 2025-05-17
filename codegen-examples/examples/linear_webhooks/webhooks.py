import modal
from codegen.extensions.events.app import CodegenApp
from codegen.extensions.linear.types import LinearEvent, LinearIssue, LinearComment
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)

# Create a Modal image with the necessary dependencies
image = modal.Image.debian_slim(python_version="3.13").apt_install("git").pip_install("fastapi[standard]", "codegen>=v0.22.2")

# Initialize the CodegenApp with a name and the image
app = CodegenApp(name="linear-webhooks", modal_api_key="", image=image)


# Define a Modal class to handle Linear events
@app.cls(secrets=[modal.Secret.from_dotenv()], keep_warm=1)
class LinearEventHandlers:
    @modal.enter()
    def enter(self):
        """Subscribe to all Linear webhook handlers when the app starts"""
        logger.info("Subscribing to Linear webhook handlers")
        app.linear.subscribe_all_handlers()

    @modal.exit()
    def exit(self):
        """Unsubscribe from all Linear webhook handlers when the app stops"""
        logger.info("Unsubscribing from Linear webhook handlers")
        app.linear.unsubscribe_all_handlers()

    @modal.web_endpoint(method="POST")
    @app.linear.event("Issue")
    def handle_issue(self, event: LinearEvent):
        """Handle Linear Issue events

        This endpoint will be triggered when an issue is created, updated, or deleted in Linear.
        """
        # Ensure data is a LinearIssue
        if not isinstance(event.data, LinearIssue):
            logger.warning(f"Received non-Issue data for Issue event: {event.action}")
            return {"status": "error", "message": "Received non-Issue data for Issue event"}
            
        logger.info(f"Received Linear Issue event: {event.action} - {event.data.title}")
        # Process the event data as needed
        return {"status": "success", "message": f"Processed Linear Issue event: {event.action}", "issue_id": event.data.id, "issue_title": event.data.title}

    @modal.web_endpoint(method="POST")
    @app.linear.event("Comment")
    def handle_comment(self, event: LinearEvent):
        """Handle Linear Comment events

        This endpoint will be triggered when a comment is created, updated, or deleted in Linear.
        """
        # Ensure data is a LinearComment
        if not isinstance(event.data, LinearComment):
            logger.warning(f"Received non-Comment data for Comment event: {event.action}")
            return {"status": "error", "message": "Received non-Comment data for Comment event"}
            
        logger.info(f"Received Linear Comment event: {event.action}")
        # Process the comment data as needed
        return {"status": "success", "message": f"Processed Linear Comment event: {event.action}", "comment_id": event.data.id}


# If running this file directly, this will deploy the app to Modal
if __name__ == "__main__":
    app.serve()
