"""
Analysis Coordinator for Codegen-on-OSS

This module provides a coordinator for the analysis pipeline, which orchestrates
the execution of different analyzers and collectors to analyze code repositories,
commits, symbols, and features.
"""

import logging
import asyncio
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Set, Tuple

from sqlalchemy.orm import Session

from codegen import Codebase
from codegen_on_oss.database import (
    get_db_session, RepositoryRepository, CommitRepository,
    FileRepository, SymbolRepository, SnapshotRepository,
    AnalysisResultRepository, MetricRepository, IssueRepository,
    Repository as DbRepository, Commit as DbCommit, 
    AnalysisResult as DbAnalysisResult
)

logger = logging.getLogger(__name__)

class AnalysisContext:
    """
    Context for an analysis run, containing state and results.
    
    This class is used to pass state and results between different analyzers
    in the analysis pipeline.
    """
    
    def __init__(
        self, 
        repo_url: str, 
        branch: Optional[str] = None,
        commit_sha: Optional[str] = None,
        codebase: Optional[Codebase] = None
    ):
        """
        Initialize an analysis context.
        
        Args:
            repo_url: The repository URL.
            branch: The branch to analyze.
            commit_sha: The commit SHA to analyze.
            codebase: The codebase object.
        """
        self.repo_url = repo_url
        self.branch = branch
        self.commit_sha = commit_sha
        self.codebase = codebase
        
        # Analysis state
        self.repository_id: Optional[int] = None
        self.commit_id: Optional[int] = None
        self.analysis_result_id: Optional[int] = None
        self.start_time = time.time()
        
        # Analysis results
        self.results: Dict[str, Any] = {}
        self.metrics: List[Dict[str, Any]] = []
        self.issues: List[Dict[str, Any]] = []
        self.symbols: List[Dict[str, Any]] = []
        self.files: List[Dict[str, Any]] = []
        self.dependencies: List[Tuple[str, str]] = []
    
    def add_result(self, key: str, value: Any):
        """Add a result to the context."""
        self.results[key] = value
    
    def add_metric(self, name: str, value: float, file_path: Optional[str] = None, 
                  symbol_name: Optional[str] = None, threshold: Optional[float] = None):
        """Add a metric to the context."""
        self.metrics.append({
            'name': name,
            'value': value,
            'file_path': file_path,
            'symbol_name': symbol_name,
            'threshold': threshold
        })
    
    def add_issue(self, type: str, severity: int, message: str, 
                 file_path: Optional[str] = None, symbol_name: Optional[str] = None,
                 line_start: Optional[int] = None, line_end: Optional[int] = None,
                 remediation: Optional[Dict[str, Any]] = None):
        """Add an issue to the context."""
        self.issues.append({
            'type': type,
            'severity': severity,
            'message': message,
            'file_path': file_path,
            'symbol_name': symbol_name,
            'line_start': line_start,
            'line_end': line_end,
            'remediation': remediation or {}
        })
    
    def add_symbol(self, name: str, qualified_name: str, type: str, 
                  file_path: str, line_start: Optional[int] = None, 
                  line_end: Optional[int] = None, content_hash: Optional[str] = None):
        """Add a symbol to the context."""
        self.symbols.append({
            'name': name,
            'qualified_name': qualified_name,
            'type': type,
            'file_path': file_path,
            'line_start': line_start,
            'line_end': line_end,
            'content_hash': content_hash
        })
    
    def add_file(self, path: str, language: Optional[str] = None, 
                content_hash: Optional[str] = None, loc: Optional[int] = None):
        """Add a file to the context."""
        self.files.append({
            'path': path,
            'language': language,
            'content_hash': content_hash,
            'loc': loc
        })
    
    def add_dependency(self, source_symbol: str, target_symbol: str):
        """Add a dependency between symbols to the context."""
        self.dependencies.append((source_symbol, target_symbol))
    
    @property
    def elapsed_time(self) -> float:
        """Get the elapsed time since the analysis started."""
        return time.time() - self.start_time


