"""
Enhanced CI/CD Orchestration Layer for Codegen

This module provides comprehensive CI/CD orchestration capabilities integrating:
- ROMA as meta-agent orchestrator
- Z.AI as AI processing engine with proxy rotation
- Grainchain for sandboxing and snapshotting
- Wandb + Weave for observation layer
- Unified data synchronization and session management

Key Components:
- EnhancedCICDOrchestrator: Central CI/CD coordination hub
- ZAIClient: Z.AI integration with parallel processing
- GrainchainManager: Sandbox and deployment management
- ROMACoordinator: Meta-agent task orchestration
- WandbWeaveObserver: Comprehensive monitoring
- UnifiedStorageManager: Multi-backend data coordination
- IntelligentProxyManager: Smart proxy rotation
- EnhancedChatInterface: Natural language CI/CD interface

Usage:
    from codegen.orchestration import get_enhanced_orchestrator
    
    orchestrator = get_enhanced_orchestrator()
    await orchestrator.initialize()
    
    # Deploy a project
    deployment_request = DeploymentRequest(
        project_name="my-app",
        repository_url="https://github.com/user/my-app"
    )
    
    async for status in orchestrator.deploy_project(deployment_request):
        print(f"Progress: {status.progress_percentage}%")
"""

import asyncio
import logging
from typing import Optional

# Enhanced orchestration imports
from codegen.orchestration.enhanced_manager import EnhancedCICDOrchestrator, DeploymentRequest, DeploymentStatus
from codegen.orchestration.chat.enhanced_interface import EnhancedChatInterface
from codegen.orchestration.config.unified_config import UnifiedConfig

# Integration imports
from codegen.orchestration.integrations.zai_client import ZAIClient
from codegen.orchestration.integrations.grainchain_manager import GrainchainManager
from codegen.orchestration.integrations.roma_coordinator import ROMACoordinator
from codegen.orchestration.integrations.wandb_weave_observer import WandbWeaveObserver
from codegen.orchestration.data.unified_storage import UnifiedStorageManager
from codegen.orchestration.proxy.intelligent_rotation import IntelligentProxyManager

# Legacy imports for backward compatibility
from codegen.orchestration.core.manager import AgentOperationsManager
from codegen.orchestration.core.service_registry import ServiceRegistry
from codegen.orchestration.core.session_manager import SessionManager
from codegen.orchestration.chat.interface import ChatInterface

logger = logging.getLogger(__name__)

__version__ = "2.0.0"

# Global orchestration instances
_enhanced_orchestrator: Optional[EnhancedCICDOrchestrator] = None
_enhanced_chat_interface: Optional[EnhancedChatInterface] = None
_legacy_manager: Optional[AgentOperationsManager] = None
_legacy_chat_interface: Optional[ChatInterface] = None

def get_enhanced_orchestrator(config: Optional[UnifiedConfig] = None) -> EnhancedCICDOrchestrator:
    """
    Get the global enhanced CI/CD orchestrator instance.
    
    Args:
        config: Optional configuration (uses default if not provided)
        
    Returns:
        EnhancedCICDOrchestrator instance
    """
    global _enhanced_orchestrator
    
    if _enhanced_orchestrator is None:
        _enhanced_orchestrator = EnhancedCICDOrchestrator(config)
    
    return _enhanced_orchestrator

def get_enhanced_chat_interface(orchestrator: Optional[EnhancedCICDOrchestrator] = None) -> EnhancedChatInterface:
    """
    Get the global enhanced chat interface instance.
    
    Args:
        orchestrator: Optional orchestrator (uses global if not provided)
        
    Returns:
        EnhancedChatInterface instance
    """
    global _enhanced_chat_interface
    
    if _enhanced_chat_interface is None:
        enhanced_orchestrator = orchestrator or get_enhanced_orchestrator()
        _enhanced_chat_interface = EnhancedChatInterface(enhanced_orchestrator)
    
    return _enhanced_chat_interface

def initialize_enhanced_orchestration(config: Optional[UnifiedConfig] = None) -> EnhancedCICDOrchestrator:
    """
    Initialize the enhanced orchestration layer with configuration.
    
    Args:
        config: Optional configuration
        
    Returns:
        Initialized EnhancedCICDOrchestrator
    """
    orchestrator = get_enhanced_orchestrator(config)
    
    # Initialize in background if not already running
    try:
        loop = asyncio.get_event_loop()
        if not loop.is_running():
            asyncio.run(orchestrator.initialize())
        else:
            # Schedule initialization
            asyncio.create_task(orchestrator.initialize())
    except RuntimeError:
        # No event loop, will be initialized when first used
        pass
    
    return orchestrator

# Legacy functions for backward compatibility
def get_orchestration_manager(config: Optional[UnifiedConfig] = None) -> AgentOperationsManager:
    """
    Get the legacy orchestration manager instance (for backward compatibility).
    
    Args:
        config: Optional configuration (uses default if not provided)
        
    Returns:
        AgentOperationsManager instance
    """
    global _legacy_manager
    
    if _legacy_manager is None:
        _legacy_manager = AgentOperationsManager(config)
    
    return _legacy_manager

def get_chat_interface(manager: Optional[AgentOperationsManager] = None) -> ChatInterface:
    """
    Get the legacy chat interface instance (for backward compatibility).
    
    Args:
        manager: Optional orchestration manager (uses global if not provided)
        
    Returns:
        ChatInterface instance
    """
    global _legacy_chat_interface
    
    if _legacy_chat_interface is None:
        orchestration_manager = manager or get_orchestration_manager()
        _legacy_chat_interface = ChatInterface(orchestration_manager)
    
    return _legacy_chat_interface

def initialize_orchestration(config_path: Optional[str] = None) -> AgentOperationsManager:
    """
    Initialize the legacy orchestration layer (for backward compatibility).
    
    Args:
        config_path: Optional path to configuration file
        
    Returns:
        Initialized AgentOperationsManager
    """
    config = UnifiedConfig.load(config_path) if config_path else None
    manager = get_orchestration_manager(config)
    
    # Initialize in background if not already running
    try:
        loop = asyncio.get_event_loop()
        if not loop.is_running():
            asyncio.run(manager.initialize())
        else:
            # Schedule initialization
            asyncio.create_task(manager.initialize())
    except RuntimeError:
        # No event loop, will be initialized when first used
        pass
    
    return manager

# Export main classes for direct import
__all__ = [
    # Enhanced orchestration (primary)
    'EnhancedCICDOrchestrator',
    'EnhancedChatInterface',
    'DeploymentRequest',
    'DeploymentStatus',
    'get_enhanced_orchestrator',
    'get_enhanced_chat_interface',
    'initialize_enhanced_orchestration',
    
    # Integration components
    'ZAIClient',
    'GrainchainManager', 
    'ROMACoordinator',
    'WandbWeaveObserver',
    'UnifiedStorageManager',
    'IntelligentProxyManager',
    
    # Configuration
    'UnifiedConfig',
    
    # Legacy components (backward compatibility)
    'AgentOperationsManager',
    'ServiceRegistry',
    'SessionManager',
    'ChatInterface',
    'get_orchestration_manager',
    'get_chat_interface',
    'initialize_orchestration'
]
