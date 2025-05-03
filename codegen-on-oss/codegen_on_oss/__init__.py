"""
Codegen-on-OSS: A system for analyzing code repositories and providing insights.

This package provides tools for analyzing code repositories, tracking changes,
and generating insights about code quality and structure.
"""

__version__ = "0.1.0"

from codegen_on_oss.analysis.code_analyzer import CodeAnalyzer
from codegen_on_oss.snapshot.enhanced_snapshot_manager import EnhancedSnapshotManager
from codegen_on_oss.events.event_bus import EventType, Event, event_bus
from codegen_on_oss.database.connection import db_manager
from codegen_on_oss.pipeline.orchestrator import pipeline
from codegen_on_oss.api.websocket_manager import websocket_manager
from codegen_on_oss.app import app, run_app

__all__ = [
    "CodeAnalyzer",
    "EnhancedSnapshotManager",
    "EventType",
    "Event",
    "event_bus",
    "db_manager",
    "pipeline",
    "websocket_manager",
    "app",
    "run_app"
]
