"""
CI/CD Orchestration System

A comprehensive orchestration layer for Codegen agent operations, powered by ROMA
meta-agent coordination with Z.AI intelligence substrate and selective service integration.

This module provides:
- ROMA-based meta-orchestration for hierarchical task coordination
- Z.AI substrate powering all agentic instances
- High-value development services (Codegen Claude + RepoMaster)
- Selective integration of specialized services based on practical value
- Unified data management across SQLite, Redis, and live APIs
- Natural language CI/CD operations through enhanced chat interface

Architecture:
    User Interface (Natural Language)
        ↓
    ROMA Meta-Orchestrator (Direct User Interaction)
        ↓
    Codegen Core Library (Foundation Layer)
        ↓
    Z.AI Substrate (Powers ALL Agentic Instances)
        ↓
    High-Value Agent Services + Selective Integration Services
"""

from .core_orchestrator import CICDOrchestrator
from .roma_integration import ROMAIntegration
from .zai_substrate import ZAISubstrate

__version__ = "0.1.0"

__all__ = [
    "CICDOrchestrator",
    "ROMAIntegration", 
    "ZAISubstrate",
]
