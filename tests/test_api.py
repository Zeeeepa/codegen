"""
Tests for the backend API server
"""

import asyncio
import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.api import app

# Test client
client = TestClient(app)

# Mock environment variables
os.environ["CODEGEN_ORG_ID"] = "test_org"
os.environ["CODEGEN_TOKEN"] = "test_token"

@pytest.fixture
def mock_agent():
    """Mock Agent class"""
    with patch("backend.api.Agent") as mock:
        yield mock

@pytest.fixture
def mock_task():
    """Mock task object"""
    task = MagicMock()
    task.id = "test_task_id"
    task.status = "in_progress"
    task.result = {
        "current_step": "Analyzing code"
    }
    return task

def test_run_agent(mock_agent, mock_task):
    """Test running an agent"""
    # Setup mock
    mock_agent.return_value.run.return_value = mock_task
    
    # Test request
    response = client.post(
        "/run",
        json={"prompt": "Test prompt", "thread_id": "test_thread"}
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == "test_task_id"
    assert data["thread_id"] == "test_thread"
    
    # Verify agent was called correctly
    mock_agent.assert_called_once_with(
        org_id="test_org",
        token="test_token"
    )
    mock_agent.return_value.run.assert_called_once_with("Test prompt")

def test_get_task_status(mock_task):
    """Test getting task status"""
    # Add mock task to active tasks
    from backend.api import active_tasks
    active_tasks["test_task_id"] = (mock_task, None)
    
    # Test request
    response = client.get("/status/test_task_id")
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "in_progress"
    assert data["result"] == {"current_step": "Analyzing code"}
    
    # Clean up
    active_tasks.clear()

def test_get_task_status_not_found():
    """Test getting status of non-existent task"""
    response = client.get("/status/nonexistent_task")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_get_task_events():
    """Test getting task events"""
    # Setup mock callback
    mock_callback = MagicMock()
    mock_callback.get_events = AsyncMock(return_value=[
        'data: {"status": "in_progress", "task_id": "test_task_id", "current_step": "Analyzing code"}\n\n',
        'data: {"status": "completed", "task_id": "test_task_id", "result": "Success"}\n\n',
        'data: [DONE]\n\n'
    ])
    
    # Add mock task to active tasks
    from backend.api import active_tasks
    active_tasks["test_task_id"] = (None, mock_callback)
    
    # Test request
    response = client.get("/events/test_task_id")
    
    # Verify response
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream"
    
    # Clean up
    active_tasks.clear()

@pytest.mark.asyncio
async def test_monitor_task():
    """Test task monitoring"""
    from backend.api import AgentCallback, monitor_task
    
    # Setup mock task
    mock_task = MagicMock()
    mock_task.status = "in_progress"
    mock_task.result = {"current_step": "Step 1"}
    
    # Create callback
    callback = AgentCallback("test_task_id", "test_thread")
    
    # Start monitoring in background
    monitor_task_future = asyncio.create_task(monitor_task(mock_task, callback))
    
    # Wait a bit for events
    await asyncio.sleep(0.1)
    
    # Simulate task completion
    mock_task.status = "completed"
    mock_task.result = "Success"
    
    # Wait for monitoring to complete
    await monitor_task_future
    
    # Verify callback was completed
    assert callback.completed == True
    assert callback.error is None

def test_task_timeout():
    """Test task timeout handling"""
    from backend.api import monitor_task, AgentCallback
    
    # Setup mock task that never completes
    mock_task = MagicMock()
    mock_task.status = "in_progress"
    
    # Create callback
    callback = AgentCallback("test_task_id")
    
    # Override max_retries for faster testing
    max_retries = 2
    
    # Run monitoring
    asyncio.run(monitor_task(mock_task, callback))
    
    # Verify timeout was handled
    assert callback.completed == True
    assert callback.error is not None
    assert "timed out" in callback.error.lower()

def test_step_tracking():
    """Test step tracking in events"""
    from backend.api import AgentCallback
    
    # Create callback
    callback = AgentCallback("test_task_id")
    
    # Simulate multiple steps
    steps = [
        {"current_step": "Analyzing code", "step_number": 1},
        {"current_step": "Making changes", "step_number": 2},
        {"current_step": "Running tests", "step_number": 3}
    ]
    
    # Process steps
    for step in steps:
        asyncio.run(callback.on_status_change("in_progress", step_info=step))
    
    # Complete the task
    asyncio.run(callback.on_status_change("completed", result="Success"))
    
    # Verify step tracking
    assert callback.current_step == 3  # Should have processed all steps
    assert callback.completed == True

