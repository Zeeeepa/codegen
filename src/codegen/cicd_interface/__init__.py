"""
Codegen CI/CD Interface - Revolutionary Visual Flow Management System

A comprehensive CI/CD interface that combines visual pipeline management with 
intelligent AI chat capabilities, all built on top of the robust Codegen platform.

Key Features:
- Visual Flow Canvas: Interactive pipeline builder with drag-and-drop
- AI Chat Interface: Natural language CI/CD operations
- Intelligent Orchestration: ROMA + Z.AI + Grainchain integration
- Trace Intelligence: Systematic learning from agent executions
- Real-time Monitoring: Comprehensive observability and analytics
"""

__version__ = "1.0.0"
__author__ = "Codegen Team"

# Core Components
from .api import EnhancedAPIClient
from .data import UnifiedDatabaseManager
from .config import ConfigurationManager

# Intelligence & Orchestration
from .orchestration import ROMAMetaOrchestrator
from .intelligence import ZAISubstrate, TraceIntelligenceEngine

# Interface Components
from .ui import VisualFlowCanvas, AIChatInterface, RealTimeDashboard
from .projects import ProjectManager

# Integration Components
from .integrations import IntegrationHub

__all__ = [
    # Core
    "EnhancedAPIClient",
    "UnifiedDatabaseManager", 
    "ConfigurationManager",
    
    # Intelligence
    "ROMAMetaOrchestrator",
    "ZAISubstrate",
    "TraceIntelligenceEngine",
    
    # Interface
    "VisualFlowCanvas",
    "AIChatInterface", 
    "RealTimeDashboard",
    "ProjectManager",
    
    # Integration
    "IntegrationHub",
]
