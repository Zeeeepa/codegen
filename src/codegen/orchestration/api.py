"""
REST API for Visual Orchestration System

This module provides REST API endpoints for managing pipelines, executions,
and real-time monitoring in the visual CI/CD orchestration system.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .engine import OrchestrationEngine, OrchestrationConfig
from .schemas import (
    PipelineDefinition, StageDefinition, PipelineExecution, TaskExecution,
    ExecutionStatus, TriggerType, StageType, AgentTaskConfig, WebhookConfig
)
from .realtime import RealtimeEventBroadcaster, RealtimeIntegration, WebSocketHandler


logger = logging.getLogger(__name__)


# Pydantic models for API requests/responses
class CreatePipelineRequest(BaseModel):
    name: str
    description: Optional[str] = None
    stages: List[Dict[str, Any]] = Field(default_factory=list)
    global_variables: Dict[str, Any] = Field(default_factory=dict)
    webhooks: List[Dict[str, Any]] = Field(default_factory=list)
    max_parallel_stages: int = 10


class UpdatePipelineRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    stages: Optional[List[Dict[str, Any]]] = None
    global_variables: Optional[Dict[str, Any]] = None
    webhooks: Optional[List[Dict[str, Any]]] = None
    max_parallel_stages: Optional[int] = None


class ExecutePipelineRequest(BaseModel):
    trigger_data: Dict[str, Any] = Field(default_factory=dict)
    variables: Dict[str, Any] = Field(default_factory=dict)


class PipelineResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    version: str
    stages: List[Dict[str, Any]]
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    tags: List[str]


class ExecutionResponse(BaseModel):
    id: str
    pipeline_id: str
    status: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_seconds: Optional[float] = None
    total_stages: int
    completed_stages: int
    failed_stages: int
    triggered_by: str
    tasks: Dict[str, Dict[str, Any]]


class OrchestrationAPI:
    """
    REST API for the orchestration system.
    """
    
    def __init__(self, engine: OrchestrationEngine):
        self.engine = engine
        self.app = FastAPI(
            title="Codegen Visual Orchestration API",
            description="REST API for managing visual CI/CD pipelines",
            version="1.0.0"
        )
        
        # Configure CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure appropriately for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Real-time components
        self.broadcaster = RealtimeEventBroadcaster()
        self.realtime_integration = RealtimeIntegration(self.broadcaster)
        self.websocket_handler = WebSocketHandler(self.broadcaster)
        
        # Setup routes
        self._setup_routes()
        
    def _setup_routes(self):
        """Setup API routes."""
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}
            
        @self.app.get("/stats")
        async def get_stats():
            """Get engine statistics."""
            stats = self.engine.get_engine_stats()
            realtime_stats = self.broadcaster.get_connection_stats()
            return {
                "engine": stats,
                "realtime": realtime_stats
            }
            
        # Pipeline management endpoints
        @self.app.post("/pipelines", response_model=PipelineResponse)
        async def create_pipeline(request: CreatePipelineRequest):
            """Create a new pipeline."""
            pipeline_id = str(uuid4())
            
            # Convert stages to StageDefinition objects
            stages = []
            for stage_data in request.stages:
                stage = StageDefinition(
                    id=stage_data.get("id", str(uuid4())),
                    name=stage_data["name"],
                    stage_type=StageType(stage_data["stage_type"]),
                    description=stage_data.get("description"),
                    depends_on=stage_data.get("depends_on", []),
                    can_run_parallel=stage_data.get("can_run_parallel", True),
                    continue_on_failure=stage_data.get("continue_on_failure", False),
                    agent_config=AgentTaskConfig(**stage_data["agent_config"]) if stage_data.get("agent_config") else None,
                    variables=stage_data.get("variables", {}),
                    tags=stage_data.get("tags", [])
                )
                stages.append(stage)
                
            # Convert webhooks
            webhooks = [WebhookConfig(**wh) for wh in request.webhooks]
            
            pipeline_def = PipelineDefinition(
                id=pipeline_id,
                name=request.name,
                description=request.description,
                stages=stages,
                global_variables=request.global_variables,
                webhooks=webhooks,
                max_parallel_stages=request.max_parallel_stages,
                created_at=datetime.now(),
                tags=[]
            )
            
            self.engine.register_pipeline(pipeline_def)
            
            return PipelineResponse(
                id=pipeline_def.id,
                name=pipeline_def.name,
                description=pipeline_def.description,
                version=pipeline_def.version,
                stages=[stage.__dict__ for stage in pipeline_def.stages],
                created_at=pipeline_def.created_at.isoformat() if pipeline_def.created_at else None,
                tags=pipeline_def.tags
            )
            
        @self.app.get("/pipelines", response_model=List[PipelineResponse])
        async def list_pipelines():
            """List all registered pipelines."""
            pipelines = []
            for pipeline_def in self.engine.pipeline_definitions.values():
                pipelines.append(PipelineResponse(
                    id=pipeline_def.id,
                    name=pipeline_def.name,
                    description=pipeline_def.description,
                    version=pipeline_def.version,
                    stages=[stage.__dict__ for stage in pipeline_def.stages],
                    created_at=pipeline_def.created_at.isoformat() if pipeline_def.created_at else None,
                    updated_at=pipeline_def.updated_at.isoformat() if pipeline_def.updated_at else None,
                    tags=pipeline_def.tags
                ))
            return pipelines
            
        @self.app.get("/pipelines/{pipeline_id}", response_model=PipelineResponse)
        async def get_pipeline(pipeline_id: str):
            """Get a specific pipeline."""
            if pipeline_id not in self.engine.pipeline_definitions:
                raise HTTPException(status_code=404, detail="Pipeline not found")
                
            pipeline_def = self.engine.pipeline_definitions[pipeline_id]
            return PipelineResponse(
                id=pipeline_def.id,
                name=pipeline_def.name,
                description=pipeline_def.description,
                version=pipeline_def.version,
                stages=[stage.__dict__ for stage in pipeline_def.stages],
                created_at=pipeline_def.created_at.isoformat() if pipeline_def.created_at else None,
                updated_at=pipeline_def.updated_at.isoformat() if pipeline_def.updated_at else None,
                tags=pipeline_def.tags
            )
            
        @self.app.delete("/pipelines/{pipeline_id}")
        async def delete_pipeline(pipeline_id: str):
            """Delete a pipeline."""
            if pipeline_id not in self.engine.pipeline_definitions:
                raise HTTPException(status_code=404, detail="Pipeline not found")
                
            del self.engine.pipeline_definitions[pipeline_id]
            return {"message": "Pipeline deleted successfully"}
            
        # Pipeline execution endpoints
        @self.app.post("/pipelines/{pipeline_id}/execute")
        async def execute_pipeline(
            pipeline_id: str, 
            request: ExecutePipelineRequest,
            background_tasks: BackgroundTasks
        ):
            """Execute a pipeline."""
            if pipeline_id not in self.engine.pipeline_definitions:
                raise HTTPException(status_code=404, detail="Pipeline not found")
                
            try:
                execution_id = await self.engine.execute_pipeline(
                    pipeline_id=pipeline_id,
                    trigger_type=TriggerType.MANUAL,
                    trigger_data=request.trigger_data
                )
                
                # Setup real-time monitoring
                background_tasks.add_task(
                    self._monitor_execution,
                    execution_id
                )
                
                return {"execution_id": execution_id, "status": "started"}
                
            except Exception as e:
                logger.error(f"Pipeline execution failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
                
        @self.app.post("/pipelines/{pipeline_id}/executions/{execution_id}/cancel")
        async def cancel_pipeline_execution(pipeline_id: str, execution_id: str):
            """Cancel a pipeline execution."""
            success = await self.engine.cancel_pipeline_execution(execution_id)
            if not success:
                raise HTTPException(status_code=404, detail="Execution not found or already completed")
                
            return {"message": "Execution cancelled successfully"}
            
        @self.app.get("/executions/{execution_id}", response_model=ExecutionResponse)
        async def get_execution_status(execution_id: str):
            """Get execution status."""
            execution = self.engine.get_pipeline_status(execution_id)
            if not execution:
                raise HTTPException(status_code=404, detail="Execution not found")
                
            return ExecutionResponse(
                id=execution.id,
                pipeline_id=execution.pipeline_id,
                status=execution.status,
                started_at=execution.started_at.isoformat() if execution.started_at else None,
                completed_at=execution.completed_at.isoformat() if execution.completed_at else None,
                duration_seconds=execution.duration_seconds,
                total_stages=execution.total_stages,
                completed_stages=execution.completed_stages,
                failed_stages=execution.failed_stages,
                triggered_by=execution.triggered_by,
                tasks={
                    stage_id: {
                        "id": task.id,
                        "status": task.status,
                        "started_at": task.started_at.isoformat() if task.started_at else None,
                        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                        "duration_seconds": task.duration_seconds,
                        "result": task.result,
                        "error_message": task.error_message,
                        "agent_run_id": task.agent_run_id,
                        "agent_web_url": task.agent_web_url
                    }
                    for stage_id, task in execution.tasks.items()
                }
            )
            
        @self.app.get("/executions", response_model=List[ExecutionResponse])
        async def list_executions(pipeline_id: Optional[str] = None):
            """List all executions."""
            all_executions = self.engine.get_all_pipeline_statuses()
            
            executions = []
            for execution in all_executions.values():
                if pipeline_id and execution.pipeline_id != pipeline_id:
                    continue
                    
                executions.append(ExecutionResponse(
                    id=execution.id,
                    pipeline_id=execution.pipeline_id,
                    status=execution.status,
                    started_at=execution.started_at.isoformat() if execution.started_at else None,
                    completed_at=execution.completed_at.isoformat() if execution.completed_at else None,
                    duration_seconds=execution.duration_seconds,
                    total_stages=execution.total_stages,
                    completed_stages=execution.completed_stages,
                    failed_stages=execution.failed_stages,
                    triggered_by=execution.triggered_by,
                    tasks={
                        stage_id: {
                            "id": task.id,
                            "status": task.status,
                            "started_at": task.started_at.isoformat() if task.started_at else None,
                            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                            "duration_seconds": task.duration_seconds,
                            "result": task.result,
                            "error_message": task.error_message,
                            "agent_run_id": task.agent_run_id,
                            "agent_web_url": task.agent_web_url
                        }
                        for stage_id, task in execution.tasks.items()
                    }
                ))
                
            return sorted(executions, key=lambda x: x.started_at or "", reverse=True)
            
        # WebSocket endpoint for real-time updates
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates."""
            await self.websocket_handler.handle_websocket(websocket)
            
        # Webhook delivery status
        @self.app.get("/webhooks/deliveries")
        async def get_webhook_deliveries(pipeline_id: Optional[str] = None):
            """Get webhook delivery status."""
            if self.engine.webhook_manager:
                deliveries = self.engine.webhook_manager.get_delivery_status(pipeline_id)
                return {"deliveries": deliveries}
            return {"deliveries": []}
            
        # Real-time events endpoint
        @self.app.get("/events/recent")
        async def get_recent_events(
            limit: int = 100,
            pipeline_id: Optional[str] = None
        ):
            """Get recent real-time events."""
            events = self.broadcaster.get_recent_events(
                limit=limit,
                pipeline_id=pipeline_id
            )
            return {"events": events}
            
    async def _monitor_execution(self, execution_id: str):
        """Monitor execution and send real-time updates."""
        last_status = None
        
        while True:
            try:
                execution = self.engine.get_pipeline_status(execution_id)
                if not execution:
                    break
                    
                # Send pipeline status updates
                if execution.status != last_status:
                    if execution.status == ExecutionStatus.RUNNING:
                        await self.realtime_integration.on_pipeline_started(execution)
                    elif execution.status in [ExecutionStatus.SUCCESS, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED]:
                        await self.realtime_integration.on_pipeline_completed(execution)
                        break  # Execution completed
                        
                    last_status = execution.status
                    
                # Send task status updates
                for stage_id, task in execution.tasks.items():
                    if task.status == ExecutionStatus.RUNNING and not hasattr(task, '_notified_started'):
                        await self.realtime_integration.on_stage_started(task)
                        task._notified_started = True
                    elif task.status in [ExecutionStatus.SUCCESS, ExecutionStatus.FAILED] and not hasattr(task, '_notified_completed'):
                        await self.realtime_integration.on_stage_completed(task)
                        task._notified_completed = True
                        
                await asyncio.sleep(2)  # Check every 2 seconds
                
            except Exception as e:
                logger.error(f"Monitoring error for execution {execution_id}: {e}")
                await asyncio.sleep(5)
                
    async def start(self):
        """Start the API and related services."""
        await self.engine.start()
        await self.broadcaster.start()
        logger.info("Orchestration API started")
        
    async def stop(self):
        """Stop the API and related services."""
        await self.broadcaster.stop()
        await self.engine.stop()
        logger.info("Orchestration API stopped")


# Factory function to create the API
def create_orchestration_api(config: Optional[OrchestrationConfig] = None) -> OrchestrationAPI:
    """
    Create and configure the orchestration API.
    
    Args:
        config: Optional orchestration configuration
        
    Returns:
        Configured OrchestrationAPI instance
    """
    if config is None:
        config = OrchestrationConfig()
        
    engine = OrchestrationEngine(config)
    api = OrchestrationAPI(engine)
    
    return api


# Example usage and testing
if __name__ == "__main__":
    import uvicorn
    
    # Create API
    api = create_orchestration_api()
    
    # Setup startup and shutdown events
    @api.app.on_event("startup")
    async def startup_event():
        await api.start()
        
    @api.app.on_event("shutdown")
    async def shutdown_event():
        await api.stop()
        
    # Run server
    uvicorn.run(
        api.app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )