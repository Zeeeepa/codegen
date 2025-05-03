"""
Analysis Orchestration Layer for Codegen-on-OSS

This module provides a central orchestration layer for managing and coordinating
various code analysis tasks.
"""

import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Any, Union, Type, TypeVar

from codegen import Codebase

from codegen_on_oss.database.manager import DatabaseManager
from codegen_on_oss.database.models import (
    AnalysisResult as DBAnalysisResult,
    CodeMetrics as DBCodeMetrics,
    SymbolAnalysis as DBSymbolAnalysis,
    DependencyGraph as DBDependencyGraph
)
from codegen_on_oss.snapshot.enhanced_snapshot import EnhancedSnapshot

logger = logging.getLogger(__name__)

# Type variable for analyzer classes
T = TypeVar('T', bound='BaseAnalyzer')


class BaseAnalyzer:
    """
    Base class for all code analyzers.
    
    This class defines the interface that all analyzers must implement.
    """
    
    def __init__(self, context: Optional[Dict[str, Any]] = None):
        """
        Initialize the analyzer.
        
        Args:
            context: Optional context data for the analyzer
        """
        self.context = context or {}
    
    def analyze(self, snapshot: EnhancedSnapshot) -> Dict[str, Any]:
        """
        Run analysis on a snapshot and return results.
        
        Args:
            snapshot: The snapshot to analyze
            
        Returns:
            A dictionary containing analysis results
        """
        raise NotImplementedError("Subclasses must implement analyze()")
    
    def get_dependencies(self) -> List[Type['BaseAnalyzer']]:
        """
        Return analyzers this analyzer depends on.
        
        Returns:
            A list of analyzer classes that this analyzer depends on
        """
        return []
    
    def supports_incremental(self) -> bool:
        """
        Whether this analyzer supports incremental analysis.
        
        Returns:
            True if incremental analysis is supported, False otherwise
        """
        return False
    
    @classmethod
    def get_analyzer_type(cls) -> str:
        """
        Get the type identifier for this analyzer.
        
        Returns:
            A string identifier for the analyzer type
        """
        return cls.__name__


class AnalysisRegistry:
    """
    Registry for analyzer classes.
    
    This class manages the registration and discovery of analyzer classes.
    """
    
    def __init__(self):
        """Initialize the registry."""
        self.analyzers: Dict[str, Type[BaseAnalyzer]] = {}
        self.dependencies: Dict[str, Set[str]] = {}
    
    def register(self, analyzer_class: Type[BaseAnalyzer]) -> None:
        """
        Register an analyzer class.
        
        Args:
            analyzer_class: The analyzer class to register
        """
        analyzer_type = analyzer_class.get_analyzer_type()
        self.analyzers[analyzer_type] = analyzer_class
        
        # Register dependencies
        self.dependencies[analyzer_type] = set()
        for dep_class in analyzer_class().get_dependencies():
            dep_type = dep_class.get_analyzer_type()
            self.dependencies[analyzer_type].add(dep_type)
            
            # Register dependency if not already registered
            if dep_type not in self.analyzers:
                self.register(dep_class)
    
    def get_analyzer(self, analyzer_type: str) -> Type[BaseAnalyzer]:
        """
        Get an analyzer class by its type.
        
        Args:
            analyzer_type: The type identifier of the analyzer
            
        Returns:
            The analyzer class
            
        Raises:
            ValueError: If the analyzer type is not registered
        """
        if analyzer_type not in self.analyzers:
            raise ValueError(f"Analyzer type {analyzer_type} not registered")
        return self.analyzers[analyzer_type]
    
    def get_dependencies(self, analyzer_type: str) -> Set[str]:
        """
        Get the dependencies of an analyzer.
        
        Args:
            analyzer_type: The type identifier of the analyzer
            
        Returns:
            A set of analyzer type identifiers that the analyzer depends on
            
        Raises:
            ValueError: If the analyzer type is not registered
        """
        if analyzer_type not in self.dependencies:
            raise ValueError(f"Analyzer type {analyzer_type} not registered")
        return self.dependencies[analyzer_type]
    
    def get_all_analyzers(self) -> Dict[str, Type[BaseAnalyzer]]:
        """
        Get all registered analyzers.
        
        Returns:
            A dictionary mapping analyzer types to analyzer classes
        """
        return self.analyzers.copy()


