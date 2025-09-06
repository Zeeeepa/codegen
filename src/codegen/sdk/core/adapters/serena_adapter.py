# Copyright 2025 Emcie Co Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Serena Integration Adapter

This module provides the adapter that integrates Serena's project management
and symbol analysis capabilities into the unified graph-sitter system.
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Callable
import threading
import time
from dataclasses import dataclass

from ..integration_interfaces import (
    IProjectManager, ISymbolResolver, UnifiedSymbol, UnifiedLocation,
    UnifiedRange, UnifiedPosition, SymbolKind
)
from ..unified_config import UnifiedConfiguration

# Serena imports
try:
    from serena.project import Project as SerenaProject
    from serena.symbol import (
        Symbol as SerenaSymbol,
        LanguageServerSymbolLocation,
        PositionInFile
    )
    from serena.agent import SerenaAgent
    from serena.config.serena_config import ProjectConfig as SerenaProjectConfig
    SERENA_AVAILABLE = True
except ImportError:
    SERENA_AVAILABLE = False
    SerenaProject = None
    SerenaSymbol = None
    LanguageServerSymbolLocation = None
    PositionInFile = None
    SerenaAgent = None
    SerenaProjectConfig = None

logger = logging.getLogger(__name__)


@dataclass
class FileWatchEvent:
    """Represents a file system change event"""
    file_path: str
    change_type: str  # 'created', 'modified', 'deleted'
    timestamp: float


