"""
Parallel Agent Execution Engine

This module provides capabilities for executing multiple codegen agents in parallel,
managing their lifecycle, and coordinating their execution within pipeline stages.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, Set
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

from codegen.agents.agent import Agent, AgentTask
from .schemas import (
    TaskExecution, ExecutionStatus, AgentTaskConfig, 
    ResourceLimits, PipelineContext
)


logger = logging.getLogger(__name__)


@dataclass
class ParallelExecutionConfig:
    """Configuration for parallel agent execution."""
    max_concurrent_agents: int = 5
    agent_timeout: Optional[int] = 3600  # 1 hour default
    resource_limits: Optional[ResourceLimits] = None
    retry_attempts: int = 3
    retry_delay: int = 10
    heartbeat_interval: int = 30  # seconds
    

class AgentExecutionContext:
    """Context for individual agent execution."""
    
    def __init__(self, task_id: str, agent_config: AgentTaskConfig, context: PipelineContext):
        self.task_id = task_id
        self.agent_config = agent_config
        self.context = context
        self.agent: Optional[Agent] = None
        self.agent_task: Optional[AgentTask] = None
        self.execution: TaskExecution = TaskExecution(
            id=task_id,
            stage_id=context.get("stage_id", "unknown"),
            pipeline_id=context.get("pipeline_id", "unknown"),
            status=ExecutionStatus.PENDING
        )
        self.callbacks: List[Callable] = []
        self.started_at: Optional[datetime] = None
        
    def add_callback(self, callback: Callable[[TaskExecution], None]):
        """Add a callback to be called when execution completes."""
        self.callbacks.append(callback)
        
    async def execute_callbacks(self):
        """Execute all registered callbacks."""
        for callback in self.callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(self.execution)
                else:
                    callback(self.execution)
            except Exception as e:
                logger.error(f"Callback execution failed for task {self.task_id}: {e}")


class ParallelAgentExecutor:
    """
    Manages parallel execution of multiple codegen agents with resource management,
    monitoring, and webhook callback support.
    """
    
    def __init__(self, config: ParallelExecutionConfig):
        self.config = config
        self.active_executions: Dict[str, AgentExecutionContext] = {}
        self.executor = ThreadPoolExecutor(max_workers=config.max_concurrent_agents)
        self.completion_callbacks: List[Callable] = []
        self._shutdown = False
        self._monitor_task: Optional[asyncio.Task] = None
        
    async def start_monitoring(self):
        """Start background monitoring of agent executions."""
        if self._monitor_task is None:
            self._monitor_task = asyncio.create_task(self._monitor_executions())
            
    async def stop_monitoring(self):
        """Stop background monitoring."""
        if self._monitor_task:
            self._shutdown = True
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None
            
    def add_completion_callback(self, callback: Callable[[TaskExecution], None]):
        """Add global completion callback for all executions."""
        self.completion_callbacks.append(callback)
        
    async def execute_agent_task(
        self, 
        agent_config: AgentTaskConfig, 
        context: PipelineContext,
        task_id: Optional[str] = None
    ) -> TaskExecution:
        """
        Execute a single agent task asynchronously.
        
        Args:
            agent_config: Configuration for the agent task
            context: Pipeline execution context
            task_id: Optional task ID (generates UUID if not provided)
            
        Returns:
            TaskExecution object with results
        """
        if task_id is None:
            task_id = str(uuid.uuid4())
            
        execution_context = AgentExecutionContext(task_id, agent_config, context)
        self.active_executions[task_id] = execution_context
        
        # Add global completion callbacks
        for callback in self.completion_callbacks:
            execution_context.add_callback(callback)
            
        try:
            # Execute in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            execution = await loop.run_in_executor(
                self.executor,
                self._execute_single_agent,
                execution_context
            )
            
            await execution_context.execute_callbacks()
            return execution
            
        except Exception as e:
            logger.error(f"Agent execution failed for task {task_id}: {e}")
            execution_context.execution.status = ExecutionStatus.FAILED
            execution_context.execution.error_message = str(e)
            execution_context.execution.completed_at = datetime.now()
            
            await execution_context.execute_callbacks()
            return execution_context.execution
            
        finally:
            # Clean up
            self.active_executions.pop(task_id, None)
            
    async def execute_parallel_agents(
        self,
        agent_configs: List[AgentTaskConfig],
        context: PipelineContext,
        wait_for_all: bool = True
    ) -> List[TaskExecution]:
        """
        Execute multiple agents in parallel.
        
        Args:
            agent_configs: List of agent configurations to execute
            context: Shared pipeline context
            wait_for_all: Whether to wait for all agents to complete
            
        Returns:
            List of TaskExecution results
        """
        if not agent_configs:
            return []
            
        logger.info(f"Starting parallel execution of {len(agent_configs)} agents")
        
        # Create tasks for all agent executions
        tasks = []
        for i, config in enumerate(agent_configs):
            task_id = f"{context.get('stage_id', 'unknown')}_agent_{i}"
            task = asyncio.create_task(
                self.execute_agent_task(config, context, task_id)
            )
            tasks.append(task)
            
        if wait_for_all:
            # Wait for all tasks to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Convert exceptions to failed executions
            executions = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    execution = TaskExecution(
                        id=f"failed_{i}",
                        stage_id=context.get("stage_id", "unknown"),
                        pipeline_id=context.get("pipeline_id", "unknown"),
                        status=ExecutionStatus.FAILED,
                        error_message=str(result),
                        completed_at=datetime.now()
                    )
                    executions.append(execution)
                else:
                    executions.append(result)
                    
            return executions
        else:
            # Return immediately with task futures
            return [await task for task in tasks]
            
    def _execute_single_agent(self, execution_context: AgentExecutionContext) -> TaskExecution:
        """
        Execute a single agent in a thread (blocking operation).
        
        This method runs in the thread pool executor to avoid blocking the async loop.
        """
        execution = execution_context.execution
        config = execution_context.agent_config
        
        try:
            execution.status = ExecutionStatus.RUNNING
            execution.started_at = datetime.now()
            execution_context.started_at = execution.started_at
            
            logger.info(f"Starting agent execution for task {execution.id}")
            
            # Initialize agent
            agent = Agent(
                token=config.api_token,
                org_id=config.org_id,
                base_url=config.base_url
            )
            execution_context.agent = agent
            
            # Execute agent task
            agent_task = agent.run(config.prompt)
            execution_context.agent_task = agent_task
            execution.agent_run_id = agent_task.id
            execution.agent_web_url = agent_task.web_url
            
            # Poll for completion with timeout
            timeout = config.timeout or self.config.agent_timeout
            start_time = datetime.now()
            
            while agent_task.status not in ["completed", "failed", "cancelled"]:
                if timeout and (datetime.now() - start_time).total_seconds() > timeout:
                    execution.status = ExecutionStatus.FAILED
                    execution.error_message = f"Agent execution timeout after {timeout} seconds"
                    break
                    
                # Refresh task status
                agent_task.refresh()
                asyncio.sleep(5)  # Poll every 5 seconds
                
            # Set final status and results
            if agent_task.status == "completed":
                execution.status = ExecutionStatus.SUCCESS
                execution.result = agent_task.result
            elif agent_task.status == "failed":
                execution.status = ExecutionStatus.FAILED
                execution.error_message = "Agent task failed"
            else:
                execution.status = ExecutionStatus.CANCELLED
                
            execution.completed_at = datetime.now()
            execution.duration_seconds = (
                execution.completed_at - execution.started_at
            ).total_seconds()
            
            logger.info(
                f"Agent execution completed for task {execution.id}: "
                f"{execution.status} in {execution.duration_seconds:.2f}s"
            )
            
        except Exception as e:
            logger.error(f"Agent execution failed for task {execution.id}: {e}")
            execution.status = ExecutionStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.now()
            if execution.started_at:
                execution.duration_seconds = (
                    execution.completed_at - execution.started_at
                ).total_seconds()
                
        return execution
        
    async def _monitor_executions(self):
        """
        Background task to monitor active executions and handle timeouts.
        """
        while not self._shutdown:
            try:
                current_time = datetime.now()
                
                for task_id, context in list(self.active_executions.items()):
                    if context.started_at is None:
                        continue
                        
                    # Check for timeout
                    timeout = (
                        context.agent_config.timeout or 
                        self.config.agent_timeout
                    )
                    if timeout:
                        elapsed = (current_time - context.started_at).total_seconds()
                        if elapsed > timeout:
                            logger.warning(f"Task {task_id} timeout after {elapsed}s")
                            context.execution.status = ExecutionStatus.FAILED
                            context.execution.error_message = f"Timeout after {elapsed}s"
                            
                    # Send heartbeat for running tasks
                    if context.execution.status == ExecutionStatus.RUNNING:
                        logger.debug(f"Heartbeat for task {task_id}")
                        
                await asyncio.sleep(self.config.heartbeat_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitor execution error: {e}")
                await asyncio.sleep(self.config.heartbeat_interval)
                
    def get_active_executions(self) -> Dict[str, TaskExecution]:
        """Get status of all active executions."""
        return {
            task_id: context.execution 
            for task_id, context in self.active_executions.items()
        }
        
    async def cancel_execution(self, task_id: str) -> bool:
        """
        Cancel an active execution.
        
        Args:
            task_id: ID of the task to cancel
            
        Returns:
            True if cancelled successfully
        """
        context = self.active_executions.get(task_id)
        if not context:
            return False
            
        context.execution.status = ExecutionStatus.CANCELLED
        context.execution.completed_at = datetime.now()
        
        if context.started_at:
            context.execution.duration_seconds = (
                context.execution.completed_at - context.started_at
            ).total_seconds()
            
        logger.info(f"Cancelled execution for task {task_id}")
        await context.execute_callbacks()
        return True
        
    async def shutdown(self):
        """Shutdown the executor gracefully."""
        logger.info("Shutting down parallel agent executor")
        
        await self.stop_monitoring()
        
        # Cancel all active executions
        for task_id in list(self.active_executions.keys()):
            await self.cancel_execution(task_id)
            
        # Shutdown thread pool
        self.executor.shutdown(wait=True)
        
    def get_resource_usage(self) -> Dict[str, Any]:
        """Get current resource usage statistics."""
        return {
            "active_executions": len(self.active_executions),
            "max_concurrent": self.config.max_concurrent_agents,
            "thread_pool_size": self.executor._max_workers,
            "executions": {
                task_id: {
                    "status": context.execution.status,
                    "duration": (
                        datetime.now() - context.started_at
                    ).total_seconds() if context.started_at else 0
                }
                for task_id, context in self.active_executions.items()
            }
        }