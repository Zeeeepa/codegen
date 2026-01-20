"""
Test orchestration and scheduling.

Manages test execution across distributed execution grid.
"""

from __future__ import annotations

import os
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

import structlog
from redis import asyncio as aioredis

logger = structlog.get_logger(__name__)


class JobStatus(StrEnum):
    """Status of a test job."""

    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class JobPriority(StrEnum):
    """Priority levels for test jobs."""

    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


@dataclass
class TestJob:
    """A test execution job."""

    id: str
    test_spec_path: str | None = None
    test_spec_content: str | None = None
    suite_name: str | None = None
    test_name: str | None = None
    status: JobStatus = JobStatus.PENDING
    priority: JobPriority = JobPriority.NORMAL
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    finished_at: datetime | None = None
    worker_id: str | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    retries: int = 0
    max_retries: int = 2
    timeout_seconds: int = 600
    environment: str | None = None
    variables: dict[str, str] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    ci_metadata: dict[str, str] = field(default_factory=dict)


@dataclass
class WorkerInfo:
    """Information about an execution worker."""

    id: str
    hostname: str
    status: str = "idle"
    current_job_id: str | None = None
    last_heartbeat: datetime = field(default_factory=lambda: datetime.now(UTC))
    capabilities: list[str] = field(default_factory=list)
    max_concurrent_jobs: int = 1
    active_jobs: int = 0


