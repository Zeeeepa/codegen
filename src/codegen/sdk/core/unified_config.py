"""
Unified Configuration System for Graph-Sitter + SolidLSP + Serena Integration

This module provides a comprehensive configuration schema that maps graph-sitter config parameters
to underlying SolidLSP and Serena configurations, enabling unified project management.
"""

import os
import json
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from enum import Enum

from solidlsp.ls_config import Language, LanguageServerConfig
from solidlsp.settings import SolidLSPSettings
from serena.config.serena_config import ProjectConfig as SerenaProjectConfig


class IntegrationMode(Enum):
    """Integration modes for the unified system"""
    MINIMAL = "minimal"  # Basic tree-sitter only
    LSP_ONLY = "lsp_only"  # Tree-sitter + LSP
    ENHANCED = "enhanced"  # Full integration with Serena
    FULL = "full"  # All features enabled


@dataclass
class LSPConfiguration:
    """Configuration for SolidLSP integration"""
    enabled: bool = True
    auto_start: bool = True
    timeout: int = 30
    max_retries: int = 3
    languages: List[str] = field(default_factory=list)
    custom_servers: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    def to_solidlsp_settings(self) -> SolidLSPSettings:
        """Convert to SolidLSP settings format"""
        return SolidLSPSettings(
            timeout=self.timeout,
            max_retries=self.max_retries
        )


@dataclass
class DiagnosticsConfiguration:
    """Configuration for diagnostic collection and processing"""
    enabled: bool = True
    real_time: bool = True
    severity_filter: List[str] = field(default_factory=lambda: ["error", "warning", "info"])
    auto_refresh: bool = True
    refresh_interval: int = 1000  # milliseconds
    max_diagnostics: int = 1000
    
    def should_include_severity(self, severity: str) -> bool:
        """Check if a diagnostic severity should be included"""
        return severity.lower() in [s.lower() for s in self.severity_filter]


@dataclass
class ErrorResolutionConfiguration:
    """Configuration for automatic error resolution"""
    enabled: bool = True
    auto_apply: bool = False  # Require confirmation by default
    max_attempts: int = 3
    timeout_per_fix: int = 10  # seconds
    backup_before_fix: bool = True
    rollback_on_failure: bool = True
    resolution_strategies: List[str] = field(default_factory=lambda: [
        "lsp_code_actions",
        "pattern_matching",
        "ai_assisted"
    ])
    
    def is_strategy_enabled(self, strategy: str) -> bool:
        """Check if a resolution strategy is enabled"""
        return strategy in self.resolution_strategies


@dataclass
class EnhancedContextConfiguration:
    """Configuration for enhanced context retrieval using AutogenLib"""
    enabled: bool = True
    max_context_depth: int = 3
    include_dependencies: bool = True
    include_type_info: bool = True
    include_variable_scope: bool = True
    include_call_hierarchy: bool = True
    context_cache_size: int = 100
    
    def get_context_features(self) -> Dict[str, bool]:
        """Get enabled context features as a dictionary"""
        return {
            "dependencies": self.include_dependencies,
            "type_info": self.include_type_info,
            "variable_scope": self.include_variable_scope,
            "call_hierarchy": self.include_call_hierarchy
        }


@dataclass
class PerformanceConfiguration:
    """Configuration for performance optimization"""
    cache_enabled: bool = True
    cache_size_mb: int = 256
    lazy_loading: bool = True
    parallel_processing: bool = True
    max_worker_threads: int = 4
    memory_limit_mb: int = 1024
    
    def get_worker_count(self) -> int:
        """Get optimal worker thread count"""
        import multiprocessing
        cpu_count = multiprocessing.cpu_count()
        return min(self.max_worker_threads, cpu_count)


