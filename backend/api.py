"""
Backend API server using official Codegen SDK
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import AsyncGenerator, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from codegen.agents.agent import Agent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active tasks
active_tasks = {}

class TaskRequest(BaseModel):
    prompt: str
    thread_id: Optional[str] = None

class TaskResponse(BaseModel):
    task_id: str
    thread_id: Optional[str] = None

class TaskStatusResponse(BaseModel):
    status: str
    result: Optional[str] = None
    error: Optional[str] = None

class AgentCallback:
    def __init__(self, task_id: str, thread_id: Optional[str] = None):
        self.task_id = task_id
        self.thread_id = thread_id
        self.queue = asyncio.Queue()
        self.completed = False
        self.error = None
        self.current_step = 0
        self.total_steps = 0

    async def on_status_change(self, status: str, result: Optional[str] = None, error: Optional[str] = None, step_info: Optional[dict] = None):
        """Handle status change events"""
        event_data = {
            "status": status,
            "task_id": self.task_id,
            "timestamp": datetime.now().isoformat()
        }
        
        if self.thread_id:
            event_data["thread_id"] = self.thread_id
            
        if result:
            event_data["result"] = result
        if error:
            event_data["error"] = error
            
        # Include step information if available
        if step_info:
            event_data.update(step_info)
            
        # Format as proper SSE event
        event_str = f"data: {json.dumps(event_data)}\n\n"
        await self.queue.put(event_str)
        
        if status in ["completed", "failed"]:
            self.completed = True
            if error:
                self.error = error
            # Send completion event
            await self.queue.put("data: [DONE]\n\n")

    async def get_events(self):
        """Get events from the queue"""
        try:
            while not self.completed or not self.queue.empty():
                try:
                    # Use timeout to prevent infinite waiting
                    event = await asyncio.wait_for(self.queue.get(), timeout=5.0)
                    yield event
                except asyncio.TimeoutError:
                    # Send heartbeat to keep connection alive
                    yield ": heartbeat\n\n"
                except Exception as e:
                    logger.error(f"Error getting events: {e}")
                    yield f"data: {json.dumps({'status': 'error', 'error': str(e)})}\n\n"
                    yield "data: [DONE]\n\n"
                    break
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"data: {json.dumps({'status': 'error', 'error': str(e)})}\n\n"
            yield "data: [DONE]\n\n"

async def monitor_task(task, callback: AgentCallback):
    """Monitor task status and trigger callbacks"""
    try:
        logger.info(f"Starting to monitor task {callback.task_id}")
        max_retries = 900  # 30 minutes with 2-second intervals
        retry_count = 0
        last_step = None
        
        while not callback.completed and retry_count < max_retries:
            task.refresh()
            status = task.status.lower() if task.status else "unknown"
            logger.info(f"Task {callback.task_id} status: {status}")
            
            # Extract step information from task
            current_step = None
            try:
                # Try to get step information from task.result or task.summary
                if hasattr(task, 'result') and isinstance(task.result, dict):
                    current_step = task.result.get('current_step')
                elif hasattr(task, 'summary') and isinstance(task.summary, dict):
                    current_step = task.summary.get('current_step')
            except Exception as e:
                logger.warning(f"Could not extract step info: {e}")
            
            # Only send update if step has changed
            if current_step and current_step != last_step:
                step_info = {
                    'current_step': current_step,
                    'step_number': callback.current_step + 1
                }
                await callback.on_status_change(status, step_info=step_info)
                last_step = current_step
                callback.current_step += 1
            
            if status == "completed":
                result = (
                    getattr(task, 'result', None) or 
                    getattr(task, 'summary', None) or 
                    getattr(task, 'output', None) or 
                    "Task completed successfully."
                )
                logger.info(f"Task {callback.task_id} completed with result")
                await callback.on_status_change("completed", result=result)
                break
            elif status == "failed":
                error = getattr(task, 'error', None) or getattr(task, 'failure_reason', None) or 'Task failed'
                logger.error(f"Task {callback.task_id} failed: {error}")
                await callback.on_status_change("failed", error=error)
                break
            elif status != "unknown":
                logger.info(f"Task {callback.task_id} status update: {status}")
                await callback.on_status_change(status)
            
            await asyncio.sleep(2)  # Poll every 2 seconds
            retry_count += 1
            
        if retry_count >= max_retries:
            logger.error(f"Task {callback.task_id} timed out after {max_retries * 2} seconds")
            await callback.on_status_change("failed", error="Task timed out")
            
    except Exception as e:
        logger.error(f"Error monitoring task {callback.task_id}: {e}")
        await callback.on_status_change("error", error=str(e))
    finally:
        # Clean up
        active_tasks.pop(callback.task_id, None)
        logger.info(f"Cleaned up task {callback.task_id}")

@app.post("/run", response_model=TaskResponse)
async def run_agent(request: TaskRequest):
    """Run an agent with the given prompt"""
    try:
        # Initialize the agent
        agent = Agent(
            org_id=os.getenv("CODEGEN_ORG_ID"),
            token=os.getenv("CODEGEN_TOKEN")
        )
        
        # Run the agent
        task = agent.run(request.prompt)
        
        if not task or not task.id:
            raise HTTPException(status_code=500, detail="Failed to create task")
        
        # Create callback and start monitoring
        callback = AgentCallback(task.id, request.thread_id)
        active_tasks[task.id] = (task, callback)
        
        # Start monitoring task in background
        asyncio.create_task(monitor_task(task, callback))
        
        return TaskResponse(task_id=task.id, thread_id=request.thread_id)
        
    except Exception as e:
        logger.error(f"Error running agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status/{task_id}")
async def get_task_status(task_id: str) -> TaskStatusResponse:
    """Get task status"""
    try:
        if task_id not in active_tasks:
            raise HTTPException(status_code=404, detail="Task not found")
            
        task, _ = active_tasks[task_id]
        task.refresh()
        
        return TaskStatusResponse(
            status=task.status.lower() if task.status else "unknown",
            result=getattr(task, 'result', None),
            error=getattr(task, 'error', None)
        )
        
    except Exception as e:
        logger.error(f"Error getting task status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/events/{task_id}")
async def get_task_events(task_id: str) -> StreamingResponse:
    """Get SSE events for task status updates"""
    try:
        if task_id not in active_tasks:
            raise HTTPException(status_code=404, detail="Task not found")
            
        _, callback = active_tasks[task_id]
        
        return StreamingResponse(
            callback.get_events(),
            media_type="text/event-stream"
        )
        
    except Exception as e:
        logger.error(f"Error getting task events: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("SERVER_PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)

