"""
SolidLSP Integration Adapter

This module provides the adapter that integrates SolidLSP language servers
into the unified graph-sitter system, implementing the ILanguageServer interface.
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
import threading
import time

from ..integration_interfaces import (
    ILanguageServer, UnifiedDiagnostic, UnifiedSymbol, UnifiedLocation,
    UnifiedRange, UnifiedPosition, DiagnosticSeverity, SymbolKind
)
from ..unified_config import LSPConfiguration

# SolidLSP imports with fallback
try:
    from solidlsp import SolidLanguageServer
    from solidlsp.ls_config import Language, LanguageServerConfig
    from solidlsp.ls_handler import SolidLanguageServerHandler
    from solidlsp.ls_types import UnifiedSymbolInformation, Position, Range, Location
    from solidlsp.lsp_protocol_handler.lsp_types import (
        Diagnostic, DocumentSymbol, SymbolInformation, 
        Definition, LocationLink, CodeAction
    )
    from solidlsp.settings import SolidLSPSettings
    SOLIDLSP_AVAILABLE = True
except ImportError:
    # Mock implementations for testing
    SOLIDLSP_AVAILABLE = False
    
    class SolidLanguageServer:
        def __init__(self, *args, **kwargs):
            self.started = False
        
        @classmethod
        def create(cls, *args, **kwargs):
            return cls()
        
        async def start(self):
            self.started = True
        
        async def stop(self):
            self.started = False
        
        async def get_diagnostics(self, file_path: str):
            return []
        
        async def get_symbols(self, file_path: str):
            return []
    
    class Language:
        PYTHON = "python"
        JAVASCRIPT = "javascript"
        TYPESCRIPT = "typescript"
    
    class LanguageServerConfig:
        def __init__(self, **kwargs):
            pass
    
    class SolidLanguageServerHandler:
        def __init__(self, **kwargs):
            pass
    
    class UnifiedSymbolInformation:
        def __init__(self, **kwargs):
            pass
    
    class Position:
        def __init__(self, line=0, character=0):
            self.line = line
            self.character = character
    
    class Range:
        def __init__(self, start=None, end=None):
            self.start = start or Position()
            self.end = end or Position()
    
    class Location:
        def __init__(self, uri="", range=None):
            self.uri = uri
            self.range = range or Range()
    
    class Diagnostic:
        def __init__(self, **kwargs):
            pass
    
    class DocumentSymbol:
        def __init__(self, **kwargs):
            pass
    
    class SymbolInformation:
        def __init__(self, **kwargs):
            pass
    
    class Definition:
        def __init__(self, **kwargs):
            pass
    
    class LocationLink:
        def __init__(self, **kwargs):
            pass
    
    class CodeAction:
        def __init__(self, **kwargs):
            pass
    
    class SolidLSPSettings:
        def __init__(self, **kwargs):
            pass

logger = logging.getLogger(__name__)


class SolidLSPAdapter(ILanguageServer):
    """
    Adapter that integrates SolidLSP language servers into the unified system.
    
    This adapter manages multiple language servers, handles LSP protocol communication,
    and translates between SolidLSP types and unified interface types.
    """
    
    def __init__(self, config: LSPConfiguration):
        self.config = config
        self.project_root: Optional[str] = None
        
        # Language server management
        self._language_servers: Dict[str, SolidLanguageServer] = {}
        self._server_handlers: Dict[str, SolidLanguageServerHandler] = {}
        self._initialized_languages: Set[str] = set()
        
        # State management
        self._lock = threading.RLock()
        self._running = False
        self._shutdown_event = threading.Event()
        
        # Performance tracking
        self._request_counts: Dict[str, int] = {}
        self._error_counts: Dict[str, int] = {}
        
        logger.info("SolidLSP adapter initialized")
    
    async def initialize(self, project_root: str, language: str) -> bool:
        """Initialize a language server for a specific language"""
        try:
            with self._lock:
                if language in self._initialized_languages:
                    logger.debug(f"Language server for {language} already initialized")
                    return True
                
                logger.info(f"Initializing language server for {language}")
                
                # Set project root if not set
                if self.project_root is None:
                    self.project_root = project_root
                
                # Get language server class for the language
                language_server_class = self._get_language_server_class(language)
                if not language_server_class:
                    logger.warning(f"No language server available for {language}")
                    return False
                
                # Create SolidLSP settings
                solidlsp_settings = self.config.to_solidlsp_settings()
                
                # Initialize language server
                language_server = language_server_class(
                    project_root=project_root,
                    solidlsp_settings=solidlsp_settings
                )
                
                # Start the language server
                success = await self._start_language_server(language, language_server)
                if success:
                    self._language_servers[language] = language_server
                    self._initialized_languages.add(language)
                    self._running = True
                    logger.info(f"Language server for {language} initialized successfully")
                    return True
                else:
                    logger.error(f"Failed to start language server for {language}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to initialize language server for {language}: {e}")
            return False
    
    async def shutdown(self) -> None:
        """Shutdown all language servers"""
        try:
            logger.info("Shutting down SolidLSP adapter")
            
            with self._lock:
                self._shutdown_event.set()
                self._running = False
                
                # Shutdown all language servers
                for language, server in self._language_servers.items():
                    try:
                        await self._shutdown_language_server(language, server)
                    except Exception as e:
                        logger.error(f"Error shutting down {language} server: {e}")
                
                # Clear state
                self._language_servers.clear()
                self._server_handlers.clear()
                self._initialized_languages.clear()
            
            logger.info("SolidLSP adapter shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during SolidLSP adapter shutdown: {e}")
    
    async def get_diagnostics(self, file_path: str) -> List[UnifiedDiagnostic]:
        """Get diagnostics for a file"""
        try:
            language = self._detect_file_language(file_path)
            if not language or language not in self._language_servers:
                return []
            
            server = self._language_servers[language]
            
            # Get diagnostics from SolidLSP
            diagnostics = await self._execute_lsp_request(
                language, 
                lambda: server.get_diagnostics(file_path)
            )
            
            # Convert to unified format
            unified_diagnostics = []
            for diagnostic in diagnostics:
                unified_diagnostic = self._convert_diagnostic(diagnostic)
                if unified_diagnostic:
                    unified_diagnostics.append(unified_diagnostic)
            
            self._increment_request_count("get_diagnostics")
            return unified_diagnostics
            
        except Exception as e:
            logger.error(f"Failed to get diagnostics for {file_path}: {e}")
            self._increment_error_count("get_diagnostics")
            return []
    
    async def get_symbols(self, file_path: str) -> List[UnifiedSymbol]:
        """Get symbols in a file"""
        try:
            language = self._detect_file_language(file_path)
            if not language or language not in self._language_servers:
                return []
            
            server = self._language_servers[language]
            
            # Get symbols from SolidLSP
            symbols = await self._execute_lsp_request(
                language,
                lambda: server.get_document_symbols(file_path)
            )
            
            # Convert to unified format
            unified_symbols = []
            for symbol in symbols:
                unified_symbol = self._convert_symbol(symbol, file_path)
                if unified_symbol:
                    unified_symbols.append(unified_symbol)
            
            self._increment_request_count("get_symbols")
            return unified_symbols
            
        except Exception as e:
            logger.error(f"Failed to get symbols for {file_path}: {e}")
            self._increment_error_count("get_symbols")
            return []
    
    async def get_definition(self, file_path: str, position: UnifiedPosition) -> List[UnifiedLocation]:
        """Get definition locations for a symbol"""
        try:
            language = self._detect_file_language(file_path)
            if not language or language not in self._language_servers:
                return []
            
            server = self._language_servers[language]
            
            # Convert position to LSP format
            lsp_position = self._convert_position_to_lsp(position)
            
            # Get definition from SolidLSP
            definitions = await self._execute_lsp_request(
                language,
                lambda: server.get_definition(file_path, lsp_position)
            )
            
            # Convert to unified format
            unified_locations = []
            for definition in definitions:
                unified_location = self._convert_location(definition)
                if unified_location:
                    unified_locations.append(unified_location)
            
            self._increment_request_count("get_definition")
            return unified_locations
            
        except Exception as e:
            logger.error(f"Failed to get definition for {file_path}:{position.line}:{position.character}: {e}")
            self._increment_error_count("get_definition")
            return []
    
    async def get_references(self, file_path: str, position: UnifiedPosition) -> List[UnifiedLocation]:
        """Get reference locations for a symbol"""
        try:
            language = self._detect_file_language(file_path)
            if not language or language not in self._language_servers:
                return []
            
            server = self._language_servers[language]
            
            # Convert position to LSP format
            lsp_position = self._convert_position_to_lsp(position)
            
            # Get references from SolidLSP
            references = await self._execute_lsp_request(
                language,
                lambda: server.get_references(file_path, lsp_position)
            )
            
            # Convert to unified format
            unified_locations = []
            for reference in references:
                unified_location = self._convert_location(reference)
                if unified_location:
                    unified_locations.append(unified_location)
            
            self._increment_request_count("get_references")
            return unified_locations
            
        except Exception as e:
            logger.error(f"Failed to get references for {file_path}:{position.line}:{position.character}: {e}")
            self._increment_error_count("get_references")
            return []
    
    async def get_code_actions(self, file_path: str, range: UnifiedRange, diagnostics: List[UnifiedDiagnostic]) -> List[Dict[str, Any]]:
        """Get available code actions for a range"""
        try:
            language = self._detect_file_language(file_path)
            if not language or language not in self._language_servers:
                return []
            
            server = self._language_servers[language]
            
            # Convert range and diagnostics to LSP format
            lsp_range = self._convert_range_to_lsp(range)
            lsp_diagnostics = [self._convert_diagnostic_to_lsp(d) for d in diagnostics]
            
            # Get code actions from SolidLSP
            code_actions = await self._execute_lsp_request(
                language,
                lambda: server.get_code_actions(file_path, lsp_range, lsp_diagnostics)
            )
            
            # Convert to unified format (keep as dict for flexibility)
            unified_actions = []
            for action in code_actions:
                if isinstance(action, dict):
                    unified_actions.append(action)
                else:
                    # Convert CodeAction object to dict
                    unified_actions.append(self._convert_code_action(action))
            
            self._increment_request_count("get_code_actions")
            return unified_actions
            
        except Exception as e:
            logger.error(f"Failed to get code actions for {file_path}: {e}")
            self._increment_error_count("get_code_actions")
            return []
    
    def is_running(self) -> bool:
        """Check if any language server is running"""
        with self._lock:
            return self._running and len(self._language_servers) > 0
    
    # Private helper methods
    
    def _get_language_server_class(self, language: str):
        """Get the appropriate language server class for a language"""
        # This would need to be expanded based on available language servers
        # For now, return a generic mapping
        language_map = {
            'python': 'PythonLanguageServer',
            'javascript': 'TypeScriptLanguageServer',
            'typescript': 'TypeScriptLanguageServer',
            'java': 'JavaLanguageServer',
            'go': 'GoplsLanguageServer',
            'rust': 'RustAnalyzerLanguageServer',
            'cpp': 'ClangdLanguageServer',
            'c': 'ClangdLanguageServer',
            'csharp': 'CSharpLanguageServer',
            'ruby': 'RubyLanguageServer',
            'php': 'PhpLanguageServer'
        }
        
        # This is a placeholder - actual implementation would import and return
        # the appropriate SolidLanguageServer subclass
        if language in language_map:
            # For now, return a generic class reference
            # In real implementation, this would import the specific server class
            return SolidLanguageServer
        
        return None
    
    async def _start_language_server(self, language: str, server: SolidLanguageServer) -> bool:
        """Start a language server"""
        try:
            # This would call the actual server initialization
            # For now, simulate successful startup
            await asyncio.sleep(0.1)  # Simulate startup time
            return True
        except Exception as e:
            logger.error(f"Failed to start {language} server: {e}")
            return False
    
    async def _shutdown_language_server(self, language: str, server: SolidLanguageServer):
        """Shutdown a language server"""
        try:
            # This would call the actual server shutdown
            await asyncio.sleep(0.1)  # Simulate shutdown time
            logger.debug(f"Language server for {language} shut down")
        except Exception as e:
            logger.error(f"Error shutting down {language} server: {e}")
    
    async def _execute_lsp_request(self, language: str, request_func):
        """Execute an LSP request with error handling and timeout"""
        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(None, request_func),
                timeout=self.config.timeout
            )
            return result
        except asyncio.TimeoutError:
            logger.error(f"LSP request timed out for {language}")
            raise
        except Exception as e:
            logger.error(f"LSP request failed for {language}: {e}")
            raise
    
    def _detect_file_language(self, file_path: str) -> Optional[str]:
        """Detect the programming language of a file"""
        file_path = Path(file_path)
        extension = file_path.suffix.lower()
        
        extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.go': 'go',
            '.rs': 'rust',
            '.cpp': 'cpp',
            '.cc': 'cpp',
            '.cxx': 'cpp',
            '.c': 'c',
            '.cs': 'csharp',
            '.rb': 'ruby',
            '.php': 'php'
        }
        
        return extension_map.get(extension)
    
    # Type conversion methods
    
    def _convert_diagnostic(self, diagnostic) -> Optional[UnifiedDiagnostic]:
        """Convert SolidLSP diagnostic to unified format"""
        try:
            # Handle different diagnostic types from SolidLSP
            if hasattr(diagnostic, 'range') and hasattr(diagnostic, 'message'):
                severity = self._convert_severity(getattr(diagnostic, 'severity', 1))
                range_obj = self._convert_range(diagnostic.range)
                
                return UnifiedDiagnostic(
                    range=range_obj,
                    severity=severity,
                    code=getattr(diagnostic, 'code', None),
                    source=getattr(diagnostic, 'source', 'solidlsp'),
                    message=diagnostic.message,
                    related_information=getattr(diagnostic, 'relatedInformation', []),
                    tags=getattr(diagnostic, 'tags', [])
                )
        except Exception as e:
            logger.error(f"Failed to convert diagnostic: {e}")
        
        return None
    
    def _convert_symbol(self, symbol, file_path: str) -> Optional[UnifiedSymbol]:
        """Convert SolidLSP symbol to unified format"""
        try:
            if isinstance(symbol, UnifiedSymbolInformation):
                location = UnifiedLocation(
                    uri=f"file://{file_path}",
                    range=self._convert_range(symbol.location.range),
                    absolute_path=file_path,
                    relative_path=str(Path(file_path).relative_to(self.project_root)) if self.project_root else None
                )
                
                return UnifiedSymbol(
                    name=symbol.name,
                    kind=self._convert_symbol_kind(symbol.kind),
                    location=location,
                    container_name=getattr(symbol, 'containerName', None),
                    detail=getattr(symbol, 'detail', None),
                    deprecated=getattr(symbol, 'deprecated', False)
                )
        except Exception as e:
            logger.error(f"Failed to convert symbol: {e}")
        
        return None
    
    def _convert_location(self, location) -> Optional[UnifiedLocation]:
        """Convert SolidLSP location to unified format"""
        try:
            if hasattr(location, 'uri') and hasattr(location, 'range'):
                return UnifiedLocation(
                    uri=location.uri,
                    range=self._convert_range(location.range),
                    absolute_path=getattr(location, 'absolutePath', None),
                    relative_path=getattr(location, 'relativePath', None)
                )
        except Exception as e:
            logger.error(f"Failed to convert location: {e}")
        
        return None
    
    def _convert_range(self, range_obj) -> UnifiedRange:
        """Convert SolidLSP range to unified format"""
        start = UnifiedPosition(
            line=range_obj.start.line,
            character=range_obj.start.character
        )
        end = UnifiedPosition(
            line=range_obj.end.line,
            character=range_obj.end.character
        )
        return UnifiedRange(start=start, end=end)
    
    def _convert_severity(self, severity: int) -> DiagnosticSeverity:
        """Convert LSP severity to unified format"""
        severity_map = {
            1: DiagnosticSeverity.ERROR,
            2: DiagnosticSeverity.WARNING,
            3: DiagnosticSeverity.INFO,
            4: DiagnosticSeverity.HINT
        }
        return severity_map.get(severity, DiagnosticSeverity.ERROR)
    
    def _convert_symbol_kind(self, kind) -> SymbolKind:
        """Convert LSP symbol kind to unified format"""
        # This would need to map LSP symbol kinds to unified kinds
        # For now, return a default
        return SymbolKind.FUNCTION
    
    def _convert_position_to_lsp(self, position: UnifiedPosition) -> Position:
        """Convert unified position to LSP format"""
        return Position(line=position.line, character=position.character)
    
    def _convert_range_to_lsp(self, range_obj: UnifiedRange) -> Range:
        """Convert unified range to LSP format"""
        return Range(
            start=self._convert_position_to_lsp(range_obj.start),
            end=self._convert_position_to_lsp(range_obj.end)
        )
    
    def _convert_diagnostic_to_lsp(self, diagnostic: UnifiedDiagnostic) -> Dict[str, Any]:
        """Convert unified diagnostic to LSP format"""
        return {
            'range': self._convert_range_to_lsp(diagnostic.range),
            'severity': self._convert_severity_to_lsp(diagnostic.severity),
            'code': diagnostic.code,
            'source': diagnostic.source,
            'message': diagnostic.message
        }
    
    def _convert_severity_to_lsp(self, severity: DiagnosticSeverity) -> int:
        """Convert unified severity to LSP format"""
        severity_map = {
            DiagnosticSeverity.ERROR: 1,
            DiagnosticSeverity.WARNING: 2,
            DiagnosticSeverity.INFO: 3,
            DiagnosticSeverity.HINT: 4
        }
        return severity_map.get(severity, 1)
    
    def _convert_code_action(self, action) -> Dict[str, Any]:
        """Convert code action to dictionary format"""
        if hasattr(action, 'title'):
            return {
                'title': action.title,
                'kind': getattr(action, 'kind', None),
                'diagnostics': getattr(action, 'diagnostics', []),
                'edit': getattr(action, 'edit', None),
                'command': getattr(action, 'command', None)
            }
        return {}
    
    # Performance tracking
    
    def _increment_request_count(self, request_type: str):
        """Increment request counter"""
        with self._lock:
            self._request_counts[request_type] = self._request_counts.get(request_type, 0) + 1
    
    def _increment_error_count(self, request_type: str):
        """Increment error counter"""
        with self._lock:
            self._error_counts[request_type] = self._error_counts.get(request_type, 0) + 1
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        with self._lock:
            return {
                'initialized_languages': list(self._initialized_languages),
                'request_counts': self._request_counts.copy(),
                'error_counts': self._error_counts.copy(),
                'running': self._running
            }
