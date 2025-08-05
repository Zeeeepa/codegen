"""
Comprehensive GitHub Repository Error Analysis using Serena LSP Integration

This module provides a complete solution for analyzing GitHub repositories and
retrieving comprehensive error information, importing all bridge defined classes.
"""

import asyncio
import logging
import tempfile
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Callable, Union
from dataclasses import dataclass, field
from collections import defaultdict
from urllib.parse import urlparse

# Import all bridge defined classes
from .serena_bridge import (
    ErrorType,
    RuntimeContext,
    ErrorInfo,
    SerenaLSPBridge,
    TransactionAwareLSPManager,
    EnhancedSerenaIntegration,
    get_lsp_manager,
    shutdown_all_lsp_managers,
    create_serena_lsp_bridge,
    create_enhanced_serena_integration,
)

# Graceful imports
try:
    from graph_sitter.shared.logging.get_logger import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


# Error analysis enums and classes
class ErrorSeverity:
    """Error severity levels."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    HINT = "hint"


class ErrorCategory:
    """Error categories for classification."""
    SYNTAX = "syntax"
    TYPE = "type"
    LOGIC = "logic"
    PERFORMANCE = "performance"
    SECURITY = "security"
    STYLE = "style"
    COMPATIBILITY = "compatibility"
    DEPENDENCY = "dependency"
    UNKNOWN = "unknown"


@dataclass
class ErrorLocation:
    """Represents the location of an error in code."""
    file_path: str
    line: int
    column: int
    end_line: Optional[int] = None
    end_column: Optional[int] = None
    
    @property
    def range_text(self) -> str:
        """Get human-readable range text."""
        if self.end_line and self.end_column:
            return f"{self.line}:{self.column}-{self.end_line}:{self.end_column}"
        return f"{self.line}:{self.column}"
    
    @property
    def file_name(self) -> str:
        """Get just the filename."""
        return Path(self.file_path).name


@dataclass
class CodeError:
    """Represents a comprehensive code error with context."""
    id: str
    message: str
    severity: str
    category: str
    location: ErrorLocation
    code: Optional[str] = None
    source: str = "serena"
    suggestions: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    related_errors: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    
    @property
    def is_critical(self) -> bool:
        """Check if error is critical (error severity)."""
        return self.severity == ErrorSeverity.ERROR
    
    @property
    def display_text(self) -> str:
        """Get formatted display text for the error."""
        return f"[{self.severity.upper()}] {self.location.file_name}:{self.location.range_text} - {self.message}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary representation."""
        return {
            'id': self.id,
            'message': self.message,
            'severity': self.severity,
            'category': self.category,
            'location': {
                'file_path': self.location.file_path,
                'line': self.location.line,
                'column': self.location.column,
                'end_line': self.location.end_line,
                'end_column': self.location.end_column
            },
            'code': self.code,
            'source': self.source,
            'suggestions': self.suggestions,
            'context': self.context,
            'related_errors': self.related_errors,
            'timestamp': self.timestamp
        }


