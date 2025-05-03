"""
Event Handlers for Codegen OSS

This module provides handlers for events in the codegen-oss system,
implementing the event-driven architecture.
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Dict, Optional

from codegen import Codebase

from ..database.service import DatabaseService
from ..snapshot.codebase_snapshot import CodebaseSnapshot
from ..analysis.codebase_analysis import get_codebase_summary
from .event_bus import Event, EventType, event_bus

logger = logging.getLogger(__name__)


class AnalysisHandler:
    """Handler for analysis-related events."""
    
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        
        # Register event handlers
        event_bus.subscribe(EventType.SNAPSHOT_CREATED, self.handle_snapshot_created)
        event_bus.subscribe(EventType.ANALYSIS_REQUESTED, self.handle_analysis_requested)
    
    def handle_snapshot_created(self, event: Event) -> None:
        """Handle a snapshot created event by triggering analysis."""
        snapshot_id = event.data.get("snapshot_id")
        repository_id = event.data.get("repository_id")
        
        if not snapshot_id or not repository_id:
            logger.error("Snapshot created event missing required data")
            return
        
        # Request dependency analysis
        dependency_analysis_event = Event(
            event_type=EventType.ANALYSIS_REQUESTED,
            data={
                "repository_id": repository_id,
                "snapshot_id": snapshot_id,
                "analysis_type": "dependency",
            }
        )
        event_bus.publish(dependency_analysis_event)
        
        # Request complexity analysis
        complexity_analysis_event = Event(
            event_type=EventType.ANALYSIS_REQUESTED,
            data={
                "repository_id": repository_id,
                "snapshot_id": snapshot_id,
                "analysis_type": "complexity",
            }
        )
        event_bus.publish(complexity_analysis_event)
    
    def handle_analysis_requested(self, event: Event) -> None:
        """Handle an analysis requested event."""
        repository_id = event.data.get("repository_id")
        snapshot_id = event.data.get("snapshot_id")
        analysis_type = event.data.get("analysis_type")
        
        if not repository_id or not analysis_type:
            logger.error("Analysis requested event missing required data")
            return
        
        # Create analysis record
        analysis = self.db_service.create_analysis(
            repository_id=repository_id,
            snapshot_id=snapshot_id,
            analysis_type=analysis_type,
        )
        
        # Publish analysis started event
        started_event = Event(
            event_type=EventType.ANALYSIS_STARTED,
            data={
                "repository_id": repository_id,
                "snapshot_id": snapshot_id,
                "analysis_id": str(analysis.id),
                "analysis_type": analysis_type,
            }
        )
        event_bus.publish(started_event)
        
        # Perform the analysis
        try:
            start_time = datetime.utcnow()
            
            # Record start metrics
            self.db_service.record_analysis_metrics(
                analysis_id=analysis.id,
                start_time=start_time,
            )
            
            # Get the snapshot
            snapshot = self.db_service.get_by_id(snapshot_id)
            if not snapshot:
                raise ValueError(f"Snapshot with ID {snapshot_id} not found")
            
            # Perform different types of analysis
            if analysis_type == "dependency":
                result = self._perform_dependency_analysis(snapshot)
            elif analysis_type == "complexity":
                result = self._perform_complexity_analysis(snapshot)
            else:
                raise ValueError(f"Unknown analysis type: {analysis_type}")
            
            # Update analysis record
            end_time = datetime.utcnow()
            self.db_service.update_analysis_status(
                analysis_id=analysis.id,
                status="completed",
                data=result["data"],
                summary=result["summary"],
            )
            
            # Update metrics
            self.db_service.record_analysis_metrics(
                analysis_id=analysis.id,
                start_time=start_time,
                end_time=end_time,
                cpu_usage_percent=result.get("cpu_usage_percent"),
                memory_usage_mb=result.get("memory_usage_mb"),
            )
            
            # Publish analysis completed event
            completed_event = Event(
                event_type=EventType.ANALYSIS_COMPLETED,
                data={
                    "repository_id": repository_id,
                    "snapshot_id": snapshot_id,
                    "analysis_id": str(analysis.id),
                    "analysis_type": analysis_type,
                    "duration_seconds": (end_time - start_time).total_seconds(),
                }
            )
            event_bus.publish(completed_event)
            
        except Exception as e:
            logger.error(f"Error performing analysis: {e}")
            
            # Update analysis record
            end_time = datetime.utcnow()
            self.db_service.update_analysis_status(
                analysis_id=analysis.id,
                status="failed",
                error_message=str(e),
            )
            
            # Update metrics
            self.db_service.record_analysis_metrics(
                analysis_id=analysis.id,
                start_time=start_time,
                end_time=end_time,
                error=str(e),
            )
            
            # Publish analysis failed event
            failed_event = Event(
                event_type=EventType.ANALYSIS_FAILED,
                data={
                    "repository_id": repository_id,
                    "snapshot_id": snapshot_id,
                    "analysis_id": str(analysis.id),
                    "analysis_type": analysis_type,
                    "error": str(e),
                }
            )
            event_bus.publish(failed_event)
    
    def _perform_dependency_analysis(self, snapshot) -> Dict[str, Any]:
        """Perform dependency analysis on a snapshot."""
        # This would be implemented with actual analysis logic
        # For now, we'll return a placeholder result
        return {
            "data": {
                "dependency_count": 100,
                "circular_dependencies": 5,
                "external_dependencies": 20,
                "internal_dependencies": 80,
            },
            "summary": "Dependency analysis completed successfully.",
            "cpu_usage_percent": 50.0,
            "memory_usage_mb": 200.0,
        }
    
    def _perform_complexity_analysis(self, snapshot) -> Dict[str, Any]:
        """Perform complexity analysis on a snapshot."""
        # This would be implemented with actual analysis logic
        # For now, we'll return a placeholder result
        return {
            "data": {
                "average_cyclomatic_complexity": 5.2,
                "max_cyclomatic_complexity": 25,
                "functions_above_threshold": 10,
                "average_function_length": 15.5,
            },
            "summary": "Complexity analysis completed successfully.",
            "cpu_usage_percent": 60.0,
            "memory_usage_mb": 250.0,
        }


class SnapshotHandler:
    """Handler for snapshot-related events."""
    
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        
        # Register event handlers
        event_bus.subscribe(EventType.REPOSITORY_ADDED, self.handle_repository_added)
        event_bus.subscribe(EventType.REPOSITORY_UPDATED, self.handle_repository_updated)
    
    def handle_repository_added(self, event: Event) -> None:
        """Handle a repository added event by creating an initial snapshot."""
        repository_id = event.data.get("repository_id")
        repository_url = event.data.get("repository_url")
        
        if not repository_id or not repository_url:
            logger.error("Repository added event missing required data")
            return
        
        try:
            # Create a codebase from the repository
            codebase = Codebase.from_repo(repository_url)
            
            # Create a snapshot
            snapshot = CodebaseSnapshot(codebase)
            
            # Store the snapshot in the database
            db_snapshot = self.db_service.store_snapshot(snapshot, repository_id)
            
            # Publish snapshot created event
            created_event = Event(
                event_type=EventType.SNAPSHOT_CREATED,
                data={
                    "repository_id": repository_id,
                    "snapshot_id": str(db_snapshot.id),
                    "commit_sha": snapshot.commit_sha,
                }
            )
            event_bus.publish(created_event)
            
        except Exception as e:
            logger.error(f"Error creating snapshot for repository {repository_url}: {e}")
            
            # Publish system error event
            error_event = Event(
                event_type=EventType.SYSTEM_ERROR,
                data={
                    "repository_id": repository_id,
                    "error": str(e),
                    "context": "Creating initial snapshot",
                }
            )
            event_bus.publish(error_event)
    
    def handle_repository_updated(self, event: Event) -> None:
        """Handle a repository updated event by creating a new snapshot."""
        repository_id = event.data.get("repository_id")
        repository_url = event.data.get("repository_url")
        commit_sha = event.data.get("commit_sha")
        
        if not repository_id or not repository_url:
            logger.error("Repository updated event missing required data")
            return
        
        try:
            # Check if we already have a snapshot for this commit
            if commit_sha:
                existing_snapshot = self.db_service.get_snapshot_by_commit(repository_id, commit_sha)
                if existing_snapshot:
                    logger.info(f"Snapshot for commit {commit_sha} already exists")
                    return
            
            # Create a codebase from the repository
            codebase = Codebase.from_repo(repository_url)
            if commit_sha:
                codebase.checkout(commit=commit_sha)
            
            # Create a snapshot
            snapshot = CodebaseSnapshot(codebase, commit_sha=commit_sha)
            
            # Store the snapshot in the database
            db_snapshot = self.db_service.store_snapshot(snapshot, repository_id)
            
            # Publish snapshot created event
            created_event = Event(
                event_type=EventType.SNAPSHOT_CREATED,
                data={
                    "repository_id": repository_id,
                    "snapshot_id": str(db_snapshot.id),
                    "commit_sha": snapshot.commit_sha,
                }
            )
            event_bus.publish(created_event)
            
        except Exception as e:
            logger.error(f"Error creating snapshot for repository {repository_url}: {e}")
            
            # Publish system error event
            error_event = Event(
                event_type=EventType.SYSTEM_ERROR,
                data={
                    "repository_id": repository_id,
                    "error": str(e),
                    "context": "Creating updated snapshot",
                }
            )
            event_bus.publish(error_event)

