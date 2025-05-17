"""Linear webhooks handler using Modal and Codegen."""

import hashlib
import hmac
import json
import os
from datetime import datetime
from typing import Any, Dict, Optional

import modal
from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel, Field

# Create image with dependencies
image = modal.Image.debian_slim(python_version="3.13").pip_install(
    "codegen>=0.6.1",
    "python-dotenv>=1.0.0",
)

# Create Modal app
app = modal.App("linear-webhooks")

# Create a volume for persistent storage
volume = modal.Volume.from_name("linear-data", create_if_missing=True)


class LinearEvent(BaseModel):
    """Linear webhook event model."""

    action: str
    type: str
    data: Dict[str, Any]
    url: Optional[str] = None
    updatedFrom: Optional[Dict[str, Any]] = None
    createdAt: datetime = Field(default_factory=datetime.now)


@app.function(
    image=image,
    secrets=[modal.Secret.from_dotenv()],
    volumes={"/data": volume},
)
@modal.asgi_app()
def fastapi_app():
    """Create FastAPI app with Linear webhook handlers."""
    web_app = FastAPI(title="Linear Webhooks Handler")

    @web_app.get("/")
    async def root():
        """Root endpoint for health checks."""
        return {"status": "ok", "message": "Linear webhooks handler is running"}

    @web_app.post("/webhook")
    async def webhook(
        request: Request,
        x_linear_delivery: Optional[str] = Header(None),
        x_linear_signature: Optional[str] = Header(None),
    ):
        """Handle Linear webhook events."""
        # Verify signature if provided
        if x_linear_signature:
            signing_secret = os.environ.get("LINEAR_SIGNING_SECRET")
            if not signing_secret:
                raise HTTPException(status_code=500, detail="LINEAR_SIGNING_SECRET not configured")

            body = await request.body()
            signature = hmac.new(
                signing_secret.encode("utf-8"),
                body,
                hashlib.sha256,
            ).hexdigest()

            if not hmac.compare_digest(signature, x_linear_signature):
                raise HTTPException(status_code=401, detail="Invalid signature")

        # Parse event data
        try:
            data = await request.json()
            event = LinearEvent(**data)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid event data: {str(e)}")

        # Log event
        log_event(event)

        # Handle different event types
        if event.type == "Issue":
            return handle_issue_event(event)
        elif event.type == "Comment":
            return handle_comment_event(event)
        else:
            return {"status": "ignored", "message": f"Event type {event.type} not handled"}

    return web_app


def log_event(event: LinearEvent):
    """Log Linear event to file."""
    log_file = f"/data/linear_events_{datetime.now().strftime('%Y%m%d')}.jsonl"
    with open(log_file, "a") as f:
        f.write(json.dumps(event.dict()) + "\n")
    print(f"Logged {event.type} {event.action} event")


def handle_issue_event(event: LinearEvent) -> Dict[str, str]:
    """Handle Linear issue events."""
    action = event.action
    issue_data = event.data
    issue_id = issue_data.get("id")
    issue_title = issue_data.get("title")

    print(f"Handling issue event: {action} - {issue_title} ({issue_id})")

    if action == "create":
        # Handle issue creation
        return {"status": "success", "message": f"Processed issue creation: {issue_title}"}
    elif action == "update":
        # Handle issue update
        updated_fields = event.updatedFrom or {}
        return {
            "status": "success",
            "message": f"Processed issue update: {issue_title}",
            "updated_fields": list(updated_fields.keys()),
        }
    elif action == "remove":
        # Handle issue deletion
        return {"status": "success", "message": f"Processed issue deletion: {issue_id}"}
    else:
        return {"status": "ignored", "message": f"Issue action {action} not handled"}


def handle_comment_event(event: LinearEvent) -> Dict[str, str]:
    """Handle Linear comment events."""
    action = event.action
    comment_data = event.data
    comment_id = comment_data.get("id")
    comment_data.get("body")

    print(f"Handling comment event: {action} - {comment_id}")

    if action == "create":
        # Handle comment creation
        return {"status": "success", "message": "Processed comment creation"}
    elif action == "update":
        # Handle comment update
        return {"status": "success", "message": "Processed comment update"}
    elif action == "remove":
        # Handle comment deletion
        return {"status": "success", "message": "Processed comment deletion"}
    else:
        return {"status": "ignored", "message": f"Comment action {action} not handled"}


if __name__ == "__main__":
    # When running directly, deploy the app
    print("Deploying linear-webhooks to Modal...")
    modal.serve.deploy(fastapi_app)
    print("Deployment complete! Check status with 'modal app status linear-webhooks'")
