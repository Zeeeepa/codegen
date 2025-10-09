"""
ChatKit Type Definitions
Core types for ChatKit protocol
"""

from typing import Any, Dict, List, Optional, Union, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class TextContent(BaseModel):
    """Text content in a message"""
    type: Literal["text"] = "text"
    text: str


class ToolCall(BaseModel):
    """Tool call request"""
    id: str
    type: Literal["function"] = "function"
    function: Dict[str, Any]


class ToolResult(BaseModel):
    """Tool execution result"""
    tool_call_id: str
    output: str


class Message(BaseModel):
    """Chat message"""
    role: Literal["user", "assistant", "system", "tool"]
    content: Union[str, List[TextContent], None] = None
    tool_calls: Optional[List[ToolCall]] = None
    tool_call_id: Optional[str] = None


class Widget(BaseModel):
    """Interactive widget"""
    type: str
    data: Dict[str, Any] = Field(default_factory=dict)


class ChatKitReq(BaseModel):
    """ChatKit request"""
    messages: List[Message]
    thread_id: Optional[str] = None
    model: str = "gpt-4"
    stream: bool = True
    tools: Optional[List[Dict[str, Any]]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ChatKitResp(BaseModel):
    """ChatKit response"""
    id: str
    object: Literal["chat.completion", "chat.completion.chunk"] = "chat.completion"
    created: int = Field(default_factory=lambda: int(datetime.now().timestamp()))
    model: str
    choices: List[Dict[str, Any]]
    usage: Optional[Dict[str, int]] = None


class AgentState(BaseModel):
    """Agent execution state"""
    agent_id: str
    status: Literal["idle", "running", "complete", "error"] = "idle"
    progress: int = 0
    current_step: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

