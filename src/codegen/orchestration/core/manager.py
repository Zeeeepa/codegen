"""
Agent Operations Manager - Central Orchestration Hub

This module implements the core AgentOperationsManager that serves as the central
coordination hub for all agent operations. It manages service discovery, request
routing, session persistence, and cross-cutting concerns like rate limiting and
proxy rotation.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import threading
import uuid

from codegen.orchestration.core.service_registry import ServiceRegistry, ServiceInfo
from codegen.orchestration.core.session_manager import SessionManager, UnifiedSession
from codegen.orchestration.core.health_monitor import HealthMonitor
from codegen.orchestration.config.unified_config import UnifiedConfig
from codegen.orchestration.data.sync_manager import DataSyncManager
from codegen.orchestration.rate_limiting.coordinator import RateLimitCoordinator
from codegen.orchestration.proxy.rotation_manager import ProxyRotationManager
from codegen.orchestration.monitoring.tracer import DistributedTracer

logger = logging.getLogger(__name__)

class OperationStatus(Enum):
    """Status of orchestration operations."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class OperationRequest:
    """Unified request structure for all operations."""
    operation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    operation_type: str = ""
    user_id: str = ""
    session_id: str = ""
    service_preference: Optional[str] = None
    priority: int = 5  # 1-10, higher is more priority
    timeout: int = 300  # seconds
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class OperationResponse:
    """Unified response structure for all operations."""
    operation_id: str
    status: OperationStatus
    result: Optional[Any] = None
    error: Optional[str] = None
    service_used: Optional[str] = None
    proxy_used: Optional[str] = None
    execution_time: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    completed_at: Optional[datetime] = None

