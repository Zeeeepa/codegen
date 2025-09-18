"""
Codegen Visual CI/CD Interface

A comprehensive visual flow interface for Codegen with AI chat capabilities,
intelligent trace retrieval, and full CI/CD lifecycle management.

This package provides:
- Visual workflow builder with drag-and-drop interface
- AI-powered chat interface for natural language CI/CD management
- Intelligent trace retrieval and context transfer
- ROMA meta-orchestrator integration
- Z.AI intelligence substrate integration
- Grainchain sandbox management
- Comprehensive project management with PRD support
- Real-time monitoring and observability
"""

__version__ = "1.0.0"
__author__ = "Codegen Team"
__description__ = "Visual CI/CD Interface for Codegen Platform"

# Core imports for easy access
from .core.foundation import CodegenVisualInterface
from .core.config import VisualInterfaceConfig
from .core.exceptions import (
    CodegenVisualInterfaceError,
    APIIntegrationError,
    OrchestrationError,
    TraceRetrievalError
)

# Main interface factory
def create_visual_interface(config=None):
    """
    Create and initialize the Codegen Visual Interface.
    
    Args:
        config: Optional configuration object
        
    Returns:
        CodegenVisualInterface: Initialized interface instance
    """
    if config is None:
        config = VisualInterfaceConfig.load_default()
    
    return CodegenVisualInterface(config)

# Export main components
__all__ = [
    "CodegenVisualInterface",
    "VisualInterfaceConfig", 
    "create_visual_interface",
    "CodegenVisualInterfaceError",
    "APIIntegrationError",
    "OrchestrationError",
    "TraceRetrievalError"
]
