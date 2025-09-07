"""
Configuration system for unified graph-sitter integration.

This module provides comprehensive configuration management for the 5 new
graph-sitter parameters with validation, defaults, and integration settings.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import json
import yaml
from enum import Enum


class ContextDepth(Enum):
    """Context analysis depth levels"""
    SHALLOW = 1
    MEDIUM = 3
    DEEP = 5
    COMPREHENSIVE = 10


class ErrorResolutionStrategy(Enum):
    """Error resolution strategies"""
    CONSERVATIVE = "conservative"  # Only safe, obvious fixes
    MODERATE = "moderate"         # Most common error patterns
    AGGRESSIVE = "aggressive"     # All available fixes


@dataclass
class LSPServerConfig:
    """Configuration for LSP server integration"""
    enabled: bool = True
    auto_start: bool = True
    languages: List[str] = field(default_factory=list)  # Auto-detect if empty
    timeout_seconds: int = 30
    max_diagnostics_per_file: int = 100
    enable_code_actions: bool = True
    enable_hover: bool = True
    enable_completion: bool = True
    enable_references: bool = True
    enable_rename: bool = True
    
    # Advanced LSP settings
    workspace_folders: List[str] = field(default_factory=list)
    initialization_options: Dict[str, Any] = field(default_factory=dict)
    server_settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DiagnosticsConfig:
    """Configuration for diagnostic collection"""
    enabled: bool = True
    collect_from_lsp: bool = True
    collect_from_tree_sitter: bool = True
    collect_from_serena: bool = True
    
    # Filtering options
    min_severity: str = "hint"  # hint, info, warning, error
    max_diagnostics_total: int = 1000
    exclude_patterns: List[str] = field(default_factory=list)
    include_patterns: List[str] = field(default_factory=list)
    
    # Real-time updates
    enable_real_time_updates: bool = True
    update_debounce_ms: int = 500
    batch_update_size: int = 50


@dataclass
class ErrorAutoResolveConfig:
    """Configuration for automatic error resolution"""
    enabled: bool = True
    strategy: ErrorResolutionStrategy = ErrorResolutionStrategy.MODERATE
    
    # Resolution types
    resolve_import_errors: bool = True
    resolve_type_errors: bool = False  # More conservative by default
    resolve_syntax_errors: bool = True
    resolve_unused_imports: bool = True
    resolve_missing_docstrings: bool = False
    
    # Safety settings
    require_confirmation: bool = False
    create_backup: bool = True
    max_fixes_per_file: int = 10
    max_fixes_per_session: int = 100
    
    # Context requirements
    require_enhanced_context: bool = True
    min_confidence_score: float = 0.8
    
    # Integration settings
    use_lsp_code_actions: bool = True
    use_serena_tools: bool = True
    use_tree_sitter_analysis: bool = True


@dataclass
class EnhancedContextConfig:
    """Configuration for enhanced context analysis"""
    enabled: bool = True
    depth: ContextDepth = ContextDepth.MEDIUM
    
    # Component integration
    enable_autogenlib: bool = True
    enable_solidlsp_context: bool = True
    enable_serena_symbols: bool = True
    enable_graph_sitter_analysis: bool = True
    
    # Context types
    include_symbol_definitions: bool = True
    include_type_information: bool = True
    include_parameter_info: bool = True
    include_variable_scope: bool = True
    include_import_dependencies: bool = True
    include_usage_patterns: bool = True
    include_similar_code: bool = True
    
    # Analysis settings
    max_context_size_tokens: int = 50000
    max_related_symbols: int = 100
    max_similar_patterns: int = 20
    
    # Performance settings
    enable_caching: bool = True
    cache_ttl_seconds: int = 3600
    enable_parallel_analysis: bool = True
    max_concurrent_analyses: int = 4
    
    # AutogenLib specific
    autogenlib_description: str = "Enhanced context analysis for comprehensive code understanding"
    autogenlib_enable_caching: bool = True
    autogenlib_enable_exception_handler: bool = True


@dataclass
class DocGenConfig:
    """Configuration for documentation generation"""
    enabled: bool = True
    
    # Generation targets
    generate_api_docs: bool = True
    generate_symbol_docs: bool = True
    generate_usage_examples: bool = True
    generate_type_docs: bool = True
    
    # Output formats
    output_formats: List[str] = field(default_factory=lambda: ["json", "mdx"])
    output_directory: str = "docs/generated"
    
    # Content settings
    include_private_symbols: bool = False
    include_inherited_methods: bool = True
    include_source_links: bool = True
    include_type_annotations: bool = True
    
    # Integration with tools
    use_reveal_symbol: bool = True
    use_generate_docs_json: bool = True
    use_mdx_generation: bool = True
    use_document_functions: bool = True
    
    # Advanced features
    auto_update_on_changes: bool = True
    generate_cross_references: bool = True
    include_dependency_graphs: bool = True
    include_usage_statistics: bool = True
    
    # Performance settings
    max_symbols_per_batch: int = 100
    enable_incremental_generation: bool = True
    cache_generated_docs: bool = True


@dataclass
class IntegrationConfig:
    """Master configuration for all integration components"""
    
    # Core parameters (the 5 new graph-sitter parameters)
    lsp_server: bool = True
    diagnostics: bool = True
    error_auto_resolve: bool = True
    enhanced_context: bool = True
    doc_gen: bool = True
    
    # Component configurations
    lsp_config: LSPServerConfig = field(default_factory=LSPServerConfig)
    diagnostics_config: DiagnosticsConfig = field(default_factory=DiagnosticsConfig)
    error_resolve_config: ErrorAutoResolveConfig = field(default_factory=ErrorAutoResolveConfig)
    context_config: EnhancedContextConfig = field(default_factory=EnhancedContextConfig)
    doc_config: DocGenConfig = field(default_factory=DocGenConfig)
    
    # Global settings
    project_root: Optional[str] = None
    config_file_path: Optional[str] = None
    enable_logging: bool = True
    log_level: str = "INFO"
    
    # Performance and resource management
    max_memory_usage_mb: int = 2048
    enable_resource_monitoring: bool = True
    cleanup_on_exit: bool = True
    
    def __post_init__(self):
        """Validate and adjust configuration after initialization"""
        # Disable dependent features if core features are disabled
        if not self.lsp_server:
            self.diagnostics_config.collect_from_lsp = False
            self.error_resolve_config.use_lsp_code_actions = False
            self.context_config.enable_solidlsp_context = False
        
        if not self.enhanced_context:
            self.error_resolve_config.require_enhanced_context = False
            self.context_config.enabled = False
        
        if not self.diagnostics:
            self.error_resolve_config.enabled = False
            self.diagnostics_config.enabled = False
        
        # Adjust resource limits based on enabled features
        active_features = sum([
            self.lsp_server,
            self.diagnostics, 
            self.error_auto_resolve,
            self.enhanced_context,
            self.doc_gen
        ])
        
        # Scale resources based on active features
        if active_features >= 4:
            self.max_memory_usage_mb = max(self.max_memory_usage_mb, 4096)
            self.context_config.max_concurrent_analyses = min(
                self.context_config.max_concurrent_analyses, 2
            )


@dataclass
class GraphSitterIntegrationConfig:
    """Graph-sitter specific configuration wrapper"""
    
    # Graph-sitter core settings
    tree_sitter_languages: List[str] = field(default_factory=list)
    enable_incremental_parsing: bool = True
    enable_syntax_highlighting: bool = True
    
    # Integration configuration
    integration: IntegrationConfig = field(default_factory=IntegrationConfig)
    
    # Graph-sitter specific features
    enable_query_analysis: bool = True
    enable_pattern_matching: bool = True
    enable_structural_search: bool = True
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'GraphSitterIntegrationConfig':
        """Create configuration from dictionary"""
        # Extract integration parameters
        integration_params = {}
        graph_sitter_params = {}
        
        # Map the 5 core parameters
        param_mapping = {
            'lsp_server': 'lsp_server',
            'lspserver': 'lsp_server',  # Alternative naming
            'diagnostics': 'diagnostics',
            'error_auto_resolve': 'error_auto_resolve',
            'errorautoresolve': 'error_auto_resolve',  # Alternative naming
            'enhanced_context': 'enhanced_context',
            'enhancedcontext': 'enhanced_context',  # Alternative naming
            'doc_gen': 'doc_gen',
            'docgen': 'doc_gen'  # Alternative naming
        }
        
        for key, value in config_dict.items():
            if key in param_mapping:
                integration_params[param_mapping[key]] = value
            elif key.startswith('tree_sitter_') or key.startswith('enable_'):
                graph_sitter_params[key] = value
            else:
                # Try to map to component configs
                if key.endswith('_config'):
                    integration_params[key] = value
        
        # Create integration config
        integration_config = IntegrationConfig(**integration_params)
        
        # Create graph-sitter config
        return cls(
            integration=integration_config,
            **graph_sitter_params
        )
    
    @classmethod
    def from_file(cls, config_path: Union[str, Path]) -> 'GraphSitterIntegrationConfig':
        """Load configuration from file (JSON or YAML)"""
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            if config_path.suffix.lower() in ['.yml', '.yaml']:
                config_dict = yaml.safe_load(f)
            elif config_path.suffix.lower() == '.json':
                config_dict = json.load(f)
            else:
                raise ValueError(f"Unsupported configuration file format: {config_path.suffix}")
        
        config = cls.from_dict(config_dict)
        config.integration.config_file_path = str(config_path)
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        result = {
            # Core parameters
            'lsp_server': self.integration.lsp_server,
            'diagnostics': self.integration.diagnostics,
            'error_auto_resolve': self.integration.error_auto_resolve,
            'enhanced_context': self.integration.enhanced_context,
            'doc_gen': self.integration.doc_gen,
            
            # Graph-sitter settings
            'tree_sitter_languages': self.tree_sitter_languages,
            'enable_incremental_parsing': self.enable_incremental_parsing,
            'enable_syntax_highlighting': self.enable_syntax_highlighting,
            'enable_query_analysis': self.enable_query_analysis,
            'enable_pattern_matching': self.enable_pattern_matching,
            'enable_structural_search': self.enable_structural_search,
        }
        
        # Add component configurations if they differ from defaults
        default_integration = IntegrationConfig()
        
        if self.integration.lsp_config != default_integration.lsp_config:
            result['lsp_config'] = self.integration.lsp_config.__dict__
        
        if self.integration.diagnostics_config != default_integration.diagnostics_config:
            result['diagnostics_config'] = self.integration.diagnostics_config.__dict__
        
        if self.integration.error_resolve_config != default_integration.error_resolve_config:
            result['error_resolve_config'] = self.integration.error_resolve_config.__dict__
        
        if self.integration.context_config != default_integration.context_config:
            result['context_config'] = self.integration.context_config.__dict__
        
        if self.integration.doc_config != default_integration.doc_config:
            result['doc_config'] = self.integration.doc_config.__dict__
        
        return result
    
    def save_to_file(self, config_path: Union[str, Path], format: str = 'yaml') -> None:
        """Save configuration to file"""
        config_path = Path(config_path)
        config_dict = self.to_dict()
        
        with open(config_path, 'w', encoding='utf-8') as f:
            if format.lower() in ['yml', 'yaml']:
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)
            elif format.lower() == 'json':
                json.dump(config_dict, f, indent=2)
            else:
                raise ValueError(f"Unsupported format: {format}")
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of issues"""
        issues = []
        
        # Check for conflicting settings
        if self.integration.error_auto_resolve and not self.integration.diagnostics:
            issues.append("error_auto_resolve requires diagnostics to be enabled")
        
        if self.integration.error_resolve_config.require_enhanced_context and not self.integration.enhanced_context:
            issues.append("error resolution requires enhanced_context when require_enhanced_context=True")
        
        # Check resource limits
        if self.integration.context_config.max_context_size_tokens > 100000:
            issues.append("max_context_size_tokens is very large and may cause performance issues")
        
        if self.integration.error_resolve_config.max_fixes_per_session > 500:
            issues.append("max_fixes_per_session is very large and may cause instability")
        
        # Check file paths
        if self.integration.project_root and not Path(self.integration.project_root).exists():
            issues.append(f"project_root does not exist: {self.integration.project_root}")
        
        return issues


