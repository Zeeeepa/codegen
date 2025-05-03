"""
Task queue for the codegen-on-oss system.

This module provides a task queue for running long-running analyses in the background
using Redis and RQ.
"""

import logging
import uuid
import json
from typing import Dict, List, Optional, Any, Union

import redis
from rq import Queue, Worker, Connection
from rq.job import Job

from codegen_on_oss.config import settings
from codegen_on_oss.api.app import manager  # WebSocket connection manager

logger = logging.getLogger(__name__)


class AnalysisTaskQueue:
    """Manages background analysis tasks"""
    
    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize the analysis task queue.
        
        Args:
            redis_url: URL of the Redis server, defaults to settings.redis_url
        """
        self.redis_url = redis_url or settings.redis_url
        
        if not self.redis_url:
            logger.warning("Redis URL not configured, task queue will not be available")
            self.redis = None
            self.task_queue = None
            return
        
        try:
            self.redis = redis.from_url(self.redis_url)
            self.task_queue = Queue("analysis_tasks", connection=self.redis)
            logger.info(f"Task queue initialized with Redis at {self.redis_url}")
        except Exception as e:
            logger.error(f"Failed to initialize task queue: {str(e)}")
            self.redis = None
            self.task_queue = None
    
    async def enqueue_analysis(self, analysis_request: Dict[str, Any]) -> Optional[str]:
        """
        Add an analysis task to the queue.
        
        Args:
            analysis_request: Analysis request parameters
            
        Returns:
            Optional[str]: Job ID if successful, None otherwise
        """
        if not self.task_queue:
            logger.warning("Task queue not available, cannot enqueue analysis")
            return None
        
        try:
            # Import here to avoid circular imports
            from codegen_on_oss.tasks.workers import perform_analysis
            
            job = self.task_queue.enqueue(
                perform_analysis,
                kwargs=analysis_request,
                job_id=f"analysis_{uuid.uuid4()}",
                timeout=settings.task_timeout
            )
            
            logger.info(f"Enqueued analysis job: {job.id}")
            return job.id
        
        except Exception as e:
            logger.error(f"Failed to enqueue analysis: {str(e)}")
            return None
    
    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get the status of a job.
        
        Args:
            job_id: ID of the job
            
        Returns:
            Dict[str, Any]: Job status information
        """
        if not self.task_queue:
            logger.warning("Task queue not available, cannot get job status")
            return {"status": "unavailable"}
        
        try:
            job = Job.fetch(job_id, connection=self.redis)
            
            if not job:
                return {"status": "not_found"}
            
            return {
                "job_id": job.id,
                "status": job.get_status(),
                "progress": job.meta.get("progress", 0),
                "result": job.result if job.is_finished else None,
                "error": str(job.exc_info) if job.is_failed else None,
                "enqueued_at": job.enqueued_at.isoformat() if job.enqueued_at else None,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "ended_at": job.ended_at.isoformat() if job.ended_at else None,
            }
        
        except Exception as e:
            logger.error(f"Failed to get job status: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def update_job_progress(self, job_id: str, progress: int, data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update the progress of a job and send a WebSocket notification.
        
        Args:
            job_id: ID of the job
            progress: Progress percentage (0-100)
            data: Optional data to include in the progress update
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.task_queue:
            logger.warning("Task queue not available, cannot update job progress")
            return False
        
        try:
            job = Job.fetch(job_id, connection=self.redis)
            
            if not job:
                logger.warning(f"Job not found: {job_id}")
                return False
            
            # Update job metadata
            job.meta["progress"] = progress
            if data:
                job.meta["data"] = data
            job.save_meta()
            
            # Send WebSocket notification if WebSockets are enabled
            if settings.enable_websockets:
                try:
                    await manager.send_message(
                        {
                            "job_id": job_id,
                            "progress": progress,
                            "status": job.get_status(),
                            "data": data
                        },
                        job_id
                    )
                except Exception as e:
                    logger.warning(f"Failed to send WebSocket notification: {str(e)}")
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to update job progress: {str(e)}")
            return False
    
    def start_worker(self, num_workers: int = 1):
        """
        Start worker processes to process tasks from the queue.
        
        Args:
            num_workers: Number of worker processes to start
        """
        if not self.task_queue:
            logger.warning("Task queue not available, cannot start workers")
            return
        
        with Connection(self.redis):
            workers = []
            
            for i in range(num_workers):
                worker = Worker([self.task_queue])
                worker.work(burst=False)  # Run continuously
                workers.append(worker)
            
            logger.info(f"Started {num_workers} workers")


# Create a global task queue instance
task_queue = AnalysisTaskQueue()

