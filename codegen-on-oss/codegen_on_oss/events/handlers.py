"""
Event Handlers Module

This module provides event handlers for various events in the system.
These handlers respond to events by performing appropriate actions.
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from sqlalchemy.orm import Session

from codegen_on_oss.events.event_bus import EventType, Event, event_bus, subscribe
from codegen_on_oss.database.connection import db_manager
from codegen_on_oss.database.repositories import (
    RepositoryRepository, SnapshotRepository, AnalysisResultRepository,
    AnalysisIssueRepository, FileRepository, AnalysisJobRepository,
    WebhookConfigRepository
)
from codegen_on_oss.snapshot.enhanced_snapshot_manager import EnhancedSnapshotManager
from codegen_on_oss.analysis.code_analyzer import CodeAnalyzer

logger = logging.getLogger(__name__)

class AnalysisEventHandler:
    """
    Handler for analysis-related events.
    
    This class provides methods for handling events related to code analysis,
    such as analysis completion and failure.
    """
    
    @staticmethod
    @subscribe(EventType.ANALYSIS_STARTED)
    def handle_analysis_started(payload: Dict[str, Any]) -> None:
        """
        Handle the analysis started event.
        
        Args:
            payload: The event payload
        """
        logger.info(f"Analysis started: {payload.get('analysis_type')} for repo {payload.get('repo_id')}")
        
        with db_manager.session_scope() as session:
            job_repo = AnalysisJobRepository(session)
            job_id = payload.get('job_id')
            
            if job_id:
                job_repo.update(
                    job_id,
                    status="running",
                    started_at=datetime.now()
                )
    
    @staticmethod
    @subscribe(EventType.ANALYSIS_COMPLETED)
    def handle_analysis_completed(payload: Dict[str, Any]) -> None:
        """
        Handle the analysis completed event.
        
        Args:
            payload: The event payload
        """
        logger.info(f"Analysis completed: {payload.get('analysis_type')} for repo {payload.get('repo_id')}")
        
        with db_manager.session_scope() as session:
            job_repo = AnalysisJobRepository(session)
            job_id = payload.get('job_id')
            result_id = payload.get('result_id')
            
            if job_id:
                job_repo.update(
                    job_id,
                    status="completed",
                    completed_at=datetime.now(),
                    result_id=result_id
                )
            
            # Trigger webhook notifications if configured
            repo_id = payload.get('repo_id')
            if repo_id:
                webhook_repo = WebhookConfigRepository(session)
                webhooks = webhook_repo.get_webhooks_for_repo(repo_id)
                
                for webhook in webhooks:
                    events = webhook.events or []
                    if "analysis" in events or payload.get('analysis_type') in events:
                        # Publish webhook event
                        event_bus.publish(Event(
                            EventType.WEBHOOK_TRIGGERED,
                            {
                                "webhook_id": webhook.id,
                                "repo_id": repo_id,
                                "url": webhook.url,
                                "payload": {
                                    "event": "analysis_completed",
                                    "analysis_type": payload.get('analysis_type'),
                                    "repo_id": repo_id,
                                    "result_id": result_id
                                }
                            }
                        ))
    
    @staticmethod
    @subscribe(EventType.ANALYSIS_FAILED)
    def handle_analysis_failed(payload: Dict[str, Any]) -> None:
        """
        Handle the analysis failed event.
        
        Args:
            payload: The event payload
        """
        logger.error(f"Analysis failed: {payload.get('analysis_type')} for repo {payload.get('repo_id')}")
        logger.error(f"Error: {payload.get('error')}")
        
        with db_manager.session_scope() as session:
            job_repo = AnalysisJobRepository(session)
            job_id = payload.get('job_id')
            
            if job_id:
                job_repo.update(
                    job_id,
                    status="failed",
                    completed_at=datetime.now(),
                    error_message=payload.get('error')
                )

class SnapshotEventHandler:
    """
    Handler for snapshot-related events.
    
    This class provides methods for handling events related to codebase snapshots,
    such as snapshot creation and deletion.
    """
    
    @staticmethod
    @subscribe(EventType.SNAPSHOT_CREATED)
    def handle_snapshot_created(payload: Dict[str, Any]) -> None:
        """
        Handle the snapshot created event.
        
        Args:
            payload: The event payload
        """
        logger.info(f"Snapshot created: {payload.get('snapshot_id')} for repo {payload.get('repo_id')}")
        
        # Trigger analysis if requested
        if payload.get('analyze', False):
            event_bus.publish(Event(
                EventType.JOB_CREATED,
                {
                    "repo_id": payload.get('repo_id'),
                    "job_type": "snapshot_analysis",
                    "parameters": {
                        "snapshot_id": payload.get('snapshot_id')
                    }
                }
            ))
    
    @staticmethod
    @subscribe(EventType.SNAPSHOT_DELETED)
    def handle_snapshot_deleted(payload: Dict[str, Any]) -> None:
        """
        Handle the snapshot deleted event.
        
        Args:
            payload: The event payload
        """
        logger.info(f"Snapshot deleted: {payload.get('snapshot_id')}")
        
        # Clean up S3 files if needed
        snapshot_id = payload.get('snapshot_id')
        if snapshot_id:
            # TODO: Implement S3 cleanup logic
            pass

class RepositoryEventHandler:
    """
    Handler for repository-related events.
    
    This class provides methods for handling events related to code repositories,
    such as repository addition and deletion.
    """
    
    @staticmethod
    @subscribe(EventType.REPOSITORY_ADDED)
    def handle_repository_added(payload: Dict[str, Any]) -> None:
        """
        Handle the repository added event.
        
        Args:
            payload: The event payload
        """
        logger.info(f"Repository added: {payload.get('repo_url')}")
        
        # Create initial snapshot if requested
        if payload.get('create_snapshot', False):
            repo_id = payload.get('repo_id')
            if repo_id:
                with db_manager.session_scope() as session:
                    repo_repo = RepositoryRepository(session)
                    repository = repo_repo.get_by_id(repo_id)
                    
                    if repository:
                        # Create a snapshot manager
                        snapshot_manager = EnhancedSnapshotManager(session)
                        
                        # Create a snapshot
                        snapshot = snapshot_manager.snapshot_repo(
                            repository.url,
                            commit_sha=payload.get('commit_sha'),
                            branch=payload.get('branch')
                        )
                        
                        # Publish snapshot created event
                        event_bus.publish(Event(
                            EventType.SNAPSHOT_CREATED,
                            {
                                "repo_id": repo_id,
                                "snapshot_id": snapshot.snapshot_id,
                                "analyze": payload.get('analyze', False)
                            }
                        ))
    
    @staticmethod
    @subscribe(EventType.REPOSITORY_DELETED)
    def handle_repository_deleted(payload: Dict[str, Any]) -> None:
        """
        Handle the repository deleted event.
        
        Args:
            payload: The event payload
        """
        logger.info(f"Repository deleted: {payload.get('repo_id')}")
        
        # Clean up associated resources if needed
        repo_id = payload.get('repo_id')
        if repo_id:
            # TODO: Implement cleanup logic for snapshots, analysis results, etc.
            pass

class JobEventHandler:
    """
    Handler for job-related events.
    
    This class provides methods for handling events related to analysis jobs,
    such as job creation and completion.
    """
    
    @staticmethod
    @subscribe(EventType.JOB_CREATED)
    def handle_job_created(payload: Dict[str, Any]) -> None:
        """
        Handle the job created event.
        
        Args:
            payload: The event payload
        """
        logger.info(f"Job created: {payload.get('job_type')} for repo {payload.get('repo_id')}")
        
        with db_manager.session_scope() as session:
            job_repo = AnalysisJobRepository(session)
            
            # Create job record
            job = job_repo.create(
                repo_id=payload.get('repo_id'),
                job_type=payload.get('job_type'),
                status="pending",
                parameters=payload.get('parameters')
            )
            
            # Publish job started event
            event_bus.publish(Event(
                EventType.JOB_STARTED,
                {
                    "job_id": job.id,
                    "repo_id": job.repo_id,
                    "job_type": job.job_type,
                    "parameters": job.parameters
                }
            ))
    
    @staticmethod
    @subscribe(EventType.JOB_STARTED)
    async def handle_job_started(payload: Dict[str, Any]) -> None:
        """
        Handle the job started event.
        
        Args:
            payload: The event payload
        """
        logger.info(f"Job started: {payload.get('job_type')} for repo {payload.get('repo_id')}")
        
        job_id = payload.get('job_id')
        job_type = payload.get('job_type')
        repo_id = payload.get('repo_id')
        parameters = payload.get('parameters', {})
        
        try:
            # Update job status
            with db_manager.session_scope() as session:
                job_repo = AnalysisJobRepository(session)
                job_repo.update(
                    job_id,
                    status="running",
                    started_at=datetime.now()
                )
            
            # Publish analysis started event
            event_bus.publish(Event(
                EventType.ANALYSIS_STARTED,
                {
                    "job_id": job_id,
                    "repo_id": repo_id,
                    "analysis_type": job_type,
                    "parameters": parameters
                }
            ))
            
            # Process job based on type
            if job_type == "snapshot_analysis":
                await JobEventHandler._process_snapshot_analysis(job_id, repo_id, parameters)
            elif job_type == "commit_analysis":
                await JobEventHandler._process_commit_analysis(job_id, repo_id, parameters)
            elif job_type == "pr_analysis":
                await JobEventHandler._process_pr_analysis(job_id, repo_id, parameters)
            else:
                logger.warning(f"Unknown job type: {job_type}")
                
                # Publish job failed event
                event_bus.publish(Event(
                    EventType.JOB_FAILED,
                    {
                        "job_id": job_id,
                        "repo_id": repo_id,
                        "job_type": job_type,
                        "error": f"Unknown job type: {job_type}"
                    }
                ))
        except Exception as e:
            logger.error(f"Error processing job {job_id}: {e}")
            
            # Publish job failed event
            event_bus.publish(Event(
                EventType.JOB_FAILED,
                {
                    "job_id": job_id,
                    "repo_id": repo_id,
                    "job_type": job_type,
                    "error": str(e)
                }
            ))
    
    @staticmethod
    async def _process_snapshot_analysis(job_id: int, repo_id: int, parameters: Dict[str, Any]) -> None:
        """
        Process a snapshot analysis job.
        
        Args:
            job_id: The job ID
            repo_id: The repository ID
            parameters: The job parameters
        """
        snapshot_id = parameters.get('snapshot_id')
        if not snapshot_id:
            raise ValueError("Snapshot ID is required for snapshot analysis")
        
        with db_manager.session_scope() as session:
            snapshot_repo = SnapshotRepository(session)
            snapshot = snapshot_repo.get_by_snapshot_id(snapshot_id)
            
            if not snapshot:
                raise ValueError(f"Snapshot not found: {snapshot_id}")
            
            # Create a snapshot manager
            snapshot_manager = EnhancedSnapshotManager(session)
            
            # Load the codebase from the snapshot
            codebase = snapshot_manager.load_codebase_from_snapshot(snapshot)
            
            # Create a code analyzer
            analyzer = CodeAnalyzer(codebase)
            
            # Analyze the codebase
            analysis_result = analyzer.analyze()
            
            # Store the analysis result
            result_repo = AnalysisResultRepository(session)
            result = result_repo.create(
                repo_id=repo_id,
                snapshot_id=snapshot.id,
                analysis_type="snapshot_analysis",
                summary=analysis_result.get('summary'),
                metrics=analysis_result.get('metrics')
            )
            
            # Store issues
            issue_repo = AnalysisIssueRepository(session)
            for issue_data in analysis_result.get('issues', []):
                issue_repo.create(
                    analysis_result_id=result.id,
                    issue_type=issue_data.get('type'),
                    severity=issue_data.get('severity'),
                    message=issue_data.get('message'),
                    file_path=issue_data.get('file_path'),
                    line_number=issue_data.get('line_number'),
                    code_snippet=issue_data.get('code_snippet'),
                    suggestion=issue_data.get('suggestion')
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
    
    @staticmethod
    async def _process_commit_analysis(job_id: int, repo_id: int, parameters: Dict[str, Any]) -> None:
        """
        Process a commit analysis job.
        
        Args:
            job_id: The job ID
            repo_id: The repository ID
            parameters: The job parameters
        """
        commit_sha = parameters.get('commit_sha')
        base_commit_sha = parameters.get('base_commit_sha')
        
        if not commit_sha:
            raise ValueError("Commit SHA is required for commit analysis")
        
        with db_manager.session_scope() as session:
            repo_repo = RepositoryRepository(session)
            repository = repo_repo.get_by_id(repo_id)
            
            if not repository:
                raise ValueError(f"Repository not found: {repo_id}")
            
            # Create a snapshot manager
            snapshot_manager = EnhancedSnapshotManager(session)
            
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
                # Use the parent commit as the base
                # This would require additional Git operations to find the parent
                # For simplicity, we'll use the latest snapshot before this commit
                snapshot_repo = SnapshotRepository(session)
                base_snapshot = snapshot_repo.get_latest_for_repo(repo_id)
            
            if not base_snapshot:
                raise ValueError("Base snapshot not found for comparison")
            
            # Load the codebases from the snapshots
            commit_codebase = snapshot_manager.load_codebase_from_snapshot(commit_snapshot)
            base_codebase = snapshot_manager.load_codebase_from_snapshot(base_snapshot)
            
            # Create a commit analyzer
            from codegen_on_oss.analysis.commit_analyzer import CommitAnalyzer
            analyzer = CommitAnalyzer(
                original_codebase=base_codebase,
                commit_codebase=commit_codebase
            )
            
            # Analyze the commit
            analysis_result = analyzer.analyze_commit()
            
            # Store the analysis result
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
    
    @staticmethod
    async def _process_pr_analysis(job_id: int, repo_id: int, parameters: Dict[str, Any]) -> None:
        """
        Process a PR analysis job.
        
        Args:
            job_id: The job ID
            repo_id: The repository ID
            parameters: The job parameters
        """
        pr_number = parameters.get('pr_number')
        
        if not pr_number:
            raise ValueError("PR number is required for PR analysis")
        
        with db_manager.session_scope() as session:
            repo_repo = RepositoryRepository(session)
            repository = repo_repo.get_by_id(repo_id)
            
            if not repository:
                raise ValueError(f"Repository not found: {repo_id}")
            
            # This would require GitHub API integration to fetch PR details
            # For simplicity, we'll assume the PR head and base are provided
            pr_head_sha = parameters.get('pr_head_sha')
            pr_base_sha = parameters.get('pr_base_sha')
            
            if not pr_head_sha or not pr_base_sha:
                raise ValueError("PR head and base SHAs are required")
            
            # Create a snapshot manager
            snapshot_manager = EnhancedSnapshotManager(session)
            
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
            from codegen_on_oss.analysis.commit_analyzer import CommitAnalyzer
            analyzer = CommitAnalyzer(
                original_codebase=base_codebase,
                commit_codebase=head_codebase
            )
            
            # Analyze the PR
            analysis_result = analyzer.analyze_commit()
            
            # Store the analysis result
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
    
    @staticmethod
    @subscribe(EventType.JOB_COMPLETED)
    def handle_job_completed(payload: Dict[str, Any]) -> None:
        """
        Handle the job completed event.
        
        Args:
            payload: The event payload
        """
        logger.info(f"Job completed: {payload.get('job_type')} for repo {payload.get('repo_id')}")
        
        with db_manager.session_scope() as session:
            job_repo = AnalysisJobRepository(session)
            job_id = payload.get('job_id')
            result_id = payload.get('result_id')
            
            if job_id:
                job_repo.update(
                    job_id,
                    status="completed",
                    completed_at=datetime.now(),
                    result_id=result_id
                )
    
    @staticmethod
    @subscribe(EventType.JOB_FAILED)
    def handle_job_failed(payload: Dict[str, Any]) -> None:
        """
        Handle the job failed event.
        
        Args:
            payload: The event payload
        """
        logger.error(f"Job failed: {payload.get('job_type')} for repo {payload.get('repo_id')}")
        logger.error(f"Error: {payload.get('error')}")
        
        with db_manager.session_scope() as session:
            job_repo = AnalysisJobRepository(session)
            job_id = payload.get('job_id')
            
            if job_id:
                job_repo.update(
                    job_id,
                    status="failed",
                    completed_at=datetime.now(),
                    error_message=payload.get('error')
                )

class WebhookEventHandler:
    """
    Handler for webhook-related events.
    
    This class provides methods for handling events related to webhooks,
    such as webhook triggering and failure.
    """
    
    @staticmethod
    @subscribe(EventType.WEBHOOK_TRIGGERED)
    async def handle_webhook_triggered(payload: Dict[str, Any]) -> None:
        """
        Handle the webhook triggered event.
        
        Args:
            payload: The event payload
        """
        logger.info(f"Webhook triggered: {payload.get('webhook_id')} to {payload.get('url')}")
        
        webhook_id = payload.get('webhook_id')
        url = payload.get('url')
        webhook_payload = payload.get('payload')
        
        if not url or not webhook_payload:
            logger.error("Missing URL or payload for webhook")
            return
        
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=webhook_payload) as response:
                    if response.status >= 400:
                        error_text = await response.text()
                        logger.error(f"Webhook request failed: {response.status} - {error_text}")
                        
                        # Publish webhook failed event
                        event_bus.publish(Event(
                            EventType.WEBHOOK_FAILED,
                            {
                                "webhook_id": webhook_id,
                                "url": url,
                                "status_code": response.status,
                                "error": error_text
                            }
                        ))
                    else:
                        logger.info(f"Webhook request succeeded: {response.status}")
                        
                        # Update last triggered timestamp
                        with db_manager.session_scope() as session:
                            webhook_repo = WebhookConfigRepository(session)
                            if webhook_id:
                                webhook_repo.update(
                                    webhook_id,
                                    last_triggered=datetime.now()
                                )
        except Exception as e:
            logger.error(f"Error sending webhook request: {e}")
            
            # Publish webhook failed event
            event_bus.publish(Event(
                EventType.WEBHOOK_FAILED,
                {
                    "webhook_id": webhook_id,
                    "url": url,
                    "error": str(e)
                }
            ))
    
    @staticmethod
    @subscribe(EventType.WEBHOOK_FAILED)
    def handle_webhook_failed(payload: Dict[str, Any]) -> None:
        """
        Handle the webhook failed event.
        
        Args:
            payload: The event payload
        """
        logger.error(f"Webhook failed: {payload.get('webhook_id')} to {payload.get('url')}")
        logger.error(f"Error: {payload.get('error')}")
        
        # Could implement retry logic here
"""