class AnalysisCoordinator:
    """
    Coordinator for the analysis pipeline.
    
    This class orchestrates the execution of different analyzers and collectors
    to analyze code repositories, commits, symbols, and features.
    """
    
    def __init__(self):
        """Initialize the analysis coordinator."""
        # Repositories
        self.repo_repo = RepositoryRepository()
        self.commit_repo = CommitRepository()
        self.file_repo = FileRepository()
        self.symbol_repo = SymbolRepository()
        self.snapshot_repo = SnapshotRepository()
        self.analysis_result_repo = AnalysisResultRepository()
        self.metric_repo = MetricRepository()
        self.issue_repo = IssueRepository()
        
        # Analyzers will be initialized in the analyze method
        self.repo_analyzer = None
        self.commit_analyzer = None
        self.symbol_analyzer = None
        self.feature_analyzer = None
        self.metrics_collector = None
        self.issue_detector = None
        self.snapshot_generator = None
        self.dependency_analyzer = None
    
    async def analyze_repository(
        self, 
        repo_url: str, 
        branch: Optional[str] = None,
        commit_sha: Optional[str] = None,
        codebase: Optional[Codebase] = None
    ) -> Dict[str, Any]:
        """
        Analyze a repository.
        
        Args:
            repo_url: The repository URL.
            branch: The branch to analyze.
            commit_sha: The commit SHA to analyze.
            codebase: The codebase object.
            
        Returns:
            The analysis results.
        """
        # Create analysis context
        context = AnalysisContext(repo_url, branch, commit_sha, codebase)
        
        # Initialize analyzers with dynamic imports to avoid circular imports
        from codegen_on_oss.analysis.repository_analyzer import RepositoryAnalyzer
        from codegen_on_oss.analysis.commit_analyzer import CommitAnalyzer
        from codegen_on_oss.analysis.symbol_analyzer import SymbolAnalyzer
        from codegen_on_oss.analysis.feature_analyzer import FeatureAnalyzer
        from codegen_on_oss.analysis.metrics_collector import MetricsCollector
        from codegen_on_oss.analysis.issue_detector import IssueDetector
        from codegen_on_oss.analysis.snapshot_generator import SnapshotGenerator
        from codegen_on_oss.analysis.dependency_analyzer import DependencyAnalyzer
        
        self.repo_analyzer = RepositoryAnalyzer()
        self.commit_analyzer = CommitAnalyzer()
        self.symbol_analyzer = SymbolAnalyzer()
        self.feature_analyzer = FeatureAnalyzer()
        self.metrics_collector = MetricsCollector()
        self.issue_detector = IssueDetector()
        self.snapshot_generator = SnapshotGenerator()
        self.dependency_analyzer = DependencyAnalyzer()
        
        # Create analysis result in database
        with get_db_session() as session:
            # Create or get repository
            repo_name = repo_url.split('/')[-1]
            db_repo = self.repo_repo.get_by_name_and_url(session, repo_name, repo_url)
            if not db_repo:
                db_repo = self.repo_repo.create(
                    session,
                    name=repo_name,
                    url=repo_url,
                    default_branch=branch or "main"
                )
            context.repository_id = db_repo.id
            
            # Create analysis result
            analysis_result = self.analysis_result_repo.create(
                session,
                repository_id=db_repo.id,
                analysis_type="repository",
                status="in_progress"
            )
            context.analysis_result_id = analysis_result.id
            
            # Commit the transaction
            session.commit()
        
        try:
            # Run pipeline stages
            logger.info(f"Starting analysis of repository {repo_url}")
            
            # Repository analysis
            await self.repo_analyzer.analyze(context)
            logger.info(f"Repository analysis completed in {context.elapsed_time:.2f}s")
            
            # Commit analysis
            await self.commit_analyzer.analyze(context)
            logger.info(f"Commit analysis completed in {context.elapsed_time:.2f}s")
            
            # Symbol analysis
            await self.symbol_analyzer.analyze(context)
            logger.info(f"Symbol analysis completed in {context.elapsed_time:.2f}s")
            
            # Feature analysis
            await self.feature_analyzer.analyze(context)
            logger.info(f"Feature analysis completed in {context.elapsed_time:.2f}s")
            
            # Run analysis components
            await self.metrics_collector.collect(context)
            logger.info(f"Metrics collection completed in {context.elapsed_time:.2f}s")
            
            await self.issue_detector.detect(context)
            logger.info(f"Issue detection completed in {context.elapsed_time:.2f}s")
            
            await self.dependency_analyzer.analyze(context)
            logger.info(f"Dependency analysis completed in {context.elapsed_time:.2f}s")
            
            # Generate snapshot
            snapshot = await self.snapshot_generator.generate(context)
            logger.info(f"Snapshot generation completed in {context.elapsed_time:.2f}s")
            
            # Store results
            await self._store_results(context)
            logger.info(f"Results stored in {context.elapsed_time:.2f}s")
            
            # Mark analysis as completed
            with get_db_session() as session:
                self.analysis_result_repo.mark_completed(session, context.analysis_result_id)
                session.commit()
            
            logger.info(f"Analysis completed in {context.elapsed_time:.2f}s")
            
            return context.results
        
        except Exception as e:
            logger.error(f"Analysis failed: {e}", exc_info=True)
            
            # Mark analysis as failed
            with get_db_session() as session:
                self.analysis_result_repo.update(
                    session, 
                    context.analysis_result_id,
                    status="failure",
                    completed_at=datetime.utcnow(),
                    data={"error": str(e)}
                )
                session.commit()
            
            raise
    
    async def _store_results(self, context: AnalysisContext):
        """
        Store analysis results in the database.
        
        Args:
            context: The analysis context.
        """
        with get_db_session() as session:
            # Update analysis result with data
            self.analysis_result_repo.update(
                session,
                context.analysis_result_id,
                data=context.results
            )
            
            # Store metrics
            for metric_data in context.metrics:
                # Find file and symbol IDs
                file_id = None
                symbol_id = None
                
                if metric_data.get('file_path'):
                    file = self._find_file_by_path(session, context.commit_id, metric_data['file_path'])
                    if file:
                        file_id = file.id
                
                if metric_data.get('symbol_name') and file_id:
                    symbol = self._find_symbol_by_name(session, file_id, metric_data['symbol_name'])
                    if symbol:
                        symbol_id = symbol.id
                
                # Create metric
                self.metric_repo.create(
                    session,
                    analysis_result_id=context.analysis_result_id,
                    file_id=file_id,
                    symbol_id=symbol_id,
                    name=metric_data['name'],
                    value=metric_data['value'],
                    threshold=metric_data.get('threshold')
                )
            
            # Store issues
            for issue_data in context.issues:
                # Find file and symbol IDs
                file_id = None
                symbol_id = None
                
                if issue_data.get('file_path'):
                    file = self._find_file_by_path(session, context.commit_id, issue_data['file_path'])
                    if file:
                        file_id = file.id
                
                if issue_data.get('symbol_name') and file_id:
                    symbol = self._find_symbol_by_name(session, file_id, issue_data['symbol_name'])
                    if symbol:
                        symbol_id = symbol.id
                
                # Create issue
                self.issue_repo.create(
                    session,
                    analysis_result_id=context.analysis_result_id,
                    file_id=file_id,
                    symbol_id=symbol_id,
                    type=issue_data['type'],
                    severity=issue_data['severity'],
                    message=issue_data['message'],
                    line_start=issue_data.get('line_start'),
                    line_end=issue_data.get('line_end'),
                    remediation=issue_data.get('remediation', {})
                )
            
            # Commit the transaction
            session.commit()
    
    def _find_file_by_path(self, session: Session, commit_id: int, path: str):
        """Find a file by path in a commit."""
        return self.file_repo.get_by_path(session, commit_id, path)
    
    def _find_symbol_by_name(self, session: Session, file_id: int, name: str):
        """Find a symbol by name in a file."""
        return session.query(self.symbol_repo.model).filter(
            self.symbol_repo.model.file_id == file_id,
            self.symbol_repo.model.name == name
        ).first()

