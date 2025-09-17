"""
AI-powered chat service integrating RepoMaster code context detection and Z.AI client.
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
import logging

from ..models import (
    ChatMessage, ChatMessageType, AgentRun, Project, CodeContext,
    PRDValidation, ValidationResult, RunStatus
)
from ..config import Config
from .codegen_client import CodegenClient
from ..integrations.repomaster_client import RepoMasterClient
from ..integrations.zai_client import ZAIClient
from ..storage.memory_manager import MemoryManager
from ..utils.logger import get_logger


class ChatService:
    """
    AI-powered chat service that combines RepoMaster code analysis with Z.AI intelligence
    to provide context-aware assistance and automated agent run creation.
    """
    
    def __init__(self, config: Config, codegen_client: CodegenClient):
        """Initialize the chat service."""
        self.config = config
        self.codegen_client = codegen_client
        self.logger = get_logger(__name__)
        
        # Initialize AI clients
        self.repomaster_client = RepoMasterClient(config)
        self.zai_client = ZAIClient(config)
        self.memory_manager = MemoryManager(config)
        
        # Event callbacks
        self.on_message_received: Optional[Callable] = None
        self.on_agent_run_created: Optional[Callable] = None
        self.on_prd_validation_completed: Optional[Callable] = None
        
        # Context management
        self.current_project_context: Optional[Project] = None
        self.active_code_contexts: List[CodeContext] = []
        
        self.logger.info("Chat service initialized")
    
    async def process_message(self, user_message: str, session_id: str, 
                            project_id: Optional[str] = None) -> ChatMessage:
        """
        Process a user message and generate an AI response with context awareness.
        
        Args:
            user_message: The user's input message
            session_id: Current chat session ID
            project_id: Optional project ID for context
            
        Returns:
            AI-generated response message
        """
        try:
            self.logger.info(f"Processing message in session {session_id}")
            
            # Create user message object
            user_msg = ChatMessage(
                id=str(uuid.uuid4()),
                type=ChatMessageType.USER,
                content=user_message,
                timestamp=datetime.now(),
                user_id="user"
            )
            
            # Notify about user message
            if self.on_message_received:
                self.on_message_received(user_msg)
            
            # Analyze message intent
            intent = await self._analyze_message_intent(user_message)
            
            # Gather relevant context
            context = await self._gather_context(
                user_message, session_id, project_id, intent
            )
            
            # Generate AI response
            response_content = await self._generate_ai_response(
                user_message, context, intent
            )
            
            # Create response message
            response_msg = ChatMessage(
                id=str(uuid.uuid4()),
                type=ChatMessageType.ASSISTANT,
                content=response_content,
                timestamp=datetime.now(),
                user_id="assistant",
                context_used=[ctx.file_path for ctx in context.get('code_contexts', [])]
            )
            
            # Handle special intents (agent creation, etc.)
            await self._handle_special_intents(
                intent, user_message, context, response_msg
            )
            
            # Store conversation in memory
            await self._store_conversation_memory(user_msg, response_msg, context)
            
            # Notify about response
            if self.on_message_received:
                self.on_message_received(response_msg)
            
            return response_msg
            
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            
            # Return error message
            error_msg = ChatMessage(
                id=str(uuid.uuid4()),
                type=ChatMessageType.ASSISTANT,
                content=f"I apologize, but I encountered an error processing your request: {str(e)}",
                timestamp=datetime.now(),
                user_id="assistant"
            )
            
            if self.on_message_received:
                self.on_message_received(error_msg)
            
            return error_msg
    
    async def _analyze_message_intent(self, message: str) -> Dict[str, Any]:
        """Analyze the user's message to determine intent and extract parameters."""
        try:
            # Use Z.AI to analyze intent
            intent_prompt = f"""
            Analyze the following user message and determine the intent. Respond with JSON:
            
            Message: "{message}"
            
            Possible intents:
            - "create_agent": User wants to create a Codegen agent run
            - "analyze_code": User wants code analysis or explanation
            - "project_info": User wants information about a project
            - "general_chat": General conversation
            - "prd_validation": User wants to validate PRD requirements
            - "visualization": User wants to see code visualizations
            
            Response format:
            {{
                "intent": "intent_name",
                "confidence": 0.0-1.0,
                "parameters": {{
                    "project_name": "extracted project name if any",
                    "file_path": "extracted file path if any",
                    "task_description": "extracted task description if any"
                }}
            }}
            """
            
            response = await self.zai_client.chat_completion(
                messages=[{"role": "user", "content": intent_prompt}],
                temperature=0.1
            )
            
            # Parse JSON response
            intent_data = json.loads(response.content)
            return intent_data
            
        except Exception as e:
            self.logger.error(f"Error analyzing intent: {e}")
            return {
                "intent": "general_chat",
                "confidence": 0.5,
                "parameters": {}
            }
    
    async def _gather_context(self, message: str, session_id: str, 
                            project_id: Optional[str], intent: Dict[str, Any]) -> Dict[str, Any]:
        """Gather relevant context for the user's message."""
        context = {
            "message": message,
            "session_id": session_id,
            "project_id": project_id,
            "intent": intent,
            "code_contexts": [],
            "memory_contexts": [],
            "project_info": None
        }
        
        try:
            # Get project context if available
            if project_id:
                project_info = await self._get_project_context(project_id)
                context["project_info"] = project_info
            
            # Get relevant code context based on intent
            if intent["intent"] in ["analyze_code", "create_agent", "visualization"]:
                code_contexts = await self._get_code_context(message, project_id, intent)
                context["code_contexts"] = code_contexts
            
            # Get relevant memory context
            memory_contexts = await self._get_memory_context(message, session_id)
            context["memory_contexts"] = memory_contexts
            
            return context
            
        except Exception as e:
            self.logger.error(f"Error gathering context: {e}")
            return context
    
    async def _get_project_context(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project information and context."""
        try:
            # Get project from Codegen API
            project = await self.codegen_client.get_project(project_id)
            if not project:
                return None
            
            # Get recent agent runs for this project
            recent_runs = await self.codegen_client.get_agent_runs(
                project_id=project_id, limit=5
            )
            
            return {
                "project": project,
                "recent_runs": recent_runs,
                "prd_content": project.prd_content if hasattr(project, 'prd_content') else ""
            }
            
        except Exception as e:
            self.logger.error(f"Error getting project context: {e}")
            return None
    
    async def _get_code_context(self, message: str, project_id: Optional[str], 
                              intent: Dict[str, Any]) -> List[CodeContext]:
        """Get relevant code context using RepoMaster analysis."""
        try:
            if not project_id or not self.config.ai.repomaster_enabled:
                return []
            
            # Extract file paths or symbols from the message
            extracted_info = await self._extract_code_references(message)
            
            code_contexts = []
            
            # Get specific file analysis if file path is mentioned
            if extracted_info.get("file_paths"):
                for file_path in extracted_info["file_paths"]:
                    context = await self.repomaster_client.analyze_file(
                        project_id, file_path
                    )
                    if context:
                        code_contexts.append(context)
            
            # Get symbol analysis if symbols are mentioned
            if extracted_info.get("symbols"):
                for symbol in extracted_info["symbols"]:
                    context = await self.repomaster_client.analyze_symbol(
                        project_id, symbol
                    )
                    if context:
                        code_contexts.append(context)
            
            # If no specific references, get general project overview
            if not code_contexts and intent["intent"] in ["analyze_code", "visualization"]:
                overview = await self.repomaster_client.get_project_overview(project_id)
                if overview:
                    code_contexts.append(overview)
            
            return code_contexts[:self.config.ai.repomaster_max_context_files]
            
        except Exception as e:
            self.logger.error(f"Error getting code context: {e}")
            return []
    
    async def _extract_code_references(self, message: str) -> Dict[str, List[str]]:
        """Extract file paths and symbol references from the message."""
        try:
            extraction_prompt = f"""
            Extract file paths and code symbols from this message:
            
            "{message}"
            
            Look for:
            - File paths (e.g., src/main.py, components/Button.tsx)
            - Function names (e.g., calculate_total, handleClick)
            - Class names (e.g., UserService, ComponentBase)
            - Variable names that might be important
            
            Respond with JSON:
            {{
                "file_paths": ["path1", "path2"],
                "symbols": ["symbol1", "symbol2"]
            }}
            """
            
            response = await self.zai_client.chat_completion(
                messages=[{"role": "user", "content": extraction_prompt}],
                temperature=0.1
            )
            
            return json.loads(response.content)
            
        except Exception as e:
            self.logger.error(f"Error extracting code references: {e}")
            return {"file_paths": [], "symbols": []}
    
    async def _get_memory_context(self, message: str, session_id: str) -> List[Dict[str, Any]]:
        """Get relevant context from conversation memory."""
        try:
            if not self.config.ai.memory_enabled:
                return []
            
            # Search for relevant memories
            relevant_memories = await self.memory_manager.search_memories(
                query=message,
                session_id=session_id,
                limit=5,
                threshold=self.config.ai.context_similarity_threshold
            )
            
            return relevant_memories
            
        except Exception as e:
            self.logger.error(f"Error getting memory context: {e}")
            return []
    
    async def _generate_ai_response(self, user_message: str, context: Dict[str, Any], 
                                  intent: Dict[str, Any]) -> str:
        """Generate AI response using Z.AI with full context."""
        try:
            # Build context-aware prompt
            system_prompt = self._build_system_prompt(context, intent)
            
            # Prepare conversation messages
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            # Add memory context if available
            for memory in context.get("memory_contexts", []):
                if memory.get("type") == "conversation":
                    messages.insert(-1, {
                        "role": "assistant", 
                        "content": f"Previous context: {memory['content']}"
                    })
            
            # Generate response
            response = await self.zai_client.chat_completion(
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            return response.content
            
        except Exception as e:
            self.logger.error(f"Error generating AI response: {e}")
            return "I apologize, but I'm having trouble generating a response right now. Please try again."
    
    def _build_system_prompt(self, context: Dict[str, Any], intent: Dict[str, Any]) -> str:
        """Build a comprehensive system prompt with context."""
        prompt_parts = [
            "You are an AI assistant for the Codegen Dashboard, powered by RepoMaster code analysis and Z.AI intelligence.",
            "",
            "Your capabilities include:",
            "• Analyzing codebases with intelligent context detection",
            "• Creating and managing Codegen agent runs",
            "• Validating PRD (Product Requirements Document) requirements",
            "• Visualizing project dependencies and code structure",
            "• Providing code insights and recommendations",
            "",
            "Current context:"
        ]
        
        # Add project context
        if context.get("project_info"):
            project = context["project_info"]["project"]
            prompt_parts.extend([
                f"• Active project: {project.name}",
                f"• Project description: {project.description}",
                f"• Project status: {project.status.value}"
            ])
            
            if context["project_info"].get("prd_content"):
                prompt_parts.append(f"• PRD content available: {len(context['project_info']['prd_content'])} characters")
        
        # Add code context
        if context.get("code_contexts"):
            prompt_parts.append(f"• Code analysis available for {len(context['code_contexts'])} files/symbols")
            for code_ctx in context["code_contexts"][:3]:  # Show first 3
                prompt_parts.append(f"  - {code_ctx.file_path} ({code_ctx.analysis_type})")
        
        # Add intent information
        if intent.get("intent") != "general_chat":
            prompt_parts.append(f"• Detected intent: {intent['intent']} (confidence: {intent.get('confidence', 0):.2f})")
        
        prompt_parts.extend([
            "",
            "Guidelines:",
            "• Be helpful, accurate, and context-aware",
            "• When creating agent runs, be specific about requirements",
            "• Use code context to provide detailed analysis",
            "• Suggest follow-up actions when appropriate",
            "• If asked to create an agent run, confirm the details first"
        ])
        
        return "\n".join(prompt_parts)
    
    async def _handle_special_intents(self, intent: Dict[str, Any], user_message: str,
                                    context: Dict[str, Any], response_msg: ChatMessage):
        """Handle special intents like agent creation."""
        try:
            if intent["intent"] == "create_agent" and intent.get("confidence", 0) > 0.7:
                await self._handle_agent_creation_intent(
                    user_message, context, response_msg
                )
            elif intent["intent"] == "prd_validation":
                await self._handle_prd_validation_intent(
                    user_message, context, response_msg
                )
            elif intent["intent"] == "visualization":
                await self._handle_visualization_intent(
                    user_message, context, response_msg
                )
                
        except Exception as e:
            self.logger.error(f"Error handling special intent: {e}")
    
    async def _handle_agent_creation_intent(self, user_message: str, 
                                          context: Dict[str, Any], response_msg: ChatMessage):
        """Handle agent creation intent."""
        try:
            # Extract task details
            task_details = await self._extract_agent_task_details(user_message, context)
            
            if task_details.get("should_create", False):
                # Create agent run
                agent_run = await self.codegen_client.create_agent_run(
                    prompt=task_details["prompt"],
                    project_id=context.get("project_id"),
                    title=task_details.get("title", "Chat-created agent run")
                )
                
                # Update response message
                response_msg.type = ChatMessageType.AGENT_CREATION
                response_msg.agent_run_id = agent_run.id
                response_msg.content += f"\n\n🤖 **Agent Run Created**: [{agent_run.title}]({agent_run.url})"
                
                # Notify about agent creation
                if self.on_agent_run_created:
                    self.on_agent_run_created(agent_run, response_msg)
                
                self.logger.info(f"Created agent run {agent_run.id} from chat")
            
        except Exception as e:
            self.logger.error(f"Error handling agent creation: {e}")
            response_msg.content += f"\n\n❌ **Error**: Could not create agent run: {str(e)}"
    
    async def _extract_agent_task_details(self, user_message: str, 
                                        context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract task details for agent creation."""
        try:
            extraction_prompt = f"""
            Analyze this user message to determine if they want to create a Codegen agent run:
            
            Message: "{user_message}"
            
            Context: {json.dumps(context.get("project_info", {}), default=str)}
            
            Respond with JSON:
            {{
                "should_create": true/false,
                "title": "Brief title for the agent run",
                "prompt": "Detailed prompt for the agent including context",
                "confidence": 0.0-1.0
            }}
            
            Only set should_create to true if the user clearly wants to create an agent run.
            Include relevant code context in the prompt if available.
            """
            
            response = await self.zai_client.chat_completion(
                messages=[{"role": "user", "content": extraction_prompt}],
                temperature=0.1
            )
            
            return json.loads(response.content)
            
        except Exception as e:
            self.logger.error(f"Error extracting agent task details: {e}")
            return {"should_create": False, "confidence": 0.0}
    
    async def _handle_prd_validation_intent(self, user_message: str,
                                          context: Dict[str, Any], response_msg: ChatMessage):
        """Handle PRD validation intent."""
        # TODO: Implement PRD validation handling
        pass
    
    async def _handle_visualization_intent(self, user_message: str,
                                         context: Dict[str, Any], response_msg: ChatMessage):
        """Handle code visualization intent."""
        # TODO: Implement visualization handling
        pass
    
    async def _store_conversation_memory(self, user_msg: ChatMessage, 
                                       response_msg: ChatMessage, context: Dict[str, Any]):
        """Store conversation in memory for future context."""
        try:
            if not self.config.ai.memory_enabled:
                return
            
            # Store user message
            await self.memory_manager.store_memory(
                type="conversation",
                content=user_msg.content,
                metadata={
                    "message_type": "user",
                    "session_id": context.get("session_id"),
                    "project_id": context.get("project_id"),
                    "intent": context.get("intent", {}).get("intent"),
                    "timestamp": user_msg.timestamp.isoformat()
                }
            )
            
            # Store assistant response
            await self.memory_manager.store_memory(
                type="conversation",
                content=response_msg.content,
                metadata={
                    "message_type": "assistant",
                    "session_id": context.get("session_id"),
                    "project_id": context.get("project_id"),
                    "context_used": response_msg.context_used,
                    "agent_run_id": response_msg.agent_run_id,
                    "timestamp": response_msg.timestamp.isoformat()
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error storing conversation memory: {e}")
    
    async def validate_prd(self, agent_run: AgentRun, prd_content: str) -> PRDValidation:
        """Validate if an agent run successfully achieved PRD requirements."""
        try:
            self.logger.info(f"Validating PRD for agent run {agent_run.id}")
            
            # Get agent run results/output
            run_output = await self.codegen_client.get_agent_run_output(agent_run.id)
            
            # Use Z.AI to validate PRD achievement
            validation_prompt = f"""
            Analyze if this agent run successfully achieved the PRD requirements:
            
            PRD Requirements:
            {prd_content}
            
            Agent Run Output:
            {run_output}
            
            Agent Run Status: {agent_run.status.value}
            
            Evaluate:
            1. Were the PRD requirements met?
            2. What specific requirements are missing?
            3. What follow-up actions are needed?
            
            Respond with JSON:
            {{
                "validation_result": "success|partial|failed",
                "confidence_score": 0.0-1.0,
                "missing_requirements": ["req1", "req2"],
                "follow_up_suggestions": ["suggestion1", "suggestion2"],
                "validation_details": {{
                    "requirements_met": ["req1", "req2"],
                    "requirements_missing": ["req3", "req4"],
                    "quality_assessment": "assessment text"
                }}
            }}
            """
            
            response = await self.zai_client.chat_completion(
                messages=[{"role": "user", "content": validation_prompt}],
                temperature=0.1
            )
            
            validation_data = json.loads(response.content)
            
            # Create PRD validation result
            validation = PRDValidation(
                id=str(uuid.uuid4()),
                agent_run_id=agent_run.id,
                prd_content=prd_content,
                validation_result=ValidationResult(validation_data["validation_result"]),
                validation_details=validation_data["validation_details"],
                confidence_score=validation_data["confidence_score"],
                missing_requirements=validation_data["missing_requirements"],
                follow_up_suggestions=validation_data["follow_up_suggestions"]
            )
            
            # Notify about validation completion
            if self.on_prd_validation_completed:
                self.on_prd_validation_completed(validation)
            
            return validation
            
        except Exception as e:
            self.logger.error(f"Error validating PRD: {e}")
            
            # Return failed validation
            return PRDValidation(
                id=str(uuid.uuid4()),
                agent_run_id=agent_run.id,
                prd_content=prd_content,
                validation_result=ValidationResult.FAILED,
                validation_details={"error": str(e)},
                confidence_score=0.0,
                missing_requirements=["Validation failed due to error"],
                follow_up_suggestions=["Review agent run output manually"]
            )
    
    def generate_followup_prompt(self, original_run: AgentRun, 
                               validation_result: PRDValidation) -> str:
        """Generate a follow-up prompt based on PRD validation results."""
        try:
            prompt_parts = [
                f"This is a follow-up to agent run: {original_run.title}",
                f"Original run ID: {original_run.id}",
                "",
                "PRD Validation Results:",
                f"• Status: {validation_result.validation_result.value}",
                f"• Confidence: {validation_result.confidence_score:.2f}",
                "",
                "Missing Requirements:"
            ]
            
            for req in validation_result.missing_requirements:
                prompt_parts.append(f"• {req}")
            
            prompt_parts.extend([
                "",
                "Follow-up Actions Needed:"
            ])
            
            for suggestion in validation_result.follow_up_suggestions:
                prompt_parts.append(f"• {suggestion}")
            
            prompt_parts.extend([
                "",
                "Please address the missing requirements and complete the PRD objectives.",
                "Build upon the work from the previous agent run where possible."
            ])
            
            return "\n".join(prompt_parts)
            
        except Exception as e:
            self.logger.error(f"Error generating follow-up prompt: {e}")
            return f"Follow-up to {original_run.title}: Please complete the remaining requirements."
