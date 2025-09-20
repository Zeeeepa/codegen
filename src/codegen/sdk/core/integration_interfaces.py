"""
Integration Interfaces for Unified Graph-Sitter System

This module defines the abstract interfaces that provide unified access to
SolidLSP, Serena, and graph-sitter components for the integrated system.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Optional, Any, Union, Iterator, Callable
from pathlib import Path
from enum import Enum


class DiagnosticSeverity(Enum):
    """Unified diagnostic severity levels"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    HINT = "hint"


class SymbolKind(Enum):
    """Unified symbol kinds"""
    FILE = "file"
    MODULE = "module"
    NAMESPACE = "namespace"
    PACKAGE = "package"
    CLASS = "class"
    METHOD = "method"
    PROPERTY = "property"
    FIELD = "field"
    CONSTRUCTOR = "constructor"
    ENUM = "enum"
    INTERFACE = "interface"
    FUNCTION = "function"
    VARIABLE = "variable"
    CONSTANT = "constant"
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    KEY = "key"
    NULL = "null"
    ENUM_MEMBER = "enum_member"
    STRUCT = "struct"
    EVENT = "event"
    OPERATOR = "operator"
    TYPE_PARAMETER = "type_parameter"


@dataclass
class UnifiedPosition:
    """Unified position representation"""
    line: int  # 0-based
    character: int  # 0-based
    
    def to_lsp_position(self) -> Dict[str, int]:
        """Convert to LSP position format"""
        return {"line": self.line, "character": self.character}


@dataclass
class UnifiedRange:
    """Unified range representation"""
    start: UnifiedPosition
    end: UnifiedPosition
    
    def to_lsp_range(self) -> Dict[str, Any]:
        """Convert to LSP range format"""
        return {
            "start": self.start.to_lsp_position(),
            "end": self.end.to_lsp_position()
        }


@dataclass
class UnifiedLocation:
    """Unified location representation"""
    uri: str
    range: UnifiedRange
    absolute_path: Optional[str] = None
    relative_path: Optional[str] = None
    
    def to_lsp_location(self) -> Dict[str, Any]:
        """Convert to LSP location format"""
        return {
            "uri": self.uri,
            "range": self.range.to_lsp_range()
        }


@dataclass
class UnifiedDiagnostic:
    """Unified diagnostic representation"""
    range: UnifiedRange
    severity: DiagnosticSeverity
    code: Optional[str]
    source: Optional[str]
    message: str
    related_information: List[Dict[str, Any]] = None
    tags: List[str] = None
    data: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.related_information is None:
            self.related_information = []
        if self.tags is None:
            self.tags = []


@dataclass
class UnifiedSymbol:
    """Unified symbol representation"""
    name: str
    kind: SymbolKind
    location: UnifiedLocation
    container_name: Optional[str] = None
    detail: Optional[str] = None
    documentation: Optional[str] = None
    deprecated: bool = False
    tags: List[str] = None
    children: List['UnifiedSymbol'] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.children is None:
            self.children = []


@dataclass
class ContextInformation:
    """Enhanced context information for error resolution"""
    symbol_definitions: List[UnifiedSymbol]
    type_information: Dict[str, Any]
    variable_scope: Dict[str, Any]
    call_hierarchy: List[Dict[str, Any]]
    dependencies: List[str]
    impact_radius: List[str]  # Files that might be affected
    related_diagnostics: List[UnifiedDiagnostic]
    
    def __post_init__(self):
        if self.symbol_definitions is None:
            self.symbol_definitions = []
        if self.type_information is None:
            self.type_information = {}
        if self.variable_scope is None:
            self.variable_scope = {}
        if self.call_hierarchy is None:
            self.call_hierarchy = []
        if self.dependencies is None:
            self.dependencies = []
        if self.impact_radius is None:
            self.impact_radius = []
        if self.related_diagnostics is None:
            self.related_diagnostics = []


@dataclass
class ErrorResolutionResult:
    """Result of an error resolution attempt"""
    success: bool
    applied_fixes: List[Dict[str, Any]]
    remaining_diagnostics: List[UnifiedDiagnostic]
    error_message: Optional[str] = None
    rollback_info: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.applied_fixes is None:
            self.applied_fixes = []
        if self.remaining_diagnostics is None:
            self.remaining_diagnostics = []


