"""
Storage service for the codegen-on-oss system.

This module provides a unified interface for storing and retrieving file content
across different storage backends (local, S3, memory).
"""

import os
import logging
import uuid
from abc import ABC, abstractmethod
from typing import Dict, Optional, Union, Any, BinaryIO

import boto3
from botocore.exceptions import ClientError

from codegen_on_oss.config import settings

logger = logging.getLogger(__name__)


class BaseStorageBackend(ABC):
    """Base class for storage backends."""
    
    @abstractmethod
    async def store_file(
        self, 
        snapshot_id: uuid.UUID, 
        file_path: str, 
        content: Union[str, bytes]
    ) -> str:
        """
        Store a file in the storage backend.
        
        Args:
            snapshot_id: ID of the snapshot
            file_path: Path of the file within the snapshot
            content: Content of the file (string or bytes)
            
        Returns:
            str: Storage path where the file was stored
        """
        pass
    
    @abstractmethod
    async def get_file_content(
        self, 
        snapshot_id: uuid.UUID, 
        file_path: str
    ) -> Optional[Union[str, bytes]]:
        """
        Get the content of a file from the storage backend.
        
        Args:
            snapshot_id: ID of the snapshot
            file_path: Path of the file within the snapshot
            
        Returns:
            Optional[Union[str, bytes]]: Content of the file if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def delete_file(self, snapshot_id: uuid.UUID, file_path: str) -> bool:
        """
        Delete a file from the storage backend.
        
        Args:
            snapshot_id: ID of the snapshot
            file_path: Path of the file within the snapshot
            
        Returns:
            bool: True if the file was deleted, False otherwise
        """
        pass
    
    @abstractmethod
    def get_storage_path(self, snapshot_id: uuid.UUID, file_path: str) -> str:
        """
        Get the storage path for a file.
        
        Args:
            snapshot_id: ID of the snapshot
            file_path: Path of the file within the snapshot
            
        Returns:
            str: Storage path for the file
        """
        pass


class LocalStorageBackend(BaseStorageBackend):
    """Local filesystem storage backend."""
    
    def __init__(self, base_path: str):
        """
        Initialize the local storage backend.
        
        Args:
            base_path: Base path for storing files
        """
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)
    
    async def store_file(
        self, 
        snapshot_id: uuid.UUID, 
        file_path: str, 
        content: Union[str, bytes]
    ) -> str:
        """Store a file in the local filesystem."""
        storage_path = self.get_storage_path(snapshot_id, file_path)
        full_path = os.path.join(self.base_path, storage_path)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # Write file content
        mode = "wb" if isinstance(content, bytes) else "w"
        with open(full_path, mode) as f:
            f.write(content)
        
        return storage_path
    
    async def get_file_content(
        self, 
        snapshot_id: uuid.UUID, 
        file_path: str
    ) -> Optional[Union[str, bytes]]:
        """Get the content of a file from the local filesystem."""
        storage_path = self.get_storage_path(snapshot_id, file_path)
        full_path = os.path.join(self.base_path, storage_path)
        
        if not os.path.exists(full_path):
            return None
        
        # Try to detect if the file is binary
        try:
            with open(full_path, "r") as f:
                content = f.read()
            return content
        except UnicodeDecodeError:
            # File is binary
            with open(full_path, "rb") as f:
                content = f.read()
            return content
    
    async def delete_file(self, snapshot_id: uuid.UUID, file_path: str) -> bool:
        """Delete a file from the local filesystem."""
        storage_path = self.get_storage_path(snapshot_id, file_path)
        full_path = os.path.join(self.base_path, storage_path)
        
        if not os.path.exists(full_path):
            return False
        
        os.remove(full_path)
        return True
    
    def get_storage_path(self, snapshot_id: uuid.UUID, file_path: str) -> str:
        """Get the storage path for a file in the local filesystem."""
        return os.path.join(str(snapshot_id), file_path)


class S3StorageBackend(BaseStorageBackend):
    """Amazon S3 storage backend."""
    
    def __init__(self, bucket: str, prefix: str = "", region: Optional[str] = None):
        """
        Initialize the S3 storage backend.
        
        Args:
            bucket: S3 bucket name
            prefix: Optional prefix for S3 keys
            region: Optional AWS region
        """
        self.bucket = bucket
        self.prefix = prefix.rstrip("/")
        self.s3 = boto3.client("s3", region_name=region)
    
    async def store_file(
        self, 
        snapshot_id: uuid.UUID, 
        file_path: str, 
        content: Union[str, bytes]
    ) -> str:
        """Store a file in S3."""
        storage_path = self.get_storage_path(snapshot_id, file_path)
        
        # Convert string to bytes if needed
        if isinstance(content, str):
            content = content.encode("utf-8")
        
        try:
            self.s3.put_object(
                Bucket=self.bucket,
                Key=storage_path,
                Body=content
            )
            return storage_path
        except ClientError as e:
            logger.error(f"Error storing file in S3: {str(e)}")
            raise
    
    async def get_file_content(
        self, 
        snapshot_id: uuid.UUID, 
        file_path: str
    ) -> Optional[bytes]:
        """Get the content of a file from S3."""
        storage_path = self.get_storage_path(snapshot_id, file_path)
        
        try:
            response = self.s3.get_object(
                Bucket=self.bucket,
                Key=storage_path
            )
            return response["Body"].read()
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                return None
            logger.error(f"Error retrieving file from S3: {str(e)}")
            raise
    
    async def delete_file(self, snapshot_id: uuid.UUID, file_path: str) -> bool:
        """Delete a file from S3."""
        storage_path = self.get_storage_path(snapshot_id, file_path)
        
        try:
            self.s3.delete_object(
                Bucket=self.bucket,
                Key=storage_path
            )
            return True
        except ClientError as e:
            logger.error(f"Error deleting file from S3: {str(e)}")
            return False
    
    def get_storage_path(self, snapshot_id: uuid.UUID, file_path: str) -> str:
        """Get the storage path for a file in S3."""
        if self.prefix:
            return f"{self.prefix}/{snapshot_id}/{file_path}"
        return f"{snapshot_id}/{file_path}"


class MemoryStorageBackend(BaseStorageBackend):
    """In-memory storage backend for testing."""
    
    def __init__(self):
        """Initialize the memory storage backend."""
        self.storage: Dict[str, bytes] = {}
    
    async def store_file(
        self, 
        snapshot_id: uuid.UUID, 
        file_path: str, 
        content: Union[str, bytes]
    ) -> str:
        """Store a file in memory."""
        storage_path = self.get_storage_path(snapshot_id, file_path)
        
        # Convert string to bytes if needed
        if isinstance(content, str):
            content = content.encode("utf-8")
        
        self.storage[storage_path] = content
        return storage_path
    
    async def get_file_content(
        self, 
        snapshot_id: uuid.UUID, 
        file_path: str
    ) -> Optional[bytes]:
        """Get the content of a file from memory."""
        storage_path = self.get_storage_path(snapshot_id, file_path)
        return self.storage.get(storage_path)
    
    async def delete_file(self, snapshot_id: uuid.UUID, file_path: str) -> bool:
        """Delete a file from memory."""
        storage_path = self.get_storage_path(snapshot_id, file_path)
        
        if storage_path in self.storage:
            del self.storage[storage_path]
            return True
        return False
    
    def get_storage_path(self, snapshot_id: uuid.UUID, file_path: str) -> str:
        """Get the storage path for a file in memory."""
        return f"{snapshot_id}/{file_path}"


class StorageService:
    """
    Unified storage service that selects the appropriate backend based on configuration.
    """
    
    def __init__(self):
        """Initialize the storage service with the configured backend."""
        storage_type = settings.storage_type.lower()
        
        if storage_type == "s3":
            if not settings.s3_bucket:
                raise ValueError("S3 bucket name is required for S3 storage")
            
            self.backend = S3StorageBackend(
                bucket=settings.s3_bucket,
                prefix=settings.s3_prefix or "",
                region=settings.s3_region
            )
            logger.info(f"Using S3 storage backend with bucket: {settings.s3_bucket}")
        
        elif storage_type == "memory":
            self.backend = MemoryStorageBackend()
            logger.info("Using in-memory storage backend")
        
        else:  # Default to local
            if not settings.local_storage_path:
                raise ValueError("Local storage path is required for local storage")
            
            self.backend = LocalStorageBackend(base_path=settings.local_storage_path)
            logger.info(f"Using local storage backend with path: {settings.local_storage_path}")
    
    async def store_file(
        self, 
        snapshot_id: uuid.UUID, 
        file_path: str, 
        content: Union[str, bytes]
    ) -> str:
        """
        Store a file using the configured backend.
        
        Args:
            snapshot_id: ID of the snapshot
            file_path: Path of the file within the snapshot
            content: Content of the file (string or bytes)
            
        Returns:
            str: Storage path where the file was stored
        """
        return await self.backend.store_file(snapshot_id, file_path, content)
    
    async def get_file_content(
        self, 
        snapshot_id: uuid.UUID, 
        file_path: str
    ) -> Optional[Union[str, bytes]]:
        """
        Get the content of a file using the configured backend.
        
        Args:
            snapshot_id: ID of the snapshot
            file_path: Path of the file within the snapshot
            
        Returns:
            Optional[Union[str, bytes]]: Content of the file if found, None otherwise
        """
        return await self.backend.get_file_content(snapshot_id, file_path)
    
    async def delete_file(self, snapshot_id: uuid.UUID, file_path: str) -> bool:
        """
        Delete a file using the configured backend.
        
        Args:
            snapshot_id: ID of the snapshot
            file_path: Path of the file within the snapshot
            
        Returns:
            bool: True if the file was deleted, False otherwise
        """
        return await self.backend.delete_file(snapshot_id, file_path)
    
    def get_storage_path(self, snapshot_id: uuid.UUID, file_path: str) -> str:
        """
        Get the storage path for a file using the configured backend.
        
        Args:
            snapshot_id: ID of the snapshot
            file_path: Path of the file within the snapshot
            
        Returns:
            str: Storage path for the file
        """
        return self.backend.get_storage_path(snapshot_id, file_path)

