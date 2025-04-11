"""
Configuration manager for the PR Review Agent.
This module provides functionality for loading and managing configuration settings.
"""
import os
import yaml
import logging
from typing import Dict, Any, Optional
logger = logging.getLogger(__name__)
class ConfigManager:
    """
    Configuration manager for the PR Review Agent.
    
    Handles loading configuration from YAML files and environment variables.
    """
    
    def __init__(self, config_path: str = "config/default.yaml"):
        """
        Initialize the configuration manager.
        
        Args:
            config_path: Path to the configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from the YAML file.
        
        Returns:
            Configuration dictionary
        """
        try:
            with open(self.config_path, "r") as f:
                config = yaml.safe_load(f)
            
            # Override with environment variables
            self._override_from_env(config)
            
            return config
        except FileNotFoundError:
            logger.warning(f"Configuration file not found: {self.config_path}")
            logger.warning("Using default configuration")
            
            # Create default configuration
            default_config = self._create_default_config()
            
            # Override with environment variables
            self._override_from_env(default_config)
            
            return default_config
    
    def _create_default_config(self) -> Dict[str, Any]:
        """
        Create default configuration.
        
        Returns:
            Default configuration dictionary
        """
        return {
            "github": {
                "token": "",
                "webhook_secret": "",
                "auto_merge": False,
                "auto_review": True,
                "review_label": "needs-review"
            },
            "validation": {
                "documentation": {
                    "enabled": True,
                    "files": ["README.md", "STRUCTURE.md", "PLAN.md"],
                    "required": False
                },
                "code_quality": {
                    "enabled": True,
                    "linters": ["flake8", "eslint"],
                    "threshold": 0.8
                },
                "tests": {
                    "enabled": True,
                    "required": False,
                    "coverage_threshold": 0.7
                }
            },
            "notification": {
                "slack": {
                    "enabled": False,
                    "token": "",
                    "channel": ""
                },
                "email": {
                    "enabled": False,
                    "smtp_server": "",
                    "smtp_port": 587,
                    "username": "",
                    "password": "",
                    "from_email": "",
                    "to_emails": []
                }
            },
            "storage": {
                "type": "local",
                "path": "data"
            },
            "ai": {
                "provider": "anthropic",
                "model": "claude-3-opus-20240229",
                "api_key": "",
                "temperature": 0.2,
                "max_tokens": 4000
            },
            "server": {
                "host": "0.0.0.0",
                "port": 8000,
                "workers": 4,
                "cors_origins": ["*"]
            }
        }
    
    def _override_from_env(self, config: Dict[str, Any]) -> None:
        """
        Override configuration with environment variables.
        
        Args:
            config: Configuration dictionary to override
        """
        # GitHub configuration
        if os.environ.get("GITHUB_TOKEN"):
            config["github"]["token"] = os.environ.get("GITHUB_TOKEN")
        
        if os.environ.get("GITHUB_WEBHOOK_SECRET"):
            config["github"]["webhook_secret"] = os.environ.get("GITHUB_WEBHOOK_SECRET")
        
        # AI configuration
        if os.environ.get("ANTHROPIC_API_KEY"):
            config["ai"]["api_key"] = os.environ.get("ANTHROPIC_API_KEY")
            config["ai"]["provider"] = "anthropic"
        elif os.environ.get("OPENAI_API_KEY"):
            config["ai"]["api_key"] = os.environ.get("OPENAI_API_KEY")
            config["ai"]["provider"] = "openai"
            config["ai"]["model"] = "gpt-4-turbo"
        
        # Slack configuration
        if os.environ.get("SLACK_BOT_TOKEN"):
            config["notification"]["slack"]["token"] = os.environ.get("SLACK_BOT_TOKEN")
            config["notification"]["slack"]["enabled"] = True
        
        if os.environ.get("SLACK_CHANNEL"):
            config["notification"]["slack"]["channel"] = os.environ.get("SLACK_CHANNEL")
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get the configuration.
        
        Returns:
            Configuration dictionary
        """
        return self.config
    
    def get_value(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.
        
        Args:
            key: Configuration key (dot-separated for nested keys)
            default: Default value if key is not found
            
        Returns:
            Configuration value
        """
        keys = key.split(".")
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def save_config(self, config_path: Optional[str] = None) -> None:
        """
        Save the configuration to a YAML file.
        
        Args:
            config_path: Path to save the configuration file (defaults to self.config_path)
        """
        config_path = config_path or self.config_path
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        with open(config_path, "w") as f:
            yaml.dump(self.config, f, default_flow_style=False)
        
        logger.info(f"Configuration saved to {config_path}")