class TestOrchestrator:
    """
    Orchestrates test execution across distributed workers.

    Features:
    - Job queue management with Redis
    - Priority-based scheduling
    - Worker health monitoring
    - Automatic job retry
    - Kubernetes integration for scaling
    """

    QUEUE_KEY = "autoqa:jobs:queue"
    JOBS_KEY = "autoqa:jobs"
    WORKERS_KEY = "autoqa:workers"
    RESULTS_KEY = "autoqa:results"

    def __init__(
        self,
        redis_url: str | None = None,
        max_concurrent_jobs: int = 10,
        job_timeout_seconds: int = 600,
        enable_kubernetes: bool = False,
    ) -> None:
        self._redis_url = redis_url or os.environ.get(
            "REDIS_URL", "redis://localhost:6379/0"
        )
        self._max_concurrent = max_concurrent_jobs
        self._default_timeout = job_timeout_seconds
        self._enable_k8s = enable_kubernetes
        self._redis: aioredis.Redis | None = None
        self._log = logger.bind(component="orchestrator")
        self._running = False
        self._workers: dict[str, WorkerInfo] = {}

    async def connect(self) -> None:
        """Connect to Redis."""
        self._redis = await aioredis.from_url(
            self._redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
        self._log.info("Connected to Redis", url=self._redis_url)

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._redis:
            await self._redis.close()
            self._redis = None

    async def submit_job(
        self,
        test_spec_path: str | None = None,
        test_spec_content: str | None = None,
        suite_name: str | None = None,
        test_name: str | None = None,
        priority: JobPriority = JobPriority.NORMAL,
        timeout_seconds: int | None = None,
        environment: str | None = None,
        variables: dict[str, str] | None = None,
        tags: list[str] | None = None,
        ci_metadata: dict[str, str] | None = None,
    ) -> str:
        """
        Submit a test job for execution.

        Args:
            test_spec_path: Path to test specification file
            test_spec_content: Inline test specification YAML
            suite_name: Name of the test suite
            test_name: Specific test name to run
            priority: Job priority
            timeout_seconds: Job timeout override
            environment: Target environment
            variables: Additional variables
            tags: Job tags for filtering
            ci_metadata: CI/CD metadata

        Returns:
            Job ID
        """
        if not self._redis:
            raise RuntimeError("Not connected to Redis")

        job_id = str(uuid.uuid4())

        job = TestJob(
            id=job_id,
            test_spec_path=test_spec_path,
            test_spec_content=test_spec_content,
            suite_name=suite_name,
            test_name=test_name,
            priority=priority,
            timeout_seconds=timeout_seconds or self._default_timeout,
            environment=environment,
            variables=variables or {},
            tags=tags or [],
            ci_metadata=ci_metadata or {},
        )

        job_data = self._serialize_job(job)
        await self._redis.hset(f"{self.JOBS_KEY}:{job_id}", mapping=job_data)

        priority_score = self._get_priority_score(priority)
        await self._redis.zadd(
            self.QUEUE_KEY,
            {job_id: priority_score},
        )

        self._log.info(
            "Job submitted",
            job_id=job_id,
            priority=priority,
            suite=suite_name,
            test=test_name,
        )

        return job_id

    async def get_job(self, job_id: str) -> TestJob | None:
        """Get a job by ID."""
        if not self._redis:
            raise RuntimeError("Not connected to Redis")

        data = await self._redis.hgetall(f"{self.JOBS_KEY}:{job_id}")
        if not data:
            return None

        return self._deserialize_job(data)

    async def get_job_status(self, job_id: str) -> JobStatus | None:
        """Get the status of a job."""
        job = await self.get_job(job_id)
        return job.status if job else None

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending or running job."""
        if not self._redis:
            raise RuntimeError("Not connected to Redis")

        job = await self.get_job(job_id)
        if job is None:
            return False

        if job.status not in (JobStatus.PENDING, JobStatus.QUEUED, JobStatus.RUNNING):
            return False

        await self._redis.hset(
            f"{self.JOBS_KEY}:{job_id}",
            "status",
            JobStatus.CANCELLED,
        )
        await self._redis.zrem(self.QUEUE_KEY, job_id)

        self._log.info("Job cancelled", job_id=job_id)
        return True

    async def get_next_job(self, worker_id: str) -> TestJob | None:
        """Get the next job from the queue for a worker."""
        if not self._redis:
            raise RuntimeError("Not connected to Redis")

        result = await self._redis.zpopmin(self.QUEUE_KEY)
        if not result:
            return None

        job_id = result[0][0]
        job = await self.get_job(job_id)

        if job is None:
            return None

        job.status = JobStatus.RUNNING
        job.started_at = datetime.now(UTC)
        job.worker_id = worker_id

        await self._redis.hset(
            f"{self.JOBS_KEY}:{job_id}",
            mapping={
                "status": job.status,
                "started_at": job.started_at.isoformat(),
                "worker_id": worker_id,
            },
        )

        self._log.info("Job assigned", job_id=job_id, worker_id=worker_id)
        return job

    async def complete_job(
        self,
        job_id: str,
        result: dict[str, Any],
        error: str | None = None,
    ) -> None:
        """Mark a job as completed."""
        if not self._redis:
            raise RuntimeError("Not connected to Redis")

        status = JobStatus.COMPLETED if error is None else JobStatus.FAILED
        finished_at = datetime.now(UTC)

        await self._redis.hset(
            f"{self.JOBS_KEY}:{job_id}",
            mapping={
                "status": status,
                "finished_at": finished_at.isoformat(),
                "error": error or "",
            },
        )

        import json

        await self._redis.hset(
            f"{self.RESULTS_KEY}:{job_id}",
            mapping={"result": json.dumps(result)},
        )

        self._log.info(
            "Job completed",
            job_id=job_id,
            status=status,
            has_error=error is not None,
        )

    async def retry_job(self, job_id: str) -> bool:
        """Retry a failed job."""
        if not self._redis:
            raise RuntimeError("Not connected to Redis")

        job = await self.get_job(job_id)
        if job is None:
            return False

        if job.retries >= job.max_retries:
            self._log.warning(
                "Job max retries exceeded",
                job_id=job_id,
                retries=job.retries,
            )
            return False

        job.retries += 1
        job.status = JobStatus.PENDING
        job.started_at = None
        job.worker_id = None
        job.error = None

        await self._redis.hset(
            f"{self.JOBS_KEY}:{job_id}",
            mapping={
                "status": JobStatus.PENDING,
                "retries": str(job.retries),
                "started_at": "",
                "worker_id": "",
                "error": "",
            },
        )

        priority_score = self._get_priority_score(job.priority)
        await self._redis.zadd(self.QUEUE_KEY, {job_id: priority_score})

        self._log.info("Job requeued", job_id=job_id, retry=job.retries)
        return True

    async def register_worker(
        self,
        worker_id: str,
        hostname: str,
        capabilities: list[str] | None = None,
        max_concurrent: int = 1,
    ) -> None:
        """Register a worker with the orchestrator."""
        if not self._redis:
            raise RuntimeError("Not connected to Redis")

        worker = WorkerInfo(
            id=worker_id,
            hostname=hostname,
            capabilities=capabilities or [],
            max_concurrent_jobs=max_concurrent,
        )

        await self._redis.hset(
            f"{self.WORKERS_KEY}:{worker_id}",
            mapping={
                "id": worker.id,
                "hostname": worker.hostname,
                "status": worker.status,
                "capabilities": ",".join(worker.capabilities),
                "max_concurrent_jobs": str(worker.max_concurrent_jobs),
                "last_heartbeat": worker.last_heartbeat.isoformat(),
            },
        )

        self._workers[worker_id] = worker
        self._log.info("Worker registered", worker_id=worker_id, hostname=hostname)

    async def worker_heartbeat(self, worker_id: str) -> None:
        """Update worker heartbeat."""
        if not self._redis:
            raise RuntimeError("Not connected to Redis")

        now = datetime.now(UTC)
        await self._redis.hset(
            f"{self.WORKERS_KEY}:{worker_id}",
            "last_heartbeat",
            now.isoformat(),
        )

        if worker_id in self._workers:
            self._workers[worker_id].last_heartbeat = now

    async def get_queue_stats(self) -> dict[str, Any]:
        """Get queue statistics."""
        if not self._redis:
            raise RuntimeError("Not connected to Redis")

        queue_length = await self._redis.zcard(self.QUEUE_KEY)

        workers = []
        async for key in self._redis.scan_iter(f"{self.WORKERS_KEY}:*"):
            data = await self._redis.hgetall(key)
            if data:
                workers.append(data)

        active_workers = sum(
            1 for w in workers
            if w.get("status") == "running"
        )

        return {
            "queue_length": queue_length,
            "total_workers": len(workers),
            "active_workers": active_workers,
            "max_concurrent_jobs": self._max_concurrent,
        }

    async def list_jobs(
        self,
        status: JobStatus | None = None,
        limit: int = 100,
    ) -> list[TestJob]:
        """List jobs with optional status filter."""
        if not self._redis:
            raise RuntimeError("Not connected to Redis")

        jobs: list[TestJob] = []

        async for key in self._redis.scan_iter(f"{self.JOBS_KEY}:*"):
            if len(jobs) >= limit:
                break

            data = await self._redis.hgetall(key)
            if not data:
                continue

            job = self._deserialize_job(data)
            if status is None or job.status == status:
                jobs.append(job)

        return sorted(jobs, key=lambda j: j.created_at, reverse=True)[:limit]

    def _get_priority_score(self, priority: JobPriority) -> float:
        """Convert priority to numeric score for sorting."""
        scores = {
            JobPriority.CRITICAL: 0,
            JobPriority.HIGH: 100,
            JobPriority.NORMAL: 200,
            JobPriority.LOW: 300,
        }
        timestamp = datetime.now(UTC).timestamp()
        return scores.get(priority, 200) + (timestamp / 1e10)

    def _serialize_job(self, job: TestJob) -> dict[str, str]:
        """Serialize job to dict for Redis storage."""
        import json

        return {
            "id": job.id,
            "test_spec_path": job.test_spec_path or "",
            "test_spec_content": job.test_spec_content or "",
            "suite_name": job.suite_name or "",
            "test_name": job.test_name or "",
            "status": job.status,
            "priority": job.priority,
            "created_at": job.created_at.isoformat(),
            "started_at": job.started_at.isoformat() if job.started_at else "",
            "finished_at": job.finished_at.isoformat() if job.finished_at else "",
            "worker_id": job.worker_id or "",
            "error": job.error or "",
            "retries": str(job.retries),
            "max_retries": str(job.max_retries),
            "timeout_seconds": str(job.timeout_seconds),
            "environment": job.environment or "",
            "variables": json.dumps(job.variables),
            "tags": json.dumps(job.tags),
            "ci_metadata": json.dumps(job.ci_metadata),
        }

    def _deserialize_job(self, data: dict[str, str]) -> TestJob:
        """Deserialize job from Redis data."""
        import json

        return TestJob(
            id=data["id"],
            test_spec_path=data.get("test_spec_path") or None,
            test_spec_content=data.get("test_spec_content") or None,
            suite_name=data.get("suite_name") or None,
            test_name=data.get("test_name") or None,
            status=JobStatus(data["status"]),
            priority=JobPriority(data.get("priority", "normal")),
            created_at=datetime.fromisoformat(data["created_at"]),
            started_at=(
                datetime.fromisoformat(data["started_at"])
                if data.get("started_at")
                else None
            ),
            finished_at=(
                datetime.fromisoformat(data["finished_at"])
                if data.get("finished_at")
                else None
            ),
            worker_id=data.get("worker_id") or None,
            error=data.get("error") or None,
            retries=int(data.get("retries", "0")),
            max_retries=int(data.get("max_retries", "2")),
            timeout_seconds=int(data.get("timeout_seconds", "600")),
            environment=data.get("environment") or None,
            variables=json.loads(data.get("variables", "{}")),
            tags=json.loads(data.get("tags", "[]")),
            ci_metadata=json.loads(data.get("ci_metadata", "{}")),
        )
