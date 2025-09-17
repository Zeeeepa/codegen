"""
Core CI/CD Orchestrator

Main entry point for the CI/CD orchestration system that coordinates ROMA meta-agent,
Z.AI substrate, and Codegen core operations following KISS and YAGNI principles.

This orchestrator:
- Provides unified interface for all CI/CD operations
- Coordinates between ROMA, Z.AI, and Codegen services
- Manages high-value agent services (Claude + RepoMaster)
- Handles selective service integration based on task requirements
- Maintains session state and conversation context
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from ..agent_operations import AgentOperationsManager
from .roma_integration import ROMAIntegration
from .zai_substrate import ZAISubstrate
from .agents import CodegenClaudeAgent, RepoMasterAgent
from .services import ServiceRegistry, TaskRouter
from .storage import UnifiedStorageManager

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Task classification for intelligent routing."""
    DEVELOPMENT = "development"
    CODE_ANALYSIS = "code_analysis"
    PROJECT_MANAGEMENT = "project_management"
    UI_INTERACTION = "ui_interaction"
    RESEARCH = "research"
    DEPLOYMENT = "deployment"


@dataclass
class OrchestrationRequest:
    """Request structure for orchestration operations."""
    message: str
    session_id: str
    user_context: Optional[Dict[str, Any]] = None
    preferred_agents: Optional[List[str]] = None
    task_priority: str = "normal"  # low, normal, high, urgent


@dataclass
class OrchestrationResponse:
    """Response structure from orchestration operations."""
    content: str
    task_type: TaskType
    agents_used: List[str]
    execution_time: float
    metadata: Dict[str, Any]
    requires_followup: bool = False
    suggested_actions: List[str] = None