class ILanguageServer(ABC):
    """Interface for language server operations"""
    
    @abstractmethod
    async def initialize(self, project_root: str, language: str) -> bool:
        """Initialize the language server for a specific language"""
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the language server"""
        pass
    
    @abstractmethod
    async def get_diagnostics(self, file_path: str) -> List[UnifiedDiagnostic]:
        """Get diagnostics for a file"""
        pass
    
    @abstractmethod
    async def get_symbols(self, file_path: str) -> List[UnifiedSymbol]:
        """Get symbols in a file"""
        pass
    
    @abstractmethod
    async def get_definition(self, file_path: str, position: UnifiedPosition) -> List[UnifiedLocation]:
        """Get definition locations for a symbol"""
        pass
    
    @abstractmethod
    async def get_references(self, file_path: str, position: UnifiedPosition) -> List[UnifiedLocation]:
        """Get reference locations for a symbol"""
        pass
    
    @abstractmethod
    async def get_code_actions(self, file_path: str, range: UnifiedRange, diagnostics: List[UnifiedDiagnostic]) -> List[Dict[str, Any]]:
        """Get available code actions for a range"""
        pass
    
    @abstractmethod
    def is_running(self) -> bool:
        """Check if the language server is running"""
        pass


class IProjectManager(ABC):
    """Interface for project management operations"""
    
    @abstractmethod
    def initialize_project(self, project_root: str) -> bool:
        """Initialize project management for a directory"""
        pass
    
    @abstractmethod
    def get_project_files(self, include_ignored: bool = False) -> List[str]:
        """Get list of project files"""
        pass
    
    @abstractmethod
    def is_file_ignored(self, file_path: str) -> bool:
        """Check if a file should be ignored"""
        pass
    
    @abstractmethod
    def get_project_languages(self) -> List[str]:
        """Get detected programming languages in the project"""
        pass
    
    @abstractmethod
    def get_project_config(self) -> Dict[str, Any]:
        """Get project configuration"""
        pass
    
    @abstractmethod
    def watch_files(self, callback: Callable[[str, str], None]) -> None:
        """Start watching files for changes"""
        pass
    
    @abstractmethod
    def stop_watching(self) -> None:
        """Stop watching files"""
        pass


class IGraphBuilder(ABC):
    """Interface for graph construction operations"""
    
    @abstractmethod
    def build_graph(self, project_root: str) -> Dict[str, Any]:
        """Build a graph representation of the codebase"""
        pass
    
    @abstractmethod
    def update_graph(self, file_path: str, content: str) -> None:
        """Update graph with changes to a file"""
        pass
    
    @abstractmethod
    def get_graph_nodes(self, node_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get nodes from the graph"""
        pass
    
    @abstractmethod
    def get_graph_edges(self, edge_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get edges from the graph"""
        pass
    
    @abstractmethod
    def find_related_nodes(self, node_id: str, max_depth: int = 2) -> List[Dict[str, Any]]:
        """Find nodes related to a given node"""
        pass
    
    @abstractmethod
    def export_graph(self, format: str = "json") -> Union[str, Dict[str, Any]]:
        """Export graph in specified format"""
        pass


class IDiagnosticCollector(ABC):
    """Interface for diagnostic collection operations"""
    
    @abstractmethod
    async def collect_diagnostics(self, file_path: Optional[str] = None) -> List[UnifiedDiagnostic]:
        """Collect diagnostics from all sources"""
        pass
    
    @abstractmethod
    def add_diagnostic_source(self, source_name: str, collector: Callable[[], List[UnifiedDiagnostic]]) -> None:
        """Add a diagnostic source"""
        pass
    
    @abstractmethod
    def remove_diagnostic_source(self, source_name: str) -> None:
        """Remove a diagnostic source"""
        pass
    
    @abstractmethod
    def filter_diagnostics(self, diagnostics: List[UnifiedDiagnostic], severity: Optional[DiagnosticSeverity] = None) -> List[UnifiedDiagnostic]:
        """Filter diagnostics by criteria"""
        pass
    
    @abstractmethod
    def group_diagnostics(self, diagnostics: List[UnifiedDiagnostic]) -> Dict[str, List[UnifiedDiagnostic]]:
        """Group diagnostics by file or other criteria"""
        pass


class ISymbolResolver(ABC):
    """Interface for symbol resolution operations"""
    
    @abstractmethod
    async def resolve_symbol(self, file_path: str, position: UnifiedPosition) -> Optional[UnifiedSymbol]:
        """Resolve symbol at a position"""
        pass
    
    @abstractmethod
    async def find_symbol_references(self, symbol: UnifiedSymbol) -> List[UnifiedLocation]:
        """Find all references to a symbol"""
        pass
    
    @abstractmethod
    async def find_symbol_definition(self, symbol: UnifiedSymbol) -> Optional[UnifiedLocation]:
        """Find the definition of a symbol"""
        pass
    
    @abstractmethod
    async def get_symbol_hierarchy(self, symbol: UnifiedSymbol) -> List[UnifiedSymbol]:
        """Get the hierarchy of a symbol (parents and children)"""
        pass
    
    @abstractmethod
    async def search_symbols(self, query: str, file_path: Optional[str] = None) -> List[UnifiedSymbol]:
        """Search for symbols matching a query"""
        pass


class IErrorResolver(ABC):
    """Interface for automatic error resolution"""
    
    @abstractmethod
    async def resolve_error(self, diagnostic: UnifiedDiagnostic, context: ContextInformation) -> ErrorResolutionResult:
        """Attempt to resolve a single error"""
        pass
    
    @abstractmethod
    async def resolve_errors(self, diagnostics: List[UnifiedDiagnostic]) -> List[ErrorResolutionResult]:
        """Attempt to resolve multiple errors"""
        pass
    
    @abstractmethod
    def get_resolution_strategies(self) -> List[str]:
        """Get available resolution strategies"""
        pass
    
    @abstractmethod
    def add_resolution_strategy(self, name: str, strategy: Callable[[UnifiedDiagnostic, ContextInformation], ErrorResolutionResult]) -> None:
        """Add a custom resolution strategy"""
        pass
    
    @abstractmethod
    async def preview_resolution(self, diagnostic: UnifiedDiagnostic, context: ContextInformation) -> Dict[str, Any]:
        """Preview what changes would be made to resolve an error"""
        pass
    
    @abstractmethod
    async def rollback_resolution(self, result: ErrorResolutionResult) -> bool:
        """Rollback a previously applied resolution"""
        pass


class IContextEnhancer(ABC):
    """Interface for enhanced context retrieval"""
    
    @abstractmethod
    async def get_context_for_diagnostic(self, diagnostic: UnifiedDiagnostic, file_path: str) -> ContextInformation:
        """Get enhanced context for a diagnostic"""
        pass
    
    @abstractmethod
    async def get_context_for_symbol(self, symbol: UnifiedSymbol) -> ContextInformation:
        """Get enhanced context for a symbol"""
        pass
    
    @abstractmethod
    async def get_context_for_position(self, file_path: str, position: UnifiedPosition) -> ContextInformation:
        """Get enhanced context for a position in a file"""
        pass
    
    @abstractmethod
    async def analyze_impact_radius(self, file_path: str, changes: List[Dict[str, Any]]) -> List[str]:
        """Analyze which files might be affected by changes"""
        pass
    
    @abstractmethod
    def set_context_depth(self, depth: int) -> None:
        """Set the maximum depth for context retrieval"""
        pass
    
    @abstractmethod
    def enable_context_feature(self, feature: str, enabled: bool) -> None:
        """Enable or disable a context feature"""
        pass


class IUnifiedSystem(ABC):
    """Main interface for the unified system"""
    
    @abstractmethod
    def initialize(self, project_root: str, config: Dict[str, Any]) -> bool:
        """Initialize the unified system"""
        pass
    
    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown the unified system"""
        pass
    
    @abstractmethod
    def get_language_server(self) -> ILanguageServer:
        """Get the language server interface"""
        pass
    
    @abstractmethod
    def get_project_manager(self) -> IProjectManager:
        """Get the project manager interface"""
        pass
    
    @abstractmethod
    def get_graph_builder(self) -> IGraphBuilder:
        """Get the graph builder interface"""
        pass
    
    @abstractmethod
    def get_diagnostic_collector(self) -> IDiagnosticCollector:
        """Get the diagnostic collector interface"""
        pass
    
    @abstractmethod
    def get_symbol_resolver(self) -> ISymbolResolver:
        """Get the symbol resolver interface"""
        pass
    
    @abstractmethod
    def get_error_resolver(self) -> IErrorResolver:
        """Get the error resolver interface"""
        pass
    
    @abstractmethod
    def get_context_enhancer(self) -> IContextEnhancer:
        """Get the context enhancer interface"""
        pass
    
    @abstractmethod
    async def analyze_project(self) -> Dict[str, Any]:
        """Perform comprehensive project analysis"""
        pass
    
    @abstractmethod
    async def auto_resolve_errors(self, max_errors: int = 10) -> List[ErrorResolutionResult]:
        """Automatically resolve errors in the project"""
        pass
    
    @abstractmethod
    def get_system_status(self) -> Dict[str, Any]:
        """Get the status of all system components"""
        pass
