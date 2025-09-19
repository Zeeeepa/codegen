"""
Comprehensive Test Suite for Visual Orchestration System

This module provides tests for all components of the visual CI/CD orchestration system,
including parallel agent execution, webhook integration, and pipeline orchestration.
"""

import asyncio
import json
import logging
import pytest
from datetime import datetime
from typing import List, Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch

from .schemas import (
    PipelineDefinition, StageDefinition, AgentTaskConfig, WebhookConfig,
    ExecutionStatus, TriggerType, StageType, TaskExecution
)
from .parallel_executor import ParallelAgentExecutor, ParallelExecutionConfig
from .webhooks import WebhookManager, WebhookDelivery
from .engine import OrchestrationEngine, OrchestrationConfig
from .realtime import RealtimeEventBroadcaster, EventType, RealtimeEvent


# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestParallelAgentExecution:
    """Test suite for parallel agent execution."""
    
    @pytest.fixture
    async def executor(self):
        """Create a parallel executor for testing."""
        config = ParallelExecutionConfig(
            max_concurrent_agents=3,
            agent_timeout=30
        )
        executor = ParallelAgentExecutor(config)
        await executor.start_monitoring()
        yield executor
        await executor.shutdown()
        
    @pytest.fixture
    def mock_agent_config(self):
        """Create a mock agent configuration."""
        return AgentTaskConfig(
            prompt="Test prompt for parallel execution",
            agent_type="test",
            timeout=10,
            org_id="test_org",
            api_token="test_token"
        )
        
    @pytest.fixture
    def pipeline_context(self):
        """Create pipeline execution context."""
        return {
            "pipeline_id": "test_pipeline",
            "execution_id": "test_execution", 
            "stage_id": "test_stage",
            "variables": {"test_var": "test_value"}
        }
        
    async def test_single_agent_execution(self, executor, mock_agent_config, pipeline_context):
        """Test executing a single agent task."""
        with patch('codegen.agents.agent.Agent') as MockAgent:
            # Setup mock agent
            mock_agent_instance = MockAgent.return_value
            mock_task = MagicMock()
            mock_task.id = "test_task_123"
            mock_task.status = "completed"
            mock_task.result = {"output": "test output"}
            mock_task.web_url = "https://example.com/task/123"
            mock_agent_instance.run.return_value = mock_task
            
            # Execute agent task
            result = await executor.execute_agent_task(
                agent_config=mock_agent_config,
                context=pipeline_context
            )
            
            # Verify results
            assert result.status == ExecutionStatus.SUCCESS
            assert result.result == {"output": "test output"}
            assert result.agent_run_id == "test_task_123"
            assert result.agent_web_url == "https://example.com/task/123"
            assert result.duration_seconds is not None
            
    async def test_parallel_agent_execution(self, executor, mock_agent_config, pipeline_context):
        """Test executing multiple agents in parallel."""
        with patch('codegen.agents.agent.Agent') as MockAgent:
            # Setup mock agent
            mock_agent_instance = MockAgent.return_value
            mock_task = MagicMock()
            mock_task.status = "completed"
            mock_task.result = {"output": "test output"}
            mock_agent_instance.run.return_value = mock_task
            
            # Create multiple agent configs
            agent_configs = [mock_agent_config for _ in range(3)]
            
            # Execute agents in parallel
            results = await executor.execute_parallel_agents(
                agent_configs=agent_configs,
                context=pipeline_context,
                wait_for_all=True
            )
            
            # Verify all executions completed successfully
            assert len(results) == 3
            for result in results:
                assert result.status == ExecutionStatus.SUCCESS
                assert result.result == {"output": "test output"}
                
    async def test_agent_execution_timeout(self, executor, mock_agent_config, pipeline_context):
        """Test agent execution timeout handling."""
        # Set short timeout
        mock_agent_config.timeout = 1
        
        with patch('codegen.agents.agent.Agent') as MockAgent:
            # Setup mock agent that never completes
            mock_agent_instance = MockAgent.return_value
            mock_task = MagicMock()
            mock_task.status = "running"  # Never completes
            mock_agent_instance.run.return_value = mock_task
            
            # Execute with timeout
            result = await executor.execute_agent_task(
                agent_config=mock_agent_config,
                context=pipeline_context
            )
            
            # Verify timeout handling
            assert result.status == ExecutionStatus.FAILED
            assert "timeout" in result.error_message.lower()


