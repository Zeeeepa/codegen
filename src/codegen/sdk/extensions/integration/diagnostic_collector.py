"""
Unified Diagnostic Collector for comprehensive error and warning collection.

This module collects diagnostics from multiple sources: SolidLSP, Tree-sitter,
and Serena tools, providing a unified view of all code issues.
"""

import logging
from typing import Dict, List, Optional, Any, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
import time
import threading
from collections import defaultdict

from .config import DiagnosticsConfig

logger = logging.getLogger(__name__)


class DiagnosticSeverity(Enum):
    """Diagnostic severity levels"""
    ERROR = 1
    WARNING = 2
    INFORMATION = 3
    HINT = 4


@dataclass
class UnifiedDiagnostic:
    """Unified diagnostic representation"""
    file_path: str
    line: int
    character: int
    end_line: Optional[int] = None
    end_character: Optional[int] = None
    severity: DiagnosticSeverity = DiagnosticSeverity.ERROR
    message: str = ""
    code: Optional[str] = None
    source: str = "unknown"  # lsp, tree_sitter, serena
    related_information: List[Dict[str, Any]] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    data: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'file_path': self.file_path,
            'line': self.line,
            'character': self.character,
            'end_line': self.end_line,
            'end_character': self.end_character,
            'severity': self.severity.name.lower(),
            'message': self.message,
            'code': self.code,
            'source': self.source,
            'related_information': self.related_information,
            'tags': self.tags,
            'data': self.data
        }


@dataclass
class DiagnosticStats:
    """Statistics about collected diagnostics"""
    total_diagnostics: int = 0
    errors: int = 0
    warnings: int = 0
    information: int = 0
    hints: int = 0
    files_with_diagnostics: int = 0
    sources: Dict[str, int] = field(default_factory=dict)
    last_updated: float = field(default_factory=time.time)


