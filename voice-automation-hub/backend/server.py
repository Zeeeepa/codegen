"""
Voice Automation Hub - Main Server
FastAPI server with Server-Sent Events for real-time streaming
"""

import asyncio
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv

from agents.voice_automation_agent import VoiceAutomationAgent
from store.memory_store import MemoryStore

load_dotenv()

# Initialize store and agent
store = MemoryStore()
agent = VoiceAutomationAgent(store=store)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    print("🚀 Voice Automation Hub starting...")
    print(f"📁 Working directory: {os.getcwd()}")
    
    # Install Playwright browsers if needed
    try:
        os.system("playwright install chromium")
    except Exception as e:
        print(f"⚠️  Playwright install warning: {e}")
    
    yield
    
    # Shutdown
    print("👋 Voice Automation Hub shutting down...")


app = FastAPI(
    title="Voice Automation Hub API",
    description="Backend API for voice-controlled automation with ChatKit",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "service": "Voice Automation Hub",
        "version": "1.0.0"
    }


@app.post("/api/sessions")
async def create_session(request: Request):
    """
    Create a new ChatKit session
    Compatible with OpenAI ChatKit Sessions API format
    """
    body = await request.json()
    workflow_id = body.get("workflow", {}).get("id")
    user_id = body.get("user")
    
    # For now, return a simple client_secret
    # In production, you'd integrate with OpenAI's session management
    import secrets
    client_secret = f"cs_{secrets.token_urlsafe(32)}"
    
    return {
        "client_secret": client_secret,
        "expires_after": 3600  # 1 hour
    }


async def event_stream(request_data: dict) -> AsyncIterator[bytes]:
    """
    Server-Sent Events stream for ChatKit protocol
    Yields events in the format: data: {json}\n\n
    """
    import json
    from chatkit.types import ChatKitReq
    from pydantic import TypeAdapter
    
    try:
        # Parse ChatKit request
        parsed_req = TypeAdapter[ChatKitReq](ChatKitReq).validate_python(request_data)
        
        # Process request through agent
        result = await agent.process(parsed_req, context={})
        
        if hasattr(result, 'json_events'):
            # Streaming result
            async for event_bytes in result.json_events:
                yield b"data: " + event_bytes + b"\n\n"
        else:
            # Non-streaming result
            yield b"data: " + result.json + b"\n\n"
    
    except Exception as e:
        # Send error event
        error_event = {
            "type": "error",
            "error": {
                "code": "STREAM_ERROR",
                "message": str(e),
                "allow_retry": True
            }
        }
        yield b"data: " + json.dumps(error_event).encode() + b"\n\n"


@app.post("/api/chatkit")
async def chatkit_endpoint(request: Request):
    """
    Main ChatKit protocol endpoint
    Handles all ChatKit requests and returns Server-Sent Events stream
    """
    request_data = await request.json()
    
    return StreamingResponse(
        event_stream(request_data),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable proxy buffering
        }
    )


@app.post("/api/voice/transcribe")
async def transcribe_audio(request: Request):
    """
    Transcribe audio using OpenAI Whisper API
    Fallback for when Web Speech API isn't available
    """
    from openai import AsyncOpenAI
    
    form = await request.form()
    audio_file = await form["file"].read()
    
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Save temp file
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp:
        temp.write(audio_file)
        temp_path = temp.name
    
    try:
        # Transcribe
        with open(temp_path, "rb") as audio:
            transcript = await client.audio.transcriptions.create(
                model="whisper-1",
                file=audio,
                response_format="text"
            )
        
        return {"transcript": transcript}
    
    finally:
        # Cleanup
        os.unlink(temp_path)


@app.get("/api/health")
async def health_check():
    """Detailed health check"""
    import platform
    
    return {
        "status": "healthy",
        "platform": platform.system(),
        "python_version": platform.python_version(),
        "environment": {
            "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
            "playwright_installed": True  # TODO: Check actual installation
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    print(f"\n🎤 Voice Automation Hub API")
    print(f"📡 Running on http://localhost:{port}")
    print(f"📚 Docs: http://localhost:{port}/docs")
    print()
    
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )

