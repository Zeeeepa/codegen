"""
RepoMaster client integration for intelligent code context detection.
"""

import asyncio
import json
import subprocess
import tempfile
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from ..models import CodeContext, GraphVisualization
from ..config import Config
from ..utils.logger import get_logger


@dataclass
class AnalysisResult:
    """Result from RepoMaster analysis."""
    file_path: str
    analysis_type: str
    content: str
    symbols: List[Dict[str, Any]]
    dependencies: List[str]
    complexity_metrics: Dict[str, Any]
    visualization_data: Optional[Dict[str, Any]] = None


class RepoMasterClient:
    """
    Client for integrating with RepoMaster for intelligent code context detection
    and graph-sitter analysis.
    """
    
    def __init__(self, config: Config):
        """Initialize the RepoMaster client."""
        self.config = config
        self.logger = get_logger(__name__)
        
        # Check if RepoMaster is available
        self.repomaster_available = self._check_repomaster_availability()
        
        # Cache for analysis results
        self.analysis_cache: Dict[str, AnalysisResult] = {}
        
        if self.repomaster_available:
            self.logger.info("RepoMaster client initialized successfully")
        else:
            self.logger.warning("RepoMaster not available - code analysis will be limited")
    
    def _check_repomaster_availability(self) -> bool:
        """Check if RepoMaster is available in the system."""
        try:
            # Try to import RepoMaster modules
            import sys
            import importlib.util
            
            # Check for RepoMaster in the system
            repomaster_spec = importlib.util.find_spec("repomaster")
            if repomaster_spec is None:
                # Try to find it in a relative path or common locations
                possible_paths = [
                    "../RepoMaster/src",
                    "../../RepoMaster/src",
                    "/opt/repomaster/src",
                    os.path.expanduser("~/RepoMaster/src")
                ]
                
                for path in possible_paths:
                    if os.path.exists(path):
                        sys.path.insert(0, path)
                        try:
                            import core.tree_code
                            return True
                        except ImportError:
                            continue
                
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking RepoMaster availability: {e}")
            return False
    
    async def analyze_file(self, project_id: str, file_path: str) -> Optional[CodeContext]:
        """
        Analyze a specific file using RepoMaster.
        
        Args:
            project_id: Project identifier
            file_path: Path to the file to analyze
            
        Returns:
            CodeContext with analysis results
        """
        try:
            if not self.repomaster_available:
                return await self._fallback_file_analysis(project_id, file_path)
            
            # Check cache first
            cache_key = f"{project_id}:{file_path}"
            if cache_key in self.analysis_cache:
                cached = self.analysis_cache[cache_key]
                return self._convert_to_code_context(cached, project_id)
            
            # Get project repository path
            repo_path = await self._get_project_repo_path(project_id)
            if not repo_path:
                return None
            
            # Perform RepoMaster analysis
            analysis_result = await self._run_repomaster_analysis(
                repo_path, file_path, "file"
            )
            
            if analysis_result:
                # Cache the result
                self.analysis_cache[cache_key] = analysis_result
                
                # Convert to CodeContext
                return self._convert_to_code_context(analysis_result, project_id)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error analyzing file {file_path}: {e}")
            return await self._fallback_file_analysis(project_id, file_path)
    
    async def analyze_symbol(self, project_id: str, symbol_name: str) -> Optional[CodeContext]:
        """
        Analyze a specific symbol (function, class, etc.) using RepoMaster.
        
        Args:
            project_id: Project identifier
            symbol_name: Name of the symbol to analyze
            
        Returns:
            CodeContext with symbol analysis
        """
        try:
            if not self.repomaster_available:
                return await self._fallback_symbol_analysis(project_id, symbol_name)
            
            # Check cache first
            cache_key = f"{project_id}:symbol:{symbol_name}"
            if cache_key in self.analysis_cache:
                cached = self.analysis_cache[cache_key]
                return self._convert_to_code_context(cached, project_id)
            
            # Get project repository path
            repo_path = await self._get_project_repo_path(project_id)
            if not repo_path:
                return None
            
            # Perform RepoMaster symbol analysis
            analysis_result = await self._run_repomaster_analysis(
                repo_path, symbol_name, "symbol"
            )
            
            if analysis_result:
                # Cache the result
                self.analysis_cache[cache_key] = analysis_result
                
                # Convert to CodeContext
                return self._convert_to_code_context(analysis_result, project_id)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error analyzing symbol {symbol_name}: {e}")
            return await self._fallback_symbol_analysis(project_id, symbol_name)
    
    async def get_project_overview(self, project_id: str) -> Optional[CodeContext]:
        """
        Get a high-level overview of the project structure.
        
        Args:
            project_id: Project identifier
            
        Returns:
            CodeContext with project overview
        """
        try:
            if not self.repomaster_available:
                return await self._fallback_project_overview(project_id)
            
            # Check cache first
            cache_key = f"{project_id}:overview"
            if cache_key in self.analysis_cache:
                cached = self.analysis_cache[cache_key]
                return self._convert_to_code_context(cached, project_id)
            
            # Get project repository path
            repo_path = await self._get_project_repo_path(project_id)
            if not repo_path:
                return None
            
            # Perform RepoMaster project analysis
            analysis_result = await self._run_repomaster_analysis(
                repo_path, "", "project"
            )
            
            if analysis_result:
                # Cache the result
                self.analysis_cache[cache_key] = analysis_result
                
                # Convert to CodeContext
                return self._convert_to_code_context(analysis_result, project_id)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting project overview: {e}")
            return await self._fallback_project_overview(project_id)
    
    async def create_visualization(self, project_id: str, visualization_type: str,
                                 target_symbol: Optional[str] = None) -> Optional[GraphVisualization]:
        """
        Create a graph visualization using RepoMaster's graph-sitter analysis.
        
        Args:
            project_id: Project identifier
            visualization_type: Type of visualization (blast_radius, call_trace, etc.)
            target_symbol: Optional target symbol for the visualization
            
        Returns:
            GraphVisualization with nodes and edges
        """
        try:
            if not self.repomaster_available:
                return await self._fallback_visualization(project_id, visualization_type)
            
            # Get project repository path
            repo_path = await self._get_project_repo_path(project_id)
            if not repo_path:
                return None
            
            # Run graph-sitter visualization
            viz_data = await self._run_graph_sitter_visualization(
                repo_path, visualization_type, target_symbol
            )
            
            if viz_data:
                return GraphVisualization(
                    project_id=project_id,
                    visualization_type=visualization_type,
                    nodes=viz_data.get("nodes", []),
                    edges=viz_data.get("edges", []),
                    metadata=viz_data.get("metadata", {})
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error creating visualization: {e}")
            return await self._fallback_visualization(project_id, visualization_type)
    
    async def _get_project_repo_path(self, project_id: str) -> Optional[str]:
        """Get the local repository path for a project."""
        try:
            # This would typically involve:
            # 1. Getting project info from Codegen API
            # 2. Cloning the repository if not already local
            # 3. Returning the local path
            
            # For now, we'll use a simple mapping or temporary clone
            # In a real implementation, this would be more sophisticated
            
            # Try to find existing clone or create temporary one
            temp_dir = tempfile.mkdtemp(prefix=f"repomaster_{project_id}_")
            
            # TODO: Implement actual repository cloning logic
            # This would involve getting the git URL from the project and cloning it
            
            return temp_dir
            
        except Exception as e:
            self.logger.error(f"Error getting repo path for project {project_id}: {e}")
            return None
    
    async def _run_repomaster_analysis(self, repo_path: str, target: str, 
                                     analysis_type: str) -> Optional[AnalysisResult]:
        """Run RepoMaster analysis on the repository."""
        try:
            # Import RepoMaster modules
            from core.tree_code import GlobalCodeTreeBuilder
            from core.code_utils import _get_code_abs
            
            # Create code tree builder
            builder = GlobalCodeTreeBuilder(repo_path)
            
            # Build the code tree
            await asyncio.to_thread(builder.build_tree)
            
            # Perform specific analysis based on type
            if analysis_type == "file":
                return await self._analyze_file_with_repomaster(builder, target)
            elif analysis_type == "symbol":
                return await self._analyze_symbol_with_repomaster(builder, target)
            elif analysis_type == "project":
                return await self._analyze_project_with_repomaster(builder)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error running RepoMaster analysis: {e}")
            return None
    
    async def _analyze_file_with_repomaster(self, builder, file_path: str) -> Optional[AnalysisResult]:
        """Analyze a specific file with RepoMaster."""
        try:
            # Get file analysis
            file_info = builder.get_file_details(file_path)
            
            # Extract relevant information
            symbols = file_info.get("functions", []) + file_info.get("classes", [])
            dependencies = [imp["name"] for imp in file_info.get("imports", [])]
            complexity_metrics = file_info.get("metrics", {})
            
            # Get code content
            full_path = os.path.join(builder.repo_path, file_path)
            content = ""
            if os.path.exists(full_path):
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            
            return AnalysisResult(
                file_path=file_path,
                analysis_type="file",
                content=content,
                symbols=symbols,
                dependencies=dependencies,
                complexity_metrics=complexity_metrics
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing file with RepoMaster: {e}")
            return None
    
    async def _analyze_symbol_with_repomaster(self, builder, symbol_name: str) -> Optional[AnalysisResult]:
        """Analyze a specific symbol with RepoMaster."""
        try:
            # Get symbol analysis
            symbol_info = builder.get_symbol_details(symbol_name)
            
            if symbol_info.get("error"):
                return None
            
            # Extract relevant information
            dependencies = [dep["name"] for dep in symbol_info.get("dependencies", [])]
            
            return AnalysisResult(
                file_path=symbol_info.get("filepath", ""),
                analysis_type="symbol",
                content=symbol_info.get("summary", ""),
                symbols=[{
                    "name": symbol_name,
                    "type": symbol_info.get("symbol_type", "unknown"),
                    "context": symbol_info.get("context", {})
                }],
                dependencies=dependencies,
                complexity_metrics={}
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing symbol with RepoMaster: {e}")
            return None
    
    async def _analyze_project_with_repomaster(self, builder) -> Optional[AnalysisResult]:
        """Analyze the entire project with RepoMaster."""
        try:
            # Get project overview
            overview = builder.get_codebase_overview()
            
            # Extract key information
            symbols = []
            dependencies = []
            
            # Get entry points and key components
            entry_points = overview.get("entrypoints", {})
            for ep_type, eps in entry_points.items():
                for ep in eps:
                    symbols.append({
                        "name": ep.get("name", ""),
                        "type": ep_type,
                        "file": ep.get("file", ""),
                        "score": ep.get("score", 0)
                    })
            
            return AnalysisResult(
                file_path="",
                analysis_type="project",
                content=overview.get("summary", ""),
                symbols=symbols,
                dependencies=dependencies,
                complexity_metrics=overview.get("complexity_overview", {})
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing project with RepoMaster: {e}")
            return None
    
    async def _run_graph_sitter_visualization(self, repo_path: str, viz_type: str,
                                            target_symbol: Optional[str]) -> Optional[Dict[str, Any]]:
        """Run graph-sitter visualization analysis."""
        try:
            # Import graph-sitter analyzer
            from core.tree_code import GlobalCodeTreeBuilder
            
            # Create analyzer
            builder = GlobalCodeTreeBuilder(repo_path)
            await asyncio.to_thread(builder.build_tree)
            
            # Create visualization based on type
            if viz_type == "blast_radius" and target_symbol:
                return await self._create_blast_radius_viz(builder, target_symbol)
            elif viz_type == "call_trace" and target_symbol:
                return await self._create_call_trace_viz(builder, target_symbol)
            elif viz_type == "dependency_trace":
                return await self._create_dependency_viz(builder, target_symbol)
            elif viz_type == "method_relationships" and target_symbol:
                return await self._create_method_relationships_viz(builder, target_symbol)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error creating graph-sitter visualization: {e}")
            return None
    
    async def _create_blast_radius_viz(self, builder, symbol_name: str) -> Dict[str, Any]:
        """Create blast radius visualization."""
        try:
            viz_data = builder.create_blast_radius_visualization(symbol_name)
            return viz_data
        except Exception as e:
            self.logger.error(f"Error creating blast radius visualization: {e}")
            return {"nodes": [], "edges": [], "metadata": {"error": str(e)}}
    
    async def _create_call_trace_viz(self, builder, function_name: str) -> Dict[str, Any]:
        """Create call trace visualization."""
        try:
            viz_data = builder.create_call_trace_visualization(function_name)
            return viz_data
        except Exception as e:
            self.logger.error(f"Error creating call trace visualization: {e}")
            return {"nodes": [], "edges": [], "metadata": {"error": str(e)}}
    
    async def _create_dependency_viz(self, builder, symbol_name: Optional[str]) -> Dict[str, Any]:
        """Create dependency trace visualization."""
        try:
            if symbol_name:
                viz_data = builder.create_dependency_trace_visualization(symbol_name)
            else:
                # Create general dependency overview
                viz_data = {"nodes": [], "edges": [], "metadata": {"type": "general_dependencies"}}
            return viz_data
        except Exception as e:
            self.logger.error(f"Error creating dependency visualization: {e}")
            return {"nodes": [], "edges": [], "metadata": {"error": str(e)}}
    
    async def _create_method_relationships_viz(self, builder, class_name: str) -> Dict[str, Any]:
        """Create method relationships visualization."""
        try:
            viz_data = builder.create_method_relationships_visualization(class_name)
            return viz_data
        except Exception as e:
            self.logger.error(f"Error creating method relationships visualization: {e}")
            return {"nodes": [], "edges": [], "metadata": {"error": str(e)}}
    
    def _convert_to_code_context(self, analysis_result: AnalysisResult, project_id: str) -> CodeContext:
        """Convert AnalysisResult to CodeContext."""
        return CodeContext(
            project_id=project_id,
            file_path=analysis_result.file_path,
            content=analysis_result.content,
            analysis_type=analysis_result.analysis_type,
            symbols=analysis_result.symbols,
            dependencies=analysis_result.dependencies,
            complexity_metrics=analysis_result.complexity_metrics
        )
    
    # Fallback methods for when RepoMaster is not available
    async def _fallback_file_analysis(self, project_id: str, file_path: str) -> Optional[CodeContext]:
        """Fallback file analysis without RepoMaster."""
        try:
            # Simple file reading and basic analysis
            # This would be a simplified version without full RepoMaster capabilities
            return CodeContext(
                project_id=project_id,
                file_path=file_path,
                content="File analysis not available - RepoMaster not installed",
                analysis_type="file",
                symbols=[],
                dependencies=[],
                complexity_metrics={}
            )
        except Exception as e:
            self.logger.error(f"Error in fallback file analysis: {e}")
            return None
    
    async def _fallback_symbol_analysis(self, project_id: str, symbol_name: str) -> Optional[CodeContext]:
        """Fallback symbol analysis without RepoMaster."""
        return CodeContext(
            project_id=project_id,
            file_path="",
            content=f"Symbol analysis for '{symbol_name}' not available - RepoMaster not installed",
            analysis_type="symbol",
            symbols=[{"name": symbol_name, "type": "unknown"}],
            dependencies=[],
            complexity_metrics={}
        )
    
    async def _fallback_project_overview(self, project_id: str) -> Optional[CodeContext]:
        """Fallback project overview without RepoMaster."""
        return CodeContext(
            project_id=project_id,
            file_path="",
            content="Project overview not available - RepoMaster not installed",
            analysis_type="project",
            symbols=[],
            dependencies=[],
            complexity_metrics={}
        )
    
    async def _fallback_visualization(self, project_id: str, viz_type: str) -> Optional[GraphVisualization]:
        """Fallback visualization without RepoMaster."""
        return GraphVisualization(
            project_id=project_id,
            visualization_type=viz_type,
            nodes=[],
            edges=[],
            metadata={"error": "Visualization not available - RepoMaster not installed"}
        )
    
    def is_available(self) -> bool:
        """Check if RepoMaster is available."""
        return self.repomaster_available
    
    def clear_cache(self):
        """Clear the analysis cache."""
        self.analysis_cache.clear()
        self.logger.info("RepoMaster analysis cache cleared")