def create_default_config() -> GraphSitterIntegrationConfig:
    """Create a default configuration with all features enabled"""
    return GraphSitterIntegrationConfig()


def create_minimal_config() -> GraphSitterIntegrationConfig:
    """Create a minimal configuration with only essential features"""
    integration = IntegrationConfig(
        lsp_server=True,
        diagnostics=True,
        error_auto_resolve=False,
        enhanced_context=False,
        doc_gen=False
    )
    
    return GraphSitterIntegrationConfig(integration=integration)


def create_performance_config() -> GraphSitterIntegrationConfig:
    """Create a performance-optimized configuration"""
    integration = IntegrationConfig(
        lsp_server=True,
        diagnostics=True,
        error_auto_resolve=True,
        enhanced_context=True,
        doc_gen=False,  # Disable doc generation for performance
    )
    
    # Optimize context settings
    integration.context_config.depth = ContextDepth.SHALLOW
    integration.context_config.max_context_size_tokens = 10000
    integration.context_config.max_concurrent_analyses = 2
    integration.context_config.enable_parallel_analysis = True
    
    # Optimize error resolution
    integration.error_resolve_config.strategy = ErrorResolutionStrategy.CONSERVATIVE
    integration.error_resolve_config.max_fixes_per_file = 5
    
    return GraphSitterIntegrationConfig(integration=integration)
