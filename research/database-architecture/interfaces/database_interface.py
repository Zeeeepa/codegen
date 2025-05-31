"""
Database Interface Layer for Comprehensive Database Architecture

This module provides a unified interface for interacting with the database
architecture supporting Graph-Sitter, Codegen SDK, and Contexten integration.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass
from enum import Enum


class EntityType(Enum):
    """Supported entity types in the system."""
    TASK = "task"
    PROJECT = "project"
    CODEBASE = "codebase"
    USER = "user"
    WORKFLOW = "workflow"
    EVENT = "event"
    EVALUATION = "evaluation"


@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    postgresql_url: str
    clickhouse_url: str
    redis_url: Optional[str] = None
    connection_pool_size: int = 10
    query_timeout: int = 30
    enable_caching: bool = True
    cache_ttl: int = 3600


@dataclass
class QueryResult:
    """Standard query result wrapper."""
    data: Any
    total_count: Optional[int] = None
    page: Optional[int] = None
    page_size: Optional[int] = None
    execution_time_ms: Optional[float] = None
    from_cache: bool = False


class DatabaseInterface(ABC):
    """Abstract base class for database operations."""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
    
    @abstractmethod
    async def connect(self) -> None:
        """Establish database connections."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close database connections."""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check database health and connectivity."""
        pass


class TaskInterface(ABC):
    """Interface for task management operations."""
    
    @abstractmethod
    async def create_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new task."""
        pass
    
    @abstractmethod
    async def get_task(self, task_id: int, organization_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a task by ID."""
        pass
    
    @abstractmethod
    async def update_task(self, task_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing task."""
        pass
    
    @abstractmethod
    async def delete_task(self, task_id: int, organization_id: int) -> bool:
        """Soft delete a task."""
        pass
    
    @abstractmethod
    async def search_tasks(self, filters: Dict[str, Any]) -> QueryResult:
        """Search tasks with filters."""
        pass
    
    @abstractmethod
    async def get_task_dependencies(self, task_id: int) -> List[Dict[str, Any]]:
        """Get task dependencies."""
        pass


class ProjectInterface(ABC):
    """Interface for project management operations."""
    
    @abstractmethod
    async def create_project(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new project."""
        pass
    
    @abstractmethod
    async def get_project(self, project_id: int, organization_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a project by ID."""
        pass
    
    @abstractmethod
    async def update_project(self, project_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing project."""
        pass
    
    @abstractmethod
    async def get_project_metrics(self, project_id: int, date_range: Optional[tuple] = None) -> Dict[str, Any]:
        """Get project performance metrics."""
        pass
    
    @abstractmethod
    async def get_project_timeline(self, project_id: int) -> List[Dict[str, Any]]:
        """Get project timeline with milestones."""
        pass


class CodebaseInterface(ABC):
    """Interface for codebase analysis operations."""
    
    @abstractmethod
    async def create_codebase(self, codebase_data: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new codebase."""
        pass
    
    @abstractmethod
    async def get_codebase(self, codebase_id: int, organization_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve codebase information."""
        pass
    
    @abstractmethod
    async def update_analysis_results(self, codebase_id: int, analysis_data: Dict[str, Any]) -> bool:
        """Update codebase analysis results."""
        pass
    
    @abstractmethod
    async def get_code_relationships(self, codebase_id: int, relationship_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get code relationships and dependencies."""
        pass
    
    @abstractmethod
    async def search_code_symbols(self, codebase_id: int, query: str) -> QueryResult:
        """Search for code symbols."""
        pass


class EventInterface(ABC):
    """Interface for event processing operations."""
    
    @abstractmethod
    async def ingest_event(self, event_data: Dict[str, Any]) -> str:
        """Ingest a new event."""
        pass
    
    @abstractmethod
    async def get_events(self, filters: Dict[str, Any]) -> QueryResult:
        """Query events with filters."""
        pass
    
    @abstractmethod
    async def get_event_timeline(self, entity_type: str, entity_id: int) -> List[Dict[str, Any]]:
        """Get event timeline for an entity."""
        pass
    
    @abstractmethod
    async def correlate_events(self, correlation_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find correlated events."""
        pass


class EvaluationInterface(ABC):
    """Interface for evaluation and analytics operations."""
    
    @abstractmethod
    async def create_evaluation(self, evaluation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new evaluation."""
        pass
    
    @abstractmethod
    async def get_evaluation_results(self, evaluation_id: int) -> Optional[Dict[str, Any]]:
        """Get evaluation results."""
        pass
    
    @abstractmethod
    async def get_performance_trends(self, entity_type: str, entity_id: int, days: int = 30) -> List[Dict[str, Any]]:
        """Get performance trends for an entity."""
        pass
    
    @abstractmethod
    async def calculate_metrics(self, metric_config: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate custom metrics."""
        pass


class AnalyticsInterface(ABC):
    """Interface for analytics and reporting operations."""
    
    @abstractmethod
    async def get_dashboard_data(self, dashboard_id: int, user_id: int) -> Dict[str, Any]:
        """Get dashboard data for a user."""
        pass
    
    @abstractmethod
    async def generate_report(self, report_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a custom report."""
        pass
    
    @abstractmethod
    async def get_real_time_metrics(self, organization_id: int, metric_names: List[str]) -> Dict[str, Any]:
        """Get real-time metrics."""
        pass
    
    @abstractmethod
    async def calculate_trends(self, metric_name: str, organization_id: int, period: str = "daily") -> List[Dict[str, Any]]:
        """Calculate metric trends."""
        pass


class RelationshipInterface(ABC):
    """Interface for relationship management operations."""
    
    @abstractmethod
    async def create_relationship(self, relationship_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new relationship."""
        pass
    
    @abstractmethod
    async def get_entity_relationships(self, entity_type: str, entity_id: int) -> List[Dict[str, Any]]:
        """Get all relationships for an entity."""
        pass
    
    @abstractmethod
    async def find_path(self, source_entity: tuple, target_entity: tuple, max_depth: int = 6) -> Optional[List[Dict[str, Any]]]:
        """Find shortest path between entities."""
        pass
    
    @abstractmethod
    async def get_relationship_graph(self, graph_type: str, organization_id: int) -> Dict[str, Any]:
        """Get precomputed relationship graph."""
        pass


class CacheInterface(ABC):
    """Interface for caching operations."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get cached value."""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set cached value."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete cached value."""
        pass
    
    @abstractmethod
    async def clear_pattern(self, pattern: str) -> int:
        """Clear cache entries matching pattern."""
        pass


class ComprehensiveDatabaseInterface(
    DatabaseInterface,
    TaskInterface,
    ProjectInterface,
    CodebaseInterface,
    EventInterface,
    EvaluationInterface,
    AnalyticsInterface,
    RelationshipInterface,
    CacheInterface
):
    """
    Comprehensive database interface combining all specialized interfaces.
    
    This is the main interface that applications should use to interact
    with the database architecture.
    """
    
    async def begin_transaction(self) -> Any:
        """Begin a database transaction."""
        pass
    
    async def commit_transaction(self, transaction: Any) -> None:
        """Commit a database transaction."""
        pass
    
    async def rollback_transaction(self, transaction: Any) -> None:
        """Rollback a database transaction."""
        pass
    
    async def execute_raw_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> QueryResult:
        """Execute a raw SQL query."""
        pass
    
    async def bulk_insert(self, table: str, data: List[Dict[str, Any]]) -> int:
        """Perform bulk insert operation."""
        pass
    
    async def bulk_update(self, table: str, data: List[Dict[str, Any]], key_field: str) -> int:
        """Perform bulk update operation."""
        pass


# Factory function for creating database interface instances
def create_database_interface(config: DatabaseConfig, implementation: str = "postgresql") -> ComprehensiveDatabaseInterface:
    """
    Factory function to create database interface instances.
    
    Args:
        config: Database configuration
        implementation: Database implementation type ("postgresql", "hybrid", etc.)
    
    Returns:
        Database interface instance
    """
    if implementation == "postgresql":
        from .postgresql_implementation import PostgreSQLDatabaseInterface
        return PostgreSQLDatabaseInterface(config)
    elif implementation == "hybrid":
        from .hybrid_implementation import HybridDatabaseInterface
        return HybridDatabaseInterface(config)
    else:
        raise ValueError(f"Unknown database implementation: {implementation}")


# Exception classes
class DatabaseError(Exception):
    """Base database error."""
    pass


class ConnectionError(DatabaseError):
    """Database connection error."""
    pass


class QueryError(DatabaseError):
    """Query execution error."""
    pass


class ValidationError(DatabaseError):
    """Data validation error."""
    pass


class NotFoundError(DatabaseError):
    """Entity not found error."""
    pass


class PermissionError(DatabaseError):
    """Permission denied error."""
    pass