class CICDOrchestrator:
    """
    Core CI/CD Orchestrator that coordinates all system components.
    
    Follows single responsibility principle by focusing on coordination
    rather than implementation of specific capabilities.
    """
    
    def __init__(
        self,
        codegen_manager: Optional[AgentOperationsManager] = None,
        enable_roma: bool = True,
        enable_ui_services: bool = False,
        enable_cognition_services: bool = False
    ):
        """
        Initialize the CI/CD orchestrator.
        
        Args:
            codegen_manager: Existing Codegen operations manager
            enable_roma: Enable ROMA meta-agent coordination
            enable_ui_services: Enable UI interaction services (on-demand)
            enable_cognition_services: Enable cognition services (value-based)
        """
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Core components (always enabled)
        self.codegen_manager = codegen_manager or AgentOperationsManager()
        self.zai_substrate = ZAISubstrate()
        self.storage_manager = UnifiedStorageManager()
        self.service_registry = ServiceRegistry()
        self.task_router = TaskRouter()
        
        # ROMA integration (high value)
        self.roma_integration = ROMAIntegration() if enable_roma else None
        
        # High-value agent services
        self.codegen_claude_agent = CodegenClaudeAgent(
            codegen_manager=self.codegen_manager,
            zai_substrate=self.zai_substrate
        )
        self.repomaster_agent = RepoMasterAgent(
            zai_substrate=self.zai_substrate
        )
        
        # Selective services (conditional)
        self.ui_services_enabled = enable_ui_services
        self.cognition_services_enabled = enable_cognition_services
        
        # Session management
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        
        self.logger.info("CI/CD Orchestrator initialized")
    
    async def initialize(self) -> None:
        """Initialize all orchestrator components."""
        try:
            # Initialize core components
            await self.zai_substrate.initialize()
            await self.storage_manager.initialize()
            await self.service_registry.initialize()
            
            # Initialize ROMA if enabled
            if self.roma_integration:
                await self.roma_integration.initialize()
            
            # Initialize high-value agents
            await self.codegen_claude_agent.initialize()
            await self.repomaster_agent.initialize()
            
            # Register services
            await self._register_core_services()
            
            self.logger.info("CI/CD Orchestrator initialization complete")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize orchestrator: {e}")
            raise
    
    async def process_request(
        self, 
        request: OrchestrationRequest
    ) -> OrchestrationResponse:
        """
        Process a CI/CD orchestration request.
        
        This is the main entry point that coordinates all system components
        to fulfill user requests through intelligent task routing.
        """
        start_time = datetime.now()
        
        try:
            # Analyze request and classify task type
            task_analysis = await self._analyze_request(request)
            
            # Route to appropriate agents/services
            execution_plan = await self.task_router.create_execution_plan(
                request=request,
                task_analysis=task_analysis
            )
            
            # Execute through ROMA if available, otherwise direct execution
            if self.roma_integration:
                result = await self.roma_integration.execute_plan(execution_plan)
            else:
                result = await self._execute_plan_direct(execution_plan)
            
            # Store session context
            await self._update_session_context(request.session_id, request, result)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return OrchestrationResponse(
                content=result.get("content", ""),
                task_type=task_analysis.get("task_type", TaskType.DEVELOPMENT),
                agents_used=result.get("agents_used", []),
                execution_time=execution_time,
                metadata=result.get("metadata", {}),
                requires_followup=result.get("requires_followup", False),
                suggested_actions=result.get("suggested_actions", [])
            )
            
        except Exception as e:
            self.logger.error(f"Error processing request: {e}")
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return OrchestrationResponse(
                content=f"Error processing request: {str(e)}",
                task_type=TaskType.DEVELOPMENT,
                agents_used=[],
                execution_time=execution_time,
                metadata={"error": str(e)},
                requires_followup=True,
                suggested_actions=["Please try rephrasing your request"]
            )
    
    async def _analyze_request(
        self, 
        request: OrchestrationRequest
    ) -> Dict[str, Any]:
        """Analyze request to determine task type and routing strategy."""
        # Use Z.AI substrate for intelligent request analysis
        analysis_prompt = f"""
        Analyze this CI/CD request and classify it:
        
        Request: {request.message}
        Context: {request.user_context or {}}
        
        Classify the task type and suggest appropriate agents.
        """
        
        analysis_result = await self.zai_substrate.analyze_request(
            prompt=analysis_prompt,
            context=request.user_context or {}
        )
        
        return {
            "task_type": self._determine_task_type(request.message),
            "complexity": analysis_result.get("complexity", "medium"),
            "suggested_agents": analysis_result.get("suggested_agents", []),
            "requires_ui": "ui" in request.message.lower() or "click" in request.message.lower(),
            "requires_research": "research" in request.message.lower() or "find" in request.message.lower()
        }
    
    def _determine_task_type(self, message: str) -> TaskType:
        """Determine task type based on message content."""
        message_lower = message.lower()
        
        if any(keyword in message_lower for keyword in ["code", "function", "class", "bug", "fix"]):
            return TaskType.DEVELOPMENT
        elif any(keyword in message_lower for keyword in ["analyze", "review", "quality", "metrics"]):
            return TaskType.CODE_ANALYSIS
        elif any(keyword in message_lower for keyword in ["project", "pr", "issue", "manage"]):
            return TaskType.PROJECT_MANAGEMENT
        elif any(keyword in message_lower for keyword in ["ui", "click", "interface", "test"]):
            return TaskType.UI_INTERACTION
        elif any(keyword in message_lower for keyword in ["research", "find", "search", "learn"]):
            return TaskType.RESEARCH
        elif any(keyword in message_lower for keyword in ["deploy", "build", "release", "environment"]):
            return TaskType.DEPLOYMENT
        else:
            return TaskType.DEVELOPMENT  # Default to development
    
    async def _execute_plan_direct(self, execution_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Execute plan directly without ROMA coordination."""
        results = []
        agents_used = []
        
        for task in execution_plan.get("tasks", []):
            agent_name = task.get("agent")
            
            if agent_name == "codegen_claude":
                result = await self.codegen_claude_agent.execute_task(task)
                results.append(result)
                agents_used.append("codegen_claude")
                
            elif agent_name == "repomaster":
                result = await self.repomaster_agent.execute_task(task)
                results.append(result)
                agents_used.append("repomaster")
        
        # Combine results
        combined_content = "\n\n".join([r.get("content", "") for r in results])
        combined_metadata = {}
        for r in results:
            combined_metadata.update(r.get("metadata", {}))
        
        return {
            "content": combined_content,
            "agents_used": agents_used,
            "metadata": combined_metadata,
            "requires_followup": any(r.get("requires_followup", False) for r in results),
            "suggested_actions": [
                action for r in results 
                for action in r.get("suggested_actions", [])
            ]
        }
    
    async def _register_core_services(self) -> None:
        """Register core services with the service registry."""
        await self.service_registry.register_service(
            name="codegen_claude",
            service=self.codegen_claude_agent,
            capabilities=["development", "code_generation", "pr_creation", "analysis"]
        )
        
        await self.service_registry.register_service(
            name="repomaster",
            service=self.repomaster_agent,
            capabilities=["code_analysis", "repository_insights", "validation", "quality_assessment"]
        )
    
    async def _update_session_context(
        self, 
        session_id: str, 
        request: OrchestrationRequest,
        result: Dict[str, Any]
    ) -> None:
        """Update session context for conversation continuity."""
        if session_id not in self.active_sessions:
            self.active_sessions[session_id] = {
                "created_at": datetime.now(),
                "messages": [],
                "context": {}
            }
        
        session = self.active_sessions[session_id]
        session["messages"].append({
            "timestamp": datetime.now(),
            "request": request.message,
            "response": result.get("content", ""),
            "agents_used": result.get("agents_used", [])
        })
        
        # Store in unified storage for persistence
        await self.storage_manager.store_session_data(session_id, session)
    
    async def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for a session."""
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]["messages"]
        
        # Try to load from storage
        stored_session = await self.storage_manager.load_session_data(session_id)
        if stored_session:
            return stored_session.get("messages", [])
        
        return []
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check of all components."""
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {}
        }
        
        # Check core components
        try:
            zai_health = await self.zai_substrate.health_check()
            health_status["components"]["zai_substrate"] = zai_health
        except Exception as e:
            health_status["components"]["zai_substrate"] = {"status": "unhealthy", "error": str(e)}
            health_status["status"] = "degraded"
        
        try:
            storage_health = await self.storage_manager.health_check()
            health_status["components"]["storage"] = storage_health
        except Exception as e:
            health_status["components"]["storage"] = {"status": "unhealthy", "error": str(e)}
            health_status["status"] = "degraded"
        
        # Check ROMA if enabled
        if self.roma_integration:
            try:
                roma_health = await self.roma_integration.health_check()
                health_status["components"]["roma"] = roma_health
            except Exception as e:
                health_status["components"]["roma"] = {"status": "unhealthy", "error": str(e)}
                health_status["status"] = "degraded"
        
        return health_status
    
    async def shutdown(self) -> None:
        """Gracefully shutdown all orchestrator components."""
        self.logger.info("Shutting down CI/CD Orchestrator")
        
        try:
            # Shutdown agents
            await self.codegen_claude_agent.shutdown()
            await self.repomaster_agent.shutdown()
            
            # Shutdown core components
            await self.zai_substrate.shutdown()
            await self.storage_manager.shutdown()
            
            # Shutdown ROMA if enabled
            if self.roma_integration:
                await self.roma_integration.shutdown()
            
            self.logger.info("CI/CD Orchestrator shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
            raise
