"""
Codegen Visual Orchestration System

This module provides the core orchestration capabilities for managing
visual CI/CD pipelines with parallel agent execution and webhook integration.
"""

__version__ = "1.0.0"
__author__ = "Codegen Team"

from .schemas import PipelineDefinition, StageDefinition, AgentTask
from .engine import OrchestrationEngine
from .parallel_executor import ParallelAgentExecutor
from .webhooks import WebhookManager

__all__ = [
    "PipelineDefinition",
    "StageDefinition", 
    "AgentTask",
    "OrchestrationEngine",
    "ParallelAgentExecutor",
    "WebhookManager"
]