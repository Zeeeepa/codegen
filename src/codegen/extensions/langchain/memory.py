"""Memory implementation for LangGraph agents."""

import json
import os
from typing import Any, Dict, List, Optional, Sequence, Union

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langgraph.checkpoint import BaseCheckpointSaver
from langgraph.prebuilt import MessagesState


class MemorySaver(BaseCheckpointSaver):
    """Memory saver for LangGraph agents.
    
    This class provides a simple in-memory checkpoint saver for LangGraph agents.
    It stores the agent's state in memory and can be used to restore the agent's
    state between runs.
    """
    
    def __init__(self):
        """Initialize the memory saver."""
        self.checkpoints = {}
        
    def get_state(self, config_id: str) -> Optional[Dict[str, Any]]:
        """Get the state for a given config ID.
        
        Args:
            config_id: The ID of the configuration to get the state for
            
        Returns:
            The state for the given config ID, or None if not found
        """
        return self.checkpoints.get(config_id)
        
    def put_state(self, config_id: str, state: Dict[str, Any]) -> None:
        """Store the state for a given config ID.
        
        Args:
            config_id: The ID of the configuration to store the state for
            state: The state to store
        """
        self.checkpoints[config_id] = state
        
    def list_states(self) -> List[str]:
        """List all stored state IDs.
        
        Returns:
            List of all stored state IDs
        """
        return list(self.checkpoints.keys())
        
    def delete_state(self, config_id: str) -> None:
        """Delete the state for a given config ID.
        
        Args:
            config_id: The ID of the configuration to delete the state for
        """
        if config_id in self.checkpoints:
            del self.checkpoints[config_id]
