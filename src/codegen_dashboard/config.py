"""
Enhanced configuration management for the Codegen Dashboard with AI integration.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class APIConfig:
    """API configuration for Codegen and external services."""
    codegen_base_url: str = "https://api.codegen.com"
    codegen_api_key: str = ""
    timeout: int = 30
    max_retries: int = 3
    
    # Z.AI Configuration
    zai_base_url: str = "https://chat.z.ai"
    zai_token: str = ""
    zai_model: str = "glm-4.5v"
    zai_auto_auth: bool = True
    
    # GitHub Configuration (for PR monitoring)
    github_token: str = ""
    github_api_url: str = "https://api.github.com"


@dataclass
class UIConfig:
    """UI configuration for the dashboard."""
    theme: str = "light"  # light, dark
    window_width: int = 1400
    window_height: int = 900
    refresh_interval: int = 30  # seconds
    notification_duration: int = 5  # seconds
    max_notifications: int = 50
    
    # Chat Interface Configuration
    chat_max_messages: int = 100
    chat_context_window: int = 10  # Number of messages to include in context
    chat_auto_scroll: bool = True
    
    # Graph Visualization Configuration
    graph_layout: str = "force"  # force, hierarchical, circular
    graph_node_size: int = 20
    graph_edge_width: int = 2
    graph_max_nodes: int = 500


@dataclass
class MonitoringConfig:
    """Monitoring and polling configuration."""
    auto_refresh: bool = True
    check_interval: int = 10  # seconds
    enable_notifications: bool = True
    enable_system_notifications: bool = True
    monitor_starred_only: bool = False
    
    # Agent Run Monitoring
    poll_running_agents: bool = True
    agent_poll_interval: int = 15  # seconds
    
    # PR Monitoring
    poll_prs: bool = True
    pr_poll_interval: int = 60  # seconds


@dataclass
class AIConfig:
    """AI and analysis configuration."""
    # RepoMaster Configuration
    repomaster_enabled: bool = True
    repomaster_max_context_files: int = 50
    repomaster_analysis_depth: int = 3
    
    # PRD Validation Configuration
    prd_validation_enabled: bool = True
    prd_validation_threshold: float = 0.7  # Confidence threshold
    auto_create_followup: bool = True
    max_followup_attempts: int = 3
    
    # Memory and Context Configuration
    memory_enabled: bool = True
    memory_max_entries: int = 10000
    memory_embedding_model: str = "text-embedding-ada-002"
    context_similarity_threshold: float = 0.8


@dataclass
class DatabaseConfig:
    """Database configuration for memory and persistence."""
    # Local SQLite Configuration
    local_db_path: str = "dashboard.db"
    local_db_enabled: bool = True
    
    # Supabase Configuration
    supabase_url: str = ""
    supabase_key: str = ""
    supabase_enabled: bool = False
    
    # InfinitySQL Configuration
    infinity_sql_url: str = ""
    infinity_sql_token: str = ""
    infinity_sql_enabled: bool = False
    
    # Cache Configuration
    cache_ttl: int = 3600  # seconds
    max_cache_size: int = 1000  # entries


@dataclass
class SecurityConfig:
    """Security and validation configuration."""
    # Validation Gates
    validation_timeout: int = 300  # seconds
    max_concurrent_validations: int = 5
    sandbox_enabled: bool = True
    
    # Script Execution
    allowed_script_extensions: list = None
    script_execution_timeout: int = 600  # seconds
    
    def __post_init__(self):
        if self.allowed_script_extensions is None:
            self.allowed_script_extensions = [".py", ".sh", ".js", ".ts"]


@dataclass
class Config:
    """Main configuration class with all subsections."""
    api: APIConfig = APIConfig()
    ui: UIConfig = UIConfig()
    monitoring: MonitoringConfig = MonitoringConfig()
    ai: AIConfig = AIConfig()
    database: DatabaseConfig = DatabaseConfig()
    security: SecurityConfig = SecurityConfig()
    
    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> 'Config':
        """Load configuration from file."""
        if config_path is None:
            config_path = cls.get_default_config_path()
        
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    data = json.load(f)
                return cls.from_dict(data)
            except Exception as e:
                print(f"Error loading config: {e}")
                return cls()
        else:
            # Create default config
            config = cls()
            config.save(config_path)
            return config
    
    def save(self, config_path: Optional[Path] = None) -> None:
        """Save configuration to file."""
        if config_path is None:
            config_path = self.get_default_config_path()
        
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(config_path, 'w') as f:
                json.dump(self.to_dict(), f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Config':
        """Create config from dictionary."""
        config = cls()
        
        if 'api' in data:
            config.api = APIConfig(**data['api'])
        if 'ui' in data:
            config.ui = UIConfig(**data['ui'])
        if 'monitoring' in data:
            config.monitoring = MonitoringConfig(**data['monitoring'])
        if 'ai' in data:
            config.ai = AIConfig(**data['ai'])
        if 'database' in data:
            config.database = DatabaseConfig(**data['database'])
        if 'security' in data:
            config.security = SecurityConfig(**data['security'])
        
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            'api': asdict(self.api),
            'ui': asdict(self.ui),
            'monitoring': asdict(self.monitoring),
            'ai': asdict(self.ai),
            'database': asdict(self.database),
            'security': asdict(self.security)
        }
    
    @staticmethod
    def get_default_config_path() -> Path:
        """Get the default configuration file path."""
        if os.name == 'nt':  # Windows
            config_dir = Path(os.environ.get('APPDATA', '')) / 'CodegenDashboard'
        else:  # Unix-like
            config_dir = Path.home() / '.config' / 'codegen-dashboard'
        
        return config_dir / 'config.json'
    
    def get_codegen_api_headers(self) -> Dict[str, str]:
        """Get Codegen API headers with authentication."""
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'CodegenDashboard/1.0.0'
        }
        
        if self.api.codegen_api_key:
            headers['Authorization'] = f'Bearer {self.api.codegen_api_key}'
        
        return headers
    
    def get_github_api_headers(self) -> Dict[str, str]:
        """Get GitHub API headers with authentication."""
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'CodegenDashboard/1.0.0'
        }
        
        if self.api.github_token:
            headers['Authorization'] = f'token {self.api.github_token}'
        
        return headers
    
    def validate(self) -> list[str]:
        """Validate configuration and return list of issues."""
        issues = []
        
        # Check required API configurations
        if not self.api.codegen_api_key:
            issues.append("Codegen API key is not configured")
        
        # Check AI configuration
        if self.ai.repomaster_enabled and not self.ai.repomaster_max_context_files:
            issues.append("RepoMaster max context files must be greater than 0")
        
        if self.ai.prd_validation_threshold < 0 or self.ai.prd_validation_threshold > 1:
            issues.append("PRD validation threshold must be between 0 and 1")
        
        # Check database configuration
        if not any([
            self.database.local_db_enabled,
            self.database.supabase_enabled,
            self.database.infinity_sql_enabled
        ]):
            issues.append("At least one database backend must be enabled")
        
        if self.database.supabase_enabled and not self.database.supabase_url:
            issues.append("Supabase URL is required when Supabase is enabled")
        
        if self.database.infinity_sql_enabled and not self.database.infinity_sql_url:
            issues.append("InfinitySQL URL is required when InfinitySQL is enabled")
        
        # Check security configuration
        if self.security.validation_timeout <= 0:
            issues.append("Validation timeout must be greater than 0")
        
        if self.security.max_concurrent_validations <= 0:
            issues.append("Max concurrent validations must be greater than 0")
        
        return issues
    
    def get_memory_config(self) -> Dict[str, Any]:
        """Get memory configuration for AI context management."""
        return {
            'enabled': self.ai.memory_enabled,
            'max_entries': self.ai.memory_max_entries,
            'embedding_model': self.ai.memory_embedding_model,
            'similarity_threshold': self.ai.context_similarity_threshold,
            'database_config': {
                'local_enabled': self.database.local_db_enabled,
                'local_path': self.database.local_db_path,
                'supabase_enabled': self.database.supabase_enabled,
                'supabase_url': self.database.supabase_url,
                'supabase_key': self.database.supabase_key,
                'infinity_sql_enabled': self.database.infinity_sql_enabled,
                'infinity_sql_url': self.database.infinity_sql_url,
                'infinity_sql_token': self.database.infinity_sql_token
            }
        }


# Global configuration instance
config = Config.load()


def reload_config() -> None:
    """Reload configuration from file."""
    global config
    config = Config.load()


def save_config() -> None:
    """Save current configuration to file."""
    global config
    config.save()


def get_config() -> Config:
    """Get the global configuration instance."""
    return config