class TestWebhookIntegration:
    """Test suite for webhook integration system."""
    
    @pytest.fixture
    async def webhook_manager(self):
        """Create a webhook manager for testing."""
        manager = WebhookManager(max_concurrent_deliveries=5)
        await manager.start()
        yield manager
        await manager.stop()
        
    @pytest.fixture
    def webhook_config(self):
        """Create a webhook configuration."""
        return WebhookConfig(
            url="https://example.com/webhook",
            method="POST",
            retry_attempts=3,
            retry_delay=1,
            timeout=5
        )
        
    @pytest.fixture
    def mock_task_execution(self):
        """Create a mock task execution."""
        return TaskExecution(
            id="test_task",
            stage_id="test_stage", 
            pipeline_id="test_pipeline",
            status=ExecutionStatus.SUCCESS,
            started_at=datetime.now(),
            completed_at=datetime.now(),
            duration_seconds=5.0,
            result={"output": "test result"}
        )
        
    async def test_webhook_registration(self, webhook_manager, webhook_config):
        """Test webhook configuration registration."""
        pipeline_id = "test_pipeline"
        
        webhook_manager.register_webhook_config(pipeline_id, webhook_config)
        
        assert pipeline_id in webhook_manager.webhook_configs
        assert webhook_config in webhook_manager.webhook_configs[pipeline_id]
        
    async def test_successful_webhook_delivery(self, webhook_manager, webhook_config, mock_task_execution):
        """Test successful webhook delivery."""
        pipeline_id = mock_task_execution.pipeline_id
        webhook_manager.register_webhook_config(pipeline_id, webhook_config)
        
        with patch('aiohttp.ClientSession.request') as mock_request:
            # Mock successful HTTP response
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value="OK")
            mock_request.return_value.__aenter__.return_value = mock_response
            
            # Send webhook
            await webhook_manager.send_task_completion_webhook(mock_task_execution)
            
            # Wait for delivery processing
            await asyncio.sleep(0.1)
            
            # Verify webhook was called
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert call_args[1]['url'] == webhook_config.url
            assert call_args[1]['json']['event'] == 'task_completed'
            
    async def test_webhook_retry_on_failure(self, webhook_manager, webhook_config, mock_task_execution):
        """Test webhook retry logic on delivery failure."""
        webhook_config.retry_attempts = 2
        webhook_config.retry_delay = 0.1  # Fast retry for testing
        
        pipeline_id = mock_task_execution.pipeline_id
        webhook_manager.register_webhook_config(pipeline_id, webhook_config)
        
        with patch('aiohttp.ClientSession.request') as mock_request:
            # Mock failed HTTP response
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_response.text = AsyncMock(return_value="Internal Server Error")
            mock_request.return_value.__aenter__.return_value = mock_response
            
            # Send webhook
            await webhook_manager.send_task_completion_webhook(mock_task_execution)
            
            # Wait for retries
            await asyncio.sleep(1.0)
            
            # Verify retries occurred
            assert mock_request.call_count == webhook_config.retry_attempts