class UnifiedDiagnosticCollector:
    """Collects diagnostics from multiple sources and provides unified access"""
    
    def __init__(self, 
                 config: DiagnosticsConfig,
                 lsp_manager=None,
                 serena_agent=None,
                 tree_sitter_parser=None):
        self.config = config
        self.lsp_manager = lsp_manager
        self.serena_agent = serena_agent
        self.tree_sitter_parser = tree_sitter_parser
        self.logger = logging.getLogger(__name__)
        
        # Diagnostic storage
        self._diagnostics: Dict[str, List[UnifiedDiagnostic]] = defaultdict(list)
        self._diagnostics_lock = threading.RLock()
        
        # Statistics
        self._stats = DiagnosticStats()
        
        # Subscribers for diagnostic changes
        self._subscribers: List[Callable[[str, List[UnifiedDiagnostic]], None]] = []
        
        # Background collection thread
        self._collection_thread = None
        self._stop_collection = threading.Event()
        
        # Initialize collection
        if self.config.enabled:
            self._start_collection()
    
    def _start_collection(self) -> None:
        """Start background diagnostic collection"""
        if self.config.enable_real_time_updates:
            self._collection_thread = threading.Thread(
                target=self._collection_loop,
                daemon=True
            )
            self._collection_thread.start()
            self.logger.info("Started real-time diagnostic collection")
    
    def _collection_loop(self) -> None:
        """Background loop for collecting diagnostics"""
        while not self._stop_collection.is_set():
            try:
                self._collect_all_diagnostics()
                
                # Wait for next collection cycle
                self._stop_collection.wait(self.config.update_debounce_ms / 1000.0)
                
            except Exception as e:
                self.logger.error(f"Error in diagnostic collection loop: {e}")
                time.sleep(5)  # Wait before retrying
    
    def _collect_all_diagnostics(self) -> None:
        """Collect diagnostics from all enabled sources"""
        new_diagnostics = defaultdict(list)
        
        # Collect from LSP servers
        if self.config.collect_from_lsp and self.lsp_manager:
            try:
                lsp_diagnostics = self._collect_lsp_diagnostics()
                for file_path, diagnostics in lsp_diagnostics.items():
                    new_diagnostics[file_path].extend(diagnostics)
            except Exception as e:
                self.logger.warning(f"Failed to collect LSP diagnostics: {e}")
        
        # Collect from Tree-sitter
        if self.config.collect_from_tree_sitter and self.tree_sitter_parser:
            try:
                ts_diagnostics = self._collect_tree_sitter_diagnostics()
                for file_path, diagnostics in ts_diagnostics.items():
                    new_diagnostics[file_path].extend(diagnostics)
            except Exception as e:
                self.logger.warning(f"Failed to collect Tree-sitter diagnostics: {e}")
        
        # Collect from Serena
        if self.config.collect_from_serena and self.serena_agent:
            try:
                serena_diagnostics = self._collect_serena_diagnostics()
                for file_path, diagnostics in serena_diagnostics.items():
                    new_diagnostics[file_path].extend(diagnostics)
            except Exception as e:
                self.logger.warning(f"Failed to collect Serena diagnostics: {e}")
        
        # Filter and update diagnostics
        filtered_diagnostics = self._filter_diagnostics(new_diagnostics)
        self._update_diagnostics(filtered_diagnostics)
    
    def _collect_lsp_diagnostics(self) -> Dict[str, List[UnifiedDiagnostic]]:
        """Collect diagnostics from LSP servers"""
        diagnostics = defaultdict(list)
        
        # This would integrate with SolidLSP to get diagnostics
        # For now, return empty
        
        return diagnostics
    
    def _collect_tree_sitter_diagnostics(self) -> Dict[str, List[UnifiedDiagnostic]]:
        """Collect diagnostics from Tree-sitter parsing"""
        diagnostics = defaultdict(list)
        
        # This would use tree-sitter to find syntax errors
        # For now, return empty
        
        return diagnostics
    
    def _collect_serena_diagnostics(self) -> Dict[str, List[UnifiedDiagnostic]]:
        """Collect diagnostics from Serena tools"""
        diagnostics = defaultdict(list)
        
        # This would use Serena tools to find issues
        # For now, return empty
        
        return diagnostics
    
    def _filter_diagnostics(self, diagnostics: Dict[str, List[UnifiedDiagnostic]]) -> Dict[str, List[UnifiedDiagnostic]]:
        """Filter diagnostics based on configuration"""
        filtered = defaultdict(list)
        
        min_severity = self._parse_severity(self.config.min_severity)
        total_count = 0
        
        for file_path, file_diagnostics in diagnostics.items():
            # Check file patterns
            if not self._should_include_file(file_path):
                continue
            
            file_filtered = []
            
            for diagnostic in file_diagnostics:
                # Check severity filter
                if diagnostic.severity.value > min_severity.value:
                    continue
                
                # Check total limit
                if total_count >= self.config.max_diagnostics_total:
                    break
                
                file_filtered.append(diagnostic)
                total_count += 1
            
            if file_filtered:
                # Limit per file
                if len(file_filtered) > self.config.max_diagnostics_per_file:
                    file_filtered = file_filtered[:self.config.max_diagnostics_per_file]
                
                filtered[file_path] = file_filtered
        
        return filtered
    
    def _should_include_file(self, file_path: str) -> bool:
        """Check if file should be included based on patterns"""
        # Check exclude patterns
        for pattern in self.config.exclude_patterns:
            if pattern in file_path:
                return False
        
        # Check include patterns (if any)
        if self.config.include_patterns:
            for pattern in self.config.include_patterns:
                if pattern in file_path:
                    return True
            return False  # No include pattern matched
        
        return True  # No patterns or passed all checks
    
    def _parse_severity(self, severity_str: str) -> DiagnosticSeverity:
        """Parse severity string to enum"""
        severity_map = {
            'error': DiagnosticSeverity.ERROR,
            'warning': DiagnosticSeverity.WARNING,
            'information': DiagnosticSeverity.INFORMATION,
            'info': DiagnosticSeverity.INFORMATION,
            'hint': DiagnosticSeverity.HINT
        }
        return severity_map.get(severity_str.lower(), DiagnosticSeverity.HINT)
    
    def _update_diagnostics(self, new_diagnostics: Dict[str, List[UnifiedDiagnostic]]) -> None:
        """Update stored diagnostics and notify subscribers"""
        changed_files = set()
        
        with self._diagnostics_lock:
            # Find changed files
            for file_path in set(self._diagnostics.keys()) | set(new_diagnostics.keys()):
                old_diagnostics = self._diagnostics.get(file_path, [])
                new_file_diagnostics = new_diagnostics.get(file_path, [])
                
                if self._diagnostics_changed(old_diagnostics, new_file_diagnostics):
                    changed_files.add(file_path)
            
            # Update diagnostics
            self._diagnostics.clear()
            self._diagnostics.update(new_diagnostics)
            
            # Update statistics
            self._update_stats()
        
        # Notify subscribers of changes
        for file_path in changed_files:
            file_diagnostics = new_diagnostics.get(file_path, [])
            self._notify_subscribers(file_path, file_diagnostics)
    
    def _diagnostics_changed(self, old: List[UnifiedDiagnostic], new: List[UnifiedDiagnostic]) -> bool:
        """Check if diagnostics have changed"""
        if len(old) != len(new):
            return True
        
        # Simple comparison - could be more sophisticated
        for old_diag, new_diag in zip(old, new):
            if (old_diag.message != new_diag.message or 
                old_diag.line != new_diag.line or
                old_diag.severity != new_diag.severity):
                return True
        
        return False
    
    def _update_stats(self) -> None:
        """Update diagnostic statistics"""
        total = 0
        errors = 0
        warnings = 0
        information = 0
        hints = 0
        sources = defaultdict(int)
        
        for file_diagnostics in self._diagnostics.values():
            for diagnostic in file_diagnostics:
                total += 1
                sources[diagnostic.source] += 1
                
                if diagnostic.severity == DiagnosticSeverity.ERROR:
                    errors += 1
                elif diagnostic.severity == DiagnosticSeverity.WARNING:
                    warnings += 1
                elif diagnostic.severity == DiagnosticSeverity.INFORMATION:
                    information += 1
                elif diagnostic.severity == DiagnosticSeverity.HINT:
                    hints += 1
        
        self._stats = DiagnosticStats(
            total_diagnostics=total,
            errors=errors,
            warnings=warnings,
            information=information,
            hints=hints,
            files_with_diagnostics=len(self._diagnostics),
            sources=dict(sources),
            last_updated=time.time()
        )
    
    def _notify_subscribers(self, file_path: str, diagnostics: List[UnifiedDiagnostic]) -> None:
        """Notify subscribers of diagnostic changes"""
        for subscriber in self._subscribers:
            try:
                subscriber(file_path, diagnostics)
            except Exception as e:
                self.logger.warning(f"Subscriber notification failed: {e}")
    
    # Public API
    
    def get_workspace_diagnostics(self) -> Dict[str, List[UnifiedDiagnostic]]:
        """Get all diagnostics in the workspace"""
        with self._diagnostics_lock:
            return dict(self._diagnostics)
    
    def get_file_diagnostics(self, file_path: str) -> List[UnifiedDiagnostic]:
        """Get diagnostics for a specific file"""
        with self._diagnostics_lock:
            return self._diagnostics.get(file_path, [])
    
    def get_diagnostics_by_severity(self, severity: DiagnosticSeverity) -> Dict[str, List[UnifiedDiagnostic]]:
        """Get diagnostics filtered by severity"""
        filtered = defaultdict(list)
        
        with self._diagnostics_lock:
            for file_path, file_diagnostics in self._diagnostics.items():
                matching = [d for d in file_diagnostics if d.severity == severity]
                if matching:
                    filtered[file_path] = matching
        
        return dict(filtered)
    
    def get_errors(self) -> Dict[str, List[UnifiedDiagnostic]]:
        """Get only error diagnostics"""
        return self.get_diagnostics_by_severity(DiagnosticSeverity.ERROR)
    
    def get_warnings(self) -> Dict[str, List[UnifiedDiagnostic]]:
        """Get only warning diagnostics"""
        return self.get_diagnostics_by_severity(DiagnosticSeverity.WARNING)
    
    def get_statistics(self) -> DiagnosticStats:
        """Get diagnostic statistics"""
        return self._stats
    
    def subscribe_to_changes(self, callback: Callable[[str, List[UnifiedDiagnostic]], None]) -> None:
        """Subscribe to diagnostic change notifications"""
        self._subscribers.append(callback)
    
    def unsubscribe_from_changes(self, callback: Callable[[str, List[UnifiedDiagnostic]], None]) -> None:
        """Unsubscribe from diagnostic change notifications"""
        if callback in self._subscribers:
            self._subscribers.remove(callback)
    
    def refresh_diagnostics(self) -> None:
        """Manually refresh all diagnostics"""
        self.logger.info("Manually refreshing diagnostics...")
        self._collect_all_diagnostics()
    
    def clear_diagnostics(self, file_path: Optional[str] = None) -> None:
        """Clear diagnostics for a file or all files"""
        with self._diagnostics_lock:
            if file_path:
                if file_path in self._diagnostics:
                    del self._diagnostics[file_path]
                    self._notify_subscribers(file_path, [])
            else:
                self._diagnostics.clear()
                # Notify all subscribers of clearing
                for subscriber in self._subscribers:
                    try:
                        subscriber("", [])  # Empty file path indicates full clear
                    except Exception as e:
                        self.logger.warning(f"Subscriber notification failed: {e}")
            
            self._update_stats()
    
    def add_diagnostic(self, diagnostic: UnifiedDiagnostic) -> None:
        """Manually add a diagnostic"""
        with self._diagnostics_lock:
            self._diagnostics[diagnostic.file_path].append(diagnostic)
            self._update_stats()
            self._notify_subscribers(diagnostic.file_path, self._diagnostics[diagnostic.file_path])
    
    def remove_diagnostic(self, file_path: str, line: int, character: int) -> bool:
        """Remove a specific diagnostic"""
        with self._diagnostics_lock:
            file_diagnostics = self._diagnostics.get(file_path, [])
            
            for i, diagnostic in enumerate(file_diagnostics):
                if diagnostic.line == line and diagnostic.character == character:
                    del file_diagnostics[i]
                    self._update_stats()
                    self._notify_subscribers(file_path, file_diagnostics)
                    return True
        
        return False
    
    def get_diagnostics_summary(self) -> Dict[str, Any]:
        """Get a comprehensive summary of diagnostics"""
        stats = self.get_statistics()
        
        # Find most problematic files
        file_counts = {}
        with self._diagnostics_lock:
            for file_path, file_diagnostics in self._diagnostics.items():
                error_count = len([d for d in file_diagnostics if d.severity == DiagnosticSeverity.ERROR])
                if error_count > 0:
                    file_counts[file_path] = error_count
        
        most_problematic = sorted(file_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'statistics': {
                'total_diagnostics': stats.total_diagnostics,
                'errors': stats.errors,
                'warnings': stats.warnings,
                'information': stats.information,
                'hints': stats.hints,
                'files_with_diagnostics': stats.files_with_diagnostics,
                'sources': stats.sources,
                'last_updated': stats.last_updated
            },
            'most_problematic_files': [
                {'file_path': file_path, 'error_count': count}
                for file_path, count in most_problematic
            ],
            'configuration': {
                'enabled': self.config.enabled,
                'collect_from_lsp': self.config.collect_from_lsp,
                'collect_from_tree_sitter': self.config.collect_from_tree_sitter,
                'collect_from_serena': self.config.collect_from_serena,
                'min_severity': self.config.min_severity,
                'max_diagnostics_total': self.config.max_diagnostics_total,
                'real_time_updates': self.config.enable_real_time_updates
            }
        }
    
    def cleanup(self) -> None:
        """Cleanup resources and stop collection"""
        self.logger.info("Cleaning up diagnostic collector...")
        
        # Stop collection thread
        if self._collection_thread and self._collection_thread.is_alive():
            self._stop_collection.set()
            self._collection_thread.join(timeout=5)
        
        # Clear diagnostics and subscribers
        with self._diagnostics_lock:
            self._diagnostics.clear()
            self._subscribers.clear()
        
        self.logger.info("Diagnostic collector cleanup completed")
