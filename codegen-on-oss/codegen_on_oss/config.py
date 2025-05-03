"""
Configuration system for the codegen-on-oss system.

This module provides a unified configuration system using Pydantic settings
that can be loaded from environment variables, .env files, or explicitly set.
"""

import os
import logging
from typing import Dict, List, Optional, Union, Any
from pathlib import Path

from pydantic import Field, computed_field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class AnalysisConfig(BaseSettings):
    """Unified configuration for analysis components"""
    
    # Application settings
    app_name: str = Field("codegen-on-oss", env="APP_NAME")
    app_version: str = Field("1.0.0", env="APP_VERSION")
    debug: bool = Field(False, env="DEBUG")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    
    # Database settings
    db_url: str = Field("sqlite:///./codegen_analysis.db", env="DB_URL")
    db_echo: bool = Field(False, env="DB_ECHO")
    db_pool_size: int = Field(5, env="DB_POOL_SIZE")
    db_max_overflow: int = Field(10, env="DB_MAX_OVERFLOW")
    
    # Storage settings
    storage_type: str = Field("local", env="STORAGE_TYPE")
    s3_bucket: Optional[str] = Field(None, env="S3_BUCKET")
    s3_region: Optional[str] = Field(None, env="S3_REGION")
    s3_prefix: Optional[str] = Field("codegen-analysis", env="S3_PREFIX")
    local_storage_path: Optional[str] = Field("./storage", env="LOCAL_STORAGE_PATH")
    
    # Analysis settings
    default_analysis_types: List[str] = Field(
        ["code_quality", "dependencies", "security"],
        env="DEFAULT_ANALYSIS_TYPES"
    )
    max_file_size_mb: int = Field(10, env="MAX_FILE_SIZE_MB")
    exclude_patterns: List[str] = Field(
        [".git", "__pycache__", "*.pyc", "node_modules", "venv", ".venv"],
        env="EXCLUDE_PATTERNS"
    )
    
    # API settings
    api_host: str = Field("0.0.0.0", env="API_HOST")
    api_port: int = Field(8000, env="API_PORT")
    api_workers: int = Field(4, env="API_WORKERS")
    enable_graphql: bool = Field(True, env="ENABLE_GRAPHQL")
    enable_websockets: bool = Field(True, env="ENABLE_WEBSOCKETS")
    cors_origins: List[str] = Field(["*"], env="CORS_ORIGINS")
    
    # Authentication settings
    api_key_header: str = Field("X-API-Key", env="API_KEY_HEADER")
    api_keys: List[str] = Field([], env="API_KEYS")
    
    # Task queue settings
    redis_url: Optional[str] = Field(None, env="REDIS_URL")
    task_timeout: int = Field(3600, env="TASK_TIMEOUT")
    max_workers: int = Field(4, env="MAX_WORKERS")
    
    # GitHub settings
    github_token: Optional[str] = Field(None, env="GITHUB_TOKEN")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    @computed_field
    def db_url_safe(self) -> str:
        """Return a safe version of the database URL (with password redacted)"""
        if "://" not in self.db_url:
            return self.db_url
        
        parts = self.db_url.split("://", 1)
        if "@" in parts[1]:
            auth, rest = parts[1].split("@", 1)
            if ":" in auth:
                user, _ = auth.split(":", 1)
                return f"{parts[0]}://{user}:****@{rest}"
        
        return self.db_url
    
    @field_validator("local_storage_path")
    def validate_local_storage_path(cls, v: Optional[str]) -> Optional[str]:
        """Validate and create the local storage path if it doesn't exist"""
        if v and not os.path.exists(v):
            try:
                os.makedirs(v, exist_ok=True)
                logger.info(f"Created local storage directory: {v}")
            except Exception as e:
                logger.warning(f"Failed to create local storage directory: {v} - {str(e)}")
        
        return v
    
    @model_validator(mode="after")
    def validate_storage_config(self) -> "AnalysisConfig":
        """Validate storage configuration"""
        if self.storage_type == "s3" and not self.s3_bucket:
            logger.warning("S3 storage type selected but no S3 bucket specified")
        
        if self.storage_type not in ["local", "s3", "memory"]:
            logger.warning(f"Unknown storage type: {self.storage_type}, falling back to local")
            self.storage_type = "local"
        
        return self


# Create a global settings instance
settings = AnalysisConfig()


def configure_logging() -> None:
    """Configure logging based on settings"""
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    # Reduce verbosity of some loggers
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    logger.info(f"Logging configured at level: {settings.log_level}")


def get_settings() -> AnalysisConfig:
    """
    Get the application settings.
    
    This function is primarily used as a FastAPI dependency.
    
    Returns:
        AnalysisConfig: The application settings
    """
    return settings