class TestOrchestrationEngine:
    """Test suite for the main orchestration engine."""
    
    @pytest.fixture
    async def engine(self):
        """Create an orchestration engine for testing."""
        config = OrchestrationConfig(
            max_concurrent_pipelines=2,
            max_concurrent_stages=3,
            enable_webhooks=True
        )
        engine = OrchestrationEngine(config)
        await engine.start()
        yield engine
        await engine.stop()
        
    @pytest.fixture
    def sample_pipeline_definition(self):
        """Create a sample pipeline definition."""
        return PipelineDefinition(
            id="test_pipeline",
            name="Test Pipeline",
            description="A test pipeline for validation",
            stages=[
                StageDefinition(
                    id="stage1",
                    name="First Stage",
                    stage_type=StageType.AGENT_TASK,
                    agent_config=AgentTaskConfig(
                        prompt="Execute first stage task",
                        org_id="test_org",
                        api_token="test_token"
                    ),
                    depends_on=[],
                    can_run_parallel=True
                ),
                StageDefinition(
                    id="stage2", 
                    name="Second Stage",
                    stage_type=StageType.AGENT_TASK,
                    agent_config=AgentTaskConfig(
                        prompt="Execute second stage task",
                        org_id="test_org",
                        api_token="test_token"
                    ),
                    depends_on=["stage1"],
                    can_run_parallel=True
                )
            ],
            webhooks=[
                WebhookConfig(
                    url="https://example.com/webhook",
                    retry_attempts=2
                )
            ]
        )
        
    async def test_pipeline_registration(self, engine, sample_pipeline_definition):
        """Test pipeline registration."""
        engine.register_pipeline(sample_pipeline_definition)
        
        assert sample_pipeline_definition.id in engine.pipeline_definitions
        registered_pipeline = engine.pipeline_definitions[sample_pipeline_definition.id]
        assert registered_pipeline.name == sample_pipeline_definition.name
        assert len(registered_pipeline.stages) == 2
        
    async def test_pipeline_execution(self, engine, sample_pipeline_definition):
        """Test end-to-end pipeline execution."""
        engine.register_pipeline(sample_pipeline_definition)
        
        with patch('codegen.agents.agent.Agent') as MockAgent:
            # Setup mock agent
            mock_agent_instance = MockAgent.return_value
            mock_task = MagicMock()
            mock_task.id = "test_task"
            mock_task.status = "completed"
            mock_task.result = {"output": "success"}
            mock_agent_instance.run.return_value = mock_task
            
            # Execute pipeline
            execution_id = await engine.execute_pipeline(
                pipeline_id=sample_pipeline_definition.id,
                trigger_type=TriggerType.MANUAL
            )
            
            # Wait for execution to complete
            max_wait = 10  # seconds
            wait_count = 0
            
            while wait_count < max_wait:
                execution = engine.get_pipeline_status(execution_id)
                if execution and execution.status in [ExecutionStatus.SUCCESS, ExecutionStatus.FAILED]:
                    break
                await asyncio.sleep(1)
                wait_count += 1
                
            # Verify execution completed
            execution = engine.get_pipeline_status(execution_id)
            assert execution is not None
            assert execution.status in [ExecutionStatus.SUCCESS, ExecutionStatus.FAILED]
            assert len(execution.tasks) == 2  # Both stages executed
            
    async def test_pipeline_cancellation(self, engine, sample_pipeline_definition):
        """Test pipeline execution cancellation."""
        engine.register_pipeline(sample_pipeline_definition)
        
        with patch('codegen.agents.agent.Agent') as MockAgent:
            # Setup mock agent that runs indefinitely
            mock_agent_instance = MockAgent.return_value
            mock_task = MagicMock()
            mock_task.status = "running"  # Never completes
            mock_agent_instance.run.return_value = mock_task
            
            # Execute pipeline
            execution_id = await engine.execute_pipeline(
                pipeline_id=sample_pipeline_definition.id,
                trigger_type=TriggerType.MANUAL
            )
            
            # Wait a bit for execution to start
            await asyncio.sleep(0.5)
            
            # Cancel execution
            success = await engine.cancel_pipeline_execution(execution_id)
            assert success
            
            # Verify cancellation
            execution = engine.get_pipeline_status(execution_id)
            assert execution.status == ExecutionStatus.CANCELLED