@dataclass
class UnifiedConfiguration:
    """
    Unified configuration that coordinates all system components.
    
    This class maps graph-sitter config parameters to underlying system configurations
    and provides a single source of truth for all integration settings.
    """
    
    # Core graph-sitter parameters
    lspserver: bool = True
    diagnostics: bool = True
    errorautoresolve: bool = True
    enhancedcontext: bool = True
    
    # Integration mode
    mode: IntegrationMode = IntegrationMode.FULL
    
    # Component configurations
    lsp_config: LSPConfiguration = field(default_factory=LSPConfiguration)
    diagnostics_config: DiagnosticsConfiguration = field(default_factory=DiagnosticsConfiguration)
    resolution_config: ErrorResolutionConfiguration = field(default_factory=ErrorResolutionConfiguration)
    context_config: EnhancedContextConfiguration = field(default_factory=EnhancedContextConfiguration)
    performance_config: PerformanceConfiguration = field(default_factory=PerformanceConfiguration)
    
    # Project-specific settings
    project_root: Optional[str] = None
    project_name: Optional[str] = None
    languages: List[str] = field(default_factory=list)
    ignored_paths: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Post-initialization validation and setup"""
        # Sync core parameters with component configurations
        self.lsp_config.enabled = self.lspserver
        self.diagnostics_config.enabled = self.diagnostics
        self.resolution_config.enabled = self.errorautoresolve
        self.context_config.enabled = self.enhancedcontext
        
        # Validate configuration consistency
        self._validate_configuration()
    
    def _validate_configuration(self):
        """Validate configuration for consistency and requirements"""
        if self.resolution_config.enabled and not self.diagnostics_config.enabled:
            raise ValueError("Error resolution requires diagnostics to be enabled")
        
        if self.context_config.enabled and not self.lsp_config.enabled:
            raise ValueError("Enhanced context requires LSP to be enabled")
        
        if self.mode == IntegrationMode.MINIMAL:
            # Disable advanced features for minimal mode
            self.lsp_config.enabled = False
            self.diagnostics_config.enabled = False
            self.resolution_config.enabled = False
            self.context_config.enabled = False
    
    def get_integration_level(self) -> str:
        """Get a description of the current integration level"""
        if not self.lspserver:
            return "Tree-sitter parsing only"
        elif not self.diagnostics:
            return "Tree-sitter + LSP symbols"
        elif not self.errorautoresolve:
            return "Tree-sitter + LSP + Diagnostics"
        elif not self.enhancedcontext:
            return "Tree-sitter + LSP + Auto-resolution"
        else:
            return "Full integration with enhanced context"
    
    def to_serena_config(self) -> Optional[SerenaProjectConfig]:
        """Convert to Serena project configuration if applicable"""
        if not self.project_root:
            return None
        
        # Create basic Serena config - this would need to be expanded
        # based on actual SerenaProjectConfig requirements
        return SerenaProjectConfig(
            project_name=self.project_name or "unified_project",
            # Add other required Serena config parameters
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary format"""
        return {
            "lspserver": self.lspserver,
            "diagnostics": self.diagnostics,
            "errorautoresolve": self.errorautoresolve,
            "enhancedcontext": self.enhancedcontext,
            "mode": self.mode.value,
            "lsp_config": {
                "enabled": self.lsp_config.enabled,
                "auto_start": self.lsp_config.auto_start,
                "timeout": self.lsp_config.timeout,
                "languages": self.lsp_config.languages
            },
            "diagnostics_config": {
                "enabled": self.diagnostics_config.enabled,
                "real_time": self.diagnostics_config.real_time,
                "severity_filter": self.diagnostics_config.severity_filter
            },
            "resolution_config": {
                "enabled": self.resolution_config.enabled,
                "auto_apply": self.resolution_config.auto_apply,
                "max_attempts": self.resolution_config.max_attempts
            },
            "context_config": {
                "enabled": self.context_config.enabled,
                "max_context_depth": self.context_config.max_context_depth,
                "include_dependencies": self.context_config.include_dependencies
            },
            "project_root": self.project_root,
            "project_name": self.project_name,
            "languages": self.languages,
            "ignored_paths": self.ignored_paths
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UnifiedConfiguration":
        """Create configuration from dictionary"""
        config = cls()
        
        # Update core parameters
        config.lspserver = data.get("lspserver", True)
        config.diagnostics = data.get("diagnostics", True)
        config.errorautoresolve = data.get("errorautoresolve", True)
        config.enhancedcontext = data.get("enhancedcontext", True)
        
        # Update mode
        mode_str = data.get("mode", "full")
        config.mode = IntegrationMode(mode_str)
        
        # Update project settings
        config.project_root = data.get("project_root")
        config.project_name = data.get("project_name")
        config.languages = data.get("languages", [])
        config.ignored_paths = data.get("ignored_paths", [])
        
        # Update component configurations
        if "lsp_config" in data:
            lsp_data = data["lsp_config"]
            config.lsp_config.enabled = lsp_data.get("enabled", True)
            config.lsp_config.auto_start = lsp_data.get("auto_start", True)
            config.lsp_config.timeout = lsp_data.get("timeout", 30)
            config.lsp_config.languages = lsp_data.get("languages", [])
        
        # Trigger post-init validation
        config.__post_init__()
        
        return config
    
    @classmethod
    def load_from_file(cls, config_path: Union[str, Path]) -> "UnifiedConfiguration":
        """Load configuration from file (JSON or YAML)"""
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            if config_path.suffix.lower() in ['.yml', '.yaml']:
                data = yaml.safe_load(f)
            else:
                data = json.load(f)
        
        return cls.from_dict(data)
    
    def save_to_file(self, config_path: Union[str, Path]):
        """Save configuration to file"""
        config_path = Path(config_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = self.to_dict()
        
        with open(config_path, 'w', encoding='utf-8') as f:
            if config_path.suffix.lower() in ['.yml', '.yaml']:
                yaml.dump(data, f, default_flow_style=False, indent=2)
            else:
                json.dump(data, f, indent=2)
    
    @classmethod
    def create_default(cls, project_root: str) -> "UnifiedConfiguration":
        """Create default configuration for a project"""
        config = cls()
        config.project_root = str(Path(project_root).resolve())
        config.project_name = Path(project_root).name
        
        # Auto-detect languages based on file extensions
        config.languages = cls._detect_languages(project_root)
        
        # Set up default ignored paths
        config.ignored_paths = [
            ".git/",
            ".venv/",
            "venv/",
            "node_modules/",
            "__pycache__/",
            "*.pyc",
            ".DS_Store",
            "*.log"
        ]
        
        return config
    
    @staticmethod
    def _detect_languages(project_root: str) -> List[str]:
        """Auto-detect programming languages in the project"""
        languages = set()
        project_path = Path(project_root)
        
        # Language detection based on file extensions
        extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.jsx': 'javascript',
            '.java': 'java',
            '.go': 'go',
            '.rs': 'rust',
            '.cpp': 'cpp',
            '.cc': 'cpp',
            '.cxx': 'cpp',
            '.c': 'c',
            '.cs': 'csharp',
            '.rb': 'ruby',
            '.php': 'php',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.clj': 'clojure',
            '.ex': 'elixir',
            '.erl': 'erlang',
            '.hs': 'haskell',
            '.ml': 'ocaml',
            '.fs': 'fsharp',
            '.dart': 'dart',
            '.lua': 'lua',
            '.r': 'r',
            '.R': 'r'
        }
        
        # Scan project files (limit depth to avoid performance issues)
        for file_path in project_path.rglob('*'):
            if file_path.is_file() and file_path.suffix in extension_map:
                languages.add(extension_map[file_path.suffix])
                
                # Stop after finding a reasonable number of languages
                if len(languages) >= 10:
                    break
        
        return sorted(list(languages))


class ConfigurationManager:
    """Manager for unified configuration operations"""
    
    DEFAULT_CONFIG_NAME = "graph-sitter.config.json"
    
    def __init__(self, project_root: Optional[str] = None):
        self.project_root = project_root
        self._config: Optional[UnifiedConfiguration] = None
    
    def load_or_create_config(self, config_path: Optional[str] = None) -> UnifiedConfiguration:
        """Load existing configuration or create default"""
        if config_path is None and self.project_root:
            config_path = os.path.join(self.project_root, self.DEFAULT_CONFIG_NAME)
        
        if config_path and os.path.exists(config_path):
            self._config = UnifiedConfiguration.load_from_file(config_path)
        elif self.project_root:
            self._config = UnifiedConfiguration.create_default(self.project_root)
        else:
            self._config = UnifiedConfiguration()
        
        return self._config
    
    def get_config(self) -> UnifiedConfiguration:
        """Get current configuration"""
        if self._config is None:
            return self.load_or_create_config()
        return self._config
    
    def update_config(self, **kwargs) -> UnifiedConfiguration:
        """Update configuration with new values"""
        config = self.get_config()
        
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        # Trigger validation
        config.__post_init__()
        
        return config
    
    def save_config(self, config_path: Optional[str] = None):
        """Save current configuration to file"""
        if self._config is None:
            raise ValueError("No configuration to save")
        
        if config_path is None and self.project_root:
            config_path = os.path.join(self.project_root, self.DEFAULT_CONFIG_NAME)
        
        if config_path:
            self._config.save_to_file(config_path)
    
    def validate_environment(self) -> Dict[str, bool]:
        """Validate that the environment supports the configured features"""
        config = self.get_config()
        validation_results = {}
        
        # Check if required dependencies are available
        validation_results["tree_sitter"] = self._check_tree_sitter()
        
        if config.lspserver:
            validation_results["solidlsp"] = self._check_solidlsp()
        
        if config.enhancedcontext:
            validation_results["autogenlib"] = self._check_autogenlib()
            validation_results["serena"] = self._check_serena()
        
        return validation_results
    
    def _check_tree_sitter(self) -> bool:
        """Check if tree-sitter is available"""
        try:
            import tree_sitter
            return True
        except ImportError:
            return False
    
    def _check_solidlsp(self) -> bool:
        """Check if SolidLSP is available"""
        try:
            import solidlsp
            return True
        except ImportError:
            return False
    
    def _check_autogenlib(self) -> bool:
        """Check if AutogenLib is available"""
        try:
            from codegen.sdk.extensions import autogenlib
            return True
        except ImportError:
            return False
    
    def _check_serena(self) -> bool:
        """Check if Serena is available"""
        try:
            import serena
            return True
        except ImportError:
            return False
