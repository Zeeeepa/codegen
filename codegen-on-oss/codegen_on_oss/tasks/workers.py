"""
Worker functions for the task queue.

This module provides worker functions that are executed by the task queue
to perform long-running analyses in the background.
"""

import logging
import asyncio
from typing import Dict, Any

from codegen_on_oss.config import settings
from codegen_on_oss.database.connection import get_db_session
from codegen_on_oss.snapshot.snapshot_service import SnapshotService
from codegen_on_oss.storage.service import StorageService
from codegen_on_oss.analysis.analysis_service import AnalysisService
from codegen_on_oss.tasks.queue import task_queue

logger = logging.getLogger(__name__)


def perform_analysis(
    repo_url: str,
    commit_sha: str = None,
    branch: str = None,
    analysis_types: list = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Perform analysis on a repository.
    
    This function is executed by the task queue worker.
    
    Args:
        repo_url: URL of the repository to analyze
        commit_sha: Optional commit SHA to analyze
        branch: Optional branch name
        analysis_types: Optional list of analysis types to perform
        
    Returns:
        Dict[str, Any]: Analysis results
    """
    logger.info(f"Starting analysis of {repo_url} (commit: {commit_sha}, branch: {branch})")
    
    # Get the current job ID
    import rq
    job = rq.get_current_job()
    job_id = job.id if job else None
    
    # Create event loop for async functions
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Update progress
        if job_id:
            loop.run_until_complete(
                task_queue.update_job_progress(
                    job_id, 
                    10, 
                    {"status": "initializing"}
                )
            )
        
        # Create services
        with get_db_session() as db_session:
            storage_service = StorageService()
            snapshot_service = SnapshotService(db_session, storage_service)
            analysis_service = AnalysisService(db_session, snapshot_service)
            
            # Update progress
            if job_id:
                loop.run_until_complete(
                    task_queue.update_job_progress(
                        job_id, 
                        20, 
                        {"status": "creating_snapshot"}
                    )
                )
            
            # Create snapshot
            snapshot = loop.run_until_complete(
                snapshot_service.create_snapshot(
                    repo_url=repo_url,
                    commit_sha=commit_sha,
                    branch=branch
                )
            )
            
            # Update progress
            if job_id:
                loop.run_until_complete(
                    task_queue.update_job_progress(
                        job_id, 
                        30, 
                        {
                            "status": "snapshot_created",
                            "snapshot_id": str(snapshot.id)
                        }
                    )
                )
            
            # Perform analyses
            results = {}
            analysis_types = analysis_types or settings.default_analysis_types
            
            if "code_quality" in analysis_types:
                if job_id:
                    loop.run_until_complete(
                        task_queue.update_job_progress(
                            job_id, 
                            40, 
                            {"status": "analyzing_code_quality"}
                        )
                    )
                
                results["code_quality"] = loop.run_until_complete(
                    analysis_service.analyze_code_quality(snapshot.id)
                )
            
            if "dependencies" in analysis_types:
                if job_id:
                    loop.run_until_complete(
                        task_queue.update_job_progress(
                            job_id, 
                            60, 
                            {"status": "analyzing_dependencies"}
                        )
                    )
                
                results["dependencies"] = loop.run_until_complete(
                    analysis_service.analyze_dependencies(snapshot.id)
                )
            
            if "security" in analysis_types:
                if job_id:
                    loop.run_until_complete(
                        task_queue.update_job_progress(
                            job_id, 
                            80, 
                            {"status": "analyzing_security"}
                        )
                    )
                
                results["security"] = loop.run_until_complete(
                    analysis_service.analyze_security(snapshot.id)
                )
            
            if "file_analysis" in analysis_types:
                if job_id:
                    loop.run_until_complete(
                        task_queue.update_job_progress(
                            job_id, 
                            90, 
                            {"status": "analyzing_files"}
                        )
                    )
                
                results["file_analysis"] = loop.run_until_complete(
                    analysis_service.analyze_files(snapshot.id)
                )
            
            # Update progress
            if job_id:
                loop.run_until_complete(
                    task_queue.update_job_progress(
                        job_id, 
                        100, 
                        {"status": "completed"}
                    )
                )
            
            logger.info(f"Analysis of {repo_url} completed successfully")
            
            return {
                "snapshot_id": str(snapshot.id),
                "repository": repo_url,
                "commit_sha": commit_sha,
                "branch": branch,
                "analysis_types": analysis_types,
                "results": results
            }
    
    except Exception as e:
        logger.exception(f"Error performing analysis: {str(e)}")
        
        # Update progress
        if job_id:
            loop.run_until_complete(
                task_queue.update_job_progress(
                    job_id, 
                    100, 
                    {
                        "status": "failed",
                        "error": str(e)
                    }
                )
            )
        
        raise
    
    finally:
        loop.close()

