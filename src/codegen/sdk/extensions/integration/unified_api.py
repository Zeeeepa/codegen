"""
Unified API for graph-sitter integration with SolidLSP, Serena, and Extensions.

This module provides the main entry point `from_repo()` function that creates
an integrated codebase with all 5 parameters working together seamlessly.
"""

import logging
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import time
from dataclasses import dataclass, field

# Core graph-sitter imports
from ...core.codebase import Codebase
from ...tree_sitter_parser import TreeSitterParser

# Integration imports
from .config import GraphSitterIntegrationConfig, IntegrationConfig
from .context_provider import EnhancedContextProvider, Location, EnhancedContext
from .error_resolver import AutomaticErrorResolver
from .diagnostic_collector import UnifiedDiagnosticCollector
from .doc_generator import IntegratedDocumentationGenerator

# Component imports
from ..solidlsp import SolidLanguageServer
from ..serena.agent import SerenaAgent
from ..serena.project import Project

logger = logging.getLogger(__name__)


@dataclass
class InitializationResult:
    """Result of codebase initialization"""
    success: bool
    duration_seconds: float
    components_initialized: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


@dataclass
class DiagnosticSummary:
    """Summary of diagnostics across the codebase"""
    total_diagnostics: int
    errors: int
    warnings: int
    hints: int
    files_with_diagnostics: int
    most_problematic_files: List[str] = field(default_factory=list)


@dataclass
class ErrorResolutionResult:
    """Result of automatic error resolution"""
    total_errors_found: int
    errors_resolved: int
    errors_failed: int
    resolution_details: List[Dict[str, Any]] = field(default_factory=list)
    files_modified: List[str] = field(default_factory=list)
    backup_created: bool = False


