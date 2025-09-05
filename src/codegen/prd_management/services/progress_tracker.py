"""
Progress Tracker - Tracks and reports progress of PRD implementation
"""

import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ..core.prd_template import TaskStatus
from .websocket_service import WebSocketService


class ProgressPhase(Enum):
    PRD_GENERATION = "prd_generation"
    TASK_BREAKDOWN = "task_breakdown"
    IMPLEMENTATION = "implementation"
    VALIDATION = "validation"
    DEPLOYMENT = "deployment"
    COMPLETED = "completed"


@dataclass
class TaskProgress:
    task_id: str
    title: str
    status: TaskStatus
    progress_percentage: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    error: Optional[str] = None


@dataclass
class PhaseProgress:
    phase: ProgressPhase
    status: str = "pending"  # pending, in_progress, completed, failed
    progress_percentage: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PRDProgress:
    prd_id: str
    overall_status: str = "pending"
    overall_progress: float = 0.0
    current_phase: ProgressPhase = ProgressPhase.PRD_GENERATION
    phases: Dict[ProgressPhase, PhaseProgress] = field(default_factory=dict)
    tasks: Dict[str, TaskProgress] = field(default_factory=dict)
    start_time: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    metrics: Dict[str, Any] = field(default_factory=dict)


class ProgressTracker:
    """
    Service for tracking and reporting progress of PRD implementations
    """
    
    def __init__(self, websocket_service: WebSocketService):
        self.websocket_service = websocket_service
        self.prd_progress: Dict[str, PRDProgress] = {}
        
        # Phase weights for overall progress calculation
        self.phase_weights = {
            ProgressPhase.PRD_GENERATION: 0.15,
            ProgressPhase.TASK_BREAKDOWN: 0.10,
            ProgressPhase.IMPLEMENTATION: 0.50,
            ProgressPhase.VALIDATION: 0.20,
            ProgressPhase.DEPLOYMENT: 0.05
        }
    
    async def initialize_prd_progress(self, prd_id: str, total_tasks: int = 0) -> None:
        """
        Initialize progress tracking for a PRD
        
        Args:
            prd_id: PRD identifier
            total_tasks: Total number of tasks (if known)
        """
        
        # Initialize phases
        phases = {}
        for phase in ProgressPhase:
            phases[phase] = PhaseProgress(phase=phase)
        
        progress = PRDProgress(
            prd_id=prd_id,
            phases=phases,
            start_time=datetime.now()
        )
        
        self.prd_progress[prd_id] = progress
        
        # Broadcast initialization
        self.websocket_service.send('progress_initialized', {
            'prd_id': prd_id,
            'total_tasks': total_tasks,
            'phases': list(phase.value for phase in ProgressPhase)
        })
    
    async def start_phase(self, prd_id: str, phase: ProgressPhase, details: Dict[str, Any] = None) -> None:
        """
        Start a new phase
        
        Args:
            prd_id: PRD identifier
            phase: Phase being started
            details: Additional phase details
        """
        
        if prd_id not in self.prd_progress:
            await self.initialize_prd_progress(prd_id)
        
        progress = self.prd_progress[prd_id]
        progress.current_phase = phase
        
        phase_progress = progress.phases[phase]
        phase_progress.status = "in_progress"
        phase_progress.start_time = datetime.now()
        phase_progress.details = details or {}
        
        # Update overall progress
        await self._update_overall_progress(prd_id)
        
        # Broadcast phase start
        self.websocket_service.send('phase_started', {
            'prd_id': prd_id,
            'phase': phase.value,
            'details': details
        })
    
    async def update_phase_progress(
        self,
        prd_id: str,
        phase: ProgressPhase,
        progress_percentage: float,
        details: Dict[str, Any] = None
    ) -> None:
        """
        Update progress for a specific phase
        
        Args:
            prd_id: PRD identifier
            phase: Phase being updated
            progress_percentage: Progress percentage (0-100)
            details: Additional details
        """
        
        if prd_id not in self.prd_progress:
            return
        
        progress = self.prd_progress[prd_id]
        phase_progress = progress.phases[phase]
        
        phase_progress.progress_percentage = min(100.0, max(0.0, progress_percentage))
        if details:
            phase_progress.details.update(details)
        
        # Update overall progress
        await self._update_overall_progress(prd_id)
        
        # Broadcast phase progress
        self.websocket_service.send('phase_progress', {
            'prd_id': prd_id,
            'phase': phase.value,
            'progress': progress_percentage,
            'details': details
        })
    
    async def complete_phase(
        self,
        prd_id: str,
        phase: ProgressPhase,
        success: bool = True,
        details: Dict[str, Any] = None
    ) -> None:
        """
        Mark a phase as completed
        
        Args:
            prd_id: PRD identifier
            phase: Phase being completed
            success: Whether phase completed successfully
            details: Additional completion details
        """
        
        if prd_id not in self.prd_progress:
            return
        
        progress = self.prd_progress[prd_id]
        phase_progress = progress.phases[phase]
        
        phase_progress.status = "completed" if success else "failed"
        phase_progress.progress_percentage = 100.0 if success else phase_progress.progress_percentage
        phase_progress.end_time = datetime.now()
        
        if phase_progress.start_time:
            phase_progress.duration = (phase_progress.end_time - phase_progress.start_time).total_seconds()
        
        if details:
            phase_progress.details.update(details)
        
        # Update overall progress
        await self._update_overall_progress(prd_id)
        
        # Broadcast phase completion
        self.websocket_service.send('phase_completed', {
            'prd_id': prd_id,
            'phase': phase.value,
            'success': success,
            'duration': phase_progress.duration,
            'details': details
        })
    
    async def update_task_progress(
        self,
        prd_id: str,
        task_id: str,
        status: TaskStatus,
        progress_percentage: float = None,
        error: str = None
    ) -> None:
        """
        Update progress for a specific task
        
        Args:
            prd_id: PRD identifier
            task_id: Task identifier
            status: New task status
            progress_percentage: Task progress percentage
            error: Error message if task failed
        """
        
        if prd_id not in self.prd_progress:
            return
        
        progress = self.prd_progress[prd_id]
        
        # Initialize task progress if not exists
        if task_id not in progress.tasks:
            progress.tasks[task_id] = TaskProgress(
                task_id=task_id,
                title=f"Task {task_id}",
                status=status
            )
        
        task_progress = progress.tasks[task_id]
        old_status = task_progress.status
        task_progress.status = status
        task_progress.error = error
        
        if progress_percentage is not None:
            task_progress.progress_percentage = min(100.0, max(0.0, progress_percentage))
        
        # Update timestamps
        if old_status == TaskStatus.PENDING and status == TaskStatus.IN_PROGRESS:
            task_progress.start_time = datetime.now()
        elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            task_progress.end_time = datetime.now()
            if task_progress.start_time:
                task_progress.duration = (task_progress.end_time - task_progress.start_time).total_seconds()
        
        # Update implementation phase progress based on task completion
        await self._update_implementation_progress(prd_id)
        
        # Broadcast task progress
        self.websocket_service.send('task_progress', {
            'prd_id': prd_id,
            'task_id': task_id,
            'status': status.value,
            'progress': task_progress.progress_percentage,
            'error': error
        })
    
    async def _update_implementation_progress(self, prd_id: str) -> None:
        """Update implementation phase progress based on task completion"""
        
        progress = self.prd_progress[prd_id]
        
        if not progress.tasks:
            return
        
        total_tasks = len(progress.tasks)
        completed_tasks = sum(1 for task in progress.tasks.values() if task.status == TaskStatus.COMPLETED)
        failed_tasks = sum(1 for task in progress.tasks.values() if task.status == TaskStatus.FAILED)
        
        # Calculate implementation progress
        implementation_progress = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
        
        await self.update_phase_progress(
            prd_id,
            ProgressPhase.IMPLEMENTATION,
            implementation_progress,
            {
                'completed_tasks': completed_tasks,
                'failed_tasks': failed_tasks,
                'total_tasks': total_tasks
            }
        )
    
    async def _update_overall_progress(self, prd_id: str) -> None:
        """Update overall PRD progress based on phase progress"""
        
        progress = self.prd_progress[prd_id]
        
        # Calculate weighted progress
        total_progress = 0.0
        for phase, weight in self.phase_weights.items():
            phase_progress = progress.phases[phase].progress_percentage
            total_progress += phase_progress * weight
        
        progress.overall_progress = total_progress
        
        # Update overall status
        if total_progress >= 100.0:
            progress.overall_status = "completed"
        elif any(phase.status == "failed" for phase in progress.phases.values()):
            progress.overall_status = "failed"
        elif any(phase.status == "in_progress" for phase in progress.phases.values()):
            progress.overall_status = "in_progress"
        else:
            progress.overall_status = "pending"
        
        # Calculate metrics
        progress.metrics = self._calculate_metrics(progress)
        
        # Broadcast overall progress
        self.websocket_service.send('overall_progress', {
            'prd_id': prd_id,
            'progress': progress.overall_progress,
            'status': progress.overall_status,
            'current_phase': progress.current_phase.value,
            'metrics': progress.metrics
        })
    
    def _calculate_metrics(self, progress: PRDProgress) -> Dict[str, Any]:
        """Calculate progress metrics"""
        
        metrics = {}
        
        # Time metrics
        if progress.start_time:
            elapsed_time = (datetime.now() - progress.start_time).total_seconds()
            metrics['elapsed_time'] = elapsed_time
            
            # Estimate completion time based on current progress
            if progress.overall_progress > 0:
                estimated_total_time = elapsed_time / (progress.overall_progress / 100)
                estimated_remaining_time = estimated_total_time - elapsed_time
                metrics['estimated_remaining_time'] = max(0, estimated_remaining_time)
        
        # Task metrics
        if progress.tasks:
            total_tasks = len(progress.tasks)
            completed_tasks = sum(1 for task in progress.tasks.values() if task.status == TaskStatus.COMPLETED)
            failed_tasks = sum(1 for task in progress.tasks.values() if task.status == TaskStatus.FAILED)
            in_progress_tasks = sum(1 for task in progress.tasks.values() if task.status == TaskStatus.IN_PROGRESS)
            
            metrics.update({
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'failed_tasks': failed_tasks,
                'in_progress_tasks': in_progress_tasks,
                'completion_rate': (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0,
                'failure_rate': (failed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
            })
        
        # Phase metrics
        completed_phases = sum(1 for phase in progress.phases.values() if phase.status == "completed")
        failed_phases = sum(1 for phase in progress.phases.values() if phase.status == "failed")
        
        metrics.update({
            'completed_phases': completed_phases,
            'failed_phases': failed_phases,
            'total_phases': len(progress.phases)
        })
        
        return metrics
    
    def get_prd_progress(self, prd_id: str) -> Optional[PRDProgress]:
        """Get progress for a specific PRD"""
        return self.prd_progress.get(prd_id)
    
    def get_all_progress(self) -> Dict[str, PRDProgress]:
        """Get progress for all PRDs"""
        return self.prd_progress.copy()
    
    def get_active_prds(self) -> List[str]:
        """Get list of PRDs currently in progress"""
        return [
            prd_id for prd_id, progress in self.prd_progress.items()
            if progress.overall_status == "in_progress"
        ]
    
    def get_progress_summary(self) -> Dict[str, Any]:
        """Get summary of all progress"""
        total_prds = len(self.prd_progress)
        active_prds = len(self.get_active_prds())
        completed_prds = sum(1 for p in self.prd_progress.values() if p.overall_status == "completed")
        failed_prds = sum(1 for p in self.prd_progress.values() if p.overall_status == "failed")
        
        return {
            'total_prds': total_prds,
            'active_prds': active_prds,
            'completed_prds': completed_prds,
            'failed_prds': failed_prds,
            'success_rate': (completed_prds / total_prds) * 100 if total_prds > 0 else 0
        }