@dataclass
class ComprehensiveErrorList:
    """Comprehensive list of code errors with metadata and analysis."""
    errors: List[CodeError] = field(default_factory=list)
    total_count: int = 0
    critical_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    files_analyzed: Set[str] = field(default_factory=set)
    analysis_timestamp: float = field(default_factory=time.time)
    analysis_duration: float = 0.0
    
    def __post_init__(self):
        """Calculate counts after initialization."""
        self._update_counts()
    
    def _update_counts(self):
        """Update error counts."""
        self.total_count = len(self.errors)
        self.critical_count = sum(1 for e in self.errors if e.severity == ErrorSeverity.ERROR)
        self.warning_count = sum(1 for e in self.errors if e.severity == ErrorSeverity.WARNING)
        self.info_count = sum(1 for e in self.errors if e.severity in [ErrorSeverity.INFO, ErrorSeverity.HINT])
        self.files_analyzed = {e.location.file_path for e in self.errors}
    
    def add_error(self, error: CodeError):
        """Add an error to the list."""
        self.errors.append(error)
        self._update_counts()
    
    def add_errors(self, errors: List[CodeError]):
        """Add multiple errors to the list."""
        self.errors.extend(errors)
        self._update_counts()
    
    def get_errors_by_severity(self, severity: str) -> List[CodeError]:
        """Get errors filtered by severity."""
        return [e for e in self.errors if e.severity == severity]
    
    def get_errors_by_category(self, category: str) -> List[CodeError]:
        """Get errors filtered by category."""
        return [e for e in self.errors if e.category == category]
    
    def get_errors_by_file(self, file_path: str) -> List[CodeError]:
        """Get errors for a specific file."""
        return [e for e in self.errors if e.location.file_path == file_path]
    
    def get_critical_errors(self) -> List[CodeError]:
        """Get only critical errors."""
        return self.get_errors_by_severity(ErrorSeverity.ERROR)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics."""
        return {
            'total_errors': self.total_count,
            'critical_errors': self.critical_count,
            'warnings': self.warning_count,
            'info_hints': self.info_count,
            'files_with_errors': len(self.files_analyzed),
            'analysis_timestamp': self.analysis_timestamp,
            'analysis_duration': self.analysis_duration
        }


@dataclass
class RepositoryInfo:
    """Information about a GitHub repository."""
    url: str
    name: str
    owner: str
    local_path: str
    branch: str = "main"
    clone_depth: Optional[int] = None
    
    @classmethod
    def from_url(cls, url: str, local_path: str) -> 'RepositoryInfo':
        """Create RepositoryInfo from GitHub URL."""
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')
        
        if len(path_parts) < 2:
            raise ValueError(f"Invalid GitHub URL: {url}")
        
        owner = path_parts[0]
        name = path_parts[1].replace('.git', '')
        
        return cls(
            url=url,
            name=name,
            owner=owner,
            local_path=local_path
        )


@dataclass
class AnalysisResult:
    """Result of repository analysis."""
    repository: RepositoryInfo
    error_list: ComprehensiveErrorList
    analysis_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_errors_by_severity(self) -> Dict[str, List[CodeError]]:
        """Get errors grouped by severity."""
        errors_by_severity = {
            'critical': self.error_list.get_errors_by_severity(ErrorSeverity.ERROR),
            'warning': self.error_list.get_errors_by_severity(ErrorSeverity.WARNING),
            'info': self.error_list.get_errors_by_severity(ErrorSeverity.INFO),
            'hint': self.error_list.get_errors_by_severity(ErrorSeverity.HINT)
        }
        return errors_by_severity
    
    def get_summary_by_severity(self) -> Dict[str, Dict[str, Any]]:
        """Get summary statistics by severity."""
        errors_by_severity = self.get_errors_by_severity()
        
        summary = {}
        for severity, errors in errors_by_severity.items():
            category_counts = defaultdict(int)
            file_counts = defaultdict(int)
            
            for error in errors:
                category_counts[error.category] += 1
                file_counts[error.location.file_path] += 1
            
            summary[severity] = {
                'count': len(errors),
                'categories': dict(category_counts),
                'files_affected': len(file_counts),
                'top_files': sorted(file_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            }
        
        return summary


class GitHubRepositoryAnalyzer:
    """
    Comprehensive GitHub repository error analyzer with Serena LSP integration.
    """
    
    def __init__(self, work_dir: Optional[str] = None, enable_runtime_collection: bool = True):
        self.work_dir = Path(work_dir) if work_dir else Path(tempfile.mkdtemp())
        self.work_dir.mkdir(exist_ok=True)
        
        self.enable_runtime_collection = enable_runtime_collection
        self.repositories: Dict[str, RepositoryInfo] = {}
        self.lsp_bridges: Dict[str, SerenaLSPBridge] = {}
        self.analysis_cache: Dict[str, AnalysisResult] = {}
        
        # Performance tracking
        self.performance_stats = {
            'repositories_analyzed': 0,
            'total_analysis_time': 0.0,
            'average_analysis_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        
        logger.info(f"GitHub Repository Analyzer initialized with work_dir: {self.work_dir}")
    
    async def analyze_repository_by_url(
        self,
        repo_url: str,
        branch: str = "main",
        clone_depth: Optional[int] = 1,
        use_cache: bool = True,
        severity_filter: Optional[List[str]] = None
    ) -> AnalysisResult:
        """
        Analyze a GitHub repository by URL and return comprehensive error analysis.
        """
        start_time = time.time()
        
        try:
            # Create repository info
            local_path = self.work_dir / f"repo_{int(time.time())}"
            repo_info = RepositoryInfo.from_url(repo_url, str(local_path))
            repo_info.branch = branch
            repo_info.clone_depth = clone_depth
            
            # Check cache
            cache_key = f"{repo_url}:{branch}"
            if use_cache and cache_key in self.analysis_cache:
                self.performance_stats['cache_hits'] += 1
                cached_result = self.analysis_cache[cache_key]
                logger.info(f"Using cached analysis for {repo_url}")
                return cached_result
            
            self.performance_stats['cache_misses'] += 1
            
            # Clone repository
            logger.info(f"Cloning repository: {repo_url}")
            await self._clone_repository(repo_info)
            
            # Initialize LSP bridge
            logger.info(f"Initializing LSP analysis for: {repo_info.name}")
            lsp_bridge = await self._initialize_lsp_bridge(repo_info)
            
            # Perform comprehensive analysis
            logger.info(f"Performing comprehensive error analysis...")
            error_list = await self._analyze_repository_errors(
                lsp_bridge, 
                repo_info,
                severity_filter
            )
            
            # Create analysis result
            analysis_duration = time.time() - start_time
            error_list.analysis_duration = analysis_duration
            
            result = AnalysisResult(
                repository=repo_info,
                error_list=error_list,
                analysis_metadata={
                    'analysis_time': analysis_duration,
                    'lsp_enabled': lsp_bridge.is_initialized,
                    'runtime_collection_enabled': self.enable_runtime_collection,
                    'files_analyzed': len(error_list.files_analyzed),
                    'branch': branch,
                    'clone_depth': clone_depth
                }
            )
            
            # Cache result
            self.analysis_cache[cache_key] = result
            self.repositories[cache_key] = repo_info
            self.lsp_bridges[cache_key] = lsp_bridge
            
            # Update performance stats
            self.performance_stats['repositories_analyzed'] += 1
            self.performance_stats['total_analysis_time'] += analysis_duration
            self.performance_stats['average_analysis_time'] = (
                self.performance_stats['total_analysis_time'] / 
                self.performance_stats['repositories_analyzed']
            )
            
            logger.info(f"Analysis completed in {analysis_duration:.2f}s: "
                       f"{error_list.total_count} total errors found")
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing repository {repo_url}: {e}")
            # Return empty result with error information
            error_list = ComprehensiveErrorList()
            error_list.analysis_duration = time.time() - start_time
            
            return AnalysisResult(
                repository=RepositoryInfo.from_url(repo_url, ""),
                error_list=error_list,
                analysis_metadata={
                    'error': str(e),
                    'analysis_time': time.time() - start_time
                }
            )
    
    async def _clone_repository(self, repo_info: RepositoryInfo):
        """Clone a GitHub repository."""
        try:
            cmd = ["git", "clone"]
            
            if repo_info.clone_depth:
                cmd.extend(["--depth", str(repo_info.clone_depth)])
            
            if repo_info.branch != "main":
                cmd.extend(["--branch", repo_info.branch])
            
            cmd.extend([repo_info.url, repo_info.local_path])
            
            # Run git clone
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise RuntimeError(f"Git clone failed: {stderr.decode()}")
            
            logger.info(f"Successfully cloned {repo_info.url} to {repo_info.local_path}")
            
        except Exception as e:
            logger.error(f"Error cloning repository: {e}")
            raise
    
    async def _initialize_lsp_bridge(self, repo_info: RepositoryInfo) -> SerenaLSPBridge:
        """Initialize LSP bridge for repository analysis."""
        try:
            lsp_bridge = SerenaLSPBridge(
                repo_info.local_path,
                enable_runtime_collection=self.enable_runtime_collection
            )
            
            # Wait a moment for initialization
            await asyncio.sleep(1.0)
            
            return lsp_bridge
            
        except Exception as e:
            logger.error(f"Error initializing LSP bridge: {e}")
            # Return a minimal bridge for basic functionality
            return SerenaLSPBridge(repo_info.local_path, enable_runtime_collection=False)
    
    async def _analyze_repository_errors(
        self,
        lsp_bridge: SerenaLSPBridge,
        repo_info: RepositoryInfo,
        severity_filter: Optional[List[str]] = None
    ) -> ComprehensiveErrorList:
        """Perform comprehensive error analysis on repository."""
        try:
            # Get all diagnostics from LSP bridge
            all_errors = lsp_bridge.get_diagnostics(include_runtime=True)
            
            # Convert to CodeError format
            code_errors = []
            for error in all_errors:
                code_error = self._convert_error_info_to_code_error(error)
                
                # Apply severity filter
                if severity_filter and code_error.severity not in severity_filter:
                    continue
                
                code_errors.append(code_error)
            
            # Create comprehensive error list
            error_list = ComprehensiveErrorList()
            error_list.add_errors(code_errors)
            
            return error_list
            
        except Exception as e:
            logger.error(f"Error analyzing repository errors: {e}")
            return ComprehensiveErrorList()
    
    def _convert_error_info_to_code_error(self, error_info: ErrorInfo) -> CodeError:
        """Convert ErrorInfo to CodeError format."""
        # Create location
        location = ErrorLocation(
            file_path=error_info.file_path,
            line=error_info.line,
            column=error_info.character,
            end_line=error_info.end_line,
            end_column=error_info.end_character
        )
        
        # Create CodeError
        code_error = CodeError(
            id=f"{error_info.file_path}_{error_info.line}_{error_info.character}",
            message=error_info.message,
            severity=error_info.severity,
            category=ErrorCategory.UNKNOWN,  # Default category
            location=location,
            code=error_info.code,
            source=error_info.source or "lsp",
            suggestions=error_info.fix_suggestions.copy() if error_info.fix_suggestions else [],
            context=error_info.code_context if error_info.code_context else {}
        )
        
        return code_error
    
    async def shutdown(self):
        """Shutdown the analyzer and clean up resources."""
        try:
            # Shutdown all LSP bridges
            for lsp_bridge in self.lsp_bridges.values():
                lsp_bridge.shutdown()
            
            # Clear all caches
            self.analysis_cache.clear()
            self.repositories.clear()
            self.lsp_bridges.clear()
            
            logger.info("GitHub Repository Analyzer shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


# Convenience functions
async def analyze_github_repository(
    repo_url: str,
    branch: str = "main",
    severity_filter: Optional[List[str]] = None,
    work_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to analyze a GitHub repository and get errors by severity.
    """
    analyzer = GitHubRepositoryAnalyzer(work_dir=work_dir)
    
    try:
        # Analyze repository
        result = await analyzer.analyze_repository_by_url(
            repo_url=repo_url,
            branch=branch,
            severity_filter=severity_filter
        )
        
        # Format results
        errors_by_severity = result.get_errors_by_severity()
        summary_by_severity = result.get_summary_by_severity()
        
        return {
            'repository': {
                'url': result.repository.url,
                'name': result.repository.name,
                'owner': result.repository.owner,
                'branch': result.repository.branch
            },
            'analysis': {
                'total_errors': result.error_list.total_count,
                'critical_errors': result.error_list.critical_count,
                'warnings': result.error_list.warning_count,
                'info_hints': result.error_list.info_count,
                'files_analyzed': len(result.error_list.files_analyzed),
                'analysis_duration': result.error_list.analysis_duration
            },
            'errors_by_severity': {
                severity: [error.to_dict() for error in errors]
                for severity, errors in errors_by_severity.items()
            },
            'summary_by_severity': summary_by_severity,
            'metadata': result.analysis_metadata
        }
        
    finally:
        await analyzer.shutdown()