class SerenaAdapter(IProjectManager, ISymbolResolver):
    """
    Adapter that integrates Serena's project management and symbol analysis
    capabilities into the unified system.
    
    This adapter provides project configuration, symbol analysis, and workspace
    management capabilities through Serena's agent-based architecture.
    """
    
    def __init__(self, config: UnifiedConfiguration):
        self.config = config
        self.project_root: Optional[str] = None
        
        # Serena components
        self._serena_project: Optional[SerenaProject] = None
        self._serena_agent: Optional[SerenaAgent] = None
        self._project_config: Optional[SerenaProjectConfig] = None
        
        # State management
        self._lock = threading.RLock()
        self._initialized = False
        self._file_watchers: List[Callable[[str, str], None]] = []
        self._watching_files = False
        
        # File tracking
        self._tracked_files: Set[str] = set()
        self._ignored_patterns: Set[str] = set()
        self._detected_languages: List[str] = []
        
        # Performance tracking
        self._operation_counts: Dict[str, int] = {}
        self._error_counts: Dict[str, int] = {}
        
        if not SERENA_AVAILABLE:
            logger.warning("Serena is not available - some functionality will be limited")
        
        logger.info("Serena adapter initialized")
    
    def initialize_project(self, project_root: str) -> bool:
        """Initialize project management for a directory"""
        try:
            with self._lock:
                if self._initialized:
                    logger.debug("Serena adapter already initialized")
                    return True
                
                logger.info(f"Initializing Serena project management for {project_root}")
                
                self.project_root = project_root
                project_path = Path(project_root)
                
                if not project_path.exists():
                    logger.error(f"Project directory does not exist: {project_root}")
                    return False
                
                if not SERENA_AVAILABLE:
                    logger.warning("Serena not available - using fallback implementation")
                    return self._initialize_fallback(project_root)
                
                # Initialize Serena project
                try:
                    self._serena_project = SerenaProject.load(
                        project_root=project_path,
                        autogenerate=True
                    )
                    
                    # Get project configuration
                    self._project_config = self._serena_project.project_config
                    
                    # Initialize Serena agent if needed
                    if self.config.enhancedcontext:
                        self._serena_agent = SerenaAgent(
                            project=self._serena_project
                        )
                    
                    # Set up ignored patterns
                    self._setup_ignored_patterns()
                    
                    # Detect languages
                    self._detect_project_languages()
                    
                    # Scan project files
                    self._scan_project_files()
                    
                    self._initialized = True
                    logger.info(f"Serena project initialized successfully for {project_path.name}")
                    return True
                    
                except Exception as e:
                    logger.error(f"Failed to initialize Serena project: {e}")
                    return self._initialize_fallback(project_root)
                    
        except Exception as e:
            logger.error(f"Failed to initialize project management: {e}")
            return False
    
    def _initialize_fallback(self, project_root: str) -> bool:
        """Initialize with fallback implementation when Serena is not available"""
        try:
            self.project_root = project_root
            
            # Set up basic ignored patterns
            self._ignored_patterns = {
                ".git", ".venv", "venv", "node_modules", "__pycache__",
                "*.pyc", "*.pyo", "*.pyd", ".DS_Store", "*.log"
            }
            
            # Basic language detection
            self._detect_project_languages_fallback()
            
            # Scan project files
            self._scan_project_files()
            
            self._initialized = True
            logger.info("Fallback project management initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize fallback project management: {e}")
            return False
    
    def get_project_files(self, include_ignored: bool = False) -> List[str]:
        """Get list of project files"""
        try:
            if not self._initialized or not self.project_root:
                return []
            
            project_path = Path(self.project_root)
            files = []
            
            for file_path in project_path.rglob("*"):
                if file_path.is_file():
                    relative_path = str(file_path.relative_to(project_path))
                    
                    if not include_ignored and self.is_file_ignored(relative_path):
                        continue
                    
                    files.append(str(file_path))
            
            self._increment_operation_count("get_project_files")
            return files
            
        except Exception as e:
            logger.error(f"Failed to get project files: {e}")
            self._increment_error_count("get_project_files")
            return []
    
    def is_file_ignored(self, file_path: str) -> bool:
        """Check if a file should be ignored"""
        try:
            if self._serena_project:
                # Use Serena's ignore logic
                return self._serena_project._is_ignored_relative_path(file_path)
            else:
                # Fallback ignore logic
                return self._is_file_ignored_fallback(file_path)
                
        except Exception as e:
            logger.debug(f"Error checking if file is ignored: {e}")
            return False
    
    def _is_file_ignored_fallback(self, file_path: str) -> bool:
        """Fallback implementation for file ignore checking"""
        file_path_obj = Path(file_path)
        
        # Check if any part of the path matches ignored patterns
        for part in file_path_obj.parts:
            if part in self._ignored_patterns:
                return True
        
        # Check file extension patterns
        if file_path_obj.suffix in {".pyc", ".pyo", ".pyd", ".log"}:
            return True
        
        # Check specific filenames
        if file_path_obj.name in {".DS_Store", "Thumbs.db"}:
            return True
        
        return False
    
    def get_project_languages(self) -> List[str]:
        """Get detected programming languages in the project"""
        return self._detected_languages.copy()
    
    def get_project_config(self) -> Dict[str, Any]:
        """Get project configuration"""
        try:
            if self._project_config:
                return {
                    "project_name": self._project_config.project_name,
                    "language": self._project_config.language.value if hasattr(self._project_config.language, 'value') else str(self._project_config.language),
                    "ignored_paths": getattr(self._project_config, 'ignored_paths', []),
                    "encoding": getattr(self._project_config, 'encoding', 'utf-8')
                }
            else:
                return {
                    "project_name": Path(self.project_root).name if self.project_root else "unknown",
                    "language": "auto-detect",
                    "ignored_paths": list(self._ignored_patterns),
                    "encoding": "utf-8"
                }
                
        except Exception as e:
            logger.error(f"Failed to get project config: {e}")
            return {}
    
    def watch_files(self, callback: Callable[[str, str], None]) -> None:
        """Start watching files for changes"""
        try:
            self._file_watchers.append(callback)
            
            if not self._watching_files:
                self._start_file_watching()
                self._watching_files = True
                logger.info("File watching started")
            
        except Exception as e:
            logger.error(f"Failed to start file watching: {e}")
    
    def stop_watching(self) -> None:
        """Stop watching files"""
        try:
            self._watching_files = False
            self._file_watchers.clear()
            logger.info("File watching stopped")
            
        except Exception as e:
            logger.error(f"Failed to stop file watching: {e}")
    
    def _start_file_watching(self) -> None:
        """Start the file watching thread"""
        def watch_thread():
            """File watching thread implementation"""
            try:
                # This is a simplified implementation
                # In a real implementation, you would use a proper file watching library
                # like watchdog or similar
                
                last_scan_time = time.time()
                file_mtimes: Dict[str, float] = {}
                
                while self._watching_files:
                    try:
                        current_time = time.time()
                        
                        # Scan for changes every second
                        if current_time - last_scan_time >= 1.0:
                            self._check_file_changes(file_mtimes)
                            last_scan_time = current_time
                        
                        time.sleep(0.1)
                        
                    except Exception as e:
                        logger.error(f"Error in file watching thread: {e}")
                        time.sleep(1.0)
                        
            except Exception as e:
                logger.error(f"File watching thread failed: {e}")
        
        thread = threading.Thread(target=watch_thread, daemon=True)
        thread.start()
    
    def _check_file_changes(self, file_mtimes: Dict[str, float]) -> None:
        """Check for file changes and notify watchers"""
        try:
            if not self.project_root:
                return
            
            project_files = self.get_project_files()
            current_files = set(project_files)
            previous_files = set(file_mtimes.keys())
            
            # Check for new files
            new_files = current_files - previous_files
            for file_path in new_files:
                try:
                    mtime = os.path.getmtime(file_path)
                    file_mtimes[file_path] = mtime
                    self._notify_file_change(file_path, "created")
                except OSError:
                    pass
            
            # Check for deleted files
            deleted_files = previous_files - current_files
            for file_path in deleted_files:
                del file_mtimes[file_path]
                self._notify_file_change(file_path, "deleted")
            
            # Check for modified files
            for file_path in current_files & previous_files:
                try:
                    current_mtime = os.path.getmtime(file_path)
                    if current_mtime > file_mtimes[file_path]:
                        file_mtimes[file_path] = current_mtime
                        self._notify_file_change(file_path, "modified")
                except OSError:
                    pass
                    
        except Exception as e:
            logger.error(f"Error checking file changes: {e}")
    
    def _notify_file_change(self, file_path: str, change_type: str) -> None:
        """Notify all watchers of a file change"""
        for callback in self._file_watchers:
            try:
                callback(file_path, change_type)
            except Exception as e:
                logger.error(f"Error in file change callback: {e}")
    
    # ISymbolResolver implementation
    
    async def resolve_symbol(self, file_path: str, position: UnifiedPosition) -> Optional[UnifiedSymbol]:
        """Resolve symbol at a position"""
        try:
            if not self._serena_project:
                return None
            
            # Convert position to Serena format
            serena_position = PositionInFile(line=position.line, col=position.character)
            
            # This would use Serena's symbol resolution capabilities
            # For now, return a placeholder implementation
            
            self._increment_operation_count("resolve_symbol")
            return None
            
        except Exception as e:
            logger.error(f"Failed to resolve symbol at {file_path}:{position.line}:{position.character}: {e}")
            self._increment_error_count("resolve_symbol")
            return None
    
    async def find_symbol_references(self, symbol: UnifiedSymbol) -> List[UnifiedLocation]:
        """Find all references to a symbol"""
        try:
            if not self._serena_project:
                return []
            
            # This would use Serena's reference finding capabilities
            # For now, return empty list
            
            self._increment_operation_count("find_symbol_references")
            return []
            
        except Exception as e:
            logger.error(f"Failed to find symbol references: {e}")
            self._increment_error_count("find_symbol_references")
            return []
    
    async def find_symbol_definition(self, symbol: UnifiedSymbol) -> Optional[UnifiedLocation]:
        """Find the definition of a symbol"""
        try:
            if not self._serena_project:
                return None
            
            # This would use Serena's definition finding capabilities
            # For now, return None
            
            self._increment_operation_count("find_symbol_definition")
            return None
            
        except Exception as e:
            logger.error(f"Failed to find symbol definition: {e}")
            self._increment_error_count("find_symbol_definition")
            return None
    
    async def get_symbol_hierarchy(self, symbol: UnifiedSymbol) -> List[UnifiedSymbol]:
        """Get the hierarchy of a symbol (parents and children)"""
        try:
            if not self._serena_project:
                return []
            
            # This would use Serena's symbol hierarchy capabilities
            # For now, return empty list
            
            self._increment_operation_count("get_symbol_hierarchy")
            return []
            
        except Exception as e:
            logger.error(f"Failed to get symbol hierarchy: {e}")
            self._increment_error_count("get_symbol_hierarchy")
            return []
    
    async def search_symbols(self, query: str, file_path: Optional[str] = None) -> List[UnifiedSymbol]:
        """Search for symbols matching a query"""
        try:
            if not self._serena_project:
                return []
            
            # This would use Serena's symbol search capabilities
            # For now, return empty list
            
            self._increment_operation_count("search_symbols")
            return []
            
        except Exception as e:
            logger.error(f"Failed to search symbols: {e}")
            self._increment_error_count("search_symbols")
            return []
    
    # Private helper methods
    
    def _setup_ignored_patterns(self) -> None:
        """Set up ignored file patterns from Serena configuration"""
        try:
            if self._serena_project and hasattr(self._serena_project, '_ignored_patterns'):
                self._ignored_patterns = set(self._serena_project._ignored_patterns)
            else:
                # Default patterns
                self._ignored_patterns = {
                    ".git", ".venv", "venv", "node_modules", "__pycache__",
                    "*.pyc", "*.pyo", "*.pyd", ".DS_Store", "*.log",
                    ".pytest_cache", ".mypy_cache", ".ruff_cache"
                }
                
        except Exception as e:
            logger.error(f"Failed to setup ignored patterns: {e}")
    
    def _detect_project_languages(self) -> None:
        """Detect programming languages in the project using Serena"""
        try:
            if self._serena_project:
                # Use Serena's language detection
                language = self._serena_project.language
                if hasattr(language, 'value'):
                    self._detected_languages = [language.value]
                else:
                    self._detected_languages = [str(language)]
            else:
                self._detect_project_languages_fallback()
                
        except Exception as e:
            logger.error(f"Failed to detect project languages: {e}")
            self._detect_project_languages_fallback()
    
    def _detect_project_languages_fallback(self) -> None:
        """Fallback language detection implementation"""
        try:
            if not self.project_root:
                return
            
            languages = set()
            project_path = Path(self.project_root)
            
            # Language detection based on file extensions
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
                '.php': 'php',
                '.swift': 'swift',
                '.kt': 'kotlin',
                '.scala': 'scala'
            }
            
            # Scan files to detect languages
            file_count = 0
            for file_path in project_path.rglob("*"):
                if file_path.is_file() and not self.is_file_ignored(str(file_path.relative_to(project_path))):
                    extension = file_path.suffix.lower()
                    if extension in extension_map:
                        languages.add(extension_map[extension])
                    
                    file_count += 1
                    if file_count > 1000:  # Limit scan for performance
                        break
            
            self._detected_languages = sorted(list(languages))
            logger.info(f"Detected languages: {self._detected_languages}")
            
        except Exception as e:
            logger.error(f"Failed to detect languages (fallback): {e}")
            self._detected_languages = []
    
    def _scan_project_files(self) -> None:
        """Scan and track project files"""
        try:
            project_files = self.get_project_files()
            self._tracked_files = set(project_files)
            logger.info(f"Tracking {len(self._tracked_files)} project files")
            
        except Exception as e:
            logger.error(f"Failed to scan project files: {e}")
    
    # Performance tracking
    
    def _increment_operation_count(self, operation: str) -> None:
        """Increment operation counter"""
        with self._lock:
            self._operation_counts[operation] = self._operation_counts.get(operation, 0) + 1
    
    def _increment_error_count(self, operation: str) -> None:
        """Increment error counter"""
        with self._lock:
            self._error_counts[operation] = self._error_counts.get(operation, 0) + 1
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        with self._lock:
            return {
                'initialized': self._initialized,
                'serena_available': SERENA_AVAILABLE,
                'tracked_files': len(self._tracked_files),
                'detected_languages': self._detected_languages,
                'operation_counts': self._operation_counts.copy(),
                'error_counts': self._error_counts.copy(),
                'watching_files': self._watching_files
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get adapter status"""
        return {
            'initialized': self._initialized,
            'project_root': self.project_root,
            'serena_available': SERENA_AVAILABLE,
            'serena_project_loaded': self._serena_project is not None,
            'serena_agent_available': self._serena_agent is not None,
            'detected_languages': self._detected_languages,
            'tracked_files_count': len(self._tracked_files),
            'file_watching': self._watching_files
        }
