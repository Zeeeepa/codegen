"""
Core Orchestration Engine

This module provides the main orchestration engine that coordinates pipeline execution,
manages stage dependencies, handles parallel execution, and integrates with webhooks.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
import networkx as nx

from .schemas import (
    PipelineDefinition, StageDefinition, TaskExecution, PipelineExecution,
    ExecutionStatus, TriggerType, StageType, AgentTaskConfig,
    PipelineContext, ExecutionResult
)
from .parallel_executor import ParallelAgentExecutor, ParallelExecutionConfig
from .webhooks import WebhookManager


logger = logging.getLogger(__name__)


@dataclass
class OrchestrationConfig:
    """Configuration for the orchestration engine."""
    max_concurrent_pipelines: int = 5
    max_concurrent_stages: int = 10
    default_stage_timeout: int = 3600  # 1 hour
    pipeline_timeout: int = 14400  # 4 hours
    cleanup_completed_after: int = 86400  # 1 day
    enable_webhooks: bool = True
    enable_real_time_updates: bool = True


class PipelineExecutionManager:
    """Manages the execution of a single pipeline."""
    
    def __init__(
        self, 
        pipeline_def: PipelineDefinition, 
        execution_id: str,
        trigger_type: TriggerType,
        trigger_data: Dict[str, Any],
        agent_executor: ParallelAgentExecutor,
        webhook_manager: Optional[WebhookManager] = None
    ):
        self.pipeline_def = pipeline_def
        self.execution_id = execution_id
        self.trigger_type = trigger_type
        self.trigger_data = trigger_data
        self.agent_executor = agent_executor
        self.webhook_manager = webhook_manager
        
        # Create pipeline execution record
        self.execution = PipelineExecution(
            id=execution_id,
            pipeline_id=pipeline_def.id,
            pipeline_definition=pipeline_def,
            status=ExecutionStatus.PENDING,
            triggered_by=trigger_type,
            trigger_data=trigger_data,
            total_stages=len(pipeline_def.stages),
            variables=dict(pipeline_def.global_variables)
        )
        
        # Build dependency graph
        self.dependency_graph = self._build_dependency_graph()
        self.completed_stages: Set[str] = set()
        self.failed_stages: Set[str] = set()
        self.running_stages: Set[str] = set()
        
    def _build_dependency_graph(self) -> nx.DiGraph:
        """Build directed graph of stage dependencies."""
        graph = nx.DiGraph()
        
        # Add all stages as nodes
        for stage in self.pipeline_def.stages:
            graph.add_node(stage.id, stage=stage)
            
        # Add dependency edges
        for stage in self.pipeline_def.stages:
            for dep_id in stage.depends_on:
                if dep_id in [s.id for s in self.pipeline_def.stages]:
                    graph.add_edge(dep_id, stage.id)
                    
        # Validate no cycles
        if not nx.is_directed_acyclic_graph(graph):
            raise ValueError("Pipeline contains circular dependencies")
            
        return graph
        
    async def execute(self) -> PipelineExecution:
        """Execute the complete pipeline."""
        logger.info(f"Starting pipeline execution: {self.execution_id}")
        
        self.execution.status = ExecutionStatus.RUNNING
        self.execution.started_at = datetime.now()
        
        try:
            # Execute stages in dependency order
            await self._execute_stages()
            
            # Determine final status
            if self.failed_stages and not any(
                stage.continue_on_failure 
                for stage in self.pipeline_def.stages 
                if stage.id in self.failed_stages
            ):
                self.execution.status = ExecutionStatus.FAILED
            else:
                self.execution.status = ExecutionStatus.SUCCESS
                
        except Exception as e:
            logger.error(f"Pipeline execution error: {e}")
            self.execution.status = ExecutionStatus.FAILED
            self.execution.logs.append(f"Pipeline execution failed: {str(e)}")
            
        finally:
            self.execution.completed_at = datetime.now()
            self.execution.duration_seconds = (
                self.execution.completed_at - self.execution.started_at
            ).total_seconds()
            
            # Update stage counts
            self.execution.completed_stages = len(self.completed_stages)
            self.execution.failed_stages = len(self.failed_stages)
            self.execution.skipped_stages = (
                self.execution.total_stages - 
                self.execution.completed_stages - 
                self.execution.failed_stages
            )
            
            logger.info(
                f"Pipeline execution completed: {self.execution_id} "
                f"({self.execution.status}) in {self.execution.duration_seconds:.2f}s"
            )
            
            # Send completion webhook
            if self.webhook_manager:
                await self.webhook_manager.send_pipeline_completion_webhook(self.execution)
                
        return self.execution
        
    async def _execute_stages(self):
        """Execute all pipeline stages in dependency order."""
        # Get stages in topological order
        stage_order = list(nx.topological_sort(self.dependency_graph))
        logger.info(f"Stage execution order: {stage_order}")
        
        # Execute stages with parallel support
        while self.completed_stages | self.failed_stages != set(stage_order):
            # Find stages ready to execute
            ready_stages = self._get_ready_stages()
            
            if not ready_stages:
                # Check if we're deadlocked
                remaining_stages = set(stage_order) - self.completed_stages - self.failed_stages
                if remaining_stages:
                    logger.error(f"Deadlock detected. Remaining stages: {remaining_stages}")
                    break
                else:
                    break  # All stages processed
                    
            # Execute ready stages (potentially in parallel)
            await self._execute_stage_batch(ready_stages)
            
    def _get_ready_stages(self) -> List[StageDefinition]:
        """Get stages that are ready to execute (dependencies satisfied)."""
        ready_stages = []
        
        for stage in self.pipeline_def.stages:
            if (
                stage.id not in self.completed_stages and
                stage.id not in self.failed_stages and
                stage.id not in self.running_stages and
                all(dep_id in self.completed_stages for dep_id in stage.depends_on)
            ):
                ready_stages.append(stage)
                
        return ready_stages
        
    async def _execute_stage_batch(self, stages: List[StageDefinition]):
        """Execute a batch of stages, potentially in parallel."""
        if not stages:
            return
            
        # Separate parallel and sequential stages
        parallel_stages = [s for s in stages if s.can_run_parallel]
        sequential_stages = [s for s in stages if not s.can_run_parallel]
        
        # Execute parallel stages concurrently
        if parallel_stages:
            tasks = []
            for stage in parallel_stages:
                self.running_stages.add(stage.id)
                task = asyncio.create_task(self._execute_single_stage(stage))
                tasks.append(task)
                
            # Wait for all parallel stages to complete
            await asyncio.gather(*tasks, return_exceptions=True)
            
        # Execute sequential stages one by one
        for stage in sequential_stages:
            self.running_stages.add(stage.id)
            await self._execute_single_stage(stage)
            
    async def _execute_single_stage(self, stage: StageDefinition) -> TaskExecution:
        """Execute a single pipeline stage."""
        logger.info(f"Executing stage: {stage.id} ({stage.stage_type})")
        
        # Create task execution record
        task_execution = TaskExecution(
            id=str(uuid.uuid4()),
            stage_id=stage.id,
            pipeline_id=self.pipeline_def.id,
            status=ExecutionStatus.RUNNING,
            started_at=datetime.now(),
            variables=dict(stage.variables)
        )
        
        # Add to pipeline execution
        self.execution.tasks[stage.id] = task_execution
        
        try:
            # Create execution context
            context: PipelineContext = {
                "pipeline_id": self.pipeline_def.id,
                "execution_id": self.execution_id,
                "stage_id": stage.id,
                "variables": {**self.execution.variables, **stage.variables},
                "trigger_data": self.trigger_data
            }
            
            # Execute based on stage type
            if stage.stage_type == StageType.AGENT_TASK and stage.agent_config:
                result = await self._execute_agent_stage(stage, task_execution, context)
            elif stage.stage_type == StageType.SHELL_COMMAND and stage.shell_config:
                result = await self._execute_shell_stage(stage, task_execution, context)
            elif stage.stage_type == StageType.DOCKER_RUN and stage.docker_config:
                result = await self._execute_docker_stage(stage, task_execution, context)
            elif stage.stage_type == StageType.PARALLEL_GROUP:
                result = await self._execute_parallel_group_stage(stage, task_execution, context)
            elif stage.stage_type == StageType.CONDITIONAL and stage.conditional_config:
                result = await self._execute_conditional_stage(stage, task_execution, context)
            else:
                raise ValueError(f"Unsupported stage type: {stage.stage_type}")
                
            # Handle successful execution
            task_execution.status = ExecutionStatus.SUCCESS
            task_execution.result = result
            self.completed_stages.add(stage.id)
            
        except Exception as e:
            logger.error(f"Stage {stage.id} execution failed: {e}")
            task_execution.status = ExecutionStatus.FAILED
            task_execution.error_message = str(e)
            
            if not stage.continue_on_failure:
                self.failed_stages.add(stage.id)
            else:
                self.completed_stages.add(stage.id)  # Continue despite failure
                
        finally:
            task_execution.completed_at = datetime.now()
            task_execution.duration_seconds = (
                task_execution.completed_at - task_execution.started_at
            ).total_seconds()
            
            self.running_stages.discard(stage.id)
            
            # Send task completion webhook
            if self.webhook_manager:
                await self.webhook_manager.send_task_completion_webhook(task_execution)
                
        return task_execution
        
    async def _execute_agent_stage(
        self, 
        stage: StageDefinition, 
        task_execution: TaskExecution, 
        context: PipelineContext
    ) -> Any:
        """Execute an agent-based stage."""
        if not stage.agent_config:
            raise ValueError(f"Agent config missing for stage {stage.id}")
            
        # Execute agent task
        agent_result = await self.agent_executor.execute_agent_task(
            agent_config=stage.agent_config,
            context=context,
            task_id=task_execution.id
        )
        
        # Update task execution with agent results
        task_execution.agent_run_id = agent_result.agent_run_id
        task_execution.agent_web_url = agent_result.agent_web_url
        task_execution.result = agent_result.result
        task_execution.output = agent_result.output
        
        if agent_result.status == ExecutionStatus.FAILED:
            raise Exception(agent_result.error_message or "Agent execution failed")
            
        return agent_result.result
        
    async def _execute_shell_stage(
        self, 
        stage: StageDefinition, 
        task_execution: TaskExecution, 
        context: PipelineContext
    ) -> Any:
        """Execute a shell command stage."""
        if not stage.shell_config:
            raise ValueError(f"Shell config missing for stage {stage.id}")
            
        # This would integrate with a shell execution system
        # For now, we'll simulate the execution
        logger.info(f"Executing shell command: {stage.shell_config.command}")
        
        # Simulate shell execution
        await asyncio.sleep(0.1)  # Simulate execution time
        
        return {"command": stage.shell_config.command, "exit_code": 0}
        
    async def _execute_docker_stage(
        self, 
        stage: StageDefinition, 
        task_execution: TaskExecution, 
        context: PipelineContext
    ) -> Any:
        """Execute a Docker container stage."""
        if not stage.docker_config:
            raise ValueError(f"Docker config missing for stage {stage.id}")
            
        # This would integrate with Docker execution
        logger.info(f"Running Docker container: {stage.docker_config.image}")
        
        # Simulate Docker execution
        await asyncio.sleep(0.1)
        
        return {"image": stage.docker_config.image, "exit_code": 0}
        
    async def _execute_parallel_group_stage(
        self, 
        stage: StageDefinition, 
        task_execution: TaskExecution, 
        context: PipelineContext
    ) -> Any:
        """Execute a parallel group of sub-stages."""
        # This would execute a group of stages in parallel
        logger.info(f"Executing parallel group: {stage.id}")
        
        # Simulate parallel execution
        await asyncio.sleep(0.1)
        
        return {"parallel_group": stage.id, "sub_stages": 0}
        
    async def _execute_conditional_stage(
        self, 
        stage: StageDefinition, 
        task_execution: TaskExecution, 
        context: PipelineContext
    ) -> Any:
        """Execute a conditional stage."""
        if not stage.conditional_config:
            raise ValueError(f"Conditional config missing for stage {stage.id}")
            
        # This would evaluate the condition and execute appropriate branch
        logger.info(f"Evaluating condition: {stage.conditional_config.condition}")
        
        # Simulate condition evaluation
        await asyncio.sleep(0.1)
        
        return {"condition": stage.conditional_config.condition, "result": True}


class OrchestrationEngine:
    """
    Main orchestration engine that manages pipeline execution, agent coordination,
    and webhook integration for the visual CI/CD system.
    """
    
    def __init__(self, config: OrchestrationConfig):
        self.config = config
        
        # Initialize components
        self.agent_executor = ParallelAgentExecutor(
            ParallelExecutionConfig(
                max_concurrent_agents=config.max_concurrent_stages
            )
        )
        
        self.webhook_manager = WebhookManager() if config.enable_webhooks else None
        
        # Pipeline management
        self.pipeline_definitions: Dict[str, PipelineDefinition] = {}
        self.active_executions: Dict[str, PipelineExecutionManager] = {}
        self.completed_executions: Dict[str, PipelineExecution] = {}
        
        # Background tasks
        self.cleanup_task: Optional[asyncio.Task] = None
        self._shutdown = False
        
    async def start(self):
        """Start the orchestration engine."""
        logger.info("Starting orchestration engine")
        
        # Start agent executor monitoring
        await self.agent_executor.start_monitoring()
        
        # Start webhook manager
        if self.webhook_manager:
            await self.webhook_manager.start()
            
        # Start cleanup task
        self.cleanup_task = asyncio.create_task(self._cleanup_completed_executions())
        
        logger.info("Orchestration engine started successfully")
        
    async def stop(self):
        """Stop the orchestration engine gracefully."""
        logger.info("Stopping orchestration engine")
        
        self._shutdown = True
        
        # Cancel all active executions
        for execution_id in list(self.active_executions.keys()):
            await self.cancel_pipeline_execution(execution_id)
            
        # Stop components
        await self.agent_executor.shutdown()
        
        if self.webhook_manager:
            await self.webhook_manager.stop()
            
        # Stop cleanup task
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
                
        logger.info("Orchestration engine stopped")
        
    def register_pipeline(self, pipeline_def: PipelineDefinition):
        """Register a pipeline definition."""
        self.pipeline_definitions[pipeline_def.id] = pipeline_def
        
        # Register webhook configurations
        if self.webhook_manager and pipeline_def.webhooks:
            for webhook_config in pipeline_def.webhooks:
                self.webhook_manager.register_webhook_config(
                    pipeline_def.id, webhook_config
                )
                
        logger.info(f"Registered pipeline: {pipeline_def.id}")
        
    async def execute_pipeline(
        self,
        pipeline_id: str,
        trigger_type: TriggerType = TriggerType.MANUAL,
        trigger_data: Optional[Dict[str, Any]] = None,
        execution_id: Optional[str] = None
    ) -> str:
        """
        Execute a pipeline.
        
        Args:
            pipeline_id: ID of the pipeline to execute
            trigger_type: Type of trigger that initiated the execution
            trigger_data: Additional data from the trigger
            execution_id: Optional custom execution ID
            
        Returns:
            Execution ID for tracking
        """
        if pipeline_id not in self.pipeline_definitions:
            raise ValueError(f"Pipeline not found: {pipeline_id}")
            
        if len(self.active_executions) >= self.config.max_concurrent_pipelines:
            raise RuntimeError("Maximum concurrent pipelines exceeded")
            
        pipeline_def = self.pipeline_definitions[pipeline_id]
        execution_id = execution_id or str(uuid.uuid4())
        trigger_data = trigger_data or {}
        
        logger.info(f"Starting pipeline execution: {pipeline_id} -> {execution_id}")
        
        # Create pipeline execution manager
        manager = PipelineExecutionManager(
            pipeline_def=pipeline_def,
            execution_id=execution_id,
            trigger_type=trigger_type,
            trigger_data=trigger_data,
            agent_executor=self.agent_executor,
            webhook_manager=self.webhook_manager
        )
        
        self.active_executions[execution_id] = manager
        
        # Execute asynchronously
        asyncio.create_task(self._execute_pipeline_async(execution_id))
        
        return execution_id
        
    async def _execute_pipeline_async(self, execution_id: str):
        """Execute pipeline asynchronously and handle completion."""
        try:
            manager = self.active_executions[execution_id]
            execution_result = await manager.execute()
            
            # Move to completed executions
            self.completed_executions[execution_id] = execution_result
            
        except Exception as e:
            logger.error(f"Pipeline execution {execution_id} failed: {e}")
            
        finally:
            # Clean up active execution
            self.active_executions.pop(execution_id, None)
            
    async def cancel_pipeline_execution(self, execution_id: str) -> bool:
        """Cancel an active pipeline execution."""
        manager = self.active_executions.get(execution_id)
        if not manager:
            return False
            
        # Update execution status
        manager.execution.status = ExecutionStatus.CANCELLED
        manager.execution.completed_at = datetime.now()
        
        # Cancel running agent tasks
        for stage_id in manager.running_stages:
            task_execution = manager.execution.tasks.get(stage_id)
            if task_execution and task_execution.agent_run_id:
                await self.agent_executor.cancel_execution(task_execution.id)
                
        logger.info(f"Cancelled pipeline execution: {execution_id}")
        return True
        
    def get_pipeline_status(self, execution_id: str) -> Optional[PipelineExecution]:
        """Get status of a pipeline execution."""
        # Check active executions
        manager = self.active_executions.get(execution_id)
        if manager:
            return manager.execution
            
        # Check completed executions
        return self.completed_executions.get(execution_id)
        
    def get_all_pipeline_statuses(self) -> Dict[str, PipelineExecution]:
        """Get status of all pipeline executions."""
        statuses = {}
        
        # Add active executions
        for execution_id, manager in self.active_executions.items():
            statuses[execution_id] = manager.execution
            
        # Add completed executions
        statuses.update(self.completed_executions)
        
        return statuses
        
    async def _cleanup_completed_executions(self):
        """Background task to clean up old completed executions."""
        while not self._shutdown:
            try:
                current_time = datetime.now()
                cutoff_time = current_time.replace(
                    microsecond=0
                ) - asyncio.get_event_loop().time() - self.config.cleanup_completed_after
                
                # Find executions to cleanup
                to_cleanup = []
                for execution_id, execution in self.completed_executions.items():
                    if (
                        execution.completed_at and 
                        execution.completed_at < cutoff_time
                    ):
                        to_cleanup.append(execution_id)
                        
                # Remove old executions
                for execution_id in to_cleanup:
                    self.completed_executions.pop(execution_id, None)
                    logger.info(f"Cleaned up old execution: {execution_id}")
                    
                await asyncio.sleep(3600)  # Run cleanup every hour
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup task error: {e}")
                await asyncio.sleep(3600)
                
    def get_engine_stats(self) -> Dict[str, Any]:
        """Get engine statistics and health information."""
        return {
            "active_pipelines": len(self.active_executions),
            "completed_pipelines": len(self.completed_executions),
            "registered_pipelines": len(self.pipeline_definitions),
            "agent_executor": self.agent_executor.get_resource_usage(),
            "webhook_manager": (
                self.webhook_manager.get_delivery_status() 
                if self.webhook_manager else None
            ),
            "config": {
                "max_concurrent_pipelines": self.config.max_concurrent_pipelines,
                "max_concurrent_stages": self.config.max_concurrent_stages,
                "webhooks_enabled": self.config.enable_webhooks
            }
        }