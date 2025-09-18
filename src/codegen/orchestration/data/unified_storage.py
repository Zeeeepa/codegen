"""
Unified Storage Manager

This module provides unified data storage and synchronization across
SQLite, Redis, and live API data sources with automatic coordination
and consistency management.
"""

import asyncio
import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import uuid

from codegen.orchestration.config.unified_config import UnifiedConfig

logger = logging.getLogger(__name__)

class StorageBackend(Enum):
    """Storage backend types."""
    SQLITE = "sqlite"
    REDIS = "redis"
    MEMORY = "memory"

class SyncStrategy(Enum):
    """Data synchronization strategies."""
    WRITE_THROUGH = "write_through"
    WRITE_BEHIND = "write_behind"
    READ_THROUGH = "read_through"

@dataclass
class StorageRecord:
    """Generic storage record."""
    record_id: str
    record_type: str
    data: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    version: int = 1
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class UnifiedStorageManager:
    """
    Unified Storage Manager for Multi-Backend Data Coordination.
    
    This manager provides:
    - SQLite for persistent structured data
    - Redis for caching and session data
    - Memory for high-performance temporary data
    - Automatic synchronization between backends
    - Consistency management and conflict resolution
    """
    
    def __init__(self, config: UnifiedConfig):
        """Initialize unified storage manager."""
        self.config = config
        self._initialized = False
        
        # Configuration
        data_config = config.get_data_config()
        self.sqlite_path = data_config.sqlite_path
        self.redis_url = data_config.redis_url
        self.sync_strategy = SyncStrategy(data_config.sync_strategy)
        self.cache_ttl = data_config.cache_ttl
        
        # Storage backends
        self._sqlite_conn: Optional[sqlite3.Connection] = None
        self._redis_client: Optional[Any] = None  # Redis client
        self._memory_store: Dict[str, StorageRecord] = {}
        
        # Synchronization
        self._sync_queue: asyncio.Queue = asyncio.Queue()
        self._sync_lock = threading.RLock()
        
        # Background tasks
        self._background_tasks: List[asyncio.Task] = []
        self._shutdown_event = asyncio.Event()
        
        # Metrics
        self.total_reads = 0
        self.total_writes = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.sync_operations = 0
        
        logger.info("UnifiedStorageManager initialized")
    
    async def initialize(self) -> None:
        """Initialize all storage backends."""
        if self._initialized:
            return
        
        logger.info("Initializing unified storage manager...")
        
        # Initialize SQLite
        await self._initialize_sqlite()
        
        # Initialize Redis
        await self._initialize_redis()
        
        # Initialize memory store
        self._memory_store = {}
        
        # Start background tasks
        await self._start_background_tasks()
        
        self._initialized = True
        logger.info("Unified storage manager initialized successfully")
    
    async def shutdown(self) -> None:
        """Shutdown storage manager."""
        logger.info("Shutting down unified storage manager...")
        
        # Signal shutdown
        self._shutdown_event.set()
        
        # Process remaining sync queue
        await self._process_sync_queue()
        
        # Cancel background tasks
        if self._background_tasks:
            for task in self._background_tasks:
                task.cancel()
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
        
        # Close connections
        if self._sqlite_conn:
            self._sqlite_conn.close()
        
        if self._redis_client:
            await self._redis_client.close()
        
        self._initialized = False
        logger.info("Unified storage manager shutdown complete")
    
    async def store(
        self,
        record_type: str,
        data: Dict[str, Any],
        record_id: Optional[str] = None,
        backend: Optional[StorageBackend] = None
    ) -> str:
        """
        Store data with automatic backend selection and synchronization.
        
        Args:
            record_type: Type of record (e.g., 'deployment', 'session', 'metric')
            data: Data to store
            record_id: Optional record ID (generated if not provided)
            backend: Optional specific backend to use
            
        Returns:
            Record ID
        """
        if not self._initialized:
            await self.initialize()
        
        # Generate record ID if not provided
        if not record_id:
            record_id = f"{record_type}_{uuid.uuid4().hex[:8]}"
        
        # Create storage record
        record = StorageRecord(
            record_id=record_id,
            record_type=record_type,
            data=data,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Determine storage strategy
        if backend:
            await self._store_to_backend(record, backend)
        else:
            await self._store_with_strategy(record)
        
        self.total_writes += 1
        logger.debug(f"Stored record: {record_id} ({record_type})")
        
        return record_id
    
    async def retrieve(
        self,
        record_id: str,
        backend: Optional[StorageBackend] = None
    ) -> Optional[StorageRecord]:
        """
        Retrieve data with automatic backend selection and caching.
        
        Args:
            record_id: Record ID to retrieve
            backend: Optional specific backend to use
            
        Returns:
            StorageRecord if found, None otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        self.total_reads += 1
        
        # Try specific backend if requested
        if backend:
            return await self._retrieve_from_backend(record_id, backend)
        
        # Try memory first (fastest)
        record = await self._retrieve_from_backend(record_id, StorageBackend.MEMORY)
        if record:
            self.cache_hits += 1
            return record
        
        # Try Redis (fast cache)
        if self._redis_client:
            record = await self._retrieve_from_backend(record_id, StorageBackend.REDIS)
            if record:
                # Cache in memory for future access
                self._memory_store[record_id] = record
                self.cache_hits += 1
                return record
        
        # Try SQLite (persistent storage)
        record = await self._retrieve_from_backend(record_id, StorageBackend.SQLITE)
        if record:
            # Cache in faster backends
            await self._cache_record(record)
            self.cache_misses += 1
            return record
        
        self.cache_misses += 1
        return None
    
    async def update(
        self,
        record_id: str,
        data: Dict[str, Any],
        backend: Optional[StorageBackend] = None
    ) -> bool:
        """
        Update existing record.
        
        Args:
            record_id: Record ID to update
            data: New data
            backend: Optional specific backend to use
            
        Returns:
            True if updated successfully, False if record not found
        """
        if not self._initialized:
            await self.initialize()
        
        # Retrieve existing record
        existing_record = await self.retrieve(record_id, backend)
        if not existing_record:
            return False
        
        # Update record
        existing_record.data.update(data)
        existing_record.updated_at = datetime.utcnow()
        existing_record.version += 1
        
        # Store updated record
        if backend:
            await self._store_to_backend(existing_record, backend)
        else:
            await self._store_with_strategy(existing_record)
        
        self.total_writes += 1
        logger.debug(f"Updated record: {record_id}")
        
        return True
    
    async def delete(
        self,
        record_id: str,
        backend: Optional[StorageBackend] = None
    ) -> bool:
        """
        Delete record from storage.
        
        Args:
            record_id: Record ID to delete
            backend: Optional specific backend to use
            
        Returns:
            True if deleted successfully, False if record not found
        """
        if not self._initialized:
            await self.initialize()
        
        deleted = False
        
        if backend:
            deleted = await self._delete_from_backend(record_id, backend)
        else:
            # Delete from all backends
            for storage_backend in StorageBackend:
                if await self._delete_from_backend(record_id, storage_backend):
                    deleted = True
        
        if deleted:
            logger.debug(f"Deleted record: {record_id}")
        
        return deleted
    
    async def query(
        self,
        record_type: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        backend: Optional[StorageBackend] = None
    ) -> List[StorageRecord]:
        """
        Query records by type and filters.
        
        Args:
            record_type: Type of records to query
            filters: Optional filters to apply
            limit: Optional limit on results
            backend: Optional specific backend to use
            
        Returns:
            List of matching StorageRecord objects
        """
        if not self._initialized:
            await self.initialize()
        
        # Use SQLite for complex queries by default
        target_backend = backend or StorageBackend.SQLITE
        
        return await self._query_backend(target_backend, record_type, filters, limit)
    
    async def store_deployment_record(self, deployment_data: Dict[str, Any]) -> str:
        """Store deployment record with proper indexing."""
        return await self.store("deployment", deployment_data)
    
    async def update_deployment_status(self, deployment_id: str, status_data: Dict[str, Any]) -> bool:
        """Update deployment status."""
        return await self.update(deployment_id, status_data)
    
    async def get_deployment_history(self, limit: int = 100) -> List[StorageRecord]:
        """Get deployment history."""
        return await self.query("deployment", limit=limit)
    
    async def store_session_data(self, session_id: str, session_data: Dict[str, Any]) -> str:
        """Store session data with Redis caching."""
        # Store in Redis for fast access
        await self.store("session", session_data, session_id, StorageBackend.REDIS)
        
        # Also store in SQLite for persistence
        return await self.store("session", session_data, session_id, StorageBackend.SQLITE)
    
    async def get_session_data(self, session_id: str) -> Optional[StorageRecord]:
        """Get session data with cache optimization."""
        # Try Redis first for fast access
        record = await self.retrieve(session_id, StorageBackend.REDIS)
        if record:
            return record
        
        # Fallback to SQLite
        return await self.retrieve(session_id, StorageBackend.SQLITE)
    
    async def store_metrics(self, metrics_data: List[Dict[str, Any]]) -> List[str]:
        """Store multiple metrics efficiently."""
        record_ids = []
        
        for metric_data in metrics_data:
            record_id = await self.store("metric", metric_data, backend=StorageBackend.SQLITE)
            record_ids.append(record_id)
        
        return record_ids
    
    async def get_status(self) -> Dict[str, Any]:
        """Get comprehensive storage status."""
        return {
            "initialized": self._initialized,
            "total_reads": self.total_reads,
            "total_writes": self.total_writes,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": (self.cache_hits / max(self.total_reads, 1)) * 100,
            "sync_operations": self.sync_operations,
            "memory_records": len(self._memory_store),
            "sync_strategy": self.sync_strategy.value,
            "backends": {
                "sqlite": self._sqlite_conn is not None,
                "redis": self._redis_client is not None,
                "memory": True
            }
        }
    
    # Private methods
    
    async def _initialize_sqlite(self) -> None:
        """Initialize SQLite database."""
        try:
            self._sqlite_conn = sqlite3.connect(self.sqlite_path, check_same_thread=False)
            self._sqlite_conn.row_factory = sqlite3.Row
            
            # Create tables
            await self._create_sqlite_tables()
            
            logger.info(f"SQLite initialized: {self.sqlite_path}")
        except Exception as e:
            logger.error(f"Failed to initialize SQLite: {e}")
            raise
    
    async def _initialize_redis(self) -> None:
        """Initialize Redis connection."""
        try:
            # TODO: Implement actual Redis connection
            # import redis.asyncio as redis
            # self._redis_client = redis.from_url(self.redis_url)
            # await self._redis_client.ping()
            
            logger.info("Redis initialized (mock)")
        except Exception as e:
            logger.warning(f"Redis initialization failed: {e}")
            # Continue without Redis
    
    async def _create_sqlite_tables(self) -> None:
        """Create SQLite tables."""
        cursor = self._sqlite_conn.cursor()
        
        # Main records table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS records (
                record_id TEXT PRIMARY KEY,
                record_type TEXT NOT NULL,
                data TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                version INTEGER DEFAULT 1,
                metadata TEXT
            )
        """)
        
        # Index for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_record_type 
            ON records(record_type)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_created_at 
            ON records(created_at)
        """)
        
        self._sqlite_conn.commit()
    
    async def _store_with_strategy(self, record: StorageRecord) -> None:
        """Store record using configured sync strategy."""
        if self.sync_strategy == SyncStrategy.WRITE_THROUGH:
            # Write to all backends immediately
            await self._store_to_backend(record, StorageBackend.MEMORY)
            if self._redis_client:
                await self._store_to_backend(record, StorageBackend.REDIS)
            await self._store_to_backend(record, StorageBackend.SQLITE)
            
        elif self.sync_strategy == SyncStrategy.WRITE_BEHIND:
            # Write to memory immediately, queue for background sync
            await self._store_to_backend(record, StorageBackend.MEMORY)
            await self._sync_queue.put(("store", record))
            
        else:  # READ_THROUGH
            # Write to persistent storage immediately
            await self._store_to_backend(record, StorageBackend.SQLITE)
            await self._store_to_backend(record, StorageBackend.MEMORY)
    
    async def _store_to_backend(self, record: StorageRecord, backend: StorageBackend) -> None:
        """Store record to specific backend."""
        if backend == StorageBackend.MEMORY:
            self._memory_store[record.record_id] = record
            
        elif backend == StorageBackend.REDIS and self._redis_client:
            # TODO: Implement Redis storage
            # await self._redis_client.setex(
            #     record.record_id,
            #     self.cache_ttl,
            #     json.dumps(asdict(record), default=str)
            # )
            pass
            
        elif backend == StorageBackend.SQLITE:
            cursor = self._sqlite_conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO records 
                (record_id, record_type, data, created_at, updated_at, version, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                record.record_id,
                record.record_type,
                json.dumps(record.data),
                record.created_at.isoformat(),
                record.updated_at.isoformat(),
                record.version,
                json.dumps(record.metadata)
            ))
            self._sqlite_conn.commit()
    
    async def _retrieve_from_backend(self, record_id: str, backend: StorageBackend) -> Optional[StorageRecord]:
        """Retrieve record from specific backend."""
        if backend == StorageBackend.MEMORY:
            return self._memory_store.get(record_id)
            
        elif backend == StorageBackend.REDIS and self._redis_client:
            # TODO: Implement Redis retrieval
            # data = await self._redis_client.get(record_id)
            # if data:
            #     record_dict = json.loads(data)
            #     return StorageRecord(**record_dict)
            return None
            
        elif backend == StorageBackend.SQLITE:
            cursor = self._sqlite_conn.cursor()
            cursor.execute("""
                SELECT * FROM records WHERE record_id = ?
            """, (record_id,))
            
            row = cursor.fetchone()
            if row:
                return StorageRecord(
                    record_id=row["record_id"],
                    record_type=row["record_type"],
                    data=json.loads(row["data"]),
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                    version=row["version"],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {}
                )
        
        return None
    
    async def _delete_from_backend(self, record_id: str, backend: StorageBackend) -> bool:
        """Delete record from specific backend."""
        if backend == StorageBackend.MEMORY:
            return self._memory_store.pop(record_id, None) is not None
            
        elif backend == StorageBackend.REDIS and self._redis_client:
            # TODO: Implement Redis deletion
            # return await self._redis_client.delete(record_id) > 0
            return False
            
        elif backend == StorageBackend.SQLITE:
            cursor = self._sqlite_conn.cursor()
            cursor.execute("DELETE FROM records WHERE record_id = ?", (record_id,))
            self._sqlite_conn.commit()
            return cursor.rowcount > 0
        
        return False
    
    async def _query_backend(
        self,
        backend: StorageBackend,
        record_type: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> List[StorageRecord]:
        """Query records from specific backend."""
        results = []
        
        if backend == StorageBackend.MEMORY:
            for record in self._memory_store.values():
                if record.record_type == record_type:
                    if not filters or self._matches_filters(record, filters):
                        results.append(record)
            
        elif backend == StorageBackend.SQLITE:
            cursor = self._sqlite_conn.cursor()
            query = "SELECT * FROM records WHERE record_type = ?"
            params = [record_type]
            
            # Add filters (simplified implementation)
            if filters:
                for key, value in filters.items():
                    query += f" AND json_extract(data, '$.{key}') = ?"
                    params.append(value)
            
            query += " ORDER BY created_at DESC"
            
            if limit:
                query += " LIMIT ?"
                params.append(limit)
            
            cursor.execute(query, params)
            
            for row in cursor.fetchall():
                results.append(StorageRecord(
                    record_id=row["record_id"],
                    record_type=row["record_type"],
                    data=json.loads(row["data"]),
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                    version=row["version"],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {}
                ))
        
        return results
    
    def _matches_filters(self, record: StorageRecord, filters: Dict[str, Any]) -> bool:
        """Check if record matches filters."""
        for key, value in filters.items():
            if key not in record.data or record.data[key] != value:
                return False
        return True
    
    async def _cache_record(self, record: StorageRecord) -> None:
        """Cache record in faster backends."""
        # Cache in memory
        self._memory_store[record.record_id] = record
        
        # Cache in Redis if available
        if self._redis_client:
            await self._store_to_backend(record, StorageBackend.REDIS)
    
    async def _start_background_tasks(self) -> None:
        """Start background synchronization tasks."""
        # Sync processing task
        self._background_tasks.append(
            asyncio.create_task(self._sync_processing_loop())
        )
        
        # Cache cleanup task
        self._background_tasks.append(
            asyncio.create_task(self._cache_cleanup_loop())
        )
    
    async def _sync_processing_loop(self) -> None:
        """Background task for processing sync queue."""
        while not self._shutdown_event.is_set():
            try:
                # Process sync queue
                await self._process_sync_queue()
                await asyncio.sleep(1)  # Process every second
            except Exception as e:
                logger.error(f"Sync processing error: {e}")
                await asyncio.sleep(5)
    
    async def _process_sync_queue(self) -> None:
        """Process pending sync operations."""
        while not self._sync_queue.empty():
            try:
                operation, record = await asyncio.wait_for(
                    self._sync_queue.get(), timeout=0.1
                )
                
                if operation == "store":
                    # Sync to persistent backends
                    if self._redis_client:
                        await self._store_to_backend(record, StorageBackend.REDIS)
                    await self._store_to_backend(record, StorageBackend.SQLITE)
                    
                    self.sync_operations += 1
                    
            except asyncio.TimeoutError:
                break
            except Exception as e:
                logger.error(f"Sync operation error: {e}")
    
    async def _cache_cleanup_loop(self) -> None:
        """Background task for cache cleanup."""
        while not self._shutdown_event.is_set():
            try:
                # Clean up old memory records (keep last 1000)
                if len(self._memory_store) > 1000:
                    # Sort by updated_at and keep most recent
                    sorted_records = sorted(
                        self._memory_store.items(),
                        key=lambda x: x[1].updated_at,
                        reverse=True
                    )
                    
                    # Keep only the most recent 1000
                    self._memory_store = dict(sorted_records[:1000])
                
                await asyncio.sleep(3600)  # Cleanup every hour
            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")
                await asyncio.sleep(3600)

