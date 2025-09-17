"""
Wandb + Weave Observer Integration

This module provides comprehensive integration with Wandb and Weave for
observation, monitoring, experiment tracking, and workflow visualization
across the entire CI/CD ecosystem.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import uuid
import json

from codegen.orchestration.config.unified_config import UnifiedConfig

logger = logging.getLogger(__name__)

class ObservationType(Enum):
    """Types of observations."""
    DEPLOYMENT = "deployment"
    TASK_EXECUTION = "task_execution"
    AGENT_PERFORMANCE = "agent_performance"
    SYSTEM_METRICS = "system_metrics"
    ERROR_TRACKING = "error_tracking"
    WORKFLOW = "workflow"

class MetricType(Enum):
    """Types of metrics."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"

@dataclass
class Observation:
    """Observation data structure."""
    observation_id: str
    observation_type: ObservationType
    source: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Metric:
    """Metric data structure."""
    metric_name: str
    metric_type: MetricType
    value: Union[int, float]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    tags: Dict[str, str] = field(default_factory=dict)
    unit: Optional[str] = None

@dataclass
class Experiment:
    """Experiment tracking structure."""
    experiment_id: str
    name: str
    description: str
    config: Dict[str, Any]
    metrics: List[Metric] = field(default_factory=list)
    artifacts: List[str] = field(default_factory=list)
    status: str = "running"
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

