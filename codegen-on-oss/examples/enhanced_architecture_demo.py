"""
Demo script for the enhanced Codegen-on-OSS architecture.

This script demonstrates the key components of the enhanced architecture,
including the event system, database schema, snapshotting system, and API layer.
"""

import os
import sys
import logging
import asyncio
import json
from datetime import datetime
from pathlib import Path

# Add parent directory to path to import codegen_on_oss
sys.path.append(str(Path(__file__).parent.parent))

from codegen import Codebase
from codegen_on_oss.database import (
    init_db,
    get_db,
    CodebaseEntity,
    SnapshotEntity,
    AnalysisResultEntity,
    SymbolEntity,
    MetricsEntity,
    IssueEntity,
    RelationshipEntity,
)
from codegen_on_oss.events import EventBus, Event, EventType, EventHandler
from codegen_on_oss.snapshot.snapshot_manager import SnapshotManager
from codegen_on_oss.analysis.code_analyzer import CodeAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class DemoEventHandler(EventHandler):
    """Demo event handler that logs all events."""
    
    def handle_event(self, event: Event) -> None:
        """Handle an event by logging it."""
        logger.info(f"Received event: {event.type} from {event.source}")
        logger.info(f"Event data: {json.dumps(event.data, indent=2)}")


async def run_demo() -> None:
    """Run the demo."""
    logger.info("Initializing database...")
    init_db()
    
    logger.info("Creating event bus...")
    event_bus = EventBus()
    
    logger.info("Creating event handler...")
    event_handler = DemoEventHandler(event_bus)
    event_handler.subscribe()  # Subscribe to all events
    
    logger.info("Creating snapshot manager...")
    snapshot_manager = SnapshotManager(
        storage_path="./demo_snapshots",
        event_bus=event_bus,
    )
    
    # Get database session
    db = next(get_db())
    
    # Create a codebase
    logger.info("Creating codebase...")
    codebase_entity = CodebaseEntity(
        name="demo-codebase",
        repository_url="https://github.com/example/demo-codebase",
        default_branch="main",
        metadata={"description": "Demo codebase for enhanced architecture"},
    )
    db.add(codebase_entity)
    db.commit()
    db.refresh(codebase_entity)
    
    # Publish event
    event_bus.publish(
        Event(
            type=EventType.CODEBASE_ADDED,
            source="demo",
            data={
                "codebase_id": codebase_entity.id,
                "name": codebase_entity.name,
                "repository_url": codebase_entity.repository_url,
            },
        )
    )
    
    # Create a snapshot
    logger.info("Creating snapshot...")
    snapshot_entity = SnapshotEntity(
        codebase_id=codebase_entity.id,
        commit_hash="abcdef123456",
        branch="main",
        tag="v1.0.0",
        metadata={"description": "Initial snapshot"},
        storage_path="./demo_snapshots/demo-codebase_initial",
    )
    db.add(snapshot_entity)
    db.commit()
    db.refresh(snapshot_entity)
    
    # Publish event
    event_bus.publish(
        Event(
            type=EventType.SNAPSHOT_CREATED,
            source="demo",
            data={
                "snapshot_id": snapshot_entity.id,
                "codebase_id": codebase_entity.id,
                "commit_hash": snapshot_entity.commit_hash,
                "tag": snapshot_entity.tag,
            },
        )
    )
    
    # Create an analysis result
    logger.info("Creating analysis result...")
    analysis_result_entity = AnalysisResultEntity(
        codebase_id=codebase_entity.id,
        snapshot_id=snapshot_entity.id,
        analysis_type="code_quality",
        summary="Demo analysis result",
        details={
            "quality_score": 85,
            "issues_count": 5,
            "warnings_count": 10,
        },
        metrics={
            "lines_of_code": 1000,
            "functions_count": 50,
            "classes_count": 10,
            "complexity": 75,
        },
    )
    db.add(analysis_result_entity)
    db.commit()
    db.refresh(analysis_result_entity)
    
    # Publish event
    event_bus.publish(
        Event(
            type=EventType.ANALYSIS_COMPLETED,
            source="demo",
            data={
                "analysis_result_id": analysis_result_entity.id,
                "codebase_id": codebase_entity.id,
                "snapshot_id": snapshot_entity.id,
                "analysis_type": analysis_result_entity.analysis_type,
            },
        )
    )
    
    # Create some symbols
    logger.info("Creating symbols...")
    symbols = []
    for i in range(5):
        symbol_entity = SymbolEntity(
            codebase_id=codebase_entity.id,
            name=f"demo_function_{i}",
            symbol_type="function",
            file_path=f"src/demo_{i}.py",
            line_number=10 * i,
            signature=f"def demo_function_{i}(arg1, arg2):",
            docstring=f"Demo function {i}",
            metadata={"complexity": 5 + i},
        )
        db.add(symbol_entity)
        db.commit()
        db.refresh(symbol_entity)
        symbols.append(symbol_entity)
        
        # Publish event
        event_bus.publish(
            Event(
                type=EventType.SYMBOL_ADDED,
                source="demo",
                data={
                    "symbol_id": symbol_entity.id,
                    "codebase_id": codebase_entity.id,
                    "name": symbol_entity.name,
                    "symbol_type": symbol_entity.symbol_type,
                },
            )
        )
    
    # Create some metrics
    logger.info("Creating metrics...")
    for i, symbol in enumerate(symbols):
        metrics_entity = MetricsEntity(
            symbol_id=symbol.id,
            cyclomatic_complexity=5 + i,
            halstead_volume=100 + 10 * i,
            maintainability_index=80 - i,
            lines_of_code=20 + 5 * i,
            comment_ratio=0.2 + 0.05 * i,
            custom_metrics={
                "cognitive_complexity": 3 + i,
                "parameter_count": 2,
            },
        )
        db.add(metrics_entity)
        db.commit()
        db.refresh(metrics_entity)
    
    # Create some relationships
    logger.info("Creating relationships...")
    for i in range(len(symbols) - 1):
        relationship_entity = RelationshipEntity(
            source_id=symbols[i].id,
            target_id=symbols[i + 1].id,
            relationship_type="calls",
            metadata={"call_count": i + 1},
        )
        db.add(relationship_entity)
        db.commit()
        db.refresh(relationship_entity)
    
    # Create some issues
    logger.info("Creating issues...")
    for i in range(3):
        issue_entity = IssueEntity(
            analysis_result_id=analysis_result_entity.id,
            title=f"Demo issue {i}",
            description=f"This is a demo issue {i}",
            file_path=f"src/demo_{i}.py",
            line_number=10 * i,
            severity=["high", "medium", "low"][i],
            issue_type=["security", "performance", "style"][i],
            recommendation=f"Fix demo issue {i}",
        )
        db.add(issue_entity)
        db.commit()
        db.refresh(issue_entity)
        
        # Publish event
        event_bus.publish(
            Event(
                type=EventType.ISSUE_DETECTED,
                source="demo",
                data={
                    "issue_id": issue_entity.id,
                    "analysis_result_id": issue_entity.analysis_result_id,
                    "title": issue_entity.title,
                    "severity": issue_entity.severity,
                },
            )
        )
    
    # Resolve an issue
    logger.info("Resolving an issue...")
    issue_entity = db.query(IssueEntity).first()
    issue_entity.resolved = True
    issue_entity.resolved_at = datetime.utcnow()
    db.commit()
    db.refresh(issue_entity)
    
    # Publish event
    event_bus.publish(
        Event(
            type=EventType.ISSUE_RESOLVED,
            source="demo",
            data={
                "issue_id": issue_entity.id,
                "analysis_result_id": issue_entity.analysis_result_id,
            },
        )
    )
    
    logger.info("Demo completed successfully!")


if __name__ == "__main__":
    asyncio.run(run_demo())