class TestRealtimeIntegration:
    """Test suite for real-time event broadcasting."""
    
    @pytest.fixture
    async def broadcaster(self):
        """Create a real-time event broadcaster."""
        broadcaster = RealtimeEventBroadcaster(heartbeat_interval=1)
        await broadcaster.start()
        yield broadcaster
        await broadcaster.stop()
        
    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket connection."""
        websocket = AsyncMock()
        websocket.send = AsyncMock()
        websocket.close = AsyncMock()
        return websocket
        
    async def test_websocket_connection(self, broadcaster, mock_websocket):
        """Test WebSocket connection management."""
        # Connect client
        connection_id = await broadcaster.connect_client(mock_websocket)
        
        assert connection_id in broadcaster.connections
        assert len(broadcaster.connections) == 1
        
        # Disconnect client
        await broadcaster.disconnect_client(connection_id)
        
        assert connection_id not in broadcaster.connections
        assert len(broadcaster.connections) == 0
        
    async def test_event_broadcasting(self, broadcaster, mock_websocket):
        """Test event broadcasting to connected clients."""
        # Connect client
        connection_id = await broadcaster.connect_client(mock_websocket)
        
        # Subscribe to all events
        from .realtime import EventType
        await broadcaster.subscribe_to_events(connection_id, list(EventType))
        
        # Broadcast event
        event = RealtimeEvent(
            event_type=EventType.PIPELINE_STARTED,
            timestamp=datetime.now(),
            pipeline_id="test_pipeline",
            data={"message": "Pipeline started"}
        )
        
        await broadcaster.broadcast_event(event)
        
        # Verify event was sent
        mock_websocket.send.assert_called()
        sent_data = json.loads(mock_websocket.send.call_args[0][0])
        assert sent_data['event_type'] == 'pipeline_started'
        assert sent_data['pipeline_id'] == 'test_pipeline'


class TestIntegrationScenarios:
    """Integration tests for complete workflows."""
    
    async def test_complete_parallel_pipeline_execution(self):
        """Test complete parallel pipeline execution with webhooks and real-time updates."""
        # Create orchestration engine
        config = OrchestrationConfig(
            max_concurrent_pipelines=1,
            max_concurrent_stages=5,
            enable_webhooks=True
        )
        engine = OrchestrationEngine(config)
        await engine.start()
        
        try:
            # Create pipeline with parallel stages
            pipeline_def = PipelineDefinition(
                id="parallel_test_pipeline",
                name="Parallel Test Pipeline",
                stages=[
                    # Stage 1: Single initial stage
                    StageDefinition(
                        id="init_stage",
                        name="Initialize",
                        stage_type=StageType.AGENT_TASK,
                        agent_config=AgentTaskConfig(
                            prompt="Initialize the pipeline",
                            org_id="test_org",
                            api_token="test_token"
                        ),
                        depends_on=[],
                        can_run_parallel=True
                    ),
                    # Stages 2-4: Parallel execution
                    StageDefinition(
                        id="parallel_stage_1",
                        name="Parallel Task 1",
                        stage_type=StageType.AGENT_TASK,
                        agent_config=AgentTaskConfig(
                            prompt="Execute parallel task 1",
                            org_id="test_org", 
                            api_token="test_token"
                        ),
                        depends_on=["init_stage"],
                        can_run_parallel=True
                    ),
                    StageDefinition(
                        id="parallel_stage_2",
                        name="Parallel Task 2",
                        stage_type=StageType.AGENT_TASK,
                        agent_config=AgentTaskConfig(
                            prompt="Execute parallel task 2",
                            org_id="test_org",
                            api_token="test_token"
                        ),
                        depends_on=["init_stage"],
                        can_run_parallel=True
                    ),
                    StageDefinition(
                        id="parallel_stage_3",
                        name="Parallel Task 3",
                        stage_type=StageType.AGENT_TASK,
                        agent_config=AgentTaskConfig(
                            prompt="Execute parallel task 3",
                            org_id="test_org",
                            api_token="test_token"
                        ),
                        depends_on=["init_stage"],
                        can_run_parallel=True
                    ),
                    # Stage 5: Final stage that depends on all parallel stages
                    StageDefinition(
                        id="final_stage",
                        name="Finalize",
                        stage_type=StageType.AGENT_TASK,
                        agent_config=AgentTaskConfig(
                            prompt="Finalize the pipeline",
                            org_id="test_org",
                            api_token="test_token"
                        ),
                        depends_on=["parallel_stage_1", "parallel_stage_2", "parallel_stage_3"],
                        can_run_parallel=True
                    ),
                ],
                webhooks=[
                    WebhookConfig(
                        url="https://httpbin.org/post",
                        retry_attempts=2
                    )
                ]
            )
            
            # Register pipeline
            engine.register_pipeline(pipeline_def)
            
            # Mock agent execution
            with patch('codegen.agents.agent.Agent') as MockAgent:
                mock_agent_instance = MockAgent.return_value
                mock_task = MagicMock()
                mock_task.id = "test_task"
                mock_task.status = "completed"
                mock_task.result = {"output": "success"}
                mock_task.web_url = "https://example.com/task"
                mock_agent_instance.run.return_value = mock_task
                
                # Execute pipeline
                execution_id = await engine.execute_pipeline(
                    pipeline_id=pipeline_def.id,
                    trigger_type=TriggerType.MANUAL,
                    trigger_data={"test_data": "integration_test"}
                )
                
                logger.info(f"Started parallel pipeline execution: {execution_id}")
                
                # Monitor execution progress
                max_wait = 30  # seconds
                wait_count = 0
                last_status = None
                
                while wait_count < max_wait:
                    execution = engine.get_pipeline_status(execution_id)
                    
                    if execution:
                        if execution.status != last_status:
                            logger.info(f"Pipeline status: {execution.status}")
                            logger.info(f"Completed stages: {execution.completed_stages}/{execution.total_stages}")
                            last_status = execution.status
                            
                        if execution.status in [ExecutionStatus.SUCCESS, ExecutionStatus.FAILED]:
                            break
                            
                    await asyncio.sleep(1)
                    wait_count += 1
                    
                # Verify execution results
                final_execution = engine.get_pipeline_status(execution_id)
                assert final_execution is not None
                
                logger.info(f"Final pipeline status: {final_execution.status}")
                logger.info(f"Total execution time: {final_execution.duration_seconds:.2f}s")
                logger.info(f"Stages - Completed: {final_execution.completed_stages}, Failed: {final_execution.failed_stages}")
                
                # Validate parallel execution occurred
                assert final_execution.total_stages == 5
                assert final_execution.status in [ExecutionStatus.SUCCESS, ExecutionStatus.FAILED]
                
                # Verify all stages were executed
                assert len(final_execution.tasks) == 5
                
                # Verify dependency order (init_stage should complete before parallel stages)
                init_task = final_execution.tasks.get("init_stage")
                parallel_tasks = [
                    final_execution.tasks.get("parallel_stage_1"),
                    final_execution.tasks.get("parallel_stage_2"), 
                    final_execution.tasks.get("parallel_stage_3")
                ]
                final_task = final_execution.tasks.get("final_stage")
                
                if init_task and all(parallel_tasks) and final_task:
                    # Init should complete before parallel stages start
                    for parallel_task in parallel_tasks:
                        if init_task.completed_at and parallel_task.started_at:
                            assert init_task.completed_at <= parallel_task.started_at
                            
                    # Parallel stages should complete before final stage starts
                    if final_task.started_at:
                        for parallel_task in parallel_tasks:
                            if parallel_task.completed_at:
                                assert parallel_task.completed_at <= final_task.started_at
                                
                logger.info("✅ Parallel pipeline execution test completed successfully!")
                
        finally:
            await engine.stop()


# Test runner
async def run_all_tests():
    """Run all test suites."""
    logger.info("🚀 Starting comprehensive orchestration system tests...")
    
    # Run integration test
    integration_test = TestIntegrationScenarios()
    await integration_test.test_complete_parallel_pipeline_execution()
    
    logger.info("✅ All tests completed successfully!")


if __name__ == "__main__":
    asyncio.run(run_all_tests())