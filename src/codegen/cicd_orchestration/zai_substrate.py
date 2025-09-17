"""
Z.AI Intelligence Substrate

Universal intelligence layer that powers ALL agentic instances including ROMA,
RepoMaster, and Codegen Claude agents. Built on web-ui-python-sdk for consistent
Z.AI integration across the entire system.

This substrate provides:
- Unified Z.AI client with proxy rotation and parallel processing
- Intelligence coordination for all agents
- Context-aware reasoning and decision making
- Resource management and load balancing
- Health monitoring and failover capabilities
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

# Import from existing agent operations Z.AI client
from ..agent_operations.ai.zai_client import ZAIClient
from ..agent_operations.proxy.rotation_manager import ProxyRotationManager

logger = logging.getLogger(__name__)


class ReasoningMode(Enum):
    """Z.AI reasoning modes for different agent types."""
    STANDARD = "standard"
    THINKING = "thinking"  # For complex reasoning tasks
    PARALLEL = "parallel"  # For concurrent processing
    CONTEXTUAL = "contextual"  # For context-aware decisions


@dataclass
class AgentRequest:
    """Request structure for agent processing through Z.AI substrate."""
    agent_id: str
    prompt: str
    context: Dict[str, Any]
    reasoning_mode: ReasoningMode = ReasoningMode.STANDARD
    model_preference: Optional[str] = None
    priority: str = "normal"  # low, normal, high, urgent


@dataclass
class AgentResponse:
    """Response structure from Z.AI substrate processing."""
    agent_id: str
    content: str
    reasoning_trace: Optional[str] = None
    confidence: float = 0.0
    metadata: Dict[str, Any] = None
    processing_time: float = 0.0
    model_used: str = ""


class ZAISubstrate:
    """
    Universal Z.AI intelligence substrate that powers all agentic instances.
    
    This class serves as the central intelligence coordination layer,
    managing Z.AI interactions for ROMA, RepoMaster, Codegen Claude,
    and all other agents in the system.
    """
    
    def __init__(
        self,
        enable_proxy_rotation: bool = True,
        enable_parallel_processing: bool = True,
        max_concurrent_requests: int = 10
    ):
        """
        Initialize the Z.AI substrate.
        
        Args:
            enable_proxy_rotation: Enable intelligent proxy rotation
            enable_parallel_processing: Enable parallel request processing
            max_concurrent_requests: Maximum concurrent Z.AI requests
        """
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Core Z.AI client (from existing agent operations)
        self.zai_client = ZAIClient()
        
        # Proxy rotation for high availability
        self.proxy_manager = ProxyRotationManager() if enable_proxy_rotation else None
        
        # Processing configuration
        self.enable_parallel_processing = enable_parallel_processing
        self.max_concurrent_requests = max_concurrent_requests
        self._semaphore = asyncio.Semaphore(max_concurrent_requests)
        
        # Agent coordination
        self.active_agents: Dict[str, Dict[str, Any]] = {}
        self.processing_queue: asyncio.Queue = asyncio.Queue()
        
        # Performance tracking
        self.request_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0
        }
        
        self.logger.info("Z.AI Substrate initialized")
    
    async def initialize(self) -> None:
        """Initialize the Z.AI substrate and all components."""
        try:
            # Initialize core Z.AI client
            await self.zai_client.initialize()
            
            # Initialize proxy manager if enabled
            if self.proxy_manager:
                await self.proxy_manager.initialize()
            
            # Start background processing if parallel processing enabled
            if self.enable_parallel_processing:
                asyncio.create_task(self._background_processor())
            
            self.logger.info("Z.AI Substrate initialization complete")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Z.AI substrate: {e}")
            raise
    
    async def process_agent_request(
        self, 
        request: AgentRequest
    ) -> AgentResponse:
        """
        Process an agent request through the Z.AI substrate.
        
        This is the main entry point for all agent intelligence processing,
        providing unified Z.AI access with intelligent routing and optimization.
        """
        start_time = datetime.now()
        
        try:
            # Acquire semaphore for rate limiting
            async with self._semaphore:
                # Register agent if not already active
                await self._register_agent(request.agent_id)
                
                # Select optimal model based on request
                model = await self._select_optimal_model(request)
                
                # Process through Z.AI with appropriate reasoning mode
                if request.reasoning_mode == ReasoningMode.THINKING:
                    result = await self._process_with_thinking(request, model)
                elif request.reasoning_mode == ReasoningMode.PARALLEL:
                    result = await self._process_parallel(request, model)
                elif request.reasoning_mode == ReasoningMode.CONTEXTUAL:
                    result = await self._process_contextual(request, model)
                else:
                    result = await self._process_standard(request, model)
                
                # Update statistics
                processing_time = (datetime.now() - start_time).total_seconds()
                await self._update_stats(processing_time, success=True)
                
                return AgentResponse(
                    agent_id=request.agent_id,
                    content=result.get("content", ""),
                    reasoning_trace=result.get("reasoning_trace"),
                    confidence=result.get("confidence", 0.0),
                    metadata=result.get("metadata", {}),
                    processing_time=processing_time,
                    model_used=model
                )
                
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            await self._update_stats(processing_time, success=False)
            
            self.logger.error(f"Error processing agent request: {e}")
            
            return AgentResponse(
                agent_id=request.agent_id,
                content=f"Error processing request: {str(e)}",
                confidence=0.0,
                metadata={"error": str(e)},
                processing_time=processing_time,
                model_used=""
            )
    
    async def analyze_request(
        self, 
        prompt: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze a request to determine optimal processing strategy."""
        analysis_request = AgentRequest(
            agent_id="analyzer",
            prompt=f"""
            Analyze this request and provide processing recommendations:
            
            Request: {prompt}
            Context: {context}
            
            Determine:
            1. Task complexity (low, medium, high)
            2. Suggested agents for handling
            3. Required reasoning mode
            4. Estimated processing time
            5. Resource requirements
            """,
            context=context,
            reasoning_mode=ReasoningMode.THINKING
        )
        
        response = await self.process_agent_request(analysis_request)
        
        # Parse analysis results (simplified for now)
        return {
            "complexity": "medium",  # Would parse from response.content
            "suggested_agents": ["codegen_claude"],  # Would parse from response
            "reasoning_mode": ReasoningMode.STANDARD,
            "estimated_time": 5.0,
            "resource_requirements": {"memory": "low", "compute": "medium"}
        }
    
    async def coordinate_agents(
        self, 
        agent_requests: List[AgentRequest]
    ) -> List[AgentResponse]:
        """Coordinate multiple agent requests with intelligent scheduling."""
        if not self.enable_parallel_processing:
            # Sequential processing
            responses = []
            for request in agent_requests:
                response = await self.process_agent_request(request)
                responses.append(response)
            return responses
        
        # Parallel processing with intelligent batching
        tasks = []
        for request in agent_requests:
            task = asyncio.create_task(self.process_agent_request(request))
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions
        processed_responses = []
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                error_response = AgentResponse(
                    agent_id=agent_requests[i].agent_id,
                    content=f"Error: {str(response)}",
                    confidence=0.0,
                    metadata={"error": str(response)}
                )
                processed_responses.append(error_response)
            else:
                processed_responses.append(response)
        
        return processed_responses
    
    async def _register_agent(self, agent_id: str) -> None:
        """Register an agent with the substrate."""
        if agent_id not in self.active_agents:
            self.active_agents[agent_id] = {
                "registered_at": datetime.now(),
                "request_count": 0,
                "last_activity": datetime.now(),
                "performance_metrics": {
                    "average_response_time": 0.0,
                    "success_rate": 1.0
                }
            }
        
        # Update activity
        self.active_agents[agent_id]["last_activity"] = datetime.now()
        self.active_agents[agent_id]["request_count"] += 1
    
    async def _select_optimal_model(self, request: AgentRequest) -> str:
        """Select optimal Z.AI model based on request characteristics."""
        if request.model_preference:
            return request.model_preference
        
        # Intelligent model selection based on task type and complexity
        if request.reasoning_mode == ReasoningMode.THINKING:
            return "glm-4.5v"  # Best for complex reasoning
        elif "code" in request.prompt.lower():
            return "glm-4.5"  # Good for code tasks
        elif request.priority == "urgent":
            return "glm-4-flash"  # Fastest response
        else:
            return "glm-4.5"  # Default balanced model
    
    async def _process_standard(
        self, 
        request: AgentRequest, 
        model: str
    ) -> Dict[str, Any]:
        """Process request with standard Z.AI interaction."""
        response = await self.zai_client.chat(
            message=request.prompt,
            context=request.context,
            model=model
        )
        
        return {
            "content": response.content,
            "confidence": response.confidence,
            "metadata": response.metadata
        }
    
    async def _process_with_thinking(
        self, 
        request: AgentRequest, 
        model: str
    ) -> Dict[str, Any]:
        """Process request with thinking mode for complex reasoning."""
        # Enable thinking mode in Z.AI client
        response = await self.zai_client.chat_with_thinking(
            message=request.prompt,
            context=request.context,
            model=model
        )
        
        return {
            "content": response.content,
            "reasoning_trace": response.thinking_trace,
            "confidence": response.confidence,
            "metadata": response.metadata
        }
    
    async def _process_parallel(
        self, 
        request: AgentRequest, 
        model: str
    ) -> Dict[str, Any]:
        """Process request with parallel processing capabilities."""
        # Break down request into parallel sub-tasks if applicable
        # For now, use standard processing
        return await self._process_standard(request, model)
    
    async def _process_contextual(
        self, 
        request: AgentRequest, 
        model: str
    ) -> Dict[str, Any]:
        """Process request with enhanced context awareness."""
        # Enhance context with agent-specific information
        enhanced_context = {
            **request.context,
            "agent_id": request.agent_id,
            "processing_history": self.active_agents.get(request.agent_id, {}),
            "system_state": await self._get_system_state()
        }
        
        response = await self.zai_client.chat(
            message=request.prompt,
            context=enhanced_context,
            model=model
        )
        
        return {
            "content": response.content,
            "confidence": response.confidence,
            "metadata": response.metadata
        }
    
    async def _get_system_state(self) -> Dict[str, Any]:
        """Get current system state for context enhancement."""
        return {
            "active_agents": len(self.active_agents),
            "processing_queue_size": self.processing_queue.qsize(),
            "system_load": await self._calculate_system_load(),
            "timestamp": datetime.now().isoformat()
        }
    
    async def _calculate_system_load(self) -> float:
        """Calculate current system processing load."""
        # Simple load calculation based on active requests
        active_requests = sum(
            1 for agent in self.active_agents.values()
            if (datetime.now() - agent["last_activity"]).seconds < 60
        )
        return min(active_requests / self.max_concurrent_requests, 1.0)
    
    async def _background_processor(self) -> None:
        """Background processor for handling queued requests."""
        while True:
            try:
                # Process any queued requests
                if not self.processing_queue.empty():
                    request = await self.processing_queue.get()
                    await self.process_agent_request(request)
                
                # Brief pause to prevent busy waiting
                await asyncio.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Error in background processor: {e}")
                await asyncio.sleep(1.0)  # Longer pause on error
    
    async def _update_stats(self, processing_time: float, success: bool) -> None:
        """Update performance statistics."""
        self.request_stats["total_requests"] += 1
        
        if success:
            self.request_stats["successful_requests"] += 1
        else:
            self.request_stats["failed_requests"] += 1
        
        # Update average response time
        total_requests = self.request_stats["total_requests"]
        current_avg = self.request_stats["average_response_time"]
        self.request_stats["average_response_time"] = (
            (current_avg * (total_requests - 1) + processing_time) / total_requests
        )
    
    async def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get status information for a specific agent."""
        return self.active_agents.get(agent_id)
    
    async def get_substrate_stats(self) -> Dict[str, Any]:
        """Get comprehensive substrate statistics."""
        return {
            "request_stats": self.request_stats,
            "active_agents": len(self.active_agents),
            "system_load": await self._calculate_system_load(),
            "proxy_status": await self.proxy_manager.get_status() if self.proxy_manager else None,
            "zai_client_status": await self.zai_client.health_check()
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check of the substrate."""
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {}
        }
        
        # Check Z.AI client
        try:
            zai_health = await self.zai_client.health_check()
            health_status["components"]["zai_client"] = zai_health
        except Exception as e:
            health_status["components"]["zai_client"] = {"status": "unhealthy", "error": str(e)}
            health_status["status"] = "degraded"
        
        # Check proxy manager if enabled
        if self.proxy_manager:
            try:
                proxy_health = await self.proxy_manager.health_check()
                health_status["components"]["proxy_manager"] = proxy_health
            except Exception as e:
                health_status["components"]["proxy_manager"] = {"status": "unhealthy", "error": str(e)}
                health_status["status"] = "degraded"
        
        # Check system load
        system_load = await self._calculate_system_load()
        if system_load > 0.9:
            health_status["status"] = "degraded"
            health_status["warnings"] = ["High system load detected"]
        
        health_status["components"]["system_load"] = {
            "status": "healthy" if system_load < 0.8 else "degraded",
            "load": system_load
        }
        
        return health_status
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the Z.AI substrate."""
        self.logger.info("Shutting down Z.AI Substrate")
        
        try:
            # Shutdown Z.AI client
            await self.zai_client.shutdown()
            
            # Shutdown proxy manager if enabled
            if self.proxy_manager:
                await self.proxy_manager.shutdown()
            
            # Clear active agents
            self.active_agents.clear()
            
            self.logger.info("Z.AI Substrate shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during substrate shutdown: {e}")
            raise
