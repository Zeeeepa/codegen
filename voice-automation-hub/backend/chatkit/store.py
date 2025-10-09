"""
ChatKit Store Implementation
In-memory storage for threads and items
"""

from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import uuid


class Item(BaseModel):
    """Message or tool result item"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    thread_id: str
    type: str  # "message" or "tool_result"
    role: Optional[str] = None
    content: str = ""
    metadata: Dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)


class Thread(BaseModel):
    """Conversation thread"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: Optional[str] = None
    agent_id: Optional[str] = None
    status: str = "active"
    metadata: Dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Store:
    """In-memory store for ChatKit data"""
    
    def __init__(self):
        self.threads: Dict[str, Thread] = {}
        self.items: Dict[str, List[Item]] = {}
    
    def create_thread(self, workflow_id: Optional[str] = None, agent_id: Optional[str] = None) -> Thread:
        """Create a new thread"""
        thread = Thread(workflow_id=workflow_id, agent_id=agent_id)
        self.threads[thread.id] = thread
        self.items[thread.id] = []
        return thread
    
    def get_thread(self, thread_id: str) -> Optional[Thread]:
        """Get thread by ID"""
        return self.threads.get(thread_id)
    
    def add_item(self, thread_id: str, item: Item) -> Item:
        """Add item to thread"""
        item.thread_id = thread_id
        if thread_id not in self.items:
            self.items[thread_id] = []
        self.items[thread_id].append(item)
        
        # Update thread timestamp
        if thread_id in self.threads:
            self.threads[thread_id].updated_at = datetime.now()
        
        return item
    
    def get_items(self, thread_id: str) -> List[Item]:
        """Get all items in thread"""
        return self.items.get(thread_id, [])
    
    def list_threads(self, limit: int = 100) -> List[Thread]:
        """List recent threads"""
        threads = sorted(
            self.threads.values(),
            key=lambda t: t.updated_at,
            reverse=True
        )
        return threads[:limit]
