"""
Database management for test results persistence.

Provides PostgreSQL storage with async support.
"""

from __future__ import annotations

import os
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

import structlog
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    select,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, relationship

logger = structlog.get_logger(__name__)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""

    pass


class TestRunModel(Base):
    """Test run database model."""

    __tablename__ = "test_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    test_name = Column(String(256), nullable=False, index=True)
    suite_name = Column(String(256), nullable=True, index=True)
    status = Column(String(32), nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), nullable=False, index=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    duration_ms = Column(Integer, nullable=False, default=0)
    total_steps = Column(Integer, nullable=False, default=0)
    passed_steps = Column(Integer, nullable=False, default=0)
    failed_steps = Column(Integer, nullable=False, default=0)
    skipped_steps = Column(Integer, nullable=False, default=0)
    healed_steps = Column(Integer, nullable=False, default=0)
    video_path = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    variables = Column(JSON, nullable=True)
    artifacts = Column(JSON, nullable=True)
    run_metadata = Column("metadata", JSON, nullable=True)
    environment = Column(String(64), nullable=True, index=True)
    branch = Column(String(128), nullable=True, index=True)
    commit_sha = Column(String(64), nullable=True, index=True)
    ci_job_id = Column(String(128), nullable=True, index=True)

    step_results = relationship(
        "StepResultModel",
        back_populates="test_run",
        cascade="all, delete-orphan",
    )