class AnalysisScheduler:
    """
    Scheduler for analysis tasks.
    
    This class manages the scheduling and execution of analysis tasks.
    """
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """
        Initialize the scheduler.
        
        Args:
            db_manager: Optional DatabaseManager instance
        """
        self.db_manager = db_manager or DatabaseManager()
        self.running_analyses: Dict[str, Dict[str, Any]] = {}
    
    def schedule(
        self, 
        analysis_id: str, 
        analyzer: BaseAnalyzer, 
        snapshot: EnhancedSnapshot, 
        params: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Schedule an analysis task.
        
        Args:
            analysis_id: ID of the analysis
            analyzer: The analyzer to use
            snapshot: The snapshot to analyze
            params: Optional parameters for the analysis
        """
        # Add to running analyses
        self.running_analyses[analysis_id] = {
            "analyzer": analyzer,
            "snapshot": snapshot,
            "params": params or {},
            "start_time": datetime.now()
        }
        
        # Update analysis status in database
        with self.db_manager.get_session() as session:
            analysis = session.query(DBAnalysisResult).filter(DBAnalysisResult.id == analysis_id).first()
            if analysis:
                analysis.status = "running"
                session.commit()
        
        # Run the analysis
        try:
            result = analyzer.analyze(snapshot)
            
            # Update analysis in database
            with self.db_manager.get_session() as session:
                analysis = session.query(DBAnalysisResult).filter(DBAnalysisResult.id == analysis_id).first()
                if analysis:
                    analysis.status = "completed"
                    analysis.completed_at = datetime.now()
                    analysis.result_data = result
                    session.commit()
            
            # Store detailed results
            self._store_analysis_results(analysis_id, result)
            
        except Exception as e:
            logger.exception(f"Error running analysis {analysis_id}: {e}")
            
            # Update analysis status in database
            with self.db_manager.get_session() as session:
                analysis = session.query(DBAnalysisResult).filter(DBAnalysisResult.id == analysis_id).first()
                if analysis:
                    analysis.status = "failed"
                    analysis.completed_at = datetime.now()
                    analysis.result_data = {"error": str(e)}
                    session.commit()
        
        # Remove from running analyses
        if analysis_id in self.running_analyses:
            del self.running_analyses[analysis_id]
    
    def _store_analysis_results(self, analysis_id: str, result: Dict[str, Any]) -> None:
        """
        Store detailed analysis results in the database.
        
        Args:
            analysis_id: ID of the analysis
            result: Analysis results
        """
        # Store code metrics if available
        if "metrics" in result:
            metrics = result["metrics"]
            db_metrics = DBCodeMetrics(
                analysis_id=analysis_id,
                complexity=metrics.get("complexity", 0.0),
                maintainability=metrics.get("maintainability", 0.0),
                halstead_metrics=metrics.get("halstead", {}),
                doi_metrics=metrics.get("doi", {}),
                lines_of_code=metrics.get("loc", 0)
            )
            self.db_manager.create(db_metrics)
        
        # Store symbol analyses if available
        if "symbols" in result:
            for symbol in result["symbols"]:
                db_symbol = DBSymbolAnalysis(
                    analysis_id=analysis_id,
                    symbol_type=symbol.get("type", "unknown"),
                    symbol_name=symbol.get("name", ""),
                    file_path=symbol.get("file_path", ""),
                    line_number=symbol.get("line_number", 0),
                    complexity=symbol.get("complexity", 0.0),
                    dependencies=symbol.get("dependencies", [])
                )
                self.db_manager.create(db_symbol)
        
        # Store dependency graph if available
        if "dependency_graph" in result:
            graph = result["dependency_graph"]
            db_graph = DBDependencyGraph(
                analysis_id=analysis_id,
                graph_data=graph.get("data", {}),
                node_count=graph.get("node_count", 0),
                edge_count=graph.get("edge_count", 0),
                clusters=graph.get("clusters", []),
                central_nodes=graph.get("central_nodes", [])
            )
            self.db_manager.create(db_graph)
    
    def get_analysis_status(self, analysis_id: str) -> Dict[str, Any]:
        """
        Get the status of an analysis.
        
        Args:
            analysis_id: ID of the analysis
            
        Returns:
            A dictionary containing status information
        """
        # Check if analysis is running
        if analysis_id in self.running_analyses:
            running_info = self.running_analyses[analysis_id]
            return {
                "status": "running",
                "start_time": running_info["start_time"].isoformat(),
                "elapsed_time": (datetime.now() - running_info["start_time"]).total_seconds()
            }
        
        # Check database
        analysis = self.db_manager.get_by_id(DBAnalysisResult, analysis_id)
        if analysis:
            status_info = {
                "status": analysis.status,
                "created_at": analysis.created_at.isoformat()
            }
            
            if analysis.completed_at:
                status_info["completed_at"] = analysis.completed_at.isoformat()
                status_info["elapsed_time"] = (analysis.completed_at - analysis.created_at).total_seconds()
            
            return status_info
        
        return {"status": "not_found"}


class AnalysisOrchestrator:
    """
    Coordinates multiple analyzers and manages analysis dependencies.
    
    This class serves as the main entry point for all analysis operations.
    """
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """
        Initialize the orchestrator.
        
        Args:
            db_manager: Optional DatabaseManager instance
        """
        self.db_manager = db_manager or DatabaseManager()
        self.registry = AnalysisRegistry()
        self.scheduler = AnalysisScheduler(db_manager)
        
        # Register built-in analyzers
        self._register_built_in_analyzers()
    
    def _register_built_in_analyzers(self) -> None:
        """Register built-in analyzers."""
        # Import and register built-in analyzers
        from codegen_on_oss.analysis.code_analyzer import CodeComplexityAnalyzer
        from codegen_on_oss.analysis.diff_analyzer import DiffAnalyzer
        from codegen_on_oss.analysis.feature_analyzer import FeatureAnalyzer
        
        self.registry.register(CodeComplexityAnalyzer)
        self.registry.register(DiffAnalyzer)
        self.registry.register(FeatureAnalyzer)
    
    def register_analyzer(self, analyzer_class: Type[BaseAnalyzer]) -> None:
        """
        Register a custom analyzer.
        
        Args:
            analyzer_class: The analyzer class to register
        """
        self.registry.register(analyzer_class)
    
    def run_analysis(
        self, 
        analyzer_type: str, 
        snapshot_id: str, 
        params: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Run a specific analyzer on a snapshot.
        
        Args:
            analyzer_type: The type identifier of the analyzer
            snapshot_id: ID of the snapshot to analyze
            params: Optional parameters for the analysis
            
        Returns:
            The ID of the created analysis
            
        Raises:
            ValueError: If the analyzer type is not registered or the snapshot is not found
        """
        # Get analyzer from registry
        analyzer_class = self.registry.get_analyzer(analyzer_type)
        analyzer = analyzer_class(context=params)
        
        # Get snapshot
        from codegen_on_oss.snapshot.enhanced_snapshot import EnhancedSnapshotManager
        snapshot_manager = EnhancedSnapshotManager(db_manager=self.db_manager)
        snapshot = snapshot_manager.get_snapshot(snapshot_id)
        
        if snapshot is None:
            raise ValueError(f"Snapshot with ID {snapshot_id} not found")
        
        # Ensure dependencies are satisfied
        self._ensure_dependencies(analyzer_type, snapshot_id, params)
        
        # Create analysis record
        analysis = DBAnalysisResult(
            snapshot_id=snapshot_id,
            analyzer_type=analyzer_type,
            status="pending",
            result_data=None
        )
        self.db_manager.create(analysis)
        
        # Schedule analysis
        self.scheduler.schedule(analysis.id, analyzer, snapshot, params)
        
        return analysis.id
    
    def _ensure_dependencies(
        self, 
        analyzer_type: str, 
        snapshot_id: str, 
        params: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Ensure all dependencies of an analyzer are satisfied.
        
        Args:
            analyzer_type: The type identifier of the analyzer
            snapshot_id: ID of the snapshot to analyze
            params: Optional parameters for the analysis
        """
        dependencies = self.registry.get_dependencies(analyzer_type)
        
        for dep_type in dependencies:
            # Check if dependency analysis exists and is completed
            existing_analysis = self._find_analysis(dep_type, snapshot_id)
            
            if existing_analysis is None or existing_analysis.status != "completed":
                # Run dependency analysis
                self.run_analysis(dep_type, snapshot_id, params)
                
                # Wait for dependency to complete
                self._wait_for_analysis(dep_type, snapshot_id)
    
    def _find_analysis(self, analyzer_type: str, snapshot_id: str) -> Optional[DBAnalysisResult]:
        """
        Find an existing analysis for a given analyzer and snapshot.
        
        Args:
            analyzer_type: The type identifier of the analyzer
            snapshot_id: ID of the snapshot
            
        Returns:
            The analysis if found, None otherwise
        """
        analyses = self.db_manager.get_all(
            DBAnalysisResult, 
            analyzer_type=analyzer_type, 
            snapshot_id=snapshot_id
        )
        
        if analyses:
            return analyses[0]
        return None
    
    def _wait_for_analysis(self, analyzer_type: str, snapshot_id: str, timeout: int = 300) -> None:
        """
        Wait for an analysis to complete.
        
        Args:
            analyzer_type: The type identifier of the analyzer
            snapshot_id: ID of the snapshot
            timeout: Maximum time to wait in seconds
            
        Raises:
            TimeoutError: If the analysis does not complete within the timeout
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            analysis = self._find_analysis(analyzer_type, snapshot_id)
            
            if analysis and analysis.status in ["completed", "failed"]:
                if analysis.status == "failed":
                    logger.warning(f"Dependency analysis {analyzer_type} failed for snapshot {snapshot_id}")
                return
            
            # Wait a bit before checking again
            time.sleep(1)
        
        raise TimeoutError(f"Timed out waiting for analysis {analyzer_type} to complete for snapshot {snapshot_id}")
    
    def get_analysis_result(self, analysis_id: str) -> Dict[str, Any]:
        """
        Get the result of an analysis.
        
        Args:
            analysis_id: ID of the analysis
            
        Returns:
            A dictionary containing the analysis result
            
        Raises:
            ValueError: If the analysis is not found
        """
        analysis = self.db_manager.get_by_id(DBAnalysisResult, analysis_id)
        
        if analysis is None:
            raise ValueError(f"Analysis with ID {analysis_id} not found")
        
        result = {
            "id": analysis.id,
            "snapshot_id": analysis.snapshot_id,
            "analyzer_type": analysis.analyzer_type,
            "status": analysis.status,
            "created_at": analysis.created_at.isoformat(),
            "result_data": analysis.result_data or {}
        }
        
        if analysis.completed_at:
            result["completed_at"] = analysis.completed_at.isoformat()
        
        # Add metrics if available
        metrics = self.db_manager.get_all(DBCodeMetrics, analysis_id=analysis_id)
        if metrics:
            result["metrics"] = {
                "complexity": metrics[0].complexity,
                "maintainability": metrics[0].maintainability,
                "halstead": metrics[0].halstead_metrics,
                "doi": metrics[0].doi_metrics,
                "loc": metrics[0].lines_of_code
            }
        
        # Add symbol analyses if available
        symbols = self.db_manager.get_all(DBSymbolAnalysis, analysis_id=analysis_id)
        if symbols:
            result["symbols"] = [
                {
                    "type": s.symbol_type,
                    "name": s.symbol_name,
                    "file_path": s.file_path,
                    "line_number": s.line_number,
                    "complexity": s.complexity,
                    "dependencies": s.dependencies
                }
                for s in symbols
            ]
        
        # Add dependency graph if available
        graphs = self.db_manager.get_all(DBDependencyGraph, analysis_id=analysis_id)
        if graphs:
            result["dependency_graph"] = {
                "data": graphs[0].graph_data,
                "node_count": graphs[0].node_count,
                "edge_count": graphs[0].edge_count,
                "clusters": graphs[0].clusters,
                "central_nodes": graphs[0].central_nodes
            }
        
        return result
    
    def list_analyses(self, snapshot_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all analyses, optionally filtered by snapshot ID.
        
        Args:
            snapshot_id: Optional snapshot ID to filter by
            
        Returns:
            A list of analysis metadata dictionaries
        """
        if snapshot_id:
            analyses = self.db_manager.get_all(DBAnalysisResult, snapshot_id=snapshot_id)
        else:
            analyses = self.db_manager.get_all(DBAnalysisResult)
        
        return [
            {
                "id": a.id,
                "snapshot_id": a.snapshot_id,
                "analyzer_type": a.analyzer_type,
                "status": a.status,
                "created_at": a.created_at.isoformat(),
                "completed_at": a.completed_at.isoformat() if a.completed_at else None
            }
            for a in analyses
        ]
    
    def delete_analysis(self, analysis_id: str) -> bool:
        """
        Delete an analysis and its associated data.
        
        Args:
            analysis_id: ID of the analysis to delete
            
        Returns:
            True if the analysis was deleted, False otherwise
        """
        # Delete associated data
        self.db_manager.get_all(DBCodeMetrics, analysis_id=analysis_id)
        self.db_manager.get_all(DBSymbolAnalysis, analysis_id=analysis_id)
        self.db_manager.get_all(DBDependencyGraph, analysis_id=analysis_id)
        
        # Delete analysis
        analysis = self.db_manager.get_by_id(DBAnalysisResult, analysis_id)
        if analysis:
            return self.db_manager.delete(analysis)
        return False