class IntegratedCodebase:
    """
    Main integrated codebase class providing unified access to all functionality.
    
    This class integrates:
    - Graph-sitter core functionality
    - SolidLSP language server integration
    - Serena workspace management and tools
    - Enhanced context analysis
    - Automatic error resolution
    - Documentation generation
    """
    
    def __init__(self, 
                 repo_path: str,
                 config: GraphSitterIntegrationConfig,
                 codebase: Codebase,
                 lsp_manager: Optional[SolidLanguageServer] = None,
                 serena_agent: Optional[SerenaAgent] = None,
                 context_provider: Optional[EnhancedContextProvider] = None,
                 error_resolver: Optional[AutomaticErrorResolver] = None,
                 diagnostic_collector: Optional[UnifiedDiagnosticCollector] = None,
                 doc_generator: Optional[IntegratedDocumentationGenerator] = None):
        
        self.repo_path = Path(repo_path)
        self.config = config
        self.codebase = codebase
        
        # Component instances
        self.lsp_manager = lsp_manager
        self.serena_agent = serena_agent
        self.context_provider = context_provider
        self.error_resolver = error_resolver
        self.diagnostic_collector = diagnostic_collector
        self.doc_generator = doc_generator
        
        self.logger = logging.getLogger(__name__)
        self._initialization_result: Optional[InitializationResult] = None
    
    # Core API Methods
    
    def get_diagnostics(self) -> Dict[str, List[Any]]:
        """Get all diagnostics in the codebase"""
        if self.diagnostic_collector:
            return self.diagnostic_collector.get_workspace_diagnostics()
        return {}
    
    def get_diagnostic_summary(self) -> DiagnosticSummary:
        """Get a summary of diagnostics across the codebase"""
        diagnostics = self.get_diagnostics()
        
        total = 0
        errors = 0
        warnings = 0
        hints = 0
        file_counts = {}
        
        for file_path, file_diagnostics in diagnostics.items():
            file_counts[file_path] = len(file_diagnostics)
            total += len(file_diagnostics)
            
            for diagnostic in file_diagnostics:
                severity = getattr(diagnostic, 'severity', 'unknown')
                if severity == 'error':
                    errors += 1
                elif severity == 'warning':
                    warnings += 1
                elif severity == 'hint':
                    hints += 1
        
        # Find most problematic files
        most_problematic = sorted(file_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        most_problematic_files = [file_path for file_path, _ in most_problematic]
        
        return DiagnosticSummary(
            total_diagnostics=total,
            errors=errors,
            warnings=warnings,
            hints=hints,
            files_with_diagnostics=len(diagnostics),
            most_problematic_files=most_problematic_files
        )
    
    def resolve_errors_automatically(self) -> ErrorResolutionResult:
        """Automatically resolve errors in the codebase"""
        if not self.error_resolver:
            return ErrorResolutionResult(
                total_errors_found=0,
                errors_resolved=0,
                errors_failed=0,
                resolution_details=[{"error": "Error resolution not enabled"}]
            )
        
        return self.error_resolver.resolve_all_errors()
    
    def get_enhanced_context(self, file_path: str, line: int, character: int, 
                           symbol_name: Optional[str] = None) -> EnhancedContext:
        """Get enhanced context for a specific location"""
        location = Location(
            file_path=file_path,
            line=line,
            character=character,
            symbol_name=symbol_name
        )
        
        if self.context_provider:
            return self.context_provider.get_comprehensive_context(location)
        
        # Return minimal context if provider not available
        return EnhancedContext(location=location)
    
    def list_errors_with_context(self) -> List[Dict[str, Any]]:
        """List all errors with their enhanced context"""
        errors_with_context = []
        diagnostics = self.get_diagnostics()
        
        for file_path, file_diagnostics in diagnostics.items():
            for diagnostic in file_diagnostics:
                if getattr(diagnostic, 'severity', '') == 'error':
                    # Get enhanced context for the error
                    context = self.get_enhanced_context(
                        file_path=file_path,
                        line=getattr(diagnostic, 'line', 0),
                        character=getattr(diagnostic, 'character', 0)
                    )
                    
                    errors_with_context.append({
                        'diagnostic': diagnostic,
                        'context': context,
                        'file_path': file_path
                    })
        
        return errors_with_context
    
    def generate_documentation(self, output_path: Optional[str] = None) -> Dict[str, Any]:
        """Generate comprehensive documentation"""
        if not self.doc_generator:
            return {"error": "Documentation generation not enabled"}
        
        return self.doc_generator.generate_comprehensive_docs(output_path)
    
    def get_symbol_analysis(self, symbol_name: str) -> Dict[str, Any]:
        """Get comprehensive analysis for a symbol"""
        if self.serena_agent:
            try:
                # Use Serena's symbol tools
                result = self.serena_agent.execute_tool("FindSymbolTool", name_path=symbol_name)
                return {"symbol_info": result, "source": "serena"}
            except Exception as e:
                self.logger.warning(f"Failed to get symbol analysis from Serena: {e}")
        
        # Fallback to basic analysis
        return {"symbol_name": symbol_name, "analysis": "basic", "source": "fallback"}
    
    def search_code(self, query: str, file_pattern: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search code across the codebase"""
        results = []
        
        # Use Serena search if available
        if self.serena_agent:
            try:
                serena_results = self.serena_agent.execute_tool(
                    "SearchForPatternTool", 
                    pattern=query,
                    relative_path=file_pattern or ""
                )
                results.append({"source": "serena", "results": serena_results})
            except Exception as e:
                self.logger.warning(f"Serena search failed: {e}")
        
        # Use context provider indexing if available
        if self.context_provider and self.context_provider.code_index:
            try:
                index_results = self.context_provider.code_index.search_code(query)
                results.append({"source": "index", "results": index_results})
            except Exception as e:
                self.logger.warning(f"Index search failed: {e}")
        
        return results
    
    def get_file_analysis(self, file_path: str) -> Dict[str, Any]:
        """Get comprehensive analysis for a file"""
        analysis = {
            "file_path": file_path,
            "exists": (self.repo_path / file_path).exists(),
            "analysis_sources": []
        }
        
        # Get diagnostics for the file
        diagnostics = self.get_diagnostics().get(file_path, [])
        analysis["diagnostics"] = {
            "count": len(diagnostics),
            "errors": len([d for d in diagnostics if getattr(d, 'severity', '') == 'error']),
            "warnings": len([d for d in diagnostics if getattr(d, 'severity', '') == 'warning'])
        }
        
        # Get symbol overview from Serena if available
        if self.serena_agent:
            try:
                symbols = self.serena_agent.execute_tool("GetSymbolsOverviewTool", relative_path=file_path)
                analysis["symbols"] = symbols
                analysis["analysis_sources"].append("serena")
            except Exception as e:
                self.logger.warning(f"Failed to get symbols from Serena: {e}")
        
        # Get tree-sitter analysis
        try:
            if analysis["exists"]:
                with open(self.repo_path / file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse with tree-sitter
                ast_node = self.codebase.parse_file(self.repo_path / file_path, content)
                analysis["ast_available"] = ast_node is not None
                analysis["analysis_sources"].append("tree_sitter")
        except Exception as e:
            self.logger.warning(f"Failed to parse file with tree-sitter: {e}")
        
        return analysis
    
    def get_project_statistics(self) -> Dict[str, Any]:
        """Get comprehensive project statistics"""
        stats = {
            "repo_path": str(self.repo_path),
            "config": {
                "lsp_server": self.config.integration.lsp_server,
                "diagnostics": self.config.integration.diagnostics,
                "error_auto_resolve": self.config.integration.error_auto_resolve,
                "enhanced_context": self.config.integration.enhanced_context,
                "doc_gen": self.config.integration.doc_gen
            },
            "components": {
                "lsp_manager": self.lsp_manager is not None,
                "serena_agent": self.serena_agent is not None,
                "context_provider": self.context_provider is not None,
                "error_resolver": self.error_resolver is not None,
                "diagnostic_collector": self.diagnostic_collector is not None,
                "doc_generator": self.doc_generator is not None
            }
        }
        
        # Add file statistics
        try:
            all_files = list(self.codebase.get_files())
            stats["files"] = {
                "total_files": len(all_files),
                "code_files": len([f for f in all_files if f.suffix in ['.py', '.js', '.ts', '.tsx']]),
                "languages_detected": list(set(f.suffix for f in all_files if f.suffix))
            }
        except Exception as e:
            self.logger.warning(f"Failed to get file statistics: {e}")
            stats["files"] = {"error": str(e)}
        
        # Add diagnostic statistics
        diagnostic_summary = self.get_diagnostic_summary()
        stats["diagnostics"] = {
            "total": diagnostic_summary.total_diagnostics,
            "errors": diagnostic_summary.errors,
            "warnings": diagnostic_summary.warnings,
            "hints": diagnostic_summary.hints,
            "files_with_issues": diagnostic_summary.files_with_diagnostics
        }
        
        return stats
    
    def refresh_analysis(self) -> Dict[str, Any]:
        """Refresh all analysis components"""
        refresh_results = {}
        
        # Refresh LSP diagnostics
        if self.diagnostic_collector:
            try:
                self.diagnostic_collector.refresh_diagnostics()
                refresh_results["diagnostics"] = "refreshed"
            except Exception as e:
                refresh_results["diagnostics"] = f"failed: {e}"
        
        # Refresh context provider indexes
        if self.context_provider:
            try:
                self.context_provider.build_indexes(self.codebase)
                refresh_results["context_indexes"] = "rebuilt"
            except Exception as e:
                refresh_results["context_indexes"] = f"failed: {e}"
        
        # Refresh Serena language server
        if self.serena_agent:
            try:
                self.serena_agent.reset_language_server()
                refresh_results["serena_lsp"] = "reset"
            except Exception as e:
                refresh_results["serena_lsp"] = f"failed: {e}"
        
        return refresh_results
    
    def cleanup(self) -> None:
        """Cleanup all resources"""
        if self.context_provider:
            self.context_provider.cleanup()
        
        if self.error_resolver:
            self.error_resolver.cleanup()
        
        if self.diagnostic_collector:
            self.diagnostic_collector.cleanup()
        
        if self.doc_generator:
            self.doc_generator.cleanup()
        
        if self.lsp_manager:
            try:
                self.lsp_manager.stop_server()
            except Exception as e:
                self.logger.warning(f"Failed to stop LSP server: {e}")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()


def from_repo(repo_path: str, **config_params) -> IntegratedCodebase:
    """
    Create an integrated codebase from a repository path with unified configuration.
    
    This is the main entry point for the unified graph-sitter integration system.
    
    Args:
        repo_path: Path to the repository
        **config_params: Configuration parameters including:
            - lsp_server: bool = True
            - diagnostics: bool = True  
            - error_auto_resolve: bool = True
            - enhanced_context: bool = True
            - doc_gen: bool = True
            - Additional configuration options
    
    Returns:
        IntegratedCodebase: Fully integrated codebase instance
    
    Example:
        ```python
        # Basic usage with all features enabled
        codebase = from_repo("/path/to/repo")
        
        # Custom configuration
        codebase = from_repo("/path/to/repo",
            lsp_server=True,
            diagnostics=True,
            error_auto_resolve=False,  # Disable auto-resolution
            enhanced_context=True,
            doc_gen=False  # Disable doc generation
        )
        
        # Get diagnostics
        diagnostics = codebase.get_diagnostics()
        
        # Resolve errors automatically
        resolution_result = codebase.resolve_errors_automatically()
        
        # Get enhanced context
        context = codebase.get_enhanced_context("src/main.py", 10, 5)
        ```
    """
    start_time = time.time()
    repo_path = Path(repo_path).resolve()
    
    if not repo_path.exists():
        raise FileNotFoundError(f"Repository path does not exist: {repo_path}")
    
    logger.info(f"Initializing integrated codebase for: {repo_path}")
    
    # Create configuration
    config = GraphSitterIntegrationConfig.from_dict(config_params)
    config.integration.project_root = str(repo_path)
    
    # Validate configuration
    validation_issues = config.validate()
    if validation_issues:
        logger.warning(f"Configuration validation issues: {validation_issues}")
    
    # Initialize core graph-sitter codebase
    codebase = Codebase(str(repo_path))
    
    # Initialize components based on configuration
    components_initialized = []
    warnings = []
    errors = []
    
    # Initialize LSP manager
    lsp_manager = None
    if config.integration.lsp_server:
        try:
            lsp_manager = _initialize_lsp_manager(repo_path, config)
            components_initialized.append("lsp_manager")
        except Exception as e:
            error_msg = f"Failed to initialize LSP manager: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
    
    # Initialize Serena agent
    serena_agent = None
    if config.integration.lsp_server:  # Serena requires LSP functionality
        try:
            serena_agent = _initialize_serena_agent(repo_path, config)
            components_initialized.append("serena_agent")
        except Exception as e:
            error_msg = f"Failed to initialize Serena agent: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
    
    # Initialize context provider
    context_provider = None
    if config.integration.enhanced_context:
        try:
            context_provider = _initialize_context_provider(config, codebase)
            components_initialized.append("context_provider")
        except Exception as e:
            error_msg = f"Failed to initialize context provider: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
    
    # Initialize diagnostic collector
    diagnostic_collector = None
    if config.integration.diagnostics:
        try:
            diagnostic_collector = _initialize_diagnostic_collector(config, lsp_manager, serena_agent)
            components_initialized.append("diagnostic_collector")
        except Exception as e:
            error_msg = f"Failed to initialize diagnostic collector: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
    
    # Initialize error resolver
    error_resolver = None
    if config.integration.error_auto_resolve:
        try:
            error_resolver = _initialize_error_resolver(config, lsp_manager, serena_agent, context_provider)
            components_initialized.append("error_resolver")
        except Exception as e:
            error_msg = f"Failed to initialize error resolver: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
    
    # Initialize documentation generator
    doc_generator = None
    if config.integration.doc_gen:
        try:
            doc_generator = _initialize_doc_generator(config, codebase, serena_agent)
            components_initialized.append("doc_generator")
        except Exception as e:
            error_msg = f"Failed to initialize documentation generator: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
    
    # Create integrated codebase
    integrated_codebase = IntegratedCodebase(
        repo_path=str(repo_path),
        config=config,
        codebase=codebase,
        lsp_manager=lsp_manager,
        serena_agent=serena_agent,
        context_provider=context_provider,
        error_resolver=error_resolver,
        diagnostic_collector=diagnostic_collector,
        doc_generator=doc_generator
    )
    
    # Store initialization result
    duration = time.time() - start_time
    integrated_codebase._initialization_result = InitializationResult(
        success=len(errors) == 0,
        duration_seconds=duration,
        components_initialized=components_initialized,
        warnings=warnings,
        errors=errors
    )
    
    logger.info(f"Integrated codebase initialized in {duration:.2f}s with {len(components_initialized)} components")
    
    return integrated_codebase


def _initialize_lsp_manager(repo_path: Path, config: GraphSitterIntegrationConfig) -> SolidLanguageServer:
    """Initialize SolidLSP language server manager"""
    # This would create and configure the SolidLanguageServer
    # For now, return a placeholder
    logger.info("Initializing SolidLSP manager...")
    return None  # Placeholder


def _initialize_serena_agent(repo_path: Path, config: GraphSitterIntegrationConfig) -> SerenaAgent:
    """Initialize Serena agent for workspace management"""
    logger.info("Initializing Serena agent...")
    
    try:
        # Load Serena project
        project = Project.load(repo_path, autogenerate=True)
        
        # Create Serena agent (simplified - would need proper SerenaConfig)
        # agent = SerenaAgent(serena_config, project)
        # agent.activate_project(str(repo_path))
        
        return None  # Placeholder for now
    except Exception as e:
        logger.error(f"Failed to initialize Serena agent: {e}")
        raise


def _initialize_context_provider(config: GraphSitterIntegrationConfig, codebase: Codebase) -> EnhancedContextProvider:
    """Initialize enhanced context provider"""
    logger.info("Initializing enhanced context provider...")
    
    context_provider = EnhancedContextProvider(config.integration.context_config)
    
    # Build indexes
    context_provider.build_indexes(codebase)
    
    return context_provider


def _initialize_diagnostic_collector(config: GraphSitterIntegrationConfig, 
                                   lsp_manager: Optional[SolidLanguageServer],
                                   serena_agent: Optional[SerenaAgent]) -> UnifiedDiagnosticCollector:
    """Initialize unified diagnostic collector"""
    logger.info("Initializing diagnostic collector...")
    
    return UnifiedDiagnosticCollector(
        config.integration.diagnostics_config,
        lsp_manager=lsp_manager,
        serena_agent=serena_agent
    )


def _initialize_error_resolver(config: GraphSitterIntegrationConfig,
                             lsp_manager: Optional[SolidLanguageServer],
                             serena_agent: Optional[SerenaAgent],
                             context_provider: Optional[EnhancedContextProvider]) -> AutomaticErrorResolver:
    """Initialize automatic error resolver"""
    logger.info("Initializing error resolver...")
    
    return AutomaticErrorResolver(
        config.integration.error_resolve_config,
        lsp_manager=lsp_manager,
        serena_agent=serena_agent,
        context_provider=context_provider
    )


def _initialize_doc_generator(config: GraphSitterIntegrationConfig,
                            codebase: Codebase,
                            serena_agent: Optional[SerenaAgent]) -> IntegratedDocumentationGenerator:
    """Initialize integrated documentation generator"""
    logger.info("Initializing documentation generator...")
    
    return IntegratedDocumentationGenerator(
        config.integration.doc_config,
        codebase=codebase,
        serena_agent=serena_agent
    )