class StepResultModel(Base):
    """Step result database model."""

    __tablename__ = "step_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    test_run_id = Column(
        UUID(as_uuid=True),
        ForeignKey("test_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    step_index = Column(Integer, nullable=False)
    step_name = Column(String(256), nullable=True)
    action = Column(String(64), nullable=False)
    status = Column(String(32), nullable=False, index=True)
    duration_ms = Column(Integer, nullable=False, default=0)
    error = Column(Text, nullable=True)
    error_traceback = Column(Text, nullable=True)
    screenshot_path = Column(Text, nullable=True)
    retries = Column(Integer, nullable=False, default=0)
    healed = Column(Boolean, nullable=False, default=False)
    healed_selector = Column(Text, nullable=True)
    healing_strategy = Column(String(64), nullable=True)
    healing_confidence = Column(Float, nullable=True)

    test_run = relationship("TestRunModel", back_populates="step_results")


class VisualBaselineModel(Base):
    """Visual baseline database model."""

    __tablename__ = "visual_baselines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(256), nullable=False, unique=True, index=True)
    test_name = Column(String(256), nullable=True, index=True)
    storage_path = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    baseline_metadata = Column("metadata", JSON, nullable=True)


# ========================================================================
# Web2API Models - Service Management
# ========================================================================

class ServiceModel(Base):
    """Web2API Service database model.

    Represents a web service (e.g., k2think.ai) that can be accessed
    via OpenAI-compatible API endpoints.
    """

    __tablename__ = "web2api_services"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(256), nullable=False, index=True)
    base_url = Column(Text, nullable=False)
    description = Column(Text, nullable=True)

    # Credentials reference (encrypted, stored separately)
    credentials_ref = Column(String(256), nullable=True)

    # Service status and capabilities
    status = Column(String(32), nullable=False, default="registered", index=True)  # registered, discovering, active, error
    capabilities = Column(JSON, nullable=True)  # Discovered operations/features

    # Discovery metadata
    last_discovery_at = Column(DateTime(timezone=True), nullable=True)
    discovery_version = Column(Integer, nullable=False, default=1)

    # Service health metrics
    last_health_check = Column(DateTime(timezone=True), nullable=True)
    health_status = Column(String(32), nullable=True)  # healthy, degraded, down
    uptime_percentage = Column(Float, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # Relationships
    sessions = relationship("ServiceSessionModel", back_populates="service", cascade="all, delete-orphan")
    operations = relationship("OperationModel", back_populates="service", cascade="all, delete-orphan")


class ServiceSessionModel(Base):
    """Service session database model.

    Manages authenticated browser sessions for web services.
    """

    __tablename__ = "web2api_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_id = Column(
        UUID(as_uuid=True),
        ForeignKey("web2api_services.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Owl-Browser session tracking
    owl_session_id = Column(String(256), nullable=True)  # Remote browser session ID

    # Tab management
    tabs = Column(JSON, nullable=True)  # List of active tab IDs

    # Cookie storage (encrypted reference)
    cookies_ref = Column(String(256), nullable=True)

    # Media references
    stream_id = Column(String(256), nullable=True)  # Live viewport stream
    recording_ref = Column(String(256), nullable=True)  # Video recording

    # Session state
    state = Column(String(32), nullable=False, default="active", index=True)  # active, expired, revoked
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Session usage
    last_used_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    request_count = Column(Integer, nullable=False, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # Relationships
    service = relationship("ServiceModel", back_populates="sessions")
    operations = relationship("OperationModel", back_populates="session", cascade="all, delete-orphan")


class OperationModel(Base):
    """Operation execution database model.

    Tracks execution of operations against web services.
    """

    __tablename__ = "web2api_operations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_id = Column(
        UUID(as_uuid=True),
        ForeignKey("web2api_services.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("web2api_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Operation type and inputs
    type = Column(String(64), nullable=False, index=True)  # chat, completion, embedding, image_generation
    operation_name = Column(String(256), nullable=False)
    inputs = Column(JSON, nullable=False)  # Request parameters

    # Execution status
    status = Column(String(32), nullable=False, default="queued", index=True)  # queued, executing, completed, failed

    # Outputs
    outputs = Column(JSON, nullable=True)  # Response data
    error = Column(Text, nullable=True)
    error_traceback = Column(Text, nullable=True)

    # Timing
    queued_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_ms = Column(Integer, nullable=True)

    # Metadata
    metadata = Column(JSON, nullable=True)  # Additional operation metadata

    # Relationships
    service = relationship("ServiceModel", back_populates="operations")
    session = relationship("ServiceSessionModel", back_populates="operations")


class StreamModel(Base):
    """Live stream database model.

    Tracks live viewport streams for monitoring.
    """

    __tablename__ = "web2api_streams"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("web2api_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Stream type and endpoints
    type = Column(String(32), nullable=False)  # viewport, audio, video
    endpoints = Column(JSON, nullable=False)  # WebSocket URLs, stream URLs

    # Stream status
    status = Column(String(32), nullable=False, default="active", index=True)  # active, stopped, error

    # Timestamps
    started_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    stopped_at = Column(DateTime(timezone=True), nullable=True)


class ArtifactModel(Base):
    """Artifact database model.

    Stores artifacts from service operations (screenshots, videos, logs).
    """

    __tablename__ = "web2api_artifacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("web2api_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    operation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("web2api_operations.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Artifact type and storage
    type = Column(String(64), nullable=False, index=True)  # screenshot, video, log, trace
    path = Column(Text, nullable=False)  # Storage path/URL
    metadata = Column(JSON, nullable=True)  # Additional metadata

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class DatabaseManager:
    """Manages database connections and sessions."""

    def __init__(
        self,
        database_url: str | None = None,
        pool_size: int = 5,
        max_overflow: int = 10,
    ) -> None:
        url = database_url or os.environ.get(
            "DATABASE_URL",
            "postgresql+asyncpg://autoqa:autoqa@localhost:5432/autoqa",
        )

        self._engine = create_async_engine(
            url,
            pool_size=pool_size,
            max_overflow=max_overflow,
            echo=os.environ.get("SQL_ECHO", "false").lower() == "true",
        )

        self._session_factory = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        self._log = logger.bind(component="database_manager")

    async def create_tables(self) -> None:
        """Create all database tables."""
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self._log.info("Database tables created")

    async def drop_tables(self) -> None:
        """Drop all database tables."""
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        self._log.info("Database tables dropped")

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session."""
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def close(self) -> None:
        """Close database connection."""
        await self._engine.dispose()


class TestResultRepository:
    """Repository for test result operations."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self._db = db_manager
        self._log = logger.bind(component="test_result_repository")

    async def save_test_run(
        self,
        test_name: str,
        status: str,
        started_at: datetime,
        finished_at: datetime | None = None,
        duration_ms: int = 0,
        total_steps: int = 0,
        passed_steps: int = 0,
        failed_steps: int = 0,
        skipped_steps: int = 0,
        healed_steps: int = 0,
        video_path: str | None = None,
        error: str | None = None,
        variables: dict[str, Any] | None = None,
        artifacts: dict[str, str] | None = None,
        metadata: dict[str, Any] | None = None,
        suite_name: str | None = None,
        environment: str | None = None,
        branch: str | None = None,
        commit_sha: str | None = None,
        ci_job_id: str | None = None,
    ) -> str:
        """Save a test run to the database."""
        run_id = uuid.uuid4()

        async with self._db.session() as session:
            run = TestRunModel(
                id=run_id,
                test_name=test_name,
                suite_name=suite_name,
                status=status,
                started_at=started_at,
                finished_at=finished_at,
                duration_ms=duration_ms,
                total_steps=total_steps,
                passed_steps=passed_steps,
                failed_steps=failed_steps,
                skipped_steps=skipped_steps,
                healed_steps=healed_steps,
                video_path=video_path,
                error=error,
                variables=variables,
                artifacts=artifacts,
                run_metadata=metadata,
                environment=environment,
                branch=branch,
                commit_sha=commit_sha,
                ci_job_id=ci_job_id,
            )
            session.add(run)

        self._log.info("Test run saved", run_id=str(run_id), test_name=test_name)
        return str(run_id)

    async def save_step_result(
        self,
        test_run_id: str,
        step_index: int,
        action: str,
        status: str,
        step_name: str | None = None,
        duration_ms: int = 0,
        error: str | None = None,
        error_traceback: str | None = None,
        screenshot_path: str | None = None,
        retries: int = 0,
        healed: bool = False,
        healed_selector: str | None = None,
        healing_strategy: str | None = None,
        healing_confidence: float | None = None,
    ) -> str:
        """Save a step result to the database."""
        step_id = uuid.uuid4()

        async with self._db.session() as session:
            step = StepResultModel(
                id=step_id,
                test_run_id=uuid.UUID(test_run_id),
                step_index=step_index,
                step_name=step_name,
                action=action,
                status=status,
                duration_ms=duration_ms,
                error=error,
                error_traceback=error_traceback,
                screenshot_path=screenshot_path,
                retries=retries,
                healed=healed,
                healed_selector=healed_selector,
                healing_strategy=healing_strategy,
                healing_confidence=healing_confidence,
            )
            session.add(step)

        return str(step_id)

    async def get_test_run(self, run_id: str) -> dict[str, Any] | None:
        """Get a test run by ID."""
        async with self._db.session() as session:
            result = await session.execute(
                select(TestRunModel).where(TestRunModel.id == uuid.UUID(run_id))
            )
            run = result.scalar_one_or_none()

            if run is None:
                return None

            return {
                "id": str(run.id),
                "test_name": run.test_name,
                "suite_name": run.suite_name,
                "status": run.status,
                "started_at": run.started_at,
                "finished_at": run.finished_at,
                "duration_ms": run.duration_ms,
                "total_steps": run.total_steps,
                "passed_steps": run.passed_steps,
                "failed_steps": run.failed_steps,
                "skipped_steps": run.skipped_steps,
                "healed_steps": run.healed_steps,
                "video_path": run.video_path,
                "error": run.error,
                "variables": run.variables,
                "artifacts": run.artifacts,
                "metadata": run.run_metadata,
                "environment": run.environment,
                "branch": run.branch,
                "commit_sha": run.commit_sha,
                "ci_job_id": run.ci_job_id,
            }

    async def list_test_runs(
        self,
        suite_name: str | None = None,
        status: str | None = None,
        environment: str | None = None,
        branch: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List test runs with filtering."""
        async with self._db.session() as session:
            query = select(TestRunModel).order_by(TestRunModel.started_at.desc())

            if suite_name:
                query = query.where(TestRunModel.suite_name == suite_name)
            if status:
                query = query.where(TestRunModel.status == status)
            if environment:
                query = query.where(TestRunModel.environment == environment)
            if branch:
                query = query.where(TestRunModel.branch == branch)

            query = query.limit(limit).offset(offset)

            result = await session.execute(query)
            runs = result.scalars().all()

            return [
                {
                    "id": str(run.id),
                    "test_name": run.test_name,
                    "suite_name": run.suite_name,
                    "status": run.status,
                    "started_at": run.started_at,
                    "duration_ms": run.duration_ms,
                    "total_steps": run.total_steps,
                    "passed_steps": run.passed_steps,
                    "failed_steps": run.failed_steps,
                    "healed_steps": run.healed_steps,
                }
                for run in runs
            ]

    async def get_step_results(self, test_run_id: str) -> list[dict[str, Any]]:
        """Get step results for a test run."""
        async with self._db.session() as session:
            result = await session.execute(
                select(StepResultModel)
                .where(StepResultModel.test_run_id == uuid.UUID(test_run_id))
                .order_by(StepResultModel.step_index)
            )
            steps = result.scalars().all()

            return [
                {
                    "id": str(step.id),
                    "step_index": step.step_index,
                    "step_name": step.step_name,
                    "action": step.action,
                    "status": step.status,
                    "duration_ms": step.duration_ms,
                    "error": step.error,
                    "screenshot_path": step.screenshot_path,
                    "retries": step.retries,
                    "healed": step.healed,
                    "healed_selector": step.healed_selector,
                    "healing_strategy": step.healing_strategy,
                    "healing_confidence": step.healing_confidence,
                }
                for step in steps
            ]

    async def delete_test_run(self, run_id: str) -> bool:
        """Delete a test run and its step results."""
        async with self._db.session() as session:
            result = await session.execute(
                select(TestRunModel).where(TestRunModel.id == uuid.UUID(run_id))
            )
            run = result.scalar_one_or_none()

            if run is None:
                return False

            await session.delete(run)
            self._log.info("Test run deleted", run_id=run_id)
            return True

    async def get_test_statistics(
        self,
        suite_name: str | None = None,
        days: int = 30,
    ) -> dict[str, Any]:
        """Get test execution statistics."""
        from sqlalchemy import func

        cutoff = datetime.now(UTC).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        cutoff = cutoff.replace(day=cutoff.day - days)

        async with self._db.session() as session:
            query = select(
                func.count(TestRunModel.id).label("total"),
                func.sum(
                    func.case((TestRunModel.status == "passed", 1), else_=0)
                ).label("passed"),
                func.sum(
                    func.case((TestRunModel.status == "failed", 1), else_=0)
                ).label("failed"),
                func.avg(TestRunModel.duration_ms).label("avg_duration"),
                func.sum(TestRunModel.healed_steps).label("total_healed"),
            ).where(TestRunModel.started_at >= cutoff)

            if suite_name:
                query = query.where(TestRunModel.suite_name == suite_name)

            result = await session.execute(query)
            row = result.one()

            total = row.total or 0
            passed = row.passed or 0
            failed = row.failed or 0

            return {
                "total_runs": total,
                "passed_runs": passed,
                "failed_runs": failed,
                "pass_rate": passed / total if total > 0 else 0.0,
                "avg_duration_ms": float(row.avg_duration or 0),
                "total_healed_steps": row.total_healed or 0,
                "period_days": days,
            }