class WandbWeaveObserver:
    """
    Wandb + Weave Observer for Comprehensive Monitoring.
    
    This observer provides:
    - Experiment tracking with Wandb
    - Workflow visualization with Weave
    - Real-time metrics collection
    - Performance monitoring
    - Error tracking and alerting
    - Artifact management
    """
    
    def __init__(self, config: UnifiedConfig):
        """Initialize Wandb + Weave observer."""
        self.config = config
        self._initialized = False
        
        # Configuration
        self.wandb_config = config.get("wandb", {})
        self.weave_config = config.get("weave", {})
        
        self.wandb_project = self.wandb_config.get("project", "codegen-orchestration")
        self.wandb_entity = self.wandb_config.get("entity", "codegen")
        self.weave_project = self.weave_config.get("project", "orchestration-workflows")
        
        # Data storage
        self._observations: List[Observation] = []
        self._metrics: List[Metric] = []
        self._experiments: Dict[str, Experiment] = {}
        self._active_workflows: Dict[str, Dict[str, Any]] = {}
        
        # Background tasks
        self._background_tasks: List[asyncio.Task] = []
        self._shutdown_event = asyncio.Event()
        
        # Metrics aggregation
        self._metric_buffers: Dict[str, List[Metric]] = {}
        self._buffer_size = 100
        self._flush_interval = 30  # seconds
        
        logger.info("WandbWeaveObserver initialized")
    
    async def initialize(self) -> None:
        """Initialize the observer."""
        if self._initialized:
            return
        
        logger.info("Initializing Wandb + Weave observer...")
        
        # Initialize Wandb
        await self._initialize_wandb()
        
        # Initialize Weave
        await self._initialize_weave()
        
        # Start background tasks
        await self._start_background_tasks()
        
        self._initialized = True
        logger.info("Wandb + Weave observer initialized successfully")
    
    async def shutdown(self) -> None:
        """Shutdown the observer."""
        logger.info("Shutting down Wandb + Weave observer...")
        
        # Signal shutdown
        self._shutdown_event.set()
        
        # Flush remaining data
        await self._flush_all_data()
        
        # Cancel background tasks
        if self._background_tasks:
            for task in self._background_tasks:
                task.cancel()
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
        
        # Cleanup connections
        await self._cleanup_connections()
        
        self._initialized = False
        logger.info("Wandb + Weave observer shutdown complete")
    
    async def observe(self, observation: Union[Dict[str, Any], Observation]) -> None:
        """Record an observation."""
        if not self._initialized:
            await self.initialize()
        
        # Convert dict to Observation if needed
        if isinstance(observation, dict):
            obs = Observation(
                observation_id=f"obs_{uuid.uuid4().hex[:8]}",
                observation_type=ObservationType(observation["type"]),
                source=observation["source"],
                data=observation["data"],
                tags=observation.get("tags", {}),
                metadata=observation.get("metadata", {})
            )
        else:
            obs = observation
        
        # Store observation
        self._observations.append(obs)
        
        # Send to appropriate backend
        if obs.observation_type in [ObservationType.DEPLOYMENT, ObservationType.SYSTEM_METRICS]:
            await self._send_to_wandb(obs)
        
        if obs.observation_type in [ObservationType.WORKFLOW, ObservationType.TASK_EXECUTION]:
            await self._send_to_weave(obs)
        
        logger.debug(f"Recorded observation: {obs.observation_id}")
    
    async def record_metric(self, metric: Union[Dict[str, Any], Metric]) -> None:
        """Record a metric."""
        if not self._initialized:
            await self.initialize()
        
        # Convert dict to Metric if needed
        if isinstance(metric, dict):
            m = Metric(
                metric_name=metric["name"],
                metric_type=MetricType(metric["type"]),
                value=metric["value"],
                tags=metric.get("tags", {}),
                unit=metric.get("unit")
            )
        else:
            m = metric
        
        # Store metric
        self._metrics.append(m)
        
        # Buffer for batch processing
        if m.metric_name not in self._metric_buffers:
            self._metric_buffers[m.metric_name] = []
        
        self._metric_buffers[m.metric_name].append(m)
        
        # Flush if buffer is full
        if len(self._metric_buffers[m.metric_name]) >= self._buffer_size:
            await self._flush_metric_buffer(m.metric_name)
        
        logger.debug(f"Recorded metric: {m.metric_name} = {m.value}")
    
    async def start_experiment(self, experiment_config: Dict[str, Any]) -> str:
        """Start a new experiment."""
        experiment = Experiment(
            experiment_id=f"exp_{uuid.uuid4().hex[:8]}",
            name=experiment_config["name"],
            description=experiment_config.get("description", ""),
            config=experiment_config.get("config", {})
        )
        
        self._experiments[experiment.experiment_id] = experiment
        
        # Initialize in Wandb
        await self._start_wandb_run(experiment)
        
        logger.info(f"Started experiment: {experiment.name} ({experiment.experiment_id})")
        return experiment.experiment_id
    
    async def end_experiment(self, experiment_id: str, status: str = "completed") -> None:
        """End an experiment."""
        experiment = self._experiments.get(experiment_id)
        if not experiment:
            return
        
        experiment.status = status
        experiment.completed_at = datetime.utcnow()
        
        # Finalize in Wandb
        await self._end_wandb_run(experiment)
        
        logger.info(f"Ended experiment: {experiment.name} ({experiment_id})")
    
    async def track_workflow(self, workflow_config: Dict[str, Any]) -> str:
        """Start tracking a workflow."""
        workflow_id = f"wf_{uuid.uuid4().hex[:8]}"
        
        workflow = {
            "workflow_id": workflow_id,
            "name": workflow_config["name"],
            "description": workflow_config.get("description", ""),
            "steps": workflow_config.get("steps", []),
            "current_step": 0,
            "status": "running",
            "started_at": datetime.utcnow(),
            "metadata": workflow_config.get("metadata", {})
        }
        
        self._active_workflows[workflow_id] = workflow
        
        # Initialize in Weave
        await self._start_weave_workflow(workflow)
        
        logger.info(f"Started tracking workflow: {workflow['name']} ({workflow_id})")
        return workflow_id
    
    async def update_workflow_step(self, workflow_id: str, step_index: int, step_data: Dict[str, Any]) -> None:
        """Update a workflow step."""
        workflow = self._active_workflows.get(workflow_id)
        if not workflow:
            return
        
        workflow["current_step"] = step_index
        workflow["last_updated"] = datetime.utcnow()
        
        # Update in Weave
        await self._update_weave_workflow_step(workflow, step_index, step_data)
        
        logger.debug(f"Updated workflow {workflow_id} step {step_index}")
    
    async def complete_workflow(self, workflow_id: str, status: str = "completed") -> None:
        """Complete a workflow."""
        workflow = self._active_workflows.get(workflow_id)
        if not workflow:
            return
        
        workflow["status"] = status
        workflow["completed_at"] = datetime.utcnow()
        
        # Complete in Weave
        await self._complete_weave_workflow(workflow)
        
        # Move to history
        self._active_workflows.pop(workflow_id, None)
        
        logger.info(f"Completed workflow: {workflow['name']} ({workflow_id})")
    
    async def setup_monitoring(self, monitoring_config: Dict[str, Any]) -> Dict[str, Any]:
        """Setup monitoring for a deployment."""
        deployment_id = monitoring_config["deployment_id"]
        project_name = monitoring_config["project_name"]
        
        # Start experiment for deployment
        experiment_id = await self.start_experiment({
            "name": f"deployment_{project_name}_{deployment_id}",
            "description": f"Monitoring deployment of {project_name}",
            "config": monitoring_config
        })
        
        # Start workflow tracking
        workflow_id = await self.track_workflow({
            "name": f"deployment_workflow_{project_name}",
            "description": f"Deployment workflow for {project_name}",
            "steps": [
                "sandbox_creation",
                "environment_setup",
                "dependency_installation",
                "application_deployment",
                "validation",
                "monitoring_setup"
            ],
            "metadata": {
                "deployment_id": deployment_id,
                "experiment_id": experiment_id
            }
        })
        
        # Record initial observation
        await self.observe({
            "type": "deployment",
            "source": "orchestration",
            "data": {
                "deployment_id": deployment_id,
                "project_name": project_name,
                "phase": "monitoring_setup",
                "experiment_id": experiment_id,
                "workflow_id": workflow_id
            },
            "tags": {
                "project": project_name,
                "deployment": deployment_id
            }
        })
        
        return {
            "experiment_id": experiment_id,
            "workflow_id": workflow_id,
            "monitoring_enabled": True
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on observation services."""
        try:
            wandb_status = await self._check_wandb_health()
            weave_status = await self._check_weave_health()
            
            return {
                "status": "healthy" if wandb_status and weave_status else "unhealthy",
                "wandb_status": wandb_status,
                "weave_status": weave_status,
                "observations_count": len(self._observations),
                "metrics_count": len(self._metrics),
                "active_experiments": len(self._experiments),
                "active_workflows": len(self._active_workflows)
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def get_status(self) -> Dict[str, Any]:
        """Get comprehensive observer status."""
        return {
            "initialized": self._initialized,
            "observations_count": len(self._observations),
            "metrics_count": len(self._metrics),
            "active_experiments": len(self._experiments),
            "active_workflows": len(self._active_workflows),
            "metric_buffers": {name: len(buffer) for name, buffer in self._metric_buffers.items()}
        }
    
    # Private methods
    
    async def _initialize_wandb(self) -> None:
        """Initialize Wandb connection."""
        # TODO: Implement actual Wandb initialization
        # This would initialize wandb with proper credentials and project settings
        logger.info("Wandb initialized (mock)")
    
    async def _initialize_weave(self) -> None:
        """Initialize Weave connection."""
        # TODO: Implement actual Weave initialization
        # This would initialize weave with proper credentials and project settings
        logger.info("Weave initialized (mock)")
    
    async def _send_to_wandb(self, observation: Observation) -> None:
        """Send observation to Wandb."""
        # TODO: Implement actual Wandb logging
        logger.debug(f"Sent observation to Wandb: {observation.observation_id}")
    
    async def _send_to_weave(self, observation: Observation) -> None:
        """Send observation to Weave."""
        # TODO: Implement actual Weave logging
        logger.debug(f"Sent observation to Weave: {observation.observation_id}")
    
    async def _start_wandb_run(self, experiment: Experiment) -> None:
        """Start a Wandb run for experiment."""
        # TODO: Implement actual Wandb run initialization
        logger.debug(f"Started Wandb run for experiment: {experiment.experiment_id}")
    
    async def _end_wandb_run(self, experiment: Experiment) -> None:
        """End a Wandb run."""
        # TODO: Implement actual Wandb run finalization
        logger.debug(f"Ended Wandb run for experiment: {experiment.experiment_id}")
    
    async def _start_weave_workflow(self, workflow: Dict[str, Any]) -> None:
        """Start a Weave workflow."""
        # TODO: Implement actual Weave workflow initialization
        logger.debug(f"Started Weave workflow: {workflow['workflow_id']}")
    
    async def _update_weave_workflow_step(self, workflow: Dict[str, Any], step_index: int, step_data: Dict[str, Any]) -> None:
        """Update a Weave workflow step."""
        # TODO: Implement actual Weave workflow step update
        logger.debug(f"Updated Weave workflow step: {workflow['workflow_id']} step {step_index}")
    
    async def _complete_weave_workflow(self, workflow: Dict[str, Any]) -> None:
        """Complete a Weave workflow."""
        # TODO: Implement actual Weave workflow completion
        logger.debug(f"Completed Weave workflow: {workflow['workflow_id']}")
    
    async def _flush_metric_buffer(self, metric_name: str) -> None:
        """Flush metrics buffer to backend."""
        buffer = self._metric_buffers.get(metric_name, [])
        if not buffer:
            return
        
        # TODO: Implement actual metric flushing to Wandb/Weave
        logger.debug(f"Flushed {len(buffer)} metrics for {metric_name}")
        
        # Clear buffer
        self._metric_buffers[metric_name] = []
    
    async def _flush_all_data(self) -> None:
        """Flush all buffered data."""
        # Flush all metric buffers
        for metric_name in list(self._metric_buffers.keys()):
            await self._flush_metric_buffer(metric_name)
        
        # End all active experiments
        for experiment_id in list(self._experiments.keys()):
            await self.end_experiment(experiment_id, "shutdown")
        
        # Complete all active workflows
        for workflow_id in list(self._active_workflows.keys()):
            await self.complete_workflow(workflow_id, "shutdown")
    
    async def _cleanup_connections(self) -> None:
        """Cleanup connections to external services."""
        # TODO: Implement actual connection cleanup
        logger.info("Cleaned up observer connections")
    
    async def _check_wandb_health(self) -> bool:
        """Check Wandb service health."""
        # TODO: Implement actual Wandb health check
        return True
    
    async def _check_weave_health(self) -> bool:
        """Check Weave service health."""
        # TODO: Implement actual Weave health check
        return True
    
    async def _start_background_tasks(self) -> None:
        """Start background tasks."""
        # Metric flushing task
        self._background_tasks.append(
            asyncio.create_task(self._metric_flushing_loop())
        )
        
        # Data cleanup task
        self._background_tasks.append(
            asyncio.create_task(self._data_cleanup_loop())
        )
        
        # Health monitoring task
        self._background_tasks.append(
            asyncio.create_task(self._health_monitoring_loop())
        )
    
    async def _metric_flushing_loop(self) -> None:
        """Background task for flushing metrics."""
        while not self._shutdown_event.is_set():
            try:
                # Flush all metric buffers
                for metric_name in list(self._metric_buffers.keys()):
                    if self._metric_buffers[metric_name]:
                        await self._flush_metric_buffer(metric_name)
                
                await asyncio.sleep(self._flush_interval)
            except Exception as e:
                logger.error(f"Metric flushing error: {e}")
                await asyncio.sleep(self._flush_interval)
    
    async def _data_cleanup_loop(self) -> None:
        """Background task for data cleanup."""
        while not self._shutdown_event.is_set():
            try:
                # Clean up old observations (keep last 1000)
                if len(self._observations) > 1000:
                    self._observations = self._observations[-1000:]
                
                # Clean up old metrics (keep last 1000)
                if len(self._metrics) > 1000:
                    self._metrics = self._metrics[-1000:]
                
                # Clean up completed experiments older than 24 hours
                cutoff_time = datetime.utcnow() - timedelta(hours=24)
                completed_experiments = [
                    exp_id for exp_id, exp in self._experiments.items()
                    if exp.status == "completed" and exp.completed_at and exp.completed_at < cutoff_time
                ]
                
                for exp_id in completed_experiments:
                    self._experiments.pop(exp_id, None)
                
                await asyncio.sleep(3600)  # Cleanup every hour
            except Exception as e:
                logger.error(f"Data cleanup error: {e}")
                await asyncio.sleep(3600)
    
    async def _health_monitoring_loop(self) -> None:
        """Background task for health monitoring."""
        while not self._shutdown_event.is_set():
            try:
                health_status = await self.health_check()
                if health_status["status"] != "healthy":
                    logger.warning(f"Observer health check failed: {health_status}")
                
                await asyncio.sleep(300)  # Check every 5 minutes
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(300)

