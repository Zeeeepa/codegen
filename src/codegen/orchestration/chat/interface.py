"""
Chat Interface - Top-Level User Interaction Layer

This module provides the primary chat interface for user interaction with the
orchestration layer. It handles natural language processing, intent recognition,
and coordinates with all underlying services through the orchestration manager.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, AsyncGenerator
from dataclasses import dataclass
from enum import Enum

from codegen.orchestration.core.manager import AgentOperationsManager, OperationRequest, OperationResponse

logger = logging.getLogger(__name__)

class MessageType(Enum):
    """Types of chat messages."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    ERROR = "error"

class IntentType(Enum):
    """Types of user intents."""
    AGENT_CREATE = "agent_create"
    AGENT_STATUS = "agent_status"
    AGENT_LIST = "agent_list"
    CODE_ANALYSIS = "code_analysis"
    CHAT_CONVERSATION = "chat_conversation"
    SYSTEM_STATUS = "system_status"
    HELP = "help"
    UNKNOWN = "unknown"

@dataclass
class ChatMessage:
    """Chat message structure."""
    message_id: str
    message_type: MessageType
    content: str
    timestamp: datetime
    user_id: str
    session_id: str
    metadata: Dict[str, Any]

@dataclass
class ParsedIntent:
    """Parsed user intent."""
    intent_type: IntentType
    confidence: float
    parameters: Dict[str, Any]
    raw_message: str

