"""
Service Registry - Dynamic Service Discovery and Management

This module implements the service registry that manages all available services
in the orchestration layer. It handles service registration, discovery, health
tracking, and load balancing across multiple service instances.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import threading

logger = logging.getLogger(__name__)

class ServiceStatus(Enum):
    """Service health status."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    DISABLED = "disabled"

class ServiceType(Enum):
    """Types of services in the orchestration layer."""
    AI_PROCESSING = "ai_processing"
    CODE_ANALYSIS = "code_analysis"
    CONVERSATIONAL_AI = "conversational_ai"
    SANDBOXED_EXECUTION = "sandboxed_execution"
    DATA_STORAGE = "data_storage"
    PROXY_SERVICE = "proxy_service"

@dataclass
class ServiceInfo:
    """Information about a registered service."""
    name: str
    service_type: str
    base_url: str
    health_endpoint: Optional[str] = None
    requires_proxy: bool = False
    rate_limits: Dict[str, Tuple[int, int]] = field(default_factory=dict)  # (limit, window_seconds)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Runtime information
    status: ServiceStatus = ServiceStatus.UNKNOWN
    last_health_check: Optional[datetime] = None
    consecutive_failures: int = 0
    total_requests: int = 0
    successful_requests: int = 0
    average_response_time: float = 0.0
    
    # Load balancing
    current_load: int = 0
    max_concurrent_requests: int = 100
    
    def __post_init__(self):
        """Initialize computed fields."""
        if isinstance(self.service_type, str):
            # Convert string to enum if needed
            try:
                self.service_type = ServiceType(self.service_type)
            except ValueError:
                # Keep as string if not a standard type
                pass
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100
    
    @property
    def is_available(self) -> bool:
        """Check if service is available for requests."""
        return (
            self.status == ServiceStatus.HEALTHY and
            self.current_load < self.max_concurrent_requests
        )
    
    def record_request(self, success: bool, response_time: float) -> None:
        """Record a request for metrics tracking."""
        self.total_requests += 1
        if success:
            self.successful_requests += 1
            self.consecutive_failures = 0
        else:
            self.consecutive_failures += 1
        
        # Update average response time (exponential moving average)
        alpha = 0.1  # Smoothing factor
        self.average_response_time = (
            alpha * response_time + (1 - alpha) * self.average_response_time
        )

