"""
Web2API Server - OpenAI-compatible API for web services

Provides REST API and OpenAI-compatible endpoints for accessing
web services through browser automation.
"""

import asyncio
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from autoqa.storage.database import (
    DatabaseManager,
    ServiceModel,
    ServiceSessionModel,
    OperationModel,
)
from autoqa.auth.credential_store import CredentialStore, setup_credential_store
from autoqa.auth.session_manager import SessionManager
from autoqa.adapters.owl import OwlBrowserAdapter, create_adapter

# ========================================================================
# Configuration
# ========================================================================

logger = structlog.get_logger(__name__)

# Database
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://web2api:web2api@localhost:5432/web2api"
)

# Owl-Browser
OWL_BROWSER_URL = os.environ.get("OWL_BROWSER_URL", "http://localhost:8080")
OWL_BROWSER_TOKEN = os.environ.get("OWL_BROWSER_TOKEN", "")

# Initialize components
db_manager = DatabaseManager(database_url=DATABASE_URL)
credential_store = setup_credential_store()
browser_adapter = create_adapter(
    remote_url=OWL_BROWSER_URL,
    token=OWL_BROWSER_TOKEN
)
session_manager = SessionManager(
    db_manager=db_manager,
    credential_store=credential_store,
    browser_adapter=browser_adapter
)

