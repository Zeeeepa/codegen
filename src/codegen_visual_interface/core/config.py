"""
Configuration Management for Codegen Visual Interface

This module provides comprehensive configuration management for the visual interface,
including environment-specific settings, integration configurations, and runtime parameters.
"""

import os
import json
import yaml
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

@dataclass
class APIConfig:
    """Configuration for Codegen API integration."""
    base_url: str = "https://api.codegen.com"
    api_token: Optional[str] = None
    organization_id: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3
    rate_limit_requests: int = 60
    rate_limit_window: int = 30
    
    def validate(self) -> bool:
        """Validate API configuration."""
        if not self.api_token:
            logger.error("API token is required")
            return False
        
        if not self.organization_id:
            logger.error("Organization ID is required")
            return False
        
        return True

@dataclass
class ROMAConfig:
    """Configuration for ROMA orchestrator integration."""
    endpoint: str = "http://localhost:8080"
    api_key: Optional[str] = None
    timeout: int = 300
    max_task_depth: int = 5
    task_timeout: int = 300
    parallel_limit: int = 10
    
    def validate(self) -> bool:
        """Validate ROMA configuration."""
        return True  # ROMA integration is optional

@dataclass
class ZAIConfig:
    """Configuration for Z.AI intelligence substrate."""
    base_url: str = "https://api.z.ai"
    api_key: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3
    parallel_limit: int = 50
    proxy_rotation: bool = True
    
    def validate(self) -> bool:
        """Validate Z.AI configuration."""
        return True  # Z.AI integration is optional

@dataclass
class GrainchainConfig:
    """Configuration for Grainchain sandbox management."""
    endpoint: str = "https://grainchain.example.com"
    api_key: Optional[str] = None
    timeout: int = 300
    max_sandboxes: int = 50
    default_cpu_limit: str = "2"
    default_memory_limit: str = "4Gi"
    default_storage_limit: str = "10Gi"
    
    def validate(self) -> bool:
        """Validate Grainchain configuration."""
        return True  # Grainchain integration is optional

@dataclass
class MonitoringConfig:
    """Configuration for monitoring and observability."""
    enabled: bool = True
    wandb_project: Optional[str] = None
    wandb_entity: Optional[str] = None
    wandb_api_key: Optional[str] = None
    weave_project: Optional[str] = None
    metrics_interval: int = 60
    
    def validate(self) -> bool:
        """Validate monitoring configuration."""
        return True  # Monitoring is optional

@dataclass
class StorageConfig:
    """Configuration for data storage."""
    sqlite_path: str = "data/visual_interface.db"
    redis_url: Optional[str] = None
    cache_ttl: int = 3600
    session_ttl: int = 86400  # 24 hours
    cleanup_interval: int = 3600
    
    def validate(self) -> bool:
        """Validate storage configuration."""
        # Ensure SQLite directory exists
        sqlite_dir = Path(self.sqlite_path).parent
        sqlite_dir.mkdir(parents=True, exist_ok=True)
        return True

@dataclass
class UIConfig:
    """Configuration for user interface."""
    theme: str = "dark"
    language: str = "en"
    auto_refresh_interval: int = 5
    max_workflow_nodes: int = 100
    enable_animations: bool = True
    enable_notifications: bool = True
    
    def validate(self) -> bool:
        """Validate UI configuration."""
        return True

@dataclass
class ChatConfig:
    """Configuration for AI chat interface."""
    enabled: bool = True
    model: str = "gpt-4"
    max_context_length: int = 8000
    response_timeout: int = 30
    enable_voice: bool = False
    enable_streaming: bool = True
    
    def validate(self) -> bool:
        """Validate chat configuration."""
        return True

@dataclass
class SecurityConfig:
    """Configuration for security settings."""
    enable_encryption: bool = True
    session_encryption_key: Optional[str] = None
    api_rate_limiting: bool = True
    audit_logging: bool = True
    max_session_duration: int = 28800  # 8 hours
    
    def validate(self) -> bool:
        """Validate security configuration."""
        return True

