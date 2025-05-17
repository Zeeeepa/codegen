import modal
from codegen.extensions.events.app import CodegenApp
from codegen.extensions.linear.types import LinearEvent, LinearIssue, LinearComment
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)

# Create a Modal image with the required dependencies
image = modal.Image.debian_slim(python_version="3.13").apt_install("git").pip_install("codegen>=0.26.3")

# Initialize the CodegenApp with a name and the image
app = CodegenApp(name="linear-webhooks", modal_api_key="", image=image)


# Define a Modal class to handle Linear events
@app.cls(secrets=[modal.Secret.from_dotenv()], keep_warm=1)
class LinearEventHandlers:
    """Modal class for handling Linear webhook events.

    This class defines handlers for different types of Linear events,
    such as Issue and Comment events. Each handler is decorated with
    the appropriate event type.
    """

    @modal.web_endpoint(method="POST")
    @app.linear.webhook_endpoint()
    def webhook(self, event: LinearEvent):
        """Main webhook endpoint that receives all Linear events.

        This endpoint will be triggered for all Linear webhook events.
        """
        logger.info(f"Received Linear webhook event: {event.type} - {event.action}")
        return {"status": "success", "message": "Webhook received"}

    @app.linear.event("Issue")
    def handle_issue(self, event: LinearEvent):
        """Handle Linear Issue events

        This endpoint will be triggered when an issue is created, updated, or deleted in Linear.
        """
        # Check if the data is an Issue before accessing title
        if isinstance(event.data, LinearIssue):
            issue_title = event.data.title
            logger.info(f"Received Linear Issue event: {event.action} - {issue_title}")
            return {"status": "success", "message": f"Processed Linear Issue event: {event.action}", "issue_id": event.data.id, "issue_title": issue_title}
        else:
            logger.warning(f"Received non-Issue data for Issue event: {event.action}")
            return {"status": "warning", "message": f"Received non-Issue data for Issue event: {event.action}", "id": event.data.id}

    @modal.web_endpoint(method="POST")
    @app.linear.event("Comment")
    def handle_comment(self, event: LinearEvent):
        """Handle Linear Comment events

        This endpoint will be triggered when a comment is created, updated, or deleted in Linear.
        """
        # Check if the data is a Comment before processing
        if isinstance(event.data, LinearComment):
            logger.info(f"Received Linear Comment event: {event.action}")

            # Get the comment body and user information if available
            comment_body = event.data.body
            user_info = ""
            if event.data.user:
                user_info = f" by {event.data.user.name}"

            logger.info(f"Comment{user_info}: {comment_body}")

            return {"status": "success", "message": f"Processed Linear Comment event: {event.action}", "comment_id": event.data.id, "comment_body": comment_body}
        else:
            logger.warning(f"Received non-Comment data for Comment event: {event.action}")
            return {"status": "warning", "message": f"Received non-Comment data for Comment event: {event.action}", "id": event.data.id}

    @modal.web_endpoint(method="POST")
    @app.linear.event("*")
    def handle_generic(self, event: LinearEvent):
        """Handle any other Linear events

        This endpoint will be triggered for any Linear event type not explicitly handled.
        """
        logger.info(f"Received Linear event: {event.type} - {event.action}")
        return {"status": "success", "message": f"Processed Linear event: {event.type} - {event.action}", "event_type": event.type, "event_action": event.action}


# If running this file directly, this will deploy the app to Modal
if __name__ == "__main__":
    app.serve()

