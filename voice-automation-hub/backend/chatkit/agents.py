"""
ChatKit Agent Base Classes
"""

from typing import Any, Dict, List, Optional, AsyncIterator
from abc import ABC, abstractmethod
from pydantic import BaseModel
from .types import ChatKitReq, Message, Widget
from .store import Store, Thread


class AgentContext(BaseModel):
    """Context passed to agent during execution"""
    thread_id: str
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = {}
    store: Any = None  # Store instance


class Agent(ABC):
    """Base agent class"""
    
    def __init__(self, store: Store, name: str = "Agent"):
        self.store = store
        self.name = name
        self.tools: List[Any] = []
    
    @abstractmethod
    async def process(self, request: ChatKitReq, context: AgentContext) -> AsyncIterator[bytes]:
        """
        Process incoming request and yield response events
        
        Yields:
            bytes: JSON event data in format: {"type": "...", "data": {...}}
        """
        pass
    
    async def emit_widget(self, widget: Widget, context: AgentContext):
        """Emit a widget to the client"""
        import json
        event = {
            "type": "widget",
            "widget": widget.dict()
        }
        return json.dumps(event).encode()
    
    async def emit_message(self, content: str, context: AgentContext):
        """Emit a text message"""
        import json
        event = {
            "type": "message",
            "content": content
        }
        return json.dumps(event).encode()
    
    async def emit_progress(self, progress: int, message: str, context: AgentContext):
        """Emit progress update"""
        import json
        event = {
            "type": "progress",
            "progress": progress,
            "message": message
        }
        return json.dumps(event).encode()

