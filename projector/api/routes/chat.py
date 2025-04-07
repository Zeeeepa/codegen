"""
API routes for chat functionality.
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from projector.backend.project_database import ProjectDatabase
from projector.backend.ai_user_agent import AIUserAgent
from projector.api.main import get_project_database, get_ai_user_agent

router = APIRouter()

class ChatMessage(BaseModel):
    """Model for a chat message."""
    role: str
    content: str

class ChatRequest(BaseModel):
    """Model for a chat request."""
    project_id: Optional[str] = None
    message: str
    chat_history: Optional[List[ChatMessage]] = None

class ChatResponse(BaseModel):
    """Model for a chat response."""
    response: str
    chat_history: List[ChatMessage]

@router.post("/", response_model=ChatResponse)
async def chat(
    chat_request: ChatRequest,
    project_database: ProjectDatabase = Depends(get_project_database),
    ai_user_agent: AIUserAgent = Depends(get_ai_user_agent)
):
    """Chat with the AI assistant."""
    # Initialize chat history if not provided
    chat_history = chat_request.chat_history or []
    
    # Add user message to chat history
    chat_history.append(ChatMessage(role="user", content=chat_request.message))
    
    # Get response from AI assistant
    if chat_request.project_id:
        # Check if project exists
        project = project_database.get_project(chat_request.project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get response for project-specific chat
        response = ai_user_agent.get_chat_response(
            project_id=chat_request.project_id,
            message=chat_request.message,
            chat_history=[{"role": msg.role, "content": msg.content} for msg in chat_history]
        )
    else:
        # Get response for general chat
        response = "I'm here to help with your projects. Please select a project to get context-aware assistance."
    
    # Add assistant response to chat history
    chat_history.append(ChatMessage(role="assistant", content=response))
    
    return ChatResponse(
        response=response,
        chat_history=chat_history
    )

@router.post("/upload", response_model=ChatResponse)
async def upload_file(
    project_id: str = Form(...),
    message: str = Form(...),
    file: UploadFile = File(...),
    project_database: ProjectDatabase = Depends(get_project_database),
    ai_user_agent: AIUserAgent = Depends(get_ai_user_agent)
):
    """Upload a file and chat with the AI assistant."""
    # Check if project exists
    project = project_database.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Read file content
    file_content = await file.read()
    
    # Initialize chat history
    chat_history = [
        ChatMessage(role="system", content=f"File uploaded: {file.filename}"),
        ChatMessage(role="user", content=message)
    ]
    
    # Get response from AI assistant
    response = ai_user_agent.get_chat_response(
        project_id=project_id,
        message=f"File: {file.filename}\n\n{message}",
        chat_history=[{"role": msg.role, "content": msg.content} for msg in chat_history]
    )
    
    # Add assistant response to chat history
    chat_history.append(ChatMessage(role="assistant", content=response))
    
    return ChatResponse(
        response=response,
        chat_history=chat_history
    )