async def get_repository_error_summary(
    repo_url: str,
    branch: str = "main",
    work_dir: Optional[str] = None
) -> Dict[str, Any]:
    """Get a quick error summary for a GitHub repository."""
    result = await analyze_github_repository(repo_url, branch, work_dir=work_dir)
    
    return {
        'repository': result['repository'],
        'summary': result['analysis'],
        'severity_breakdown': {
            severity: summary['count']
            for severity, summary in result['summary_by_severity'].items()
        },
        'category_breakdown': result['summary_by_severity']['critical']['categories'],
        'most_problematic_files': result['summary_by_severity']['critical']['top_files']
    }


async def analyze_multiple_repositories(
    repo_urls: List[str],
    branch: str = "main",
    max_concurrent: int = 3,
    work_dir: Optional[str] = None
) -> Dict[str, Dict[str, Any]]:
    """Analyze multiple GitHub repositories concurrently."""
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def analyze_single_repo(url: str) -> tuple[str, Dict[str, Any]]:
        async with semaphore:
            try:
                result = await analyze_github_repository(url, branch, work_dir=work_dir)
                return url, result
            except Exception as e:
                logger.error(f"Error analyzing {url}: {e}")
                return url, {'error': str(e)}
    
    # Run analyses concurrently
    tasks = [analyze_single_repo(url) for url in repo_urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Format results
    analysis_results = {}
    for result in results:
        if isinstance(result, Exception):
            logger.error(f"Analysis failed: {result}")
            continue
        
        url, analysis = result
        analysis_results[url] = analysis
    
    return analysis_results


__all__ = [
    # Re-export all bridge classes
    "ErrorType",
    "RuntimeContext",
    "ErrorInfo", 
    "SerenaLSPBridge",
    "TransactionAwareLSPManager",
    "EnhancedSerenaIntegration",
    "get_lsp_manager",
    "shutdown_all_lsp_managers",
    "create_serena_lsp_bridge",
    "create_enhanced_serena_integration",
    
    # Analysis classes
    "ErrorSeverity",
    "ErrorCategory",
    "ErrorLocation",
    "CodeError",
    "ComprehensiveErrorList",
    "RepositoryInfo",
    "AnalysisResult",
    "GitHubRepositoryAnalyzer",
    
    # Convenience functions
    "analyze_github_repository",
    "get_repository_error_summary",
    "analyze_multiple_repositories",
]