# FastAPI app
app = FastAPI(
    title="Web2API",
    description="OpenAI-compatible API for web services",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========================================================================
# Models
# ========================================================================

class ServiceCreateRequest(BaseModel):
    """Request to create/register a service."""
    name: str = Field(..., description="Service name")
    url: str = Field(..., description="Service base URL")
    description: Optional[str] = Field(None, description="Service description")
    credentials: Dict[str, str] = Field(..., description="Login credentials")


class ServiceResponse(BaseModel):
    """Service response."""
    id: str
    name: str
    base_url: str
    description: Optional[str]
    status: str
    capabilities: Optional[Dict[str, Any]]
    created_at: datetime
    last_discovery_at: Optional[datetime]


class ChatMessage(BaseModel):
    """Chat message."""
    role: str = Field(..., description="Message role: system, user, assistant")
    content: str = Field(..., description="Message content")


class ChatCompletionRequest(BaseModel):
    """OpenAI-compatible chat completion request."""
    model: str = Field(..., description="Model/service name")
    messages: List[ChatMessage] = Field(..., description="Conversation messages")
    temperature: Optional[float] = Field(1.0, ge=0, le=2)
    max_tokens: Optional[int] = Field(None, gt=0)
    stream: Optional[bool] = Field(False, description="Enable streaming")


class ChatCompletionChoice(BaseModel):
    """Chat completion choice."""
    index: int
    message: ChatMessage
    finish_reason: str


class ChatCompletionUsage(BaseModel):
    """Token usage."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    """OpenAI-compatible chat completion response."""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: ChatCompletionUsage


# ========================================================================
# Service Management Endpoints
# ========================================================================

@app.post("/api/services", response_model=ServiceResponse, status_code=201)
async def create_service(request: ServiceCreateRequest, background_tasks: BackgroundTasks):
    """
    Register a new web service.

    Creates a service entry and triggers auto-discovery in the background.
    """
    try:
        # Store credentials
        credentials_ref = credential_store.store_credentials(
            service_id=request.name,
            credential_type="login_password",
            data=request.credentials
        )

        # Create service in database
        async with db_manager.session() as session:
            service = ServiceModel(
                name=request.name,
                base_url=request.url,
                description=request.description,
                credentials_ref=credentials_ref,
                status="registered"
            )
            session.add(service)
            await session.flush()
            service_id = str(service.id)

        # Trigger discovery in background
        background_tasks.add_task(discover_service_task, service_id)

        logger.info("Service created", service_id=service_id, name=request.name)

        # Return created service
        async with db_manager.session() as session:
            result = await session.execute(
                select(ServiceModel).where(ServiceModel.id == uuid.UUID(service_id))
            )
            service = result.scalar_one()

            return ServiceResponse(
                id=str(service.id),
                name=service.name,
                base_url=service.base_url,
                description=service.description,
                status=service.status,
                capabilities=service.capabilities,
                created_at=service.created_at,
                last_discovery_at=service.last_discovery_at
            )

    except Exception as e:
        logger.error("Failed to create service", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/services", response_model=List[ServiceResponse])
async def list_services():
    """List all registered services."""
    try:
        async with db_manager.session() as session:
            result = await session.execute(
                select(ServiceModel).order_by(ServiceModel.created_at.desc())
            )
            services = result.scalars().all()

            return [
                ServiceResponse(
                    id=str(s.id),
                    name=s.name,
                    base_url=s.base_url,
                    description=s.description,
                    status=s.status,
                    capabilities=s.capabilities,
                    created_at=s.created_at,
                    last_discovery_at=s.last_discovery_at
                )
                for s in services
            ]

    except Exception as e:
        logger.error("Failed to list services", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/services/{service_id}", response_model=ServiceResponse)
async def get_service(service_id: str):
    """Get service details."""
    try:
        async with db_manager.session() as session:
            result = await session.execute(
                select(ServiceModel).where(ServiceModel.id == uuid.UUID(service_id))
            )
            service = result.scalar_one_or_none()

            if not service:
                raise HTTPException(status_code=404, detail="Service not found")

            return ServiceResponse(
                id=str(service.id),
                name=service.name,
                base_url=service.base_url,
                description=service.description,
                status=service.status,
                capabilities=service.capabilities,
                created_at=service.created_at,
                last_discovery_at=service.last_discovery_at
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get service", service_id=service_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/services/{service_id}/discover")
async def trigger_discovery(service_id: str, background_tasks: BackgroundTasks):
    """Trigger service discovery."""
    try:
        async with db_manager.session() as session:
            result = await session.execute(
                select(ServiceModel).where(ServiceModel.id == uuid.UUID(service_id))
            )
            service = result.scalar_one_or_none()

            if not service:
                raise HTTPException(status_code=404, detail="Service not found")

            # Update status
            service.status = "discovering"

        # Trigger discovery in background
        background_tasks.add_task(discover_service_task, service_id)

        return {"status": "discovery_started", "service_id": service_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to trigger discovery", service_id=service_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ========================================================================
# OpenAI-Compatible Endpoints
# ========================================================================

@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completion(request: ChatCompletionRequest):
    """
    OpenAI-compatible chat completions endpoint.

    Executes chat operation against the registered web service.
    """
    try:
        # Find service by name (model)
        async with db_manager.session() as session:
            result = await session.execute(
                select(ServiceModel).where(ServiceModel.name == request.model)
            )
            service = result.scalar_one_or_none()

            if not service:
                raise HTTPException(
                    status_code=404,
                    detail=f"Service '{request.model}' not found"
                )

        # Get or create session
        session_id = await get_or_create_session(str(service.id))

        # Execute chat operation
        user_message = request.messages[-1].content if request.messages else ""

        response_text = await execute_chat_operation(
            service_id=str(service.id),
            session_id=session_id,
            message=user_message
        )

        # Build OpenAI response
        completion_id = f"chatcmpl-{uuid.uuid4().hex[:24]}"
        created = int(datetime.now().timestamp())

        # Estimate tokens (rough approximation)
        prompt_tokens = sum(len(m.content.split()) for m in request.messages)
        completion_tokens = len(response_text.split())
        total_tokens = prompt_tokens + completion_tokens

        return ChatCompletionResponse(
            id=completion_id,
            created=created,
            model=request.model,
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=ChatMessage(
                        role="assistant",
                        content=response_text
                    ),
                    finish_reason="stop"
                )
            ],
            usage=ChatCompletionUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens
            )
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Chat completion failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/models")
async def list_models():
    """List available models (services)."""
    try:
        async with db_manager.session() as session:
            result = await session.execute(
                select(ServiceModel).where(ServiceModel.status == "active")
            )
            services = result.scalars().all()

            return {
                "object": "list",
                "data": [
                    {
                        "id": s.name,
                        "object": "model",
                        "created": int(s.created_at.timestamp()),
                        "owned_by": "web2api"
                    }
                    for s in services
                ]
            }

    except Exception as e:
        logger.error("Failed to list models", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ========================================================================
# Background Tasks
# ========================================================================

async def discover_service_task(service_id: str):
    """Background task for service discovery."""
    try:
        logger.info("Starting discovery", service_id=service_id)

        # Get service details
        async with db_manager.session() as session:
            result = await session.execute(
                select(ServiceModel).where(ServiceModel.id == uuid.UUID(service_id))
            )
            service = result.scalar_one()

            # TODO: Implement full discovery pipeline
            # 1. Navigate to service
            # 2. Detect auth method
            # 3. Perform login
            # 4. Map features
            # 5. Build operations
            # 6. Save capabilities

            # For now, mark as active with basic chat capability
            service.status = "active"
            service.capabilities = {
                "chat": {
                    "type": "chat",
                    "input_selector": "#chat-input",
                    "submit_selector": "button[type='submit']",
                    "response_selector": ".response, .message, .assistant-message"
                }
            }
            service.last_discovery_at = datetime.utcnow()

        logger.info("Discovery completed", service_id=service_id)

    except Exception as e:
        logger.error("Discovery failed", service_id=service_id, error=str(e))

        # Mark as error
        async with db_manager.session() as session:
            result = await session.execute(
                select(ServiceModel).where(ServiceModel.id == uuid.UUID(service_id))
            )
            service = result.scalar_one()
            service.status = "error"


async def get_or_create_session(service_id: str) -> str:
    """Get existing session or create new one."""
    # Try to find existing valid session
    async with db_manager.session() as session:
        result = await session.execute(
            select(ServiceSessionModel)
            .where(
                ServiceSessionModel.service_id == uuid.UUID(service_id),
                ServiceSessionModel.state == "active"
            )
            .order_by(ServiceSessionModel.created_at.desc())
            .limit(1)
        )
        existing_session = result.scalar_one_or_none()

        if existing_session:
            # Validate session
            is_valid = await session_manager.validate_session(str(existing_session.id))
            if is_valid:
                return str(existing_session.id)

    # Create new session
    async with db_manager.session() as session:
        result = await session.execute(
            select(ServiceModel).where(ServiceModel.id == uuid.UUID(service_id))
        )
        service = result.scalar_one()

    session_id = await session_manager.create_session(
        service_id=service_id,
        credentials_ref=service.credentials_ref,
        auto_login=True
    )

    return session_id


async def execute_chat_operation(
    service_id: str,
    session_id: str,
    message: str
) -> str:
    """Execute chat operation against service."""
    try:
        # Navigate to service
        async with db_manager.session() as session:
            result = await session.execute(
                select(ServiceModel).where(ServiceModel.id == uuid.UUID(service_id))
            )
            service = result.scalar_one()

        # Simple chat execution (would use discovered capabilities)
        browser_adapter.navigate(service.base_url)

        # Wait for page load
        import time
        time.sleep(2)

        # Try to find chat input and submit
        # This would use discovered selectors in production
        try:
            browser_adapter.type("textarea, #prompt, input[type='text']", message)
            browser_adapter.click("button[type='submit'], button:contains('Send'), button:contains('Submit')")

            # Wait for response
            time.sleep(5)

            # Extract response (would use discovered response selector)
            response = browser_adapter.query_page("What is the response to the user's message?")
            return response or "Response received"

        except Exception as e:
            logger.error("Chat execution failed", error=str(e))
            return f"Error: {str(e)}"

    except Exception as e:
        logger.error("Operation execution failed", error=str(e))
        raise


# ========================================================================
# Health Check
# ========================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "browser_connected": browser_adapter.is_connected()
    }


# ========================================================================
# Startup/Shutdown
# ========================================================================

@app.on_event("startup")
async def startup():
    """Initialize on startup."""
    logger.info("Starting Web2API server")
    await db_manager.create_tables()
    logger.info("Database tables created")


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown."""
    logger.info("Shutting down Web2API server")
    browser_adapter.disconnect()
    await db_manager.close()


# ========================================================================
# Main
# ========================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "autoqa.api.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
