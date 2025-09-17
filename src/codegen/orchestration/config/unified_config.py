"""
Unified Configuration Management

This module provides comprehensive configuration management for the orchestration
layer, supporting multiple configuration sources, environment-specific overrides,
and dynamic configuration updates.
"""

import os
import yaml
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

class Environment(Enum):
    """Deployment environment types."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"

class StorageBackend(Enum):
    """Storage backend types."""
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    REDIS = "redis"
    MEMORY = "memory"

@dataclass
class ServiceConfig:
    """Configuration for a specific service."""
    enabled: bool = True
    base_url: str = ""
    api_key: str = ""
    timeout: int = 30
    max_retries: int = 3
    rate_limits: Dict[str, tuple] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ProxyConfig:
    """Proxy configuration."""
    enabled: bool = False
    pool_size: int = 10
    health_check_interval: int = 30
    rotation_strategy: str = "round_robin"
    proxies: List[Dict[str, str]] = field(default_factory=list)
    
@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""
    global_limit: int = 1000
    per_user_limit: int = 100
    window_seconds: int = 60
    queue_size: int = 500
    burst_allowance: float = 1.5

@dataclass
class DataConfig:
    """Data storage and synchronization configuration."""
    sqlite_path: str = "orchestration.db"
    redis_url: str = "redis://localhost:6379"
    postgres_url: str = ""
    sync_strategy: str = "write_through"
    cache_ttl: int = 3600
    backup_enabled: bool = True
    backup_interval: int = 86400  # 24 hours

@dataclass
class SessionConfig:
    """Session management configuration."""
    storage_backend: str = "memory"
    default_idle_timeout: int = 3600  # 1 hour
    default_max_lifetime: int = 86400  # 24 hours
    cleanup_interval: int = 300  # 5 minutes
    persistent_sessions: bool = True

@dataclass
class MonitoringConfig:
    """Monitoring and observability configuration."""
    enabled: bool = True
    metrics_endpoint: str = "/metrics"
    health_endpoint: str = "/health"
    tracing_enabled: bool = True
    log_level: str = "INFO"
    alert_webhooks: List[str] = field(default_factory=list)

class UnifiedConfig:
    """
    Unified configuration manager for the orchestration layer.
    
    This class manages configuration from multiple sources including:
    - Configuration files (YAML/JSON)
    - Environment variables
    - Command line arguments
    - Runtime overrides
    """
    
    def __init__(self, config_data: Optional[Dict[str, Any]] = None):
        """Initialize configuration with optional data."""
        self._config_data = config_data or {}
        self._environment = self._detect_environment()
        self._config_paths = self._get_config_paths()
        
        # Load configuration from all sources
        self._load_configuration()
        
        logger.info(f"UnifiedConfig initialized for environment: {self._environment.value}")
    
    @classmethod
    def load(cls, config_path: Optional[str] = None) -> 'UnifiedConfig':
        """
        Load configuration from file or default locations.
        
        Args:
            config_path: Optional path to configuration file
            
        Returns:
            UnifiedConfig instance
        """
        config = cls()
        
        if config_path:
            config._load_config_file(config_path)
        
        return config
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.
        
        Args:
            key: Configuration key (supports dot notation)
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self._config_data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        keys = key.split('.')
        config = self._config_data
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def get_environment(self) -> Environment:
        """Get the current environment."""
        return self._environment
    
    def get_services_config(self) -> Dict[str, Dict[str, Any]]:
        """Get services configuration."""
        return self.get('orchestration.services', {})
    
    def get_service_config(self, service_name: str) -> ServiceConfig:
        """Get configuration for a specific service."""
        service_data = self.get(f'orchestration.services.{service_name}', {})
        return ServiceConfig(**service_data)
    
    def get_proxy_config(self) -> ProxyConfig:
        """Get proxy configuration."""
        proxy_data = self.get('orchestration.proxy', {})
        return ProxyConfig(**proxy_data)
    
    def get_rate_limit_config(self) -> RateLimitConfig:
        """Get rate limiting configuration."""
        rate_limit_data = self.get('orchestration.rate_limiting', {})
        return RateLimitConfig(**rate_limit_data)
    
    def get_data_config(self) -> DataConfig:
        """Get data storage configuration."""
        data_config = self.get('orchestration.data', {})
        return DataConfig(**data_config)
    
    def get_session_config(self) -> SessionConfig:
        """Get session management configuration."""
        session_data = self.get('orchestration.session', {})
        return SessionConfig(**session_data)
    
    def get_monitoring_config(self) -> MonitoringConfig:
        """Get monitoring configuration."""
        monitoring_data = self.get('orchestration.monitoring', {})
        return MonitoringConfig(**monitoring_data)
    
    # Session-specific getters for backward compatibility
    def get_session_storage_backend(self) -> str:
        """Get session storage backend."""
        return self.get_session_config().storage_backend
    
    def get_session_cleanup_interval(self) -> int:
        """Get session cleanup interval."""
        return self.get_session_config().cleanup_interval
    
    def get_default_session_idle_timeout(self) -> int:
        """Get default session idle timeout."""
        return self.get_session_config().default_idle_timeout
    
    def get_default_session_max_lifetime(self) -> int:
        """Get default session max lifetime."""
        return self.get_session_config().default_max_lifetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return self._config_data.copy()
    
    def save_to_file(self, file_path: str) -> None:
        """
        Save configuration to file.
        
        Args:
            file_path: Path to save configuration file
        """
        file_path = Path(file_path)
        
        if file_path.suffix.lower() == '.json':
            with open(file_path, 'w') as f:
                json.dump(self._config_data, f, indent=2, default=str)
        else:
            # Default to YAML
            with open(file_path, 'w') as f:
                yaml.dump(self._config_data, f, default_flow_style=False)
        
        logger.info(f"Configuration saved to {file_path}")
    
    def reload(self) -> None:
        """Reload configuration from all sources."""
        self._load_configuration()
        logger.info("Configuration reloaded")
    
    def validate(self) -> List[str]:
        """
        Validate configuration and return list of issues.
        
        Returns:
            List of validation error messages
        """
        issues = []
        
        # Validate services configuration
        services = self.get_services_config()
        for service_name, service_config in services.items():
            if service_config.get('enabled', False):
                if not service_config.get('base_url'):
                    issues.append(f"Service {service_name} is enabled but missing base_url")
                
                if service_name in ['zai', 'repomaster'] and not service_config.get('api_key'):
                    issues.append(f"Service {service_name} is enabled but missing api_key")
        
        # Validate proxy configuration
        proxy_config = self.get_proxy_config()
        if proxy_config.enabled and not proxy_config.proxies:
            issues.append("Proxy is enabled but no proxies configured")
        
        # Validate data configuration
        data_config = self.get_data_config()
        if data_config.sync_strategy not in ['write_through', 'write_behind', 'read_through']:
            issues.append(f"Invalid sync_strategy: {data_config.sync_strategy}")
        
        return issues
    
    # Private methods
    
    def _detect_environment(self) -> Environment:
        """Detect the current environment."""
        env_name = os.getenv('CODEGEN_ENV', os.getenv('ENVIRONMENT', 'development')).lower()
        
        try:
            return Environment(env_name)
        except ValueError:
            logger.warning(f"Unknown environment '{env_name}', defaulting to development")
            return Environment.DEVELOPMENT
    
    def _get_config_paths(self) -> List[Path]:
        """Get list of configuration file paths to check."""
        paths = []
        
        # Environment-specific config
        env_name = self._environment.value
        
        # Check various locations
        config_locations = [
            Path.cwd() / f"orchestration.{env_name}.yaml",
            Path.cwd() / f"orchestration.{env_name}.yml",
            Path.cwd() / f"orchestration.{env_name}.json",
            Path.cwd() / "orchestration.yaml",
            Path.cwd() / "orchestration.yml",
            Path.cwd() / "orchestration.json",
            Path.home() / ".codegen" / f"orchestration.{env_name}.yaml",
            Path.home() / ".codegen" / "orchestration.yaml",
            Path("/etc/codegen/orchestration.yaml"),
        ]
        
        # Add paths from environment variable
        config_path_env = os.getenv('CODEGEN_CONFIG_PATH')
        if config_path_env:
            paths.append(Path(config_path_env))
        
        paths.extend(config_locations)
        return paths
    
    def _load_configuration(self) -> None:
        """Load configuration from all sources."""
        # Start with default configuration
        self._config_data = self._get_default_config()
        
        # Load from configuration files
        for config_path in self._config_paths:
            if config_path.exists():
                self._load_config_file(str(config_path))
                break
        
        # Override with environment variables
        self._load_environment_variables()
        
        # Apply environment-specific overrides
        self._apply_environment_overrides()
    
    def _load_config_file(self, file_path: str) -> None:
        """Load configuration from a file."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.warning(f"Configuration file not found: {file_path}")
            return
        
        try:
            with open(file_path, 'r') as f:
                if file_path.suffix.lower() == '.json':
                    file_config = json.load(f)
                else:
                    file_config = yaml.safe_load(f)
            
            # Merge with existing configuration
            self._deep_merge(self._config_data, file_config)
            logger.info(f"Loaded configuration from {file_path}")
            
        except Exception as e:
            logger.error(f"Error loading configuration from {file_path}: {e}")
    
    def _load_environment_variables(self) -> None:
        """Load configuration from environment variables."""
        env_mappings = {
            'CODEGEN_ZAI_API_KEY': 'orchestration.services.zai.api_key',
            'CODEGEN_ZAI_BASE_URL': 'orchestration.services.zai.base_url',
            'CODEGEN_REPOMASTER_API_KEY': 'orchestration.services.repomaster.api_key',
            'CODEGEN_REPOMASTER_BASE_URL': 'orchestration.services.repomaster.base_url',
            'CODEGEN_CLAUDE_API_KEY': 'orchestration.services.claude.api_key',
            'CODEGEN_API_BASE_URL': 'orchestration.services.codegen.base_url',
            'CODEGEN_API_KEY': 'orchestration.services.codegen.api_key',
            'REDIS_URL': 'orchestration.data.redis_url',
            'DATABASE_URL': 'orchestration.data.postgres_url',
            'CODEGEN_LOG_LEVEL': 'orchestration.monitoring.log_level',
        }
        
        for env_var, config_key in env_mappings.items():
            value = os.getenv(env_var)
            if value:
                self.set(config_key, value)
    
    def _apply_environment_overrides(self) -> None:
        """Apply environment-specific configuration overrides."""
        if self._environment == Environment.DEVELOPMENT:
            # Development overrides
            self.set('orchestration.monitoring.log_level', 'DEBUG')
            self.set('orchestration.rate_limiting.global_limit', 10000)
            self.set('orchestration.data.backup_enabled', False)
            
        elif self._environment == Environment.STAGING:
            # Staging overrides
            self.set('orchestration.monitoring.log_level', 'INFO')
            self.set('orchestration.rate_limiting.global_limit', 5000)
            
        elif self._environment == Environment.PRODUCTION:
            # Production overrides
            self.set('orchestration.monitoring.log_level', 'WARNING')
            self.set('orchestration.data.backup_enabled', True)
            
        elif self._environment == Environment.TESTING:
            # Testing overrides
            self.set('orchestration.monitoring.log_level', 'ERROR')
            self.set('orchestration.data.sqlite_path', ':memory:')
            self.set('orchestration.session.storage_backend', 'memory')
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            'orchestration': {
                'services': {
                    'zai': {
                        'enabled': False,
                        'base_url': '',
                        'api_key': '',
                        'timeout': 30,
                        'max_retries': 3,
                        'rate_limits': {
                            'parallel_requests': (50, 60),
                            'single_request': (100, 60)
                        }
                    },
                    'repomaster': {
                        'enabled': False,
                        'base_url': '',
                        'api_key': '',
                        'timeout': 60,
                        'max_retries': 3,
                        'rate_limits': {
                            'analysis_request': (20, 60),
                            'file_operations': (30, 60)
                        }
                    },
                    'claude': {
                        'enabled': True,
                        'model': 'claude-3-sonnet',
                        'max_tokens': 4096,
                        'timeout': 30,
                        'rate_limits': {
                            'chat_request': (60, 60),
                            'code_generation': (30, 60)
                        }
                    },
                    'codegen': {
                        'enabled': True,
                        'base_url': 'https://api.codegen.com',
                        'timeout': 120,
                        'max_retries': 3,
                        'rate_limits': {
                            'agent_creation': (10, 60),
                            'status_check': (60, 30),
                            'log_retrieval': (5, 60)
                        }
                    }
                },
                'proxy': {
                    'enabled': False,
                    'pool_size': 10,
                    'health_check_interval': 30,
                    'rotation_strategy': 'round_robin',
                    'proxies': []
                },
                'rate_limiting': {
                    'global_limit': 1000,
                    'per_user_limit': 100,
                    'window_seconds': 60,
                    'queue_size': 500,
                    'burst_allowance': 1.5
                },
                'data': {
                    'sqlite_path': 'orchestration.db',
                    'redis_url': 'redis://localhost:6379',
                    'postgres_url': '',
                    'sync_strategy': 'write_through',
                    'cache_ttl': 3600,
                    'backup_enabled': True,
                    'backup_interval': 86400
                },
                'session': {
                    'storage_backend': 'memory',
                    'default_idle_timeout': 3600,
                    'default_max_lifetime': 86400,
                    'cleanup_interval': 300,
                    'persistent_sessions': True
                },
                'monitoring': {
                    'enabled': True,
                    'metrics_endpoint': '/metrics',
                    'health_endpoint': '/health',
                    'tracing_enabled': True,
                    'log_level': 'INFO',
                    'alert_webhooks': []
                }
            }
        }
    
    def _deep_merge(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """Deep merge source dictionary into target dictionary."""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = value