class ServiceRegistry:
    """
    Service registry for dynamic service discovery and management.
    
    This class maintains a registry of all available services, tracks their
    health status, and provides intelligent service selection for load balancing.
    """
    
    def __init__(self):
        """Initialize the service registry."""
        self._services: Dict[str, ServiceInfo] = {}
        self._lock = threading.RLock()
        self._initialized = False
        
        # Service selection strategies
        self._selection_strategies = {
            "round_robin": self._round_robin_selection,
            "least_loaded": self._least_loaded_selection,
            "fastest_response": self._fastest_response_selection,
            "highest_success_rate": self._highest_success_rate_selection
        }
        self._current_strategy = "least_loaded"
        self._round_robin_counters: Dict[str, int] = {}
        
        logger.info("ServiceRegistry initialized")
    
    async def initialize(self) -> None:
        """Initialize the service registry."""
        with self._lock:
            if self._initialized:
                return
            
            logger.info("Initializing service registry...")
            self._initialized = True
            logger.info("Service registry initialized")
    
    async def shutdown(self) -> None:
        """Shutdown the service registry."""
        logger.info("Shutting down service registry...")
        
        with self._lock:
            self._services.clear()
            self._round_robin_counters.clear()
            self._initialized = False
        
        logger.info("Service registry shutdown complete")
    
    async def register_service(self, service_info: ServiceInfo) -> bool:
        """
        Register a new service with the registry.
        
        Args:
            service_info: Information about the service to register
            
        Returns:
            True if registration was successful, False otherwise
        """
        with self._lock:
            if service_info.name in self._services:
                logger.warning(f"Service {service_info.name} already registered, updating...")
            
            self._services[service_info.name] = service_info
            self._round_robin_counters[service_info.name] = 0
            
            logger.info(f"Registered service: {service_info.name} ({service_info.service_type})")
            return True
    
    async def unregister_service(self, service_name: str) -> bool:
        """
        Unregister a service from the registry.
        
        Args:
            service_name: Name of the service to unregister
            
        Returns:
            True if unregistration was successful, False if service not found
        """
        with self._lock:
            if service_name not in self._services:
                logger.warning(f"Service {service_name} not found for unregistration")
                return False
            
            del self._services[service_name]
            self._round_robin_counters.pop(service_name, None)
            
            logger.info(f"Unregistered service: {service_name}")
            return True
    
    async def get_service(self, service_name: str) -> Optional[ServiceInfo]:
        """
        Get information about a specific service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            ServiceInfo if found, None otherwise
        """
        with self._lock:
            return self._services.get(service_name)
    
    async def list_services(self, service_type: Optional[str] = None) -> List[ServiceInfo]:
        """
        List all registered services, optionally filtered by type.
        
        Args:
            service_type: Optional service type filter
            
        Returns:
            List of ServiceInfo objects
        """
        with self._lock:
            services = list(self._services.values())
            
            if service_type:
                services = [
                    s for s in services 
                    if str(s.service_type) == service_type
                ]
            
            return services
    
    async def get_healthy_services(self, service_type: Optional[str] = None) -> List[ServiceInfo]:
        """
        Get all healthy services, optionally filtered by type.
        
        Args:
            service_type: Optional service type filter
            
        Returns:
            List of healthy ServiceInfo objects
        """
        services = await self.list_services(service_type)
        return [s for s in services if s.status == ServiceStatus.HEALTHY]
    
    async def get_available_services(self, service_type: Optional[str] = None) -> List[ServiceInfo]:
        """
        Get all available services (healthy and not overloaded).
        
        Args:
            service_type: Optional service type filter
            
        Returns:
            List of available ServiceInfo objects
        """
        services = await self.list_services(service_type)
        return [s for s in services if s.is_available]
    
    async def select_service(
        self,
        service_type: Optional[str] = None,
        strategy: Optional[str] = None,
        exclude_services: Optional[List[str]] = None
    ) -> Optional[ServiceInfo]:
        """
        Select the best service based on the specified strategy.
        
        Args:
            service_type: Optional service type filter
            strategy: Selection strategy (round_robin, least_loaded, etc.)
            exclude_services: List of service names to exclude
            
        Returns:
            Selected ServiceInfo or None if no suitable service found
        """
        available_services = await self.get_available_services(service_type)
        
        if exclude_services:
            available_services = [
                s for s in available_services 
                if s.name not in exclude_services
            ]
        
        if not available_services:
            logger.warning(f"No available services found for type: {service_type}")
            return None
        
        # Use specified strategy or default
        strategy = strategy or self._current_strategy
        selection_func = self._selection_strategies.get(strategy, self._least_loaded_selection)
        
        selected = selection_func(available_services)
        
        if selected:
            logger.debug(f"Selected service: {selected.name} using strategy: {strategy}")
        
        return selected
    
    async def update_service_status(
        self,
        service_name: str,
        status: ServiceStatus,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update the status of a service.
        
        Args:
            service_name: Name of the service
            status: New status
            metadata: Optional metadata to update
            
        Returns:
            True if update was successful, False if service not found
        """
        with self._lock:
            service = self._services.get(service_name)
            if not service:
                return False
            
            old_status = service.status
            service.status = status
            service.last_health_check = datetime.utcnow()
            
            if metadata:
                service.metadata.update(metadata)
            
            if old_status != status:
                logger.info(f"Service {service_name} status changed: {old_status} -> {status}")
            
            return True
    
    async def record_service_request(
        self,
        service_name: str,
        success: bool,
        response_time: float
    ) -> bool:
        """
        Record a request to a service for metrics tracking.
        
        Args:
            service_name: Name of the service
            success: Whether the request was successful
            response_time: Response time in seconds
            
        Returns:
            True if recording was successful, False if service not found
        """
        with self._lock:
            service = self._services.get(service_name)
            if not service:
                return False
            
            service.record_request(success, response_time)
            return True
    
    async def increment_service_load(self, service_name: str) -> bool:
        """
        Increment the current load counter for a service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            True if increment was successful, False if service not found
        """
        with self._lock:
            service = self._services.get(service_name)
            if not service:
                return False
            
            service.current_load += 1
            return True
    
    async def decrement_service_load(self, service_name: str) -> bool:
        """
        Decrement the current load counter for a service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            True if decrement was successful, False if service not found
        """
        with self._lock:
            service = self._services.get(service_name)
            if not service:
                return False
            
            service.current_load = max(0, service.current_load - 1)
            return True
    
    async def get_service_metrics(self, service_name: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive metrics for a service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Dictionary of metrics or None if service not found
        """
        with self._lock:
            service = self._services.get(service_name)
            if not service:
                return None
            
            return {
                "name": service.name,
                "type": str(service.service_type),
                "status": service.status.value,
                "current_load": service.current_load,
                "max_concurrent_requests": service.max_concurrent_requests,
                "total_requests": service.total_requests,
                "successful_requests": service.successful_requests,
                "success_rate": service.success_rate,
                "average_response_time": service.average_response_time,
                "consecutive_failures": service.consecutive_failures,
                "last_health_check": service.last_health_check.isoformat() if service.last_health_check else None,
                "requires_proxy": service.requires_proxy,
                "rate_limits": service.rate_limits
            }
    
    async def get_registry_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive metrics for the entire registry.
        
        Returns:
            Dictionary of registry metrics
        """
        with self._lock:
            total_services = len(self._services)
            healthy_services = len([s for s in self._services.values() if s.status == ServiceStatus.HEALTHY])
            available_services = len([s for s in self._services.values() if s.is_available])
            
            service_types = {}
            for service in self._services.values():
                service_type = str(service.service_type)
                if service_type not in service_types:
                    service_types[service_type] = {"total": 0, "healthy": 0, "available": 0}
                
                service_types[service_type]["total"] += 1
                if service.status == ServiceStatus.HEALTHY:
                    service_types[service_type]["healthy"] += 1
                if service.is_available:
                    service_types[service_type]["available"] += 1
            
            return {
                "total_services": total_services,
                "healthy_services": healthy_services,
                "available_services": available_services,
                "service_types": service_types,
                "selection_strategy": self._current_strategy
            }
    
    def set_selection_strategy(self, strategy: str) -> bool:
        """
        Set the default service selection strategy.
        
        Args:
            strategy: Strategy name
            
        Returns:
            True if strategy was set, False if invalid strategy
        """
        if strategy not in self._selection_strategies:
            logger.error(f"Invalid selection strategy: {strategy}")
            return False
        
        self._current_strategy = strategy
        logger.info(f"Service selection strategy set to: {strategy}")
        return True
    
    # Private selection strategy methods
    
    def _round_robin_selection(self, services: List[ServiceInfo]) -> Optional[ServiceInfo]:
        """Round-robin service selection."""
        if not services:
            return None
        
        # Find the service with the lowest round-robin counter
        min_counter = min(self._round_robin_counters.get(s.name, 0) for s in services)
        candidates = [s for s in services if self._round_robin_counters.get(s.name, 0) == min_counter]
        
        selected = candidates[0]
        self._round_robin_counters[selected.name] += 1
        
        return selected
    
    def _least_loaded_selection(self, services: List[ServiceInfo]) -> Optional[ServiceInfo]:
        """Select service with lowest current load."""
        if not services:
            return None
        
        return min(services, key=lambda s: s.current_load)
    
    def _fastest_response_selection(self, services: List[ServiceInfo]) -> Optional[ServiceInfo]:
        """Select service with fastest average response time."""
        if not services:
            return None
        
        # Filter out services with no recorded response times
        services_with_times = [s for s in services if s.average_response_time > 0]
        if not services_with_times:
            return services[0]  # Fallback to first service
        
        return min(services_with_times, key=lambda s: s.average_response_time)
    
    def _highest_success_rate_selection(self, services: List[ServiceInfo]) -> Optional[ServiceInfo]:
        """Select service with highest success rate."""
        if not services:
            return None
        
        # Filter out services with no recorded requests
        services_with_requests = [s for s in services if s.total_requests > 0]
        if not services_with_requests:
            return services[0]  # Fallback to first service
        
        return max(services_with_requests, key=lambda s: s.success_rate)