class ChatInterface:
    """
    Top-level chat interface for the orchestration layer.
    
    This class provides a natural language interface for users to interact
    with all orchestration services through conversational commands.
    """
    
    def __init__(self, orchestration_manager: AgentOperationsManager):
        """Initialize the chat interface."""
        self.orchestration_manager = orchestration_manager
        self._initialized = False
        
        # Intent patterns for simple NLP
        self._intent_patterns = {
            IntentType.AGENT_CREATE: [
                "create agent", "new agent", "start agent", "run agent",
                "create a new", "start a new", "begin", "execute"
            ],
            IntentType.AGENT_STATUS: [
                "status", "check status", "how is", "what's the status",
                "progress", "update", "current state"
            ],
            IntentType.AGENT_LIST: [
                "list agents", "show agents", "all agents", "my agents",
                "what agents", "agent list", "running agents"
            ],
            IntentType.CODE_ANALYSIS: [
                "analyze", "review", "check code", "code analysis",
                "examine", "inspect", "audit"
            ],
            IntentType.CHAT_CONVERSATION: [
                "chat", "talk", "discuss", "conversation", "ask",
                "tell me", "explain", "help me understand"
            ],
            IntentType.SYSTEM_STATUS: [
                "system status", "health", "metrics", "performance",
                "system health", "service status"
            ],
            IntentType.HELP: [
                "help", "how to", "what can", "commands", "usage",
                "guide", "tutorial", "instructions"
            ]
        }
        
        logger.info("ChatInterface initialized")
    
    async def initialize(self) -> None:
        """Initialize the chat interface."""
        if self._initialized:
            return
        
        # Ensure orchestration manager is initialized
        await self.orchestration_manager.initialize()
        
        self._initialized = True
        logger.info("Chat interface initialized")
    
    async def process_message(
        self,
        message: str,
        user_id: str,
        session_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Process a user message and yield response chunks.
        
        Args:
            message: User message text
            user_id: User identifier
            session_id: Optional session identifier
            
        Yields:
            Response text chunks
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Parse user intent
            intent = await self._parse_intent(message)
            
            # Create operation request based on intent
            operation_request = await self._create_operation_request(
                intent, user_id, session_id
            )
            
            # Execute operation through orchestration manager
            response = await self.orchestration_manager.execute_operation(operation_request)
            
            # Format and yield response
            async for chunk in self._format_response(response, intent):
                yield chunk
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            yield f"❌ **Error**: {str(e)}\n\nI encountered an issue processing your request. Please try again or contact support if the problem persists."
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status for the chat interface."""
        if not self._initialized:
            await self.initialize()
        
        return await self.orchestration_manager.get_system_metrics()
    
    async def get_help_text(self) -> str:
        """Get help text for available commands."""
        return """
🤖 **Codegen Orchestration Chat Interface**

I can help you with the following operations:

**Agent Operations:**
- `create agent for [task]` - Create a new agent run
- `status of agent [id]` - Check agent status
- `list my agents` - Show all your agents
- `cancel agent [id]` - Cancel a running agent

**Code Analysis:**
- `analyze [repository/file]` - Perform code analysis
- `review [code/PR]` - Review code or pull request
- `check quality of [project]` - Run quality checks

**Conversation:**
- `chat about [topic]` - Start a conversation
- `explain [concept]` - Get explanations
- `help with [task]` - Get assistance

**System:**
- `system status` - Check system health
- `my sessions` - View active sessions
- `help` - Show this help message

**Examples:**
- "Create an agent to analyze the user authentication system"
- "What's the status of agent abc123?"
- "Analyze the code quality of my React project"
- "Chat about best practices for API design"

Just type your request naturally - I'll understand what you want to do! 🚀
        """
    
    # Private methods
    
    async def _parse_intent(self, message: str) -> ParsedIntent:
        """Parse user message to determine intent."""
        message_lower = message.lower()
        
        # Simple pattern matching for intent recognition
        best_intent = IntentType.UNKNOWN
        best_confidence = 0.0
        
        for intent_type, patterns in self._intent_patterns.items():
            for pattern in patterns:
                if pattern in message_lower:
                    confidence = len(pattern) / len(message_lower)
                    if confidence > best_confidence:
                        best_intent = intent_type
                        best_confidence = confidence
        
        # Extract parameters based on intent
        parameters = await self._extract_parameters(message, best_intent)
        
        return ParsedIntent(
            intent_type=best_intent,
            confidence=best_confidence,
            parameters=parameters,
            raw_message=message
        )
    
    async def _extract_parameters(self, message: str, intent: IntentType) -> Dict[str, Any]:
        """Extract parameters from message based on intent."""
        parameters = {}
        
        if intent == IntentType.AGENT_CREATE:
            # Extract task description
            task_keywords = ["for", "to", "that", "which"]
            for keyword in task_keywords:
                if keyword in message.lower():
                    parts = message.lower().split(keyword, 1)
                    if len(parts) > 1:
                        parameters["task"] = parts[1].strip()
                        break
            
            if "task" not in parameters:
                parameters["task"] = message  # Use entire message as task
        
        elif intent == IntentType.AGENT_STATUS:
            # Extract agent ID
            words = message.split()
            for word in words:
                if len(word) > 6 and (word.isalnum() or "-" in word):
                    parameters["agent_id"] = word
                    break
        
        elif intent == IntentType.CODE_ANALYSIS:
            # Extract repository or file path
            words = message.split()
            for word in words:
                if "/" in word or "." in word:
                    parameters["target"] = word
                    break
        
        return parameters
    
    async def _create_operation_request(
        self,
        intent: ParsedIntent,
        user_id: str,
        session_id: Optional[str]
    ) -> OperationRequest:
        """Create operation request from parsed intent."""
        operation_type = self._intent_to_operation_type(intent.intent_type)
        
        return OperationRequest(
            operation_type=operation_type,
            user_id=user_id,
            session_id=session_id or f"chat_{user_id}_{datetime.utcnow().timestamp()}",
            metadata={
                "intent": intent.intent_type.value,
                "confidence": intent.confidence,
                "parameters": intent.parameters,
                "raw_message": intent.raw_message
            }
        )
    
    def _intent_to_operation_type(self, intent: IntentType) -> str:
        """Convert intent type to operation type."""
        mapping = {
            IntentType.AGENT_CREATE: "codegen.agent.create",
            IntentType.AGENT_STATUS: "codegen.agent.status",
            IntentType.AGENT_LIST: "codegen.agent.list",
            IntentType.CODE_ANALYSIS: "repomaster.analyze",
            IntentType.CHAT_CONVERSATION: "claude.chat",
            IntentType.SYSTEM_STATUS: "orchestration.system.status",
            IntentType.HELP: "orchestration.help",
            IntentType.UNKNOWN: "orchestration.unknown"
        }
        
        return mapping.get(intent, "orchestration.unknown")
    
    async def _format_response(
        self,
        response: OperationResponse,
        intent: ParsedIntent
    ) -> AsyncGenerator[str, None]:
        """Format operation response for chat interface."""
        if response.status.value == "failed":
            yield f"❌ **Operation Failed**\n\n{response.error}\n\n"
            yield "Please try again or rephrase your request."
            return
        
        # Format based on intent type
        if intent.intent_type == IntentType.AGENT_CREATE:
            yield f"🚀 **Agent Created Successfully!**\n\n"
            yield f"**Operation ID:** `{response.operation_id}`\n"
            yield f"**Service:** {response.service_used}\n"
            if response.result:
                yield f"**Status:** {response.result.get('status', 'Unknown')}\n\n"
            yield "Your agent is now running. You can check its status anytime!"
        
        elif intent.intent_type == IntentType.SYSTEM_STATUS:
            yield f"📊 **System Status**\n\n"
            if response.result:
                metrics = response.result
                yield f"**Active Operations:** {metrics.get('active_operations', 0)}\n"
                yield f"**Total Operations:** {metrics.get('total_operations', 0)}\n"
                yield f"**Service Health:** {metrics.get('service_health', {}).get('status', 'Unknown')}\n"
            yield f"\n**Response Time:** {response.execution_time:.2f}s"
        
        elif intent.intent_type == IntentType.HELP:
            yield await self.get_help_text()
        
        else:
            # Generic response formatting
            yield f"✅ **Operation Completed**\n\n"
            yield f"**Operation ID:** `{response.operation_id}`\n"
            yield f"**Service:** {response.service_used}\n"
            if response.execution_time:
                yield f"**Execution Time:** {response.execution_time:.2f}s\n\n"
            
            if response.result:
                yield f"**Result:**\n```json\n{response.result}\n```"

