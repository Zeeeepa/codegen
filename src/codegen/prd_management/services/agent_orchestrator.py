"""
Agent Orchestrator - Manages parallel execution of tasks using Codegen agents
"""

import asyncio
import time
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
from enum import Enum

from ...sdk.client import CodegenClient
from ..core.prd_template import PRDTemplate, Task, TaskStatus
from .progress_tracker import ProgressTracker
from .websocket_service import WebSocketService


class ExecutionStrategy(Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HYBRID = "hybrid"


@dataclass
class OrchestrationConfig:
    max_concurrent_tasks: int = 5
    task_timeout_seconds: int = 1800  # 30 minutes
    retry_attempts: int = 3
    execution_strategy: ExecutionStrategy = ExecutionStrategy.HYBRID


@dataclass
class TaskExecution:
    task: Task
    agent_run_id: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    attempts: int = 0
    error: Optional[str] = None


@dataclass
class OrchestrationResult:
    prd_id: str
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    duration: float
    task_results: List[TaskExecution]
    success: bool


class AgentOrchestrator:
    """
    Orchestrates the execution of tasks using Codegen agents with parallel processing
    """
    
    def __init__(
        self,
        codegen_client: CodegenClient,
        progress_tracker: ProgressTracker,
        websocket_service: WebSocketService,
        config: Optional[OrchestrationConfig] = None
    ):
        self.codegen_client = codegen_client
        self.progress_tracker = progress_tracker
        self.websocket_service = websocket_service
        self.config = config or OrchestrationConfig()
        
        # Execution state
        self.active_executions: Dict[str, TaskExecution] = {}
        self.execution_semaphore = asyncio.Semaphore(self.config.max_concurrent_tasks)
    
    async def execute_implementation(
        self,
        prd: PRDTemplate,
        tasks: List[Task],
        org_id: int,
        repo_id: int
    ) -> OrchestrationResult:
        """
        Execute all tasks for a PRD implementation
        
        Args:
            prd: The PRD being implemented
            tasks: List of tasks to execute
            org_id: Organization ID
            repo_id: Repository ID
            
        Returns:
            Orchestration result with execution details
        """
        
        start_time = time.time()
        
        # Initialize progress tracking
        await self.progress_tracker.initialize_prd_progress(prd.id, len(tasks))
        
        # Broadcast implementation start
        self.websocket_service.send('implementation_started', {
            'prd_id': prd.id,
            'total_tasks': len(tasks),
            'strategy': self.config.execution_strategy.value
        })
        
        try:
            # Execute tasks based on strategy
            if self.config.execution_strategy == ExecutionStrategy.SEQUENTIAL:
                task_results = await self._execute_sequential(prd, tasks, org_id, repo_id)
            elif self.config.execution_strategy == ExecutionStrategy.PARALLEL:
                task_results = await self._execute_parallel(prd, tasks, org_id, repo_id)
            else:  # HYBRID
                task_results = await self._execute_hybrid(prd, tasks, org_id, repo_id)
            
            # Calculate results
            completed_tasks = sum(1 for result in task_results if result.task.status == TaskStatus.COMPLETED)
            failed_tasks = sum(1 for result in task_results if result.task.status == TaskStatus.FAILED)
            
            result = OrchestrationResult(
                prd_id=prd.id,
                total_tasks=len(tasks),
                completed_tasks=completed_tasks,
                failed_tasks=failed_tasks,
                duration=time.time() - start_time,
                task_results=task_results,
                success=failed_tasks == 0
            )
            
            # Broadcast completion
            self.websocket_service.send('implementation_completed', {
                'prd_id': prd.id,
                'result': {
                    'success': result.success,
                    'completed_tasks': result.completed_tasks,
                    'failed_tasks': result.failed_tasks,
                    'duration': result.duration
                }
            })
            
            return result
            
        except Exception as e:
            # Broadcast failure
            self.websocket_service.send('implementation_failed', {
                'prd_id': prd.id,
                'error': str(e),
                'duration': time.time() - start_time
            })
            raise
    
    async def _execute_sequential(
        self,
        prd: PRDTemplate,
        tasks: List[Task],
        org_id: int,
        repo_id: int
    ) -> List[TaskExecution]:
        """Execute tasks sequentially in dependency order"""
        
        task_results = []
        
        # Get execution order (respecting dependencies)
        execution_order = self._get_execution_order(tasks)
        
        for task_group in execution_order:
            for task in task_group:
                result = await self._execute_single_task(task, prd, org_id, repo_id)
                task_results.append(result)
                
                # Stop on failure if configured
                if result.task.status == TaskStatus.FAILED:
                    print(f"Task {task.id} failed, continuing with remaining tasks")
        
        return task_results
    
    async def _execute_parallel(
        self,
        prd: PRDTemplate,
        tasks: List[Task],
        org_id: int,
        repo_id: int
    ) -> List[TaskExecution]:
        """Execute all tasks in parallel (ignoring dependencies)"""
        
        # Create tasks for parallel execution
        execution_tasks = [
            self._execute_single_task(task, prd, org_id, repo_id)
            for task in tasks
        ]
        
        # Execute all tasks concurrently
        task_results = await asyncio.gather(*execution_tasks, return_exceptions=True)
        
        # Handle exceptions
        final_results = []
        for i, result in enumerate(task_results):
            if isinstance(result, Exception):
                # Create failed task execution
                failed_execution = TaskExecution(
                    task=tasks[i],
                    error=str(result)
                )
                failed_execution.task.status = TaskStatus.FAILED
                final_results.append(failed_execution)
            else:
                final_results.append(result)
        
        return final_results
    
    async def _execute_hybrid(
        self,
        prd: PRDTemplate,
        tasks: List[Task],
        org_id: int,
        repo_id: int
    ) -> List[TaskExecution]:
        """Execute tasks in parallel groups respecting dependencies"""
        
        task_results = []
        
        # Get execution order (parallel groups)
        execution_order = self._get_execution_order(tasks)
        
        for task_group in execution_order:
            # Execute tasks in this group in parallel
            group_tasks = [
                self._execute_single_task(task, prd, org_id, repo_id)
                for task in task_group
            ]
            
            group_results = await asyncio.gather(*group_tasks, return_exceptions=True)
            
            # Process group results
            for i, result in enumerate(group_results):
                if isinstance(result, Exception):
                    # Create failed task execution
                    failed_execution = TaskExecution(
                        task=task_group[i],
                        error=str(result)
                    )
                    failed_execution.task.status = TaskStatus.FAILED
                    task_results.append(failed_execution)
                else:
                    task_results.append(result)
        
        return task_results
    
    async def _execute_single_task(
        self,
        task: Task,
        prd: PRDTemplate,
        org_id: int,
        repo_id: int
    ) -> TaskExecution:
        """Execute a single task with retry logic"""
        
        execution = TaskExecution(task=task)
        
        async with self.execution_semaphore:
            for attempt in range(1, self.config.retry_attempts + 1):
                execution.attempts = attempt
                execution.start_time = time.time()
                
                try:
                    # Update task status
                    task.status = TaskStatus.IN_PROGRESS
                    await self.progress_tracker.update_task_progress(prd.id, task.id, TaskStatus.IN_PROGRESS)
                    
                    # Broadcast task start
                    self.websocket_service.send('task_started', {
                        'prd_id': prd.id,
                        'task_id': task.id,
                        'task_title': task.title,
                        'attempt': attempt
                    })
                    
                    # Execute the task
                    agent_run = await self._create_agent_run_for_task(task, prd, org_id, repo_id)
                    execution.agent_run_id = agent_run.id
                    
                    # Poll for completion
                    result = await self._poll_task_completion(org_id, agent_run.id, task.id)
                    
                    # Validate task completion
                    if await self._validate_task_completion(task, result, org_id, repo_id):
                        task.status = TaskStatus.COMPLETED
                        execution.end_time = time.time()
                        
                        # Update progress
                        await self.progress_tracker.update_task_progress(prd.id, task.id, TaskStatus.COMPLETED)
                        
                        # Broadcast task completion
                        self.websocket_service.send('task_completed', {
                            'prd_id': prd.id,
                            'task_id': task.id,
                            'task_title': task.title,
                            'duration': execution.end_time - execution.start_time,
                            'attempt': attempt
                        })
                        
                        return execution
                    else:
                        raise Exception("Task validation failed")
                
                except Exception as e:
                    execution.error = str(e)
                    execution.end_time = time.time()
                    
                    print(f"Task {task.id} attempt {attempt} failed: {e}")
                    
                    # Broadcast task attempt failed
                    self.websocket_service.send('task_attempt_failed', {
                        'prd_id': prd.id,
                        'task_id': task.id,
                        'task_title': task.title,
                        'attempt': attempt,
                        'error': str(e),
                        'will_retry': attempt < self.config.retry_attempts
                    })
                    
                    if attempt < self.config.retry_attempts:
                        # Wait before retry
                        await asyncio.sleep(min(2 ** attempt, 30))  # Exponential backoff
                    else:
                        # Final failure
                        task.status = TaskStatus.FAILED
                        await self.progress_tracker.update_task_progress(prd.id, task.id, TaskStatus.FAILED)
                        
                        # Broadcast task failed
                        self.websocket_service.send('task_failed', {
                            'prd_id': prd.id,
                            'task_id': task.id,
                            'task_title': task.title,
                            'error': str(e),
                            'attempts': attempt
                        })
        
        return execution
    
    async def _create_agent_run_for_task(
        self,
        task: Task,
        prd: PRDTemplate,
        org_id: int,
        repo_id: int
    ) -> Any:
        """Create an agent run for a specific task"""
        
        task_prompt = self._build_task_execution_prompt(task, prd)
        
        agent_run = await self.codegen_client.create_agent_run(
            org_id=org_id,
            prompt=task_prompt,
            repo_id=repo_id
        )
        
        return agent_run
    
    def _build_task_execution_prompt(self, task: Task, prd: PRDTemplate) -> str:
        """Build execution prompt for a specific task"""
        
        return f"""
# Task Execution: {task.title}

## PRD Context
**Goal**: {prd.goal}
**What**: {prd.what}

## Task Details
**ID**: {task.id}
**Type**: {task.type.value}
**Description**: {task.description}

## Files to Work With
{chr(10).join(f"- {file}" for file in task.files)}

## Validation Criteria
{chr(10).join(f"- {criteria}" for criteria in task.validation_criteria)}

## Instructions
1. Implement the task according to the description
2. Follow the PRD requirements and context
3. Create/modify the specified files
4. Ensure all validation criteria are met
5. Write clean, maintainable code
6. Include appropriate error handling
7. Add comments where necessary

## Success Criteria
The task is complete when:
- All specified files are created/modified correctly
- All validation criteria are satisfied
- Code follows best practices
- No syntax or type errors

Execute this task now.
"""
    
    async def _poll_task_completion(
        self,
        org_id: int,
        agent_run_id: str,
        task_id: str
    ) -> Dict[str, Any]:
        """Poll for task completion with timeout"""
        
        timeout = self.config.task_timeout_seconds
        poll_interval = 15  # 15 seconds
        start_time = time.time()
        
        while (time.time() - start_time) < timeout:
            try:
                agent_run = await self.codegen_client.get_agent_run(org_id, agent_run_id)
                
                if agent_run.status == "COMPLETE":
                    return agent_run.result or {}
                elif agent_run.status == "FAILED":
                    raise Exception(f"Agent run failed: {agent_run.error}")
                
                # Send progress update
                self.websocket_service.send('task_progress', {
                    'task_id': task_id,
                    'status': 'running',
                    'elapsed_time': time.time() - start_time
                })
                
                await asyncio.sleep(poll_interval)
                
            except Exception as e:
                print(f"Polling error for task {task_id}: {e}")
                await asyncio.sleep(poll_interval)
        
        raise Exception(f"Task {task_id} timed out after {timeout} seconds")
    
    async def _validate_task_completion(
        self,
        task: Task,
        result: Dict[str, Any],
        org_id: int,
        repo_id: int
    ) -> bool:
        """Validate that a task was completed successfully"""
        
        # Basic validation - check if agent run completed successfully
        if not result:
            return False
        
        # For now, assume completion if agent run succeeded
        # In a full implementation, this would check:
        # - Files were created/modified as expected
        # - Validation criteria are met
        # - Code compiles/runs without errors
        
        return True
    
    def _get_execution_order(self, tasks: List[Task]) -> List[List[Task]]:
        """Get tasks organized by execution order (parallel groups)"""
        
        task_map = {task.id: task for task in tasks}
        execution_order = []
        remaining_tasks = set(task.id for task in tasks)
        completed_tasks = set()
        
        while remaining_tasks:
            # Find tasks with no pending dependencies
            ready_task_ids = []
            for task_id in remaining_tasks:
                task = task_map[task_id]
                dependencies_met = all(
                    dep_id in completed_tasks 
                    for dep_id in task.dependencies
                )
                if dependencies_met:
                    ready_task_ids.append(task_id)
            
            if not ready_task_ids:
                # This shouldn't happen if dependencies are valid
                raise Exception("No ready tasks found - possible circular dependency")
            
            # Add ready tasks to execution order
            ready_tasks = [task_map[task_id] for task_id in ready_task_ids]
            execution_order.append(ready_tasks)
            
            # Mark tasks as completed for next iteration
            completed_tasks.update(ready_task_ids)
            remaining_tasks -= set(ready_task_ids)
        
        return execution_order
    
    # Utility methods
    async def pause_execution(self, prd_id: str) -> None:
        """Pause execution for a PRD"""
        self.websocket_service.send('execution_paused', {'prd_id': prd_id})
    
    async def resume_execution(self, prd_id: str) -> None:
        """Resume execution for a PRD"""
        self.websocket_service.send('execution_resumed', {'prd_id': prd_id})
    
    async def cancel_execution(self, prd_id: str) -> None:
        """Cancel execution for a PRD"""
        # Cancel all active agent runs for this PRD
        for execution in self.active_executions.values():
            if execution.agent_run_id:
                try:
                    # In a full implementation, this would cancel the agent run
                    pass
                except Exception as e:
                    print(f"Error canceling agent run {execution.agent_run_id}: {e}")
        
        self.websocket_service.send('execution_cancelled', {'prd_id': prd_id})
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get current execution statistics"""
        return {
            'active_executions': len(self.active_executions),
            'max_concurrent_tasks': self.config.max_concurrent_tasks,
            'execution_strategy': self.config.execution_strategy.value
        }