class AgentOperationsManager:
    """
    Central orchestration hub for all agent operations.
    
    This class coordinates between multiple AI services (Z.AI, RepoMaster, Claude, Codegen),
    manages data synchronization, handles proxy rotation, enforces rate limiting,
    and provides unified session management.
    """
    
    def __init__(self, config: Optional[UnifiedConfig] = None):
        """Initialize the orchestration manager."""
        self.config = config or UnifiedConfig.load()
        self._lock = threading.RLock()
        self._initialized = False
        
        # Core components
        self.service_registry = ServiceRegistry()
        self.session_manager = SessionManager(self.config)
        self.health_monitor = HealthMonitor()
        self.data_sync_manager = DataSyncManager(self.config)
        self.rate_limit_coordinator = RateLimitCoordinator(self.config)
        self.proxy_manager = ProxyRotationManager(self.config)
        self.tracer = DistributedTracer()
        
        # Operation tracking
        self._active_operations: Dict[str, OperationRequest] = {}
        self._operation_history: List[OperationResponse] = []
        
        # Background tasks
        self._background_tasks: List[asyncio.Task] = []
        self._shutdown_event = asyncio.Event()
        
        logger.info("AgentOperationsManager initialized")
    
    async def initialize(self) -> None:
        """Initialize all orchestration components."""
        with self._lock:
            if self._initialized:
                return
            
            logger.info("Initializing orchestration components...")
            
            # Initialize core components
            await self.service_registry.initialize()
            await self.session_manager.initialize()
            await self.health_monitor.initialize()
            await self.data_sync_manager.initialize()
            await self.rate_limit_coordinator.initialize()
            await self.proxy_manager.initialize()
            
            # Register available services
            await self._register_services()
            
            # Start background tasks
            await self._start_background_tasks()
            
            self._initialized = True
            logger.info("Orchestration layer fully initialized")
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the orchestration layer."""
        logger.info("Shutting down orchestration layer...")
        
        # Signal shutdown to background tasks
        self._shutdown_event.set()
        
        # Cancel active operations
        for operation_id in list(self._active_operations.keys()):
            await self.cancel_operation(operation_id)
        
        # Wait for background tasks to complete
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
        
        # Shutdown components
        await self.proxy_manager.shutdown()
        await self.rate_limit_coordinator.shutdown()
        await self.data_sync_manager.shutdown()
        await self.health_monitor.shutdown()
        await self.session_manager.shutdown()
        await self.service_registry.shutdown()
        
        self._initialized = False
        logger.info("Orchestration layer shutdown complete")
    
    async def execute_operation(self, request: OperationRequest) -> OperationResponse:
        """
        Execute a unified operation through the orchestration layer.
        
        This is the main entry point for all operations. It handles:
        - Service selection and routing
        - Rate limiting and queuing
        - Proxy assignment
        - Session management
        - Error handling and recovery
        - Response processing and caching
        """
        if not self._initialized:
            await self.initialize()
        
        # Start distributed tracing
        with self.tracer.start_span(f"orchestration.{request.operation_type}") as span:
            span.set_attribute("operation_id", request.operation_id)
            span.set_attribute("user_id", request.user_id)
            span.set_attribute("session_id", request.session_id)
            
            try:
                # Track active operation
                self._active_operations[request.operation_id] = request
                
                # Get or create session
                session = await self.session_manager.get_or_create_session(
                    request.session_id, request.user_id
                )
                
                # Check rate limits
                with self.tracer.start_span("rate_limit_check") as rate_span:
                    await self.rate_limit_coordinator.check_rate_limit(
                        request.user_id, request.operation_type
                    )
                
                # Select appropriate service
                with self.tracer.start_span("service_selection") as service_span:
                    service_info = await self._select_service(request)
                    service_span.set_attribute("selected_service", service_info.name)
                
                # Assign proxy if needed
                proxy_info = None
                if service_info.requires_proxy:
                    with self.tracer.start_span("proxy_assignment") as proxy_span:
                        proxy_info = await self.proxy_manager.assign_proxy(
                            service_info.name, request.user_id
                        )
                        if proxy_info:
                            proxy_span.set_attribute("proxy_id", proxy_info.id)
                
                # Execute the operation
                with self.tracer.start_span("operation_execution") as exec_span:
                    start_time = datetime.utcnow()
                    
                    result = await self._execute_service_operation(
                        service_info, request, session, proxy_info
                    )
                    
                    execution_time = (datetime.utcnow() - start_time).total_seconds()
                    exec_span.set_attribute("execution_time", execution_time)
                
                # Process and cache response
                with self.tracer.start_span("response_processing") as response_span:
                    await self._process_response(result, session)
                
                # Create successful response
                response = OperationResponse(
                    operation_id=request.operation_id,
                    status=OperationStatus.COMPLETED,
                    result=result,
                    service_used=service_info.name,
                    proxy_used=proxy_info.id if proxy_info else None,
                    execution_time=execution_time,
                    completed_at=datetime.utcnow()
                )
                
                logger.info(f"Operation {request.operation_id} completed successfully")
                return response
                
            except Exception as e:
                logger.error(f"Operation {request.operation_id} failed: {str(e)}")
                span.set_attribute("error", True)
                span.set_attribute("error_message", str(e))
                
                # Create error response
                response = OperationResponse(
                    operation_id=request.operation_id,
                    status=OperationStatus.FAILED,
                    error=str(e),
                    completed_at=datetime.utcnow()
                )
                
                return response
                
            finally:
                # Clean up active operation tracking
                self._active_operations.pop(request.operation_id, None)
                
                # Store operation history
                if len(self._operation_history) > 1000:  # Keep last 1000 operations
                    self._operation_history = self._operation_history[-900:]
    
    async def cancel_operation(self, operation_id: str) -> bool:
        """Cancel an active operation."""
        if operation_id not in self._active_operations:
            return False
        
        # TODO: Implement operation cancellation logic
        # This would involve cancelling the underlying service call
        # and cleaning up any resources
        
        self._active_operations.pop(operation_id, None)
        logger.info(f"Operation {operation_id} cancelled")
        return True
    
    async def get_operation_status(self, operation_id: str) -> Optional[OperationStatus]:
        """Get the status of an operation."""
        if operation_id in self._active_operations:
            return OperationStatus.IN_PROGRESS
        
        # Check operation history
        for response in reversed(self._operation_history):
            if response.operation_id == operation_id:
                return response.status
        
        return None
    
    async def list_active_operations(self, user_id: Optional[str] = None) -> List[OperationRequest]:
        """List active operations, optionally filtered by user."""
        operations = list(self._active_operations.values())
        
        if user_id:
            operations = [op for op in operations if op.user_id == user_id]
        
        return operations
    
    async def get_service_health(self) -> Dict[str, Any]:
        """Get health status of all registered services."""
        return await self.health_monitor.get_all_service_health()
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get comprehensive system metrics."""
        return {
            "active_operations": len(self._active_operations),
            "total_operations": len(self._operation_history),
            "service_health": await self.get_service_health(),
            "rate_limits": await self.rate_limit_coordinator.get_current_limits(),
            "proxy_status": await self.proxy_manager.get_pool_status(),
            "data_sync_status": await self.data_sync_manager.get_sync_status()
        }
    
    # Private methods
    
    async def _register_services(self) -> None:
        """Register all available services with the service registry."""
        services_config = self.config.get_services_config()
        
        # Register Z.AI service
        if services_config.get("zai", {}).get("enabled", False):
            await self.service_registry.register_service(ServiceInfo(
                name="zai",
                service_type="ai_processing",
                base_url=services_config["zai"]["base_url"],
                health_endpoint="/health",
                requires_proxy=True,
                rate_limits={
                    "parallel_requests": (50, 60),  # 50 per minute
                    "single_request": (100, 60)     # 100 per minute
                }
            ))
        
        # Register RepoMaster service
        if services_config.get("repomaster", {}).get("enabled", False):
            await self.service_registry.register_service(ServiceInfo(
                name="repomaster",
                service_type="code_analysis",
                base_url=services_config["repomaster"]["base_url"],
                health_endpoint="/health",
                requires_proxy=False,
                rate_limits={
                    "analysis_request": (20, 60),   # 20 per minute
                    "file_operations": (30, 60)     # 30 per minute
                }
            ))
        
        # Register Claude service
        if services_config.get("claude", {}).get("enabled", False):
            await self.service_registry.register_service(ServiceInfo(
                name="claude",
                service_type="conversational_ai",
                base_url="internal://claude",  # Internal service
                health_endpoint=None,
                requires_proxy=False,
                rate_limits={
                    "chat_request": (60, 60),       # 60 per minute
                    "code_generation": (30, 60)     # 30 per minute
                }
            ))
        
        # Register Codegen API service
        if services_config.get("codegen", {}).get("enabled", False):
            await self.service_registry.register_service(ServiceInfo(
                name="codegen",
                service_type="sandboxed_execution",
                base_url=services_config["codegen"]["base_url"],
                health_endpoint="/health",
                requires_proxy=False,
                rate_limits={
                    "agent_creation": (10, 60),     # 10 per minute
                    "status_check": (60, 30),       # 60 per 30 seconds
                    "log_retrieval": (5, 60)        # 5 per minute
                }
            ))
    
    async def _select_service(self, request: OperationRequest) -> ServiceInfo:
        """Select the most appropriate service for the operation."""
        # If user specified a service preference, try to use it
        if request.service_preference:
            service = await self.service_registry.get_service(request.service_preference)
            if service and await self.health_monitor.is_service_healthy(service.name):
                return service
        
        # Select based on operation type
        operation_type = request.operation_type
        
        if operation_type.startswith("zai."):
            return await self.service_registry.get_service("zai")
        elif operation_type.startswith("repomaster."):
            return await self.service_registry.get_service("repomaster")
        elif operation_type.startswith("claude."):
            return await self.service_registry.get_service("claude")
        elif operation_type.startswith("codegen."):
            return await self.service_registry.get_service("codegen")
        
        # Default fallback logic
        available_services = await self.service_registry.get_healthy_services()
        if not available_services:
            raise RuntimeError("No healthy services available")
        
        # Simple load balancing - select least loaded service
        # TODO: Implement more sophisticated selection logic
        return available_services[0]
    
    async def _execute_service_operation(
        self,
        service_info: ServiceInfo,
        request: OperationRequest,
        session: UnifiedSession,
        proxy_info: Optional[Any] = None
    ) -> Any:
        """Execute the operation on the selected service."""
        # This is where we would call the actual service adapters
        # For now, return a placeholder response
        
        # TODO: Implement actual service adapter calls
        # - ZAI adapter for parallel processing
        # - RepoMaster adapter for code analysis
        # - Claude adapter for conversational AI
        # - Codegen adapter for sandboxed execution
        
        return {
            "service": service_info.name,
            "operation": request.operation_type,
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _process_response(self, result: Any, session: UnifiedSession) -> None:
        """Process and cache the operation response."""
        # Update session with operation result
        await self.session_manager.update_session_context(
            session.session_id,
            {"last_operation_result": result}
        )
        
        # Sync data if needed
        await self.data_sync_manager.sync_operation_result(result)
    
    async def _start_background_tasks(self) -> None:
        """Start background monitoring and maintenance tasks."""
        # Health monitoring task
        self._background_tasks.append(
            asyncio.create_task(self._health_monitoring_loop())
        )
        
        # Data synchronization task
        self._background_tasks.append(
            asyncio.create_task(self._data_sync_loop())
        )
        
        # Cleanup task
        self._background_tasks.append(
            asyncio.create_task(self._cleanup_loop())
        )
    
    async def _health_monitoring_loop(self) -> None:
        """Background task for continuous health monitoring."""
        while not self._shutdown_event.is_set():
            try:
                await self.health_monitor.check_all_services()
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(60)  # Back off on error
    
    async def _data_sync_loop(self) -> None:
        """Background task for data synchronization."""
        while not self._shutdown_event.is_set():
            try:
                await self.data_sync_manager.perform_sync()
                await asyncio.sleep(300)  # Sync every 5 minutes
            except Exception as e:
                logger.error(f"Data sync error: {e}")
                await asyncio.sleep(600)  # Back off on error
    
    async def _cleanup_loop(self) -> None:
        """Background task for cleanup and maintenance."""
        while not self._shutdown_event.is_set():
            try:
                # Clean up old operation history
                cutoff_time = datetime.utcnow().timestamp() - 86400  # 24 hours
                self._operation_history = [
                    op for op in self._operation_history
                    if op.completed_at and op.completed_at.timestamp() > cutoff_time
                ]
                
                # Clean up expired sessions
                await self.session_manager.cleanup_expired_sessions()
                
                await asyncio.sleep(3600)  # Cleanup every hour
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
                await asyncio.sleep(3600)  # Continue on error

