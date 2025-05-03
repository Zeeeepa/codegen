"""
Analysis Pipeline Orchestrator Module

This module provides a pipeline orchestrator for managing analysis workflows.
It handles task queuing, worker management, and error handling.
"""

import logging
import threading
import time
import queue
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime

from codegen_on_oss.events.event_bus import EventType, Event, event_bus
from codegen_on_oss.database.connection import db_manager
from codegen_on_oss.database.repositories import AnalysisJobRepository

logger = logging.getLogger(__name__)

class AnalysisPipeline:
    """
    Pipeline orchestrator for analysis workflows.
    
    This class manages the execution of analysis tasks, handling task queuing,
    worker management, and error handling.
    """
    
    def __init__(self, num_workers: int = 3):
        """
        Initialize the analysis pipeline.
        
        Args:
            num_workers: Number of worker threads to create
        """
        self.tasks = queue.Queue()
        self.workers = []
        self.running = False
        self.num_workers = num_workers
        self.task_handlers = {}
        
        # Register default task handlers
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default task handlers."""
        self.register_task_handler("create_snapshot", self._handle_create_snapshot)
        self.register_task_handler("snapshot_analysis", self._handle_snapshot_analysis)
        self.register_task_handler("commit_analysis", self._handle_commit_analysis)
        self.register_task_handler("pr_analysis", self._handle_pr_analysis)
    
    def register_task_handler(self, task_type: str, handler: Callable[[Dict[str, Any]], None]):
        """
        Register a task handler.
        
        Args:
            task_type: The task type
            handler: The handler function
        """
        self.task_handlers[task_type] = handler
        logger.info(f"Registered handler for task type: {task_type}")
    
    def start(self):
        """Start the pipeline workers."""
        if self.running:
            logger.warning("Pipeline is already running")
            return
        
        self.running = True
        
        # Start worker threads
        for i in range(self.num_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"AnalysisPipelineWorker-{i}",
                daemon=True
            )
            worker.start()
            self.workers.append(worker)
        
        logger.info(f"Started {self.num_workers} worker threads")
        
        # Start job poller thread
        poller = threading.Thread(
            target=self._job_poller_loop,
            name="AnalysisPipelineJobPoller",
            daemon=True
        )
        poller.start()
        self.workers.append(poller)
        
        logger.info("Started job poller thread")
    
    def stop(self):
        """Stop the pipeline workers."""
        if not self.running:
            logger.warning("Pipeline is not running")
            return
        
        self.running = False
        
        # Add a sentinel task for each worker
        for _ in range(self.num_workers):
            self.tasks.put(None)
        
        # Wait for workers to finish
        for worker in self.workers:
            if worker.is_alive():
                worker.join(timeout=5.0)
        
        self.workers = []
        logger.info("Stopped pipeline workers")
    
    def add_task(self, task_type: str, task_data: Dict[str, Any]):
        """
        Add a task to the queue.
        
        Args:
            task_type: The task type
            task_data: The task data
        """
        self.tasks.put((task_type, task_data))
        logger.debug(f"Added task of type {task_type} to queue")
    
    def _worker_loop(self):
        """Worker thread loop."""
        logger.info(f"Worker thread {threading.current_thread().name} started")
        
        while self.running:
            try:
                # Get a task from the queue
                task = self.tasks.get(timeout=1.0)
                
                # Check for sentinel task
                if task is None:
                    logger.debug(f"Worker thread {threading.current_thread().name} received sentinel task")
                    break
                
                # Process the task
                task_type, task_data = task
                self._process_task(task_type, task_data)
                
                # Mark the task as done
                self.tasks.task_done()
            except queue.Empty:
                # No tasks available, continue
                continue
            except Exception as e:
                logger.error(f"Error in worker thread: {e}", exc_info=True)
        
        logger.info(f"Worker thread {threading.current_thread().name} stopped")
    
    def _job_poller_loop(self):
        """Job poller thread loop."""
        logger.info("Job poller thread started")
        
        while self.running:
            try:
                # Poll for pending jobs
                with db_manager.session_scope() as session:
                    job_repo = AnalysisJobRepository(session)
                    pending_jobs = job_repo.get_pending_jobs()
                    
                    for job in pending_jobs:
                        # Add a task for each pending job
                        self.add_task(job.job_type, {
                            "job_id": job.id,
                            "repo_id": job.repo_id,
                            "parameters": job.parameters or {}
                        })
                        
                        # Update job status to prevent it from being picked up again
                        job_repo.update(job.id, status="queued")
                        logger.info(f"Queued job {job.id} of type {job.job_type}")
                
                # Sleep before polling again
                time.sleep(5.0)
            except Exception as e:
                logger.error(f"Error in job poller thread: {e}", exc_info=True)
                time.sleep(10.0)  # Sleep longer on error
        
        logger.info("Job poller thread stopped")
    
    def _process_task(self, task_type: str, task_data: Dict[str, Any]):
        """
        Process a task.
        
        Args:
            task_type: The task type
            task_data: The task data
        """
        logger.info(f"Processing task of type {task_type}")
        
        try:
            # Get the handler for this task type
            handler = self.task_handlers.get(task_type)
            
            if handler:
                # Call the handler
                handler(task_data)
            else:
                logger.warning(f"No handler registered for task type: {task_type}")
                
                # Update job status if job_id is provided
                job_id = task_data.get("job_id")
                if job_id:
                    with db_manager.session_scope() as session:
                        job_repo = AnalysisJobRepository(session)
                        job_repo.update(
                            job_id,
                            status="failed",
                            error_message=f"No handler registered for task type: {task_type}"
                        )
        except Exception as e:
            logger.error(f"Error processing task of type {task_type}: {e}", exc_info=True)
            
            # Update job status if job_id is provided
            job_id = task_data.get("job_id")
            if job_id:
                with db_manager.session_scope() as session:
                    job_repo = AnalysisJobRepository(session)
                    job_repo.update(
                        job_id,
                        status="failed",
                        error_message=str(e)
                    )
                
                # Publish job failed event
                event_bus.publish(Event(
                    EventType.JOB_FAILED,
                    {
                        "job_id": job_id,
                        "repo_id": task_data.get("repo_id"),
                        "job_type": task_type,
                        "error": str(e)
                    }
                ))
    
    def _handle_create_snapshot(self, task_data: Dict[str, Any]):
        """
        Handle a create_snapshot task.
        
        Args:
            task_data: The task data
        """
        job_id = task_data.get("job_id")
        repo_id = task_data.get("repo_id")
        parameters = task_data.get("parameters", {})
        
        # Update job status
        with db_manager.session_scope() as session:
            job_repo = AnalysisJobRepository(session)
            job_repo.update(
                job_id,
                status="running",
                started_at=datetime.now()
            )
        
        # Publish job started event
        event_bus.publish(Event(
            EventType.JOB_STARTED,
            {
                "job_id": job_id,
                "repo_id": repo_id,
                "job_type": "create_snapshot",
                "parameters": parameters
            }
        ))
        
        try:
            # Create a snapshot
            from codegen_on_oss.snapshot.enhanced_snapshot_manager import EnhancedSnapshotManager
            
            with db_manager.session_scope() as session:
                # Create a snapshot manager
                snapshot_manager = EnhancedSnapshotManager(session)
                
                # Get repository
                from codegen_on_oss.database.repositories import RepositoryRepository
                repo_repo = RepositoryRepository(session)
                repository = repo_repo.get_by_id(repo_id)
                
                if not repository:
                    raise ValueError(f"Repository not found: {repo_id}")
                
                # Create a snapshot
                snapshot = snapshot_manager.snapshot_repo(
                    repository.url,
                    commit_sha=parameters.get("commit_sha"),
                    branch=parameters.get("branch"),
                    github_token=parameters.get("github_token")
                )
                
                # Update job status
                job_repo.update(
                    job_id,
                    status="completed",
                    completed_at=datetime.now()
                )
                
                # Publish job completed event
                event_bus.publish(Event(
                    EventType.JOB_COMPLETED,
                    {
                        "job_id": job_id,
                        "repo_id": repo_id,
                        "job_type": "create_snapshot",
                        "snapshot_id": snapshot.snapshot_id
                    }
                ))
                
                # If analyze flag is set, create an analysis job
                if parameters.get("analyze", False):
                    # Create a new job for snapshot analysis
                    analysis_job = job_repo.create(
                        repo_id=repo_id,
                        job_type="snapshot_analysis",
                        status="pending",
                        parameters={
                            "snapshot_id": snapshot.snapshot_id
                        }
                    )
                    
                    # Publish job created event
                    event_bus.publish(Event(
                        EventType.JOB_CREATED,
                        {
                            "job_id": analysis_job.id,
                            "repo_id": repo_id,
                            "job_type": "snapshot_analysis",
                            "parameters": {
                                "snapshot_id": snapshot.snapshot_id
                            }
                        }
                    ))
        except Exception as e:
            logger.error(f"Error creating snapshot: {e}", exc_info=True)
            
            # Update job status
            with db_manager.session_scope() as session:
                job_repo = AnalysisJobRepository(session)
                job_repo.update(
                    job_id,
                    status="failed",
                    completed_at=datetime.now(),
                    error_message=str(e)
                )
            
            # Publish job failed event
            event_bus.publish(Event(
                EventType.JOB_FAILED,
                {
                    "job_id": job_id,
                    "repo_id": repo_id,
                    "job_type": "create_snapshot",
                    "error": str(e)
                }
            ))
    
    def _handle_snapshot_analysis(self, task_data: Dict[str, Any]):
        """
        Handle a snapshot_analysis task.
        
        Args:
            task_data: The task data
        """
        job_id = task_data.get("job_id")
        repo_id = task_data.get("repo_id")
        parameters = task_data.get("parameters", {})
        
        # Update job status
        with db_manager.session_scope() as session:
            job_repo = AnalysisJobRepository(session)
            job_repo.update(
                job_id,
                status="running",
                started_at=datetime.now()
            )
        
        # Publish job started event
        event_bus.publish(Event(
            EventType.JOB_STARTED,
            {
                "job_id": job_id,
                "repo_id": repo_id,
                "job_type": "snapshot_analysis",
                "parameters": parameters
            }
        ))
        
        try:
            # Analyze the snapshot
            from codegen_on_oss.snapshot.enhanced_snapshot_manager import EnhancedSnapshotManager
            from codegen_on_oss.analysis.code_analyzer import CodeAnalyzer
            
            with db_manager.session_scope() as session:
                # Create a snapshot manager
                snapshot_manager = EnhancedSnapshotManager(session)
                
                # Get the snapshot
                from codegen_on_oss.database.repositories import SnapshotRepository
                snapshot_repo = SnapshotRepository(session)
                snapshot_id = parameters.get("snapshot_id")
                snapshot = snapshot_repo.get_by_snapshot_id(snapshot_id)
                
                if not snapshot:
                    raise ValueError(f"Snapshot not found: {snapshot_id}")
                
                # Load the codebase from the snapshot
                codebase = snapshot_manager.load_codebase_from_snapshot(snapshot)
                
                # Create a code analyzer
                analyzer = CodeAnalyzer(codebase)
                
                # Analyze the codebase
                analysis_result = analyzer.analyze()
                
                # Store the analysis result
                from codegen_on_oss.database.repositories import AnalysisResultRepository
                result_repo = AnalysisResultRepository(session)
                result = result_repo.create(
                    repo_id=repo_id,
                    snapshot_id=snapshot.id,
                    analysis_type="snapshot_analysis",
                    summary=analysis_result.get("summary"),
                    metrics=analysis_result.get("metrics")
                )
                
                # Store issues
                from codegen_on_oss.database.repositories import AnalysisIssueRepository
                issue_repo = AnalysisIssueRepository(session)
                for issue_data in analysis_result.get("issues", []):
                    issue_repo.create(
                        analysis_result_id=result.id,
                        issue_type=issue_data.get("type"),
                        severity=issue_data.get("severity"),
                        message=issue_data.get("message"),
                        file_path=issue_data.get("file_path"),
                        line_number=issue_data.get("line_number"),
                        code_snippet=issue_data.get("code_snippet"),
                        suggestion=issue_data.get("suggestion")
                    )
                
                # Update job status
                job_repo.update(
                    job_id,
                    status="completed",
                    completed_at=datetime.now(),
                    result_id=result.id
                )
                
                # Publish analysis completed event
                event_bus.publish(Event(
                    EventType.ANALYSIS_COMPLETED,
                    {
                        "job_id": job_id,
                        "repo_id": repo_id,
                        "analysis_type": "snapshot_analysis",
                        "result_id": result.id
                    }
                ))
                
                # Publish job completed event
                event_bus.publish(Event(
                    EventType.JOB_COMPLETED,
                    {
                        "job_id": job_id,
                        "repo_id": repo_id,
                        "job_type": "snapshot_analysis",
                        "result_id": result.id
                    }
                ))
        except Exception as e:
            logger.error(f"Error analyzing snapshot: {e}", exc_info=True)
            
            # Update job status
            with db_manager.session_scope() as session:
                job_repo = AnalysisJobRepository(session)
                job_repo.update(
                    job_id,
                    status="failed",
                    completed_at=datetime.now(),
                    error_message=str(e)
                )
            
            # Publish job failed event
            event_bus.publish(Event(
                EventType.JOB_FAILED,
                {
                    "job_id": job_id,
                    "repo_id": repo_id,
                    "job_type": "snapshot_analysis",
                    "error": str(e)
                }
            ))
    
    def _handle_commit_analysis(self, task_data: Dict[str, Any]):
        """
        Handle a commit_analysis task.
        
        Args:
            task_data: The task data
        """
        job_id = task_data.get("job_id")
        repo_id = task_data.get("repo_id")
        parameters = task_data.get("parameters", {})
        
        # Update job status
        with db_manager.session_scope() as session:
            job_repo = AnalysisJobRepository(session)
            job_repo.update(
                job_id,
                status="running",
                started_at=datetime.now()
            )
        
        # Publish job started event
        event_bus.publish(Event(
            EventType.JOB_STARTED,
            {
                "job_id": job_id,
                "repo_id": repo_id,
                "job_type": "commit_analysis",
                "parameters": parameters
            }
        ))
        
        try:
            # Analyze the commit
            from codegen_on_oss.snapshot.enhanced_snapshot_manager import EnhancedSnapshotManager
            from codegen_on_oss.analysis.commit_analyzer import CommitAnalyzer
            
            with db_manager.session_scope() as session:
                # Create a snapshot manager
                snapshot_manager = EnhancedSnapshotManager(session)
                
                # Get repository
                from codegen_on_oss.database.repositories import RepositoryRepository
                repo_repo = RepositoryRepository(session)
                repository = repo_repo.get_by_id(repo_id)
                
                if not repository:
                    raise ValueError(f"Repository not found: {repo_id}")
                
                # Get commit SHA and base commit SHA
                commit_sha = parameters.get("commit_sha")
                base_commit_sha = parameters.get("base_commit_sha")
                
                if not commit_sha:
                    raise ValueError("Commit SHA is required for commit analysis")
                
                # Create snapshots for the commits
                commit_snapshot = snapshot_manager.snapshot_repo(
                    repository.url,
                    commit_sha=commit_sha
                )
                
                base_snapshot = None
                if base_commit_sha:
                    base_snapshot = snapshot_manager.snapshot_repo(
                        repository.url,
                        commit_sha=base_commit_sha
                    )
                else:
                    # Use the latest snapshot before this commit
                    from codegen_on_oss.database.repositories import SnapshotRepository
                    snapshot_repo = SnapshotRepository(session)
                    base_snapshot = snapshot_repo.get_latest_for_repo(repo_id)
                
                if not base_snapshot:
                    raise ValueError("Base snapshot not found for comparison")
                
                # Load the codebases from the snapshots
                commit_codebase = snapshot_manager.load_codebase_from_snapshot(commit_snapshot)
                base_codebase = snapshot_manager.load_codebase_from_snapshot(base_snapshot)
                
                # Create a commit analyzer
                analyzer = CommitAnalyzer(
                    original_codebase=base_codebase,
                    commit_codebase=commit_codebase
                )
                
                # Analyze the commit
                analysis_result = analyzer.analyze_commit()
                
                # Store the analysis result
                from codegen_on_oss.database.repositories import AnalysisResultRepository
                result_repo = AnalysisResultRepository(session)
                result = result_repo.create(
                    repo_id=repo_id,
                    snapshot_id=commit_snapshot.id,
                    analysis_type="commit_analysis",
                    summary=analysis_result.get_summary(),
                    metrics={
                        "metrics_diff": analysis_result.metrics_diff,
                        "files_added": analysis_result.files_added,
                        "files_modified": analysis_result.files_modified,
                        "files_removed": analysis_result.files_removed
                    }
                )
                
                # Store issues
                from codegen_on_oss.database.repositories import AnalysisIssueRepository
                issue_repo = AnalysisIssueRepository(session)
                for issue in analysis_result.issues:
                    issue_repo.create(
                        analysis_result_id=result.id,
                        issue_type=issue.issue_type,
                        severity=issue.severity,
                        message=issue.message,
                        file_path=issue.file_path,
                        line_number=issue.line_number,
                        code_snippet=issue.code_snippet,
                        suggestion=issue.suggestion
                    )
                
                # Update job status
                job_repo.update(
                    job_id,
                    status="completed",
                    completed_at=datetime.now(),
                    result_id=result.id
                )
                
                # Publish analysis completed event
                event_bus.publish(Event(
                    EventType.ANALYSIS_COMPLETED,
                    {
                        "job_id": job_id,
                        "repo_id": repo_id,
                        "analysis_type": "commit_analysis",
                        "result_id": result.id
                    }
                ))
                
                # Publish commit analyzed event
                event_bus.publish(Event(
                    EventType.COMMIT_ANALYZED,
                    {
                        "repo_id": repo_id,
                        "commit_sha": commit_sha,
                        "result_id": result.id
                    }
                ))
                
                # Publish job completed event
                event_bus.publish(Event(
                    EventType.JOB_COMPLETED,
                    {
                        "job_id": job_id,
                        "repo_id": repo_id,
                        "job_type": "commit_analysis",
                        "result_id": result.id
                    }
                ))
        except Exception as e:
            logger.error(f"Error analyzing commit: {e}", exc_info=True)
            
            # Update job status
            with db_manager.session_scope() as session:
                job_repo = AnalysisJobRepository(session)
                job_repo.update(
                    job_id,
                    status="failed",
                    completed_at=datetime.now(),
                    error_message=str(e)
                )
            
            # Publish job failed event
            event_bus.publish(Event(
                EventType.JOB_FAILED,
                {
                    "job_id": job_id,
                    "repo_id": repo_id,
                    "job_type": "commit_analysis",
                    "error": str(e)
                }
            ))
    
    def _handle_pr_analysis(self, task_data: Dict[str, Any]):
        """
        Handle a pr_analysis task.
        
        Args:
            task_data: The task data
        """
        job_id = task_data.get("job_id")
        repo_id = task_data.get("repo_id")
        parameters = task_data.get("parameters", {})
        
        # Update job status
        with db_manager.session_scope() as session:
            job_repo = AnalysisJobRepository(session)
            job_repo.update(
                job_id,
                status="running",
                started_at=datetime.now()
            )
        
        # Publish job started event
        event_bus.publish(Event(
            EventType.JOB_STARTED,
            {
                "job_id": job_id,
                "repo_id": repo_id,
                "job_type": "pr_analysis",
                "parameters": parameters
            }
        ))
        
        try:
            # Analyze the PR
            from codegen_on_oss.snapshot.enhanced_snapshot_manager import EnhancedSnapshotManager
            from codegen_on_oss.analysis.commit_analyzer import CommitAnalyzer
            
            with db_manager.session_scope() as session:
                # Create a snapshot manager
                snapshot_manager = EnhancedSnapshotManager(session)
                
                # Get repository
                from codegen_on_oss.database.repositories import RepositoryRepository
                repo_repo = RepositoryRepository(session)
                repository = repo_repo.get_by_id(repo_id)
                
                if not repository:
                    raise ValueError(f"Repository not found: {repo_id}")
                
                # Get PR number and head/base SHAs
                pr_number = parameters.get("pr_number")
                pr_head_sha = parameters.get("pr_head_sha")
                pr_base_sha = parameters.get("pr_base_sha")
                
                if not pr_number:
                    raise ValueError("PR number is required for PR analysis")
                
                if not pr_head_sha or not pr_base_sha:
                    raise ValueError("PR head and base SHAs are required")
                
                # Create snapshots for the PR head and base
                head_snapshot = snapshot_manager.snapshot_repo(
                    repository.url,
                    commit_sha=pr_head_sha
                )
                
                base_snapshot = snapshot_manager.snapshot_repo(
                    repository.url,
                    commit_sha=pr_base_sha
                )
                
                # Load the codebases from the snapshots
                head_codebase = snapshot_manager.load_codebase_from_snapshot(head_snapshot)
                base_codebase = snapshot_manager.load_codebase_from_snapshot(base_snapshot)
                
                # Create a commit analyzer (reused for PR analysis)
                analyzer = CommitAnalyzer(
                    original_codebase=base_codebase,
                    commit_codebase=head_codebase
                )
                
                # Analyze the PR
                analysis_result = analyzer.analyze_commit()
                
                # Store the analysis result
                from codegen_on_oss.database.repositories import AnalysisResultRepository
                result_repo = AnalysisResultRepository(session)
                result = result_repo.create(
                    repo_id=repo_id,
                    snapshot_id=head_snapshot.id,
                    analysis_type="pr_analysis",
                    summary=analysis_result.get_summary(),
                    metrics={
                        "pr_number": pr_number,
                        "metrics_diff": analysis_result.metrics_diff,
                        "files_added": analysis_result.files_added,
                        "files_modified": analysis_result.files_modified,
                        "files_removed": analysis_result.files_removed
                    }
                )
                
                # Store issues
                from codegen_on_oss.database.repositories import AnalysisIssueRepository
                issue_repo = AnalysisIssueRepository(session)
                for issue in analysis_result.issues:
                    issue_repo.create(
                        analysis_result_id=result.id,
                        issue_type=issue.issue_type,
                        severity=issue.severity,
                        message=issue.message,
                        file_path=issue.file_path,
                        line_number=issue.line_number,
                        code_snippet=issue.code_snippet,
                        suggestion=issue.suggestion
                    )
                
                # Update job status
                job_repo.update(
                    job_id,
                    status="completed",
                    completed_at=datetime.now(),
                    result_id=result.id
                )
                
                # Publish analysis completed event
                event_bus.publish(Event(
                    EventType.ANALYSIS_COMPLETED,
                    {
                        "job_id": job_id,
                        "repo_id": repo_id,
                        "analysis_type": "pr_analysis",
                        "result_id": result.id
                    }
                ))
                
                # Publish PR analyzed event
                event_bus.publish(Event(
                    EventType.PR_ANALYZED,
                    {
                        "repo_id": repo_id,
                        "pr_number": pr_number,
                        "result_id": result.id
                    }
                ))
                
                # Publish job completed event
                event_bus.publish(Event(
                    EventType.JOB_COMPLETED,
                    {
                        "job_id": job_id,
                        "repo_id": repo_id,
                        "job_type": "pr_analysis",
                        "result_id": result.id
                    }
                ))
        except Exception as e:
            logger.error(f"Error analyzing PR: {e}", exc_info=True)
            
            # Update job status
            with db_manager.session_scope() as session:
                job_repo = AnalysisJobRepository(session)
                job_repo.update(
                    job_id,
                    status="failed",
                    completed_at=datetime.now(),
                    error_message=str(e)
                )
            
            # Publish job failed event
            event_bus.publish(Event(
                EventType.JOB_FAILED,
                {
                    "job_id": job_id,
                    "repo_id": repo_id,
                    "job_type": "pr_analysis",
                    "error": str(e)
                }
            ))

# Create a global pipeline instance
pipeline = AnalysisPipeline()
"""

