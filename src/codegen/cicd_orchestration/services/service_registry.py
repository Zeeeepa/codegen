"""
Service Registry

Dynamic service registration and discovery system for the CI/CD orchestration
platform. Provides centralized management of all available services and agents
with health monitoring and load balancing capabilities.

Following KISS principles with simple, effective service coordination.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ServiceInfo:
    """Information about a registered service."""
    name: str
    service: Any
    capabilities: List[str]
    status: str = "active"
    load: float = 0.0
    registered_at: datetime = None
    last_health_check: datetime = None


class ServiceRegistry:
    """
    Simple service registry for dynamic service discovery and management.
    
    Follows KISS principle with straightforward service registration,
    discovery, and health monitoring without unnecessary complexity.
    """
    
    def __init__(self):
        """Initialize the service registry."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Service storage
        self.services: Dict[str, ServiceInfo] = {}
        
        # Health monitoring
        self.health_check_interval = 60.0  # seconds
        self._health_check_task: Optional[asyncio.Task] = None
        
        self.logger.info("Service Registry initialized")
    
    async def initialize(self) -> None:
        """Initialize the service registry."""
        try:
            # Start health monitoring
            self._health_check_task = asyncio.create_task(self._health_monitor())
            
            self.logger.info("Service Registry initialization complete")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize service registry: {e}")
            raise
    
    async def register_service(
        self,
        name: str,
        service: Any,
        capabilities: List[str]
    ) -> None:
        """
        Register a service with the registry.
        
        Args:
            name: Unique service name
            service: Service instance
            capabilities: List of service capabilities
        """
        try:
            service_info = ServiceInfo(
                name=name,
                service=service,
                capabilities=capabilities,
                registered_at=datetime.now()
            )
            
            self.services[name] = service_info
            
            self.logger.info(f"Registered service: {name} with capabilities: {capabilities}")
            
        except Exception as e:
            self.logger.error(f"Failed to register service {name}: {e}")
            raise
    
    async def unregister_service(self, name: str) -> None:
        """
        Unregister a service from the registry.
        
        Args:
            name: Service name to unregister
        """
        if name in self.services:
            del self.services[name]
            self.logger.info(f"Unregistered service: {name}")
        else:
            self.logger.warning(f"Attempted to unregister unknown service: {name}")
    
    async def get_service(self, name: str) -> Optional[Any]:
        """
        Get a service by name.
        
        Args:
            name: Service name
            
        Returns:
            Service instance or None if not found
        """
        service_info = self.services.get(name)
        return service_info.service if service_info else None
    
    async def find_services_by_capability(self, capability: str) -> List[str]:
        """
        Find services that have a specific capability.
        
        Args:
            capability: Required capability
            
        Returns:
            List of service names that have the capability
        """
        matching_services = []
        
        for name, service_info in self.services.items():
            if capability in service_info.capabilities and service_info.status == "active":
                matching_services.append(name)
        
        return matching_services
    
    async def get_best_service_for_capability(self, capability: str) -> Optional[str]:
        """
        Get the best available service for a specific capability.
        
        Args:
            capability: Required capability
            
        Returns:
            Name of the best service or None if none available
        """
        matching_services = await self.find_services_by_capability(capability)
        
        if not matching_services:
            return None
        
        # Select service with lowest load
        best_service = None
        lowest_load = float('inf')
        
        for service_name in matching_services:
            service_info = self.services[service_name]
            if service_info.load < lowest_load:
                lowest_load = service_info.load
                best_service = service_name
        
        return best_service
    
    async def update_service_load(self, name: str, load: float) -> None:
        """
        Update the load for a service.
        
        Args:
            name: Service name
            load: Current load (0.0 to 1.0)
        """
        if name in self.services:
            self.services[name].load = load
        else:
            self.logger.warning(f"Attempted to update load for unknown service: {name}")
    
    async def get_service_status(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get status information for a service.
        
        Args:
            name: Service name
            
        Returns:
            Service status information or None if not found
        """
        service_info = self.services.get(name)
        if not service_info:
            return None
        
        return {
            "name": service_info.name,
            "capabilities": service_info.capabilities,
            "status": service_info.status,
            "load": service_info.load,
            "registered_at": service_info.registered_at.isoformat(),
            "last_health_check": service_info.last_health_check.isoformat() if service_info.last_health_check else None
        }
    
    async def get_all_services(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all registered services.
        
        Returns:
            Dictionary of service information
        """
        all_services = {}
        
        for name, service_info in self.services.items():
            all_services[name] = {
                "capabilities": service_info.capabilities,
                "status": service_info.status,
                "load": service_info.load,
                "registered_at": service_info.registered_at.isoformat(),
                "last_health_check": service_info.last_health_check.isoformat() if service_info.last_health_check else None
            }
        
        return all_services
    
    async def _health_monitor(self) -> None:
        """Background task for monitoring service health."""
        while True:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self.health_check_interval)
                
            except Exception as e:
                self.logger.error(f"Error in health monitor: {e}")
                await asyncio.sleep(5.0)  # Brief pause on error
    
    async def _perform_health_checks(self) -> None:
        """Perform health checks on all registered services."""
        for name, service_info in self.services.items():
            try:
                # Check if service has health_check method
                if hasattr(service_info.service, 'health_check'):
                    health_result = await service_info.service.health_check()
                    
                    # Update service status based on health check
                    if health_result.get("status") == "healthy":
                        service_info.status = "active"
                    else:
                        service_info.status = "degraded"
                else:
                    # Assume healthy if no health check method
                    service_info.status = "active"
                
                service_info.last_health_check = datetime.now()
                
            except Exception as e:
                self.logger.warning(f"Health check failed for service {name}: {e}")
                service_info.status = "unhealthy"
                service_info.last_health_check = datetime.now()
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check of the service registry."""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "registered_services": len(self.services),
            "active_services": len([s for s in self.services.values() if s.status == "active"]),
            "degraded_services": len([s for s in self.services.values() if s.status == "degraded"]),
            "unhealthy_services": len([s for s in self.services.values() if s.status == "unhealthy"])
        }
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the service registry."""
        self.logger.info("Shutting down Service Registry")
        
        # Cancel health monitoring
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        # Clear services
        self.services.clear()
        
        self.logger.info("Service Registry shutdown complete")
