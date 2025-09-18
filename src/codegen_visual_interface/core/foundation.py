"""
Core Foundation for Codegen Visual Interface

This module provides the foundational architecture for the visual CI/CD interface,
integrating with all Codegen systems and providing the base framework for
visual workflows, AI chat, and comprehensive CI/CD management.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
import threading
import uuid

from .config import VisualInterfaceConfig
from .exceptions import CodegenVisualInterfaceError, APIIntegrationError

logger = logging.getLogger(__name__)

@dataclass
class InterfaceState:
    """Current state of the visual interface."""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    organization_id: Optional[str] = None
    active_projects: List[str] = field(default_factory=list)
    active_workflows: List[str] = field(default_factory=list)
    chat_context: Dict[str, Any] = field(default_factory=dict)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    
    # Integration states
    roma_connected: bool = False
    zai_connected: bool = False
    grainchain_connected: bool = False
    codegen_api_connected: bool = False

@dataclass
class SystemHealth:
    """System health status for all integrated components."""
    overall_status: str = "unknown"  # healthy, degraded, unhealthy
    codegen_api: str = "unknown"
    roma_orchestrator: str = "unknown"
    zai_intelligence: str = "unknown"
    grainchain_sandbox: str = "unknown"
    trace_system: str = "unknown"
    chat_engine: str = "unknown"
    visual_renderer: str = "unknown"
    last_check: datetime = field(default_factory=datetime.utcnow)
    
    def is_healthy(self) -> bool:
        """Check if all systems are healthy."""
        return all(
            status == "healthy" 
            for status in [
                self.codegen_api, self.roma_orchestrator, 
                self.zai_intelligence, self.grainchain_sandbox,
                self.trace_system, self.chat_engine, self.visual_renderer
            ]
        )

class CodegenVisualInterface:
    """
    Main Visual Interface for Codegen CI/CD Platform
    
    This class provides the foundational architecture for the comprehensive
    visual CI/CD interface, integrating all Codegen systems and providing
    unified access to visual workflows, AI chat, and project management.
    """
    
    def __init__(self, config: VisualInterfaceConfig):
        """Initialize the visual interface."""
        self.config = config
        self._lock = threading.RLock()
        self._initialized = False
        self._shutdown_event = asyncio.Event()
        
        # Core state management
        self.state = InterfaceState()
        self.health = SystemHealth()
        
        # Component managers (will be initialized in phases)
        self.api_client = None
        self.roma_orchestrator = None
        self.zai_intelligence = None
        self.grainchain_manager = None
        self.trace_manager = None
        self.chat_engine = None
        self.visual_renderer = None
        self.project_manager = None
        
        # Background tasks
        self._background_tasks: List[asyncio.Task] = []
        
        logger.info(f"CodegenVisualInterface initialized with session {self.state.session_id}")
    
    async def initialize(self) -> None:
        """Initialize all interface components."""
        if self._initialized:
            logger.warning("Interface already initialized")
            return
        
        try:
            logger.info("Initializing Codegen Visual Interface...")
            
            # Phase 1: Core foundation setup
            await self._initialize_foundation()
            
            # Phase 2: API integration layer
            await self._initialize_api_layer()
            
            # Phase 3: Health monitoring
            await self._start_health_monitoring()
            
            # Phase 4: Background services
            await self._start_background_services()
            
            self._initialized = True
            logger.info("Codegen Visual Interface initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize interface: {e}")
            raise CodegenVisualInterfaceError(f"Initialization failed: {e}")
    
    async def _initialize_foundation(self) -> None:
        """Initialize foundational components."""
        logger.info("Initializing foundation components...")
        
        # Validate configuration
        if not self.config.validate():
            raise CodegenVisualInterfaceError("Invalid configuration")
        
        # Set up session context
        self.state.user_id = self.config.user_id
        self.state.organization_id = self.config.organization_id
        
        logger.info("Foundation components initialized")
    
    async def _initialize_api_layer(self) -> None:
        """Initialize API integration layer."""
        logger.info("Initializing API integration layer...")
        
        # This will be implemented in Phase 2
        # For now, just mark as ready for integration
        self.state.codegen_api_connected = False  # Will be true after Phase 2
        
        logger.info("API layer ready for integration")
    
    async def _start_health_monitoring(self) -> None:
        """Start health monitoring for all components."""
        logger.info("Starting health monitoring...")
        
        # Create health check task
        health_task = asyncio.create_task(self._health_check_loop())
        self._background_tasks.append(health_task)
        
        logger.info("Health monitoring started")
    
    async def _start_background_services(self) -> None:
        """Start background services."""
        logger.info("Starting background services...")
        
        # Create session maintenance task
        session_task = asyncio.create_task(self._session_maintenance_loop())
        self._background_tasks.append(session_task)
        
        logger.info("Background services started")
    
    async def _health_check_loop(self) -> None:
        """Continuous health checking loop."""
        while not self._shutdown_event.is_set():
            try:
                await self._perform_health_check()
                await asyncio.sleep(self.config.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")
                await asyncio.sleep(5)  # Brief pause on error
    
    async def _perform_health_check(self) -> None:
        """Perform comprehensive health check."""
        logger.debug("Performing health check...")
        
        # Check each component
        self.health.codegen_api = await self._check_codegen_api_health()
        self.health.roma_orchestrator = await self._check_roma_health()
        self.health.zai_intelligence = await self._check_zai_health()
        self.health.grainchain_sandbox = await self._check_grainchain_health()
        self.health.trace_system = await self._check_trace_system_health()
        self.health.chat_engine = await self._check_chat_engine_health()
        self.health.visual_renderer = await self._check_visual_renderer_health()
        
        # Update overall status
        if self.health.is_healthy():
            self.health.overall_status = "healthy"
        elif any(status == "unhealthy" for status in [
            self.health.codegen_api, self.health.roma_orchestrator,
            self.health.zai_intelligence, self.health.grainchain_sandbox
        ]):
            self.health.overall_status = "unhealthy"
        else:
            self.health.overall_status = "degraded"
        
        self.health.last_check = datetime.utcnow()
        
        logger.debug(f"Health check complete: {self.health.overall_status}")
    
    async def _check_codegen_api_health(self) -> str:
        """Check Codegen API health."""
        if not self.api_client:
            return "not_initialized"
        
        # Will implement actual health check in Phase 2
        return "pending_implementation"
    
    async def _check_roma_health(self) -> str:
        """Check ROMA orchestrator health."""
        if not self.roma_orchestrator:
            return "not_initialized"
        
        # Will implement actual health check in Phase 3
        return "pending_implementation"
    
    async def _check_zai_health(self) -> str:
        """Check Z.AI intelligence health."""
        if not self.zai_intelligence:
            return "not_initialized"
        
        # Will implement actual health check in Phase 4
        return "pending_implementation"
    
    async def _check_grainchain_health(self) -> str:
        """Check Grainchain sandbox health."""
        if not self.grainchain_manager:
            return "not_initialized"
        
        # Will implement actual health check in Phase 5
        return "pending_implementation"
    
    async def _check_trace_system_health(self) -> str:
        """Check trace system health."""
        if not self.trace_manager:
            return "not_initialized"
        
        # Will implement actual health check in Phase 7
        return "pending_implementation"
    
    async def _check_chat_engine_health(self) -> str:
        """Check chat engine health."""
        if not self.chat_engine:
            return "not_initialized"
        
        # Will implement actual health check in Phase 9
        return "pending_implementation"
    
    async def _check_visual_renderer_health(self) -> str:
        """Check visual renderer health."""
        if not self.visual_renderer:
            return "not_initialized"
        
        # Will implement actual health check in Phase 8
        return "pending_implementation"
    
    async def _session_maintenance_loop(self) -> None:
        """Session maintenance loop."""
        while not self._shutdown_event.is_set():
            try:
                await self._maintain_session()
                await asyncio.sleep(self.config.session_maintenance_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Session maintenance error: {e}")
                await asyncio.sleep(10)
    
    async def _maintain_session(self) -> None:
        """Maintain session state and cleanup."""
        logger.debug("Performing session maintenance...")
        
        # Update last activity
        self.state.last_activity = datetime.utcnow()
        
        # Clean up expired data
        await self._cleanup_expired_data()
        
        # Persist session state if needed
        await self._persist_session_state()
    
    async def _cleanup_expired_data(self) -> None:
        """Clean up expired data."""
        # Will implement cleanup logic as components are added
        pass
    
    async def _persist_session_state(self) -> None:
        """Persist session state."""
        # Will implement persistence logic in later phases
        pass
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        return {
            "session_id": self.state.session_id,
            "initialized": self._initialized,
            "health": {
                "overall_status": self.health.overall_status,
                "components": {
                    "codegen_api": self.health.codegen_api,
                    "roma_orchestrator": self.health.roma_orchestrator,
                    "zai_intelligence": self.health.zai_intelligence,
                    "grainchain_sandbox": self.health.grainchain_sandbox,
                    "trace_system": self.health.trace_system,
                    "chat_engine": self.health.chat_engine,
                    "visual_renderer": self.health.visual_renderer
                },
                "last_check": self.health.last_check.isoformat()
            },
            "state": {
                "user_id": self.state.user_id,
                "organization_id": self.state.organization_id,
                "active_projects": len(self.state.active_projects),
                "active_workflows": len(self.state.active_workflows),
                "last_activity": self.state.last_activity.isoformat()
            }
        }
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the interface."""
        logger.info("Shutting down Codegen Visual Interface...")
        
        # Signal shutdown
        self._shutdown_event.set()
        
        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
        
        # Shutdown components
        if self.api_client:
            await self.api_client.shutdown()
        
        if self.roma_orchestrator:
            await self.roma_orchestrator.shutdown()
        
        if self.zai_intelligence:
            await self.zai_intelligence.shutdown()
        
        if self.grainchain_manager:
            await self.grainchain_manager.shutdown()
        
        if self.trace_manager:
            await self.trace_manager.shutdown()
        
        if self.chat_engine:
            await self.chat_engine.shutdown()
        
        if self.visual_renderer:
            await self.visual_renderer.shutdown()
        
        if self.project_manager:
            await self.project_manager.shutdown()
        
        logger.info("Codegen Visual Interface shutdown complete")
    
    def __repr__(self) -> str:
        """String representation."""
        return f"CodegenVisualInterface(session={self.state.session_id}, status={self.health.overall_status})"
