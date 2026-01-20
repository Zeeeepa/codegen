"""
Storage module for artifacts and test results.

Provides S3 artifact storage and PostgreSQL result persistence.
"""

from autoqa.storage.artifact_manager import ArtifactManager, ArtifactType
from autoqa.storage.database import DatabaseManager, TestResultRepository

__all__ = [
    "ArtifactManager",
    "ArtifactType",
    "DatabaseManager",
    "TestResultRepository",
]
