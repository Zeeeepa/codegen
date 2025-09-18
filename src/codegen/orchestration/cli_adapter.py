"""
CLI Adapter for Orchestration Layer

This module provides integration between the existing CLI and the new orchestration
layer, ensuring backward compatibility while adding new orchestration features.
"""

import asyncio
import logging
from typing import Dict, Any, Optional

from codegen.orchestration import get_orchestration_manager
from codegen.orchestration.chat.interface import ChatInterface

logger = logging.getLogger(__name__)

class OrchestrationCLIAdapter:
    """
    CLI adapter for orchestration layer integration.
    
    This class provides a bridge between the existing CLI commands and the
    new orchestration layer, ensuring seamless integration and backward compatibility.
    """
    
    def __init__(self):
        """Initialize the CLI adapter."""
        self._orchestration_manager = None
        self._chat_interface = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the orchestration components."""
        if self._initialized:
            return
        
        self._orchestration_manager = get_orchestration_manager()
        await self._orchestration_manager.initialize()
        
        self._chat_interface = ChatInterface(self._orchestration_manager)
        await self._chat_interface.initialize()
        
        self._initialized = True
        logger.info("OrchestrationCLIAdapter initialized")
    
    async def execute_chat_command(
        self,
        message: str,
        user_id: str = "cli_user",
        session_id: Optional[str] = None
    ) -> str:
        """
        Execute a chat command through the orchestration layer.
        
        Args:
            message: User message/command
            user_id: User identifier
            session_id: Optional session identifier
            
        Returns:
            Response text
        """
        if not self._initialized:
            await self.initialize()
        
        response_parts = []
        async for chunk in self._chat_interface.process_message(message, user_id, session_id):
            response_parts.append(chunk)
        
        return "".join(response_parts)
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get system status through orchestration layer."""
        if not self._initialized:
            await self.initialize()
        
        return await self._orchestration_manager.get_system_metrics()
    
    async def shutdown(self) -> None:
        """Shutdown the orchestration components."""
        if self._orchestration_manager:
            await self._orchestration_manager.shutdown()
        
        self._initialized = False
        logger.info("OrchestrationCLIAdapter shutdown")

# Global adapter instance
_cli_adapter = None

def get_cli_adapter() -> OrchestrationCLIAdapter:
    """Get the global CLI adapter instance."""
    global _cli_adapter
    
    if _cli_adapter is None:
        _cli_adapter = OrchestrationCLIAdapter()
    
    return _cli_adapter

# Convenience functions for CLI integration
def execute_orchestration_command(message: str, user_id: str = "cli_user") -> str:
    """Execute an orchestration command synchronously."""
    adapter = get_cli_adapter()
    return asyncio.run(adapter.execute_chat_command(message, user_id))

def get_orchestration_status() -> Dict[str, Any]:
    """Get orchestration system status synchronously."""
    adapter = get_cli_adapter()
    return asyncio.run(adapter.get_system_status())

