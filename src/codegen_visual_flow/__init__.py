"""
Codegen Visual Flow Interface
============================

A comprehensive CICD visual flow interface that leverages all of Codegen's capabilities
including agent orchestration, trace intelligence, and AI-powered workflow management.

Key Features:
- Interactive pipeline builder with drag-and-drop interface
- Real-time monitoring and execution tracking
- Intelligent trace content transfer between agent runs
- AI-powered chat interface for natural language workflow management
- Advanced agent orchestration with ROMA meta-coordination
- Z.AI substrate integration for intelligent analysis
- Grainchain sandboxing for secure execution environments

Architecture:
- Event-driven architecture with real-time synchronization
- Microservices-based backend with API gateway
- React-based frontend with TypeScript
- WebSocket communication for live updates
- Redis for caching and state management
- PostgreSQL for persistent storage
"""

__version__ = "1.0.0"
__author__ = "Codegen Team"
__email__ = "team@codegen.com"

# Core modules
from .core import EventSystem, MessageQueue, StateManager
from .gateway import APIGateway, RequestRouter
from .websocket import SocketManager, EventHandlers
from .cache import CacheManager, InvalidationEngine
from .auth import AuthManager, RBACController

# Intelligence modules
from .intelligence import TraceAnalyzer, ContextExtractor
from .ai import RecommendationEngine, PatternAnalyzer

# Integration modules
from .plugins import PluginManager, BasePlugin
from .integrations import GitHubEnhanced, LinearEnhanced, SlackEnhanced

# Visual interface modules
from .frontend import WorkflowBuilder, AgentOrchestrator, TraceVisualization

__all__ = [
    # Core
    "EventSystem", "MessageQueue", "StateManager",
    "APIGateway", "RequestRouter",
    "SocketManager", "EventHandlers",
    "CacheManager", "InvalidationEngine",
    "AuthManager", "RBACController",
    
    # Intelligence
    "TraceAnalyzer", "ContextExtractor",
    "RecommendationEngine", "PatternAnalyzer",
    
    # Integration
    "PluginManager", "BasePlugin",
    "GitHubEnhanced", "LinearEnhanced", "SlackEnhanced",
    
    # Frontend
    "WorkflowBuilder", "AgentOrchestrator", "TraceVisualization",
]