class VisualInterfaceConfig:
    """
    Comprehensive configuration for Codegen Visual Interface
    
    This class manages all configuration aspects of the visual interface,
    including API integrations, UI settings, security, and runtime parameters.
    """
    
    def __init__(self):
        """Initialize configuration with defaults."""
        # Core configurations
        self.api = APIConfig()
        self.roma = ROMAConfig()
        self.zai = ZAIConfig()
        self.grainchain = GrainchainConfig()
        self.monitoring = MonitoringConfig()
        self.storage = StorageConfig()
        self.ui = UIConfig()
        self.chat = ChatConfig()
        self.security = SecurityConfig()
        
        # Runtime settings
        self.environment: str = "development"
        self.debug: bool = False
        self.log_level: str = "INFO"
        
        # System settings
        self.health_check_interval: int = 30
        self.session_maintenance_interval: int = 300
        self.background_task_interval: int = 60
        
        # User context
        self.user_id: Optional[str] = None
        self.organization_id: Optional[str] = None
        
        # Feature flags
        self.features: Dict[str, bool] = {
            "roma_integration": True,
            "zai_integration": True,
            "grainchain_integration": True,
            "visual_workflows": True,
            "ai_chat": True,
            "trace_intelligence": True,
            "project_management": True,
            "real_time_monitoring": True
        }
    
    @classmethod
    def load_default(cls) -> 'VisualInterfaceConfig':
        """Load default configuration."""
        config = cls()
        config._load_from_environment()
        return config
    
    @classmethod
    def load_from_file(cls, config_path: Union[str, Path]) -> 'VisualInterfaceConfig':
        """Load configuration from file."""
        config = cls()
        config_path = Path(config_path)
        
        if not config_path.exists():
            logger.warning(f"Configuration file not found: {config_path}")
            config._load_from_environment()
            return config
        
        try:
            if config_path.suffix.lower() in ['.yaml', '.yml']:
                with open(config_path, 'r') as f:
                    data = yaml.safe_load(f)
            elif config_path.suffix.lower() == '.json':
                with open(config_path, 'r') as f:
                    data = json.load(f)
            else:
                logger.error(f"Unsupported configuration file format: {config_path.suffix}")
                config._load_from_environment()
                return config
            
            config._load_from_dict(data)
            config._load_from_environment()  # Environment variables override file settings
            
        except Exception as e:
            logger.error(f"Failed to load configuration from {config_path}: {e}")
            config._load_from_environment()
        
        return config
    
    def _load_from_environment(self) -> None:
        """Load configuration from environment variables."""
        # API configuration
        self.api.api_token = os.getenv('CODEGEN_API_TOKEN', self.api.api_token)
        self.api.organization_id = os.getenv('CODEGEN_ORG_ID', self.api.organization_id)
        self.api.base_url = os.getenv('CODEGEN_API_URL', self.api.base_url)
        
        # ROMA configuration
        self.roma.endpoint = os.getenv('ROMA_ENDPOINT', self.roma.endpoint)
        self.roma.api_key = os.getenv('ROMA_API_KEY', self.roma.api_key)
        
        # Z.AI configuration
        self.zai.api_key = os.getenv('ZAI_API_KEY', self.zai.api_key)
        self.zai.base_url = os.getenv('ZAI_BASE_URL', self.zai.base_url)
        
        # Grainchain configuration
        self.grainchain.endpoint = os.getenv('GRAINCHAIN_ENDPOINT', self.grainchain.endpoint)
        self.grainchain.api_key = os.getenv('GRAINCHAIN_API_KEY', self.grainchain.api_key)
        
        # Monitoring configuration
        self.monitoring.wandb_api_key = os.getenv('WANDB_API_KEY', self.monitoring.wandb_api_key)
        self.monitoring.wandb_project = os.getenv('WANDB_PROJECT', self.monitoring.wandb_project)
        self.monitoring.wandb_entity = os.getenv('WANDB_ENTITY', self.monitoring.wandb_entity)
        
        # Storage configuration
        self.storage.redis_url = os.getenv('REDIS_URL', self.storage.redis_url)
        self.storage.sqlite_path = os.getenv('SQLITE_PATH', self.storage.sqlite_path)
        
        # Runtime settings
        self.environment = os.getenv('ENVIRONMENT', self.environment)
        self.debug = os.getenv('DEBUG', 'false').lower() == 'true'
        self.log_level = os.getenv('LOG_LEVEL', self.log_level)
        
        # User context
        self.user_id = os.getenv('USER_ID', self.user_id)
        self.organization_id = os.getenv('ORGANIZATION_ID', self.organization_id)
    
    def _load_from_dict(self, data: Dict[str, Any]) -> None:
        """Load configuration from dictionary."""
        # API configuration
        if 'api' in data:
            api_data = data['api']
            self.api.base_url = api_data.get('base_url', self.api.base_url)
            self.api.timeout = api_data.get('timeout', self.api.timeout)
            self.api.max_retries = api_data.get('max_retries', self.api.max_retries)
        
        # ROMA configuration
        if 'roma' in data:
            roma_data = data['roma']
            self.roma.endpoint = roma_data.get('endpoint', self.roma.endpoint)
            self.roma.timeout = roma_data.get('timeout', self.roma.timeout)
            self.roma.max_task_depth = roma_data.get('max_task_depth', self.roma.max_task_depth)
        
        # Z.AI configuration
        if 'zai' in data:
            zai_data = data['zai']
            self.zai.base_url = zai_data.get('base_url', self.zai.base_url)
            self.zai.timeout = zai_data.get('timeout', self.zai.timeout)
            self.zai.parallel_limit = zai_data.get('parallel_limit', self.zai.parallel_limit)
        
        # Grainchain configuration
        if 'grainchain' in data:
            grainchain_data = data['grainchain']
            self.grainchain.endpoint = grainchain_data.get('endpoint', self.grainchain.endpoint)
            self.grainchain.timeout = grainchain_data.get('timeout', self.grainchain.timeout)
            self.grainchain.max_sandboxes = grainchain_data.get('max_sandboxes', self.grainchain.max_sandboxes)
        
        # Storage configuration
        if 'storage' in data:
            storage_data = data['storage']
            self.storage.sqlite_path = storage_data.get('sqlite_path', self.storage.sqlite_path)
            self.storage.cache_ttl = storage_data.get('cache_ttl', self.storage.cache_ttl)
        
        # UI configuration
        if 'ui' in data:
            ui_data = data['ui']
            self.ui.theme = ui_data.get('theme', self.ui.theme)
            self.ui.language = ui_data.get('language', self.ui.language)
            self.ui.auto_refresh_interval = ui_data.get('auto_refresh_interval', self.ui.auto_refresh_interval)
        
        # Feature flags
        if 'features' in data:
            self.features.update(data['features'])
        
        # Runtime settings
        self.environment = data.get('environment', self.environment)
        self.debug = data.get('debug', self.debug)
        self.log_level = data.get('log_level', self.log_level)
    
    def validate(self) -> bool:
        """Validate all configuration sections."""
        valid = True
        
        # Validate each configuration section
        if not self.api.validate():
            logger.error("API configuration validation failed")
            valid = False
        
        if not self.roma.validate():
            logger.error("ROMA configuration validation failed")
            valid = False
        
        if not self.zai.validate():
            logger.error("Z.AI configuration validation failed")
            valid = False
        
        if not self.grainchain.validate():
            logger.error("Grainchain configuration validation failed")
            valid = False
        
        if not self.monitoring.validate():
            logger.error("Monitoring configuration validation failed")
            valid = False
        
        if not self.storage.validate():
            logger.error("Storage configuration validation failed")
            valid = False
        
        if not self.ui.validate():
            logger.error("UI configuration validation failed")
            valid = False
        
        if not self.chat.validate():
            logger.error("Chat configuration validation failed")
            valid = False
        
        if not self.security.validate():
            logger.error("Security configuration validation failed")
            valid = False
        
        return valid
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'api': {
                'base_url': self.api.base_url,
                'timeout': self.api.timeout,
                'max_retries': self.api.max_retries,
                'rate_limit_requests': self.api.rate_limit_requests,
                'rate_limit_window': self.api.rate_limit_window
            },
            'roma': {
                'endpoint': self.roma.endpoint,
                'timeout': self.roma.timeout,
                'max_task_depth': self.roma.max_task_depth,
                'task_timeout': self.roma.task_timeout,
                'parallel_limit': self.roma.parallel_limit
            },
            'zai': {
                'base_url': self.zai.base_url,
                'timeout': self.zai.timeout,
                'max_retries': self.zai.max_retries,
                'parallel_limit': self.zai.parallel_limit,
                'proxy_rotation': self.zai.proxy_rotation
            },
            'grainchain': {
                'endpoint': self.grainchain.endpoint,
                'timeout': self.grainchain.timeout,
                'max_sandboxes': self.grainchain.max_sandboxes,
                'default_cpu_limit': self.grainchain.default_cpu_limit,
                'default_memory_limit': self.grainchain.default_memory_limit,
                'default_storage_limit': self.grainchain.default_storage_limit
            },
            'monitoring': {
                'enabled': self.monitoring.enabled,
                'metrics_interval': self.monitoring.metrics_interval
            },
            'storage': {
                'sqlite_path': self.storage.sqlite_path,
                'cache_ttl': self.storage.cache_ttl,
                'session_ttl': self.storage.session_ttl,
                'cleanup_interval': self.storage.cleanup_interval
            },
            'ui': {
                'theme': self.ui.theme,
                'language': self.ui.language,
                'auto_refresh_interval': self.ui.auto_refresh_interval,
                'max_workflow_nodes': self.ui.max_workflow_nodes,
                'enable_animations': self.ui.enable_animations,
                'enable_notifications': self.ui.enable_notifications
            },
            'chat': {
                'enabled': self.chat.enabled,
                'model': self.chat.model,
                'max_context_length': self.chat.max_context_length,
                'response_timeout': self.chat.response_timeout,
                'enable_voice': self.chat.enable_voice,
                'enable_streaming': self.chat.enable_streaming
            },
            'security': {
                'enable_encryption': self.security.enable_encryption,
                'api_rate_limiting': self.security.api_rate_limiting,
                'audit_logging': self.security.audit_logging,
                'max_session_duration': self.security.max_session_duration
            },
            'environment': self.environment,
            'debug': self.debug,
            'log_level': self.log_level,
            'features': self.features,
            'health_check_interval': self.health_check_interval,
            'session_maintenance_interval': self.session_maintenance_interval,
            'background_task_interval': self.background_task_interval
        }
    
    def save_to_file(self, config_path: Union[str, Path]) -> None:
        """Save configuration to file."""
        config_path = Path(config_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = self.to_dict()
        
        try:
            if config_path.suffix.lower() in ['.yaml', '.yml']:
                with open(config_path, 'w') as f:
                    yaml.dump(data, f, default_flow_style=False, indent=2)
            elif config_path.suffix.lower() == '.json':
                with open(config_path, 'w') as f:
                    json.dump(data, f, indent=2)
            else:
                logger.error(f"Unsupported configuration file format: {config_path.suffix}")
                return
            
            logger.info(f"Configuration saved to {config_path}")
            
        except Exception as e:
            logger.error(f"Failed to save configuration to {config_path}: {e}")
    
    def is_feature_enabled(self, feature: str) -> bool:
        """Check if a feature is enabled."""
        return self.features.get(feature, False)
    
    def enable_feature(self, feature: str) -> None:
        """Enable a feature."""
        self.features[feature] = True
    
    def disable_feature(self, feature: str) -> None:
        """Disable a feature."""
        self.features[feature] = False
    
    def __repr__(self) -> str:
        """String representation."""
        return f"VisualInterfaceConfig(environment={self.environment}, features={len(self.features)})"
