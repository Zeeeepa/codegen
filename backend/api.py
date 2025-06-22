"""
Comprehensive Codebase Analysis API Server

This module provides REST API endpoints to orchestrate all analysis and visualization features:
- /analyze - comprehensive codebase analysis
- /functions/important - get ALL important functions with definitions
- /entrypoints - get ALL detected entry points
- /issues - get detected issues with context
- /visualize - get visualization data
- /symbols/{symbol_id} - get symbol context
- /search - search symbols and code
- /hierarchy - get hierarchical views

Built with FastAPI for high performance and automatic API documentation.
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import traceback

from fastapi import FastAPI, HTTPException, Query, Path as FastAPIPath, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from backend.analysis import ComprehensiveAnalyzer, create_analyzer, EntryPoint, ImportantFunction, CodeIssue
from backend.visualize import InteractiveVisualizer, create_visualizer, FilterOptions, LayoutOptions


# Pydantic models for request/response validation
class AnalysisRequest(BaseModel):
    """Request model for codebase analysis"""
    codebase_path: str = Field(..., description="Path to the codebase to analyze")
    language: str = Field(default="python", description="Programming language of the codebase")
    include_tests: bool = Field(default=False, description="Whether to include test files in analysis")
    max_files: int = Field(default=1000, description="Maximum number of files to analyze")


class FilterRequest(BaseModel):
    """Request model for filtering options"""
    node_types: Optional[List[str]] = Field(default=None, description="Types of nodes to include")
    min_importance: float = Field(default=0.0, description="Minimum importance score")
    max_complexity: int = Field(default=100, description="Maximum complexity threshold")
    show_entry_points_only: bool = Field(default=False, description="Show only entry points")
    show_issues_only: bool = Field(default=False, description="Show only nodes with issues")
    file_patterns: Optional[List[str]] = Field(default=None, description="File patterns to include")


class LayoutRequest(BaseModel):
    """Request model for layout options"""
    algorithm: str = Field(default="force_directed", description="Layout algorithm")
    spacing: float = Field(default=1.0, description="Node spacing factor")
    iterations: int = Field(default=50, description="Layout iterations")
    cluster_by: str = Field(default="file", description="Clustering strategy")


class VisualizationRequest(BaseModel):
    """Request model for visualization"""
    filter_options: Optional[FilterRequest] = None
    layout_options: Optional[LayoutRequest] = None
    export_format: str = Field(default="json", description="Export format (json, cytoscape, d3)")


class SearchRequest(BaseModel):
    """Request model for symbol search"""
    query: str = Field(..., description="Search query")
    limit: int = Field(default=20, description="Maximum number of results")
    search_in_source: bool = Field(default=False, description="Search in source code")


class AnalysisResponse(BaseModel):
    """Response model for analysis results"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


# Global cache for analyzers and visualizers
analyzer_cache: Dict[str, ComprehensiveAnalyzer] = {}
visualizer_cache: Dict[str, InteractiveVisualizer] = {}


# FastAPI app initialization
app = FastAPI(
    title="Comprehensive Codebase Analysis API",
    description="REST API for comprehensive codebase analysis and interactive visualization",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Utility functions
def get_cache_key(codebase_path: str, language: str) -> str:
    """Generate cache key for analyzer"""
    return f"{codebase_path}:{language}"


def get_or_create_analyzer(codebase_path: str, language: str) -> ComprehensiveAnalyzer:
    """Get analyzer from cache or create new one"""
    cache_key = get_cache_key(codebase_path, language)
    
    if cache_key not in analyzer_cache:
        if not os.path.exists(codebase_path):
            raise HTTPException(status_code=404, detail=f"Codebase path not found: {codebase_path}")
        
        analyzer_cache[cache_key] = create_analyzer(codebase_path, language)
    
    return analyzer_cache[cache_key]


def get_or_create_visualizer(analyzer: ComprehensiveAnalyzer) -> InteractiveVisualizer:
    """Get visualizer from cache or create new one"""
    cache_key = f"{analyzer.codebase_path}:{analyzer.language}"
    
    if cache_key not in visualizer_cache:
        visualizer_cache[cache_key] = create_visualizer(analyzer)
    
    return visualizer_cache[cache_key]


def convert_filter_options(filter_req: Optional[FilterRequest]) -> FilterOptions:
    """Convert request model to filter options"""
    if not filter_req:
        return FilterOptions()
    
    return FilterOptions(
        node_types=filter_req.node_types,
        min_importance=filter_req.min_importance,
        max_complexity=filter_req.max_complexity,
        show_entry_points_only=filter_req.show_entry_points_only,
        show_issues_only=filter_req.show_issues_only,
        file_patterns=filter_req.file_patterns
    )


def convert_layout_options(layout_req: Optional[LayoutRequest]) -> LayoutOptions:
    """Convert request model to layout options"""
    if not layout_req:
        return LayoutOptions()
    
    return LayoutOptions(
        algorithm=layout_req.algorithm,
        spacing=layout_req.spacing,
        iterations=layout_req.iterations,
        cluster_by=layout_req.cluster_by
    )


# API Endpoints

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Comprehensive Codebase Analysis API",
        "version": "1.0.0",
        "description": "REST API for comprehensive codebase analysis and interactive visualization",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_codebase(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """
    Perform comprehensive codebase analysis.
    
    Returns summary of analysis including:
    - Total files, functions, classes, symbols
    - Entry points summary
    - Important functions summary
    - Issues summary
    """
    try:
        analyzer = get_or_create_analyzer(request.codebase_path, request.language)
        
        # Get analysis summary
        summary = analyzer.get_analysis_summary()
        
        # Add request metadata
        summary["request"] = {
            "codebase_path": request.codebase_path,
            "language": request.language,
            "include_tests": request.include_tests,
            "max_files": request.max_files
        }
        
        return AnalysisResponse(
            success=True,
            message="Codebase analysis completed successfully",
            data=summary
        )
        
    except Exception as e:
        return AnalysisResponse(
            success=False,
            message="Analysis failed",
            error=str(e)
        )


@app.get("/functions/important", response_model=AnalysisResponse)
async def get_important_functions(
    codebase_path: str = Query(..., description="Path to the codebase"),
    language: str = Query(default="python", description="Programming language"),
    limit: int = Query(default=50, description="Maximum number of functions to return"),
    min_importance: float = Query(default=0.0, description="Minimum importance score")
):
    """
    Get ALL most important functions with their full definitions.
    
    Returns comprehensive list of important functions including:
    - Function name and full qualified name
    - Source code and location
    - Importance metrics
    - Usage and dependency information
    - Context and metadata
    """
    try:
        analyzer = get_or_create_analyzer(codebase_path, language)
        important_functions = analyzer.get_all_important_functions()
        
        # Filter by minimum importance
        filtered_functions = [
            func for func in important_functions 
            if func.importance_score >= min_importance
        ][:limit]
        
        # Convert to serializable format
        functions_data = []
        for func in filtered_functions:
            functions_data.append({
                "name": func.name,
                "full_name": func.full_name,
                "filepath": func.filepath,
                "line_number": func.line_number,
                "source_code": func.source_code,
                "importance_score": func.importance_score,
                "usage_count": func.usage_count,
                "dependency_count": func.dependency_count,
                "is_public_api": func.is_public_api,
                "is_entry_point": func.is_entry_point,
                "call_graph_centrality": func.call_graph_centrality,
                "context": func.context
            })
        
        return AnalysisResponse(
            success=True,
            message=f"Found {len(functions_data)} important functions",
            data={
                "functions": functions_data,
                "total_analyzed": len(important_functions),
                "filters_applied": {
                    "min_importance": min_importance,
                    "limit": limit
                }
            }
        )
        
    except Exception as e:
        return AnalysisResponse(
            success=False,
            message="Failed to get important functions",
            error=str(e)
        )


@app.get("/entrypoints", response_model=AnalysisResponse)
async def get_all_entry_points(
    codebase_path: str = Query(..., description="Path to the codebase"),
    language: str = Query(default="python", description="Programming language"),
    entry_type: Optional[str] = Query(default=None, description="Filter by entry point type")
):
    """
    Get ALL detected entry points in the codebase.
    
    Returns comprehensive list of entry points including:
    - Main functions
    - CLI entry points (argparse, click, typer)
    - Web endpoints (FastAPI, Flask)
    - Exported functions
    - Framework-specific entry points
    """
    try:
        analyzer = get_or_create_analyzer(codebase_path, language)
        entry_points = analyzer.get_all_entry_points()
        
        # Filter by type if specified
        if entry_type:
            entry_points = [ep for ep in entry_points if ep.type == entry_type]
        
        # Convert to serializable format
        entry_points_data = []
        for ep in entry_points:
            entry_points_data.append({
                "name": ep.name,
                "type": ep.type,
                "filepath": ep.filepath,
                "line_number": ep.line_number,
                "source_code": ep.source_code,
                "context": ep.context
            })
        
        # Group by type for summary
        by_type = {}
        for ep in entry_points:
            if ep.type not in by_type:
                by_type[ep.type] = []
            by_type[ep.type].append(ep.name)
        
        return AnalysisResponse(
            success=True,
            message=f"Found {len(entry_points_data)} entry points",
            data={
                "entry_points": entry_points_data,
                "summary": {
                    "total": len(entry_points_data),
                    "by_type": {k: len(v) for k, v in by_type.items()},
                    "types_found": list(by_type.keys())
                },
                "filters_applied": {
                    "entry_type": entry_type
                }
            }
        )
        
    except Exception as e:
        return AnalysisResponse(
            success=False,
            message="Failed to get entry points",
            error=str(e)
        )


@app.get("/issues", response_model=AnalysisResponse)
async def get_detected_issues(
    codebase_path: str = Query(..., description="Path to the codebase"),
    language: str = Query(default="python", description="Programming language"),
    issue_type: Optional[str] = Query(default=None, description="Filter by issue type"),
    severity: Optional[str] = Query(default=None, description="Filter by severity")
):
    """
    Get detected code issues with context.
    
    Returns issues including:
    - Unused code
    - Circular dependencies
    - Missing documentation
    - Architectural violations
    """
    try:
        analyzer = get_or_create_analyzer(codebase_path, language)
        issues = analyzer.detect_issues()
        
        # Apply filters
        if issue_type:
            issues = [issue for issue in issues if issue.type == issue_type]
        if severity:
            issues = [issue for issue in issues if issue.severity == severity]
        
        # Convert to serializable format
        issues_data = []
        for issue in issues:
            issues_data.append({
                "type": issue.type,
                "severity": issue.severity,
                "message": issue.message,
                "filepath": issue.filepath,
                "line_number": issue.line_number,
                "context": issue.context
            })
        
        # Create summary
        by_type = {}
        by_severity = {}
        for issue in issues:
            by_type[issue.type] = by_type.get(issue.type, 0) + 1
            by_severity[issue.severity] = by_severity.get(issue.severity, 0) + 1
        
        return AnalysisResponse(
            success=True,
            message=f"Found {len(issues_data)} issues",
            data={
                "issues": issues_data,
                "summary": {
                    "total": len(issues_data),
                    "by_type": by_type,
                    "by_severity": by_severity
                },
                "filters_applied": {
                    "issue_type": issue_type,
                    "severity": severity
                }
            }
        )
        
    except Exception as e:
        return AnalysisResponse(
            success=False,
            message="Failed to get issues",
            error=str(e)
        )


@app.post("/visualize", response_model=AnalysisResponse)
async def create_visualization(
    codebase_path: str = Query(..., description="Path to the codebase"),
    language: str = Query(default="python", description="Programming language"),
    request: VisualizationRequest = None
):
    """
    Create interactive visualization data.
    
    Returns visualization graph with nodes and edges for:
    - Functions and their relationships
    - Classes and inheritance
    - Files and containment
    - Issues and their locations
    """
    try:
        if request is None:
            request = VisualizationRequest()
        
        analyzer = get_or_create_analyzer(codebase_path, language)
        visualizer = get_or_create_visualizer(analyzer)
        
        # Convert request models to options
        filter_options = convert_filter_options(request.filter_options)
        layout_options = convert_layout_options(request.layout_options)
        
        # Create visualization graph
        graph = visualizer.create_interactive_graph(filter_options, layout_options)
        
        # Export in requested format
        if request.export_format == "json":
            graph_data = {
                "nodes": [
                    {
                        "id": node.id,
                        "label": node.label,
                        "type": node.type,
                        "size": node.size,
                        "color": node.color,
                        "position": node.position,
                        "metadata": node.metadata
                    }
                    for node in graph.nodes
                ],
                "edges": [
                    {
                        "source": edge.source,
                        "target": edge.target,
                        "type": edge.type,
                        "weight": edge.weight,
                        "color": edge.color,
                        "metadata": edge.metadata
                    }
                    for edge in graph.edges
                ],
                "metadata": graph.metadata
            }
        else:
            graph_data = json.loads(visualizer.export_graph(request.export_format))
        
        return AnalysisResponse(
            success=True,
            message="Visualization created successfully",
            data={
                "graph": graph_data,
                "export_format": request.export_format,
                "options_applied": {
                    "filter_options": filter_options.__dict__,
                    "layout_options": layout_options.__dict__
                }
            }
        )
        
    except Exception as e:
        return AnalysisResponse(
            success=False,
            message="Failed to create visualization",
            error=str(e)
        )


@app.get("/symbols/{symbol_id}", response_model=AnalysisResponse)
async def get_symbol_context(
    symbol_id: str = FastAPIPath(..., description="Symbol ID from visualization"),
    codebase_path: str = Query(..., description="Path to the codebase"),
    language: str = Query(default="python", description="Programming language")
):
    """
    Get comprehensive context for a selected symbol.
    
    Returns detailed information including:
    - Symbol definition and source code
    - Usage locations and patterns
    - Dependencies and relationships
    - Related symbols and context
    """
    try:
        analyzer = get_or_create_analyzer(codebase_path, language)
        visualizer = get_or_create_visualizer(analyzer)
        
        # Get symbol details from visualizer
        symbol_details = visualizer.get_symbol_details(symbol_id)
        
        if not symbol_details:
            raise HTTPException(status_code=404, detail=f"Symbol not found: {symbol_id}")
        
        # Get additional context from analyzer if it's a function or class
        additional_context = {}
        if symbol_details['type'] == 'function':
            symbol_context = analyzer.get_symbol_context(symbol_details['name'])
            if symbol_context:
                additional_context = {
                    "usages": symbol_context.usages,
                    "dependencies": symbol_context.dependencies,
                    "definition_context": symbol_context.definition_context,
                    "related_symbols": symbol_context.related_symbols
                }
        
        return AnalysisResponse(
            success=True,
            message="Symbol context retrieved successfully",
            data={
                "symbol": symbol_details,
                "additional_context": additional_context,
                "symbol_id": symbol_id
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return AnalysisResponse(
            success=False,
            message="Failed to get symbol context",
            error=str(e)
        )


@app.post("/search", response_model=AnalysisResponse)
async def search_symbols(
    codebase_path: str = Query(..., description="Path to the codebase"),
    language: str = Query(default="python", description="Programming language"),
    request: SearchRequest = None
):
    """
    Search for symbols and code elements.
    
    Supports searching in:
    - Function and class names
    - Source code content
    - File paths
    - Documentation
    """
    try:
        if not request or not request.query:
            raise HTTPException(status_code=400, detail="Search query is required")
        
        analyzer = get_or_create_analyzer(codebase_path, language)
        visualizer = get_or_create_visualizer(analyzer)
        
        # Perform search
        results = visualizer.search_symbols(request.query, request.limit)
        
        return AnalysisResponse(
            success=True,
            message=f"Found {len(results)} search results",
            data={
                "results": results,
                "query": request.query,
                "limit": request.limit,
                "search_in_source": request.search_in_source
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return AnalysisResponse(
            success=False,
            message="Search failed",
            error=str(e)
        )


@app.get("/hierarchy", response_model=AnalysisResponse)
async def get_hierarchy_view(
    codebase_path: str = Query(..., description="Path to the codebase"),
    language: str = Query(default="python", description="Programming language"),
    root_type: str = Query(default="file", description="Root type for hierarchy (file, class, function)")
):
    """
    Get hierarchical view of the codebase.
    
    Supports different hierarchy types:
    - file: File and directory structure
    - class: Class inheritance hierarchy
    - function: Function call hierarchy
    """
    try:
        analyzer = get_or_create_analyzer(codebase_path, language)
        visualizer = get_or_create_visualizer(analyzer)
        
        # Get hierarchy
        hierarchy = visualizer.get_hierarchy_view(root_type)
        
        return AnalysisResponse(
            success=True,
            message="Hierarchy retrieved successfully",
            data={
                "hierarchy": hierarchy,
                "root_type": root_type
            }
        )
        
    except Exception as e:
        return AnalysisResponse(
            success=False,
            message="Failed to get hierarchy",
            error=str(e)
        )


@app.delete("/cache", response_model=AnalysisResponse)
async def clear_cache(
    codebase_path: Optional[str] = Query(default=None, description="Specific codebase to clear (optional)")
):
    """
    Clear analysis cache.
    
    If codebase_path is provided, clears cache for that specific codebase.
    Otherwise, clears all cached data.
    """
    try:
        if codebase_path:
            # Clear specific codebase cache
            keys_to_remove = [key for key in analyzer_cache.keys() if key.startswith(codebase_path)]
            for key in keys_to_remove:
                del analyzer_cache[key]
                if key in visualizer_cache:
                    del visualizer_cache[key]
            
            message = f"Cache cleared for codebase: {codebase_path}"
        else:
            # Clear all cache
            analyzer_cache.clear()
            visualizer_cache.clear()
            message = "All cache cleared"
        
        return AnalysisResponse(
            success=True,
            message=message,
            data={
                "remaining_cached_codebases": len(analyzer_cache)
            }
        )
        
    except Exception as e:
        return AnalysisResponse(
            success=False,
            message="Failed to clear cache",
            error=str(e)
        )


@app.get("/health", response_model=Dict[str, Any])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "cached_codebases": len(analyzer_cache),
        "api_version": "1.0.0"
    }


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "error": str(exc),
            "traceback": traceback.format_exc() if app.debug else None
        }
    )


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    print("🚀 Comprehensive Codebase Analysis API starting up...")
    print("📚 API Documentation available at: /docs")
    print("🔍 ReDoc documentation available at: /redoc")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    print("🛑 Comprehensive Codebase Analysis API shutting down...")
    # Clear caches
    analyzer_cache.clear()
    visualizer_cache.clear()


# Main entry point
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Comprehensive Codebase Analysis API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    # Set debug mode
    app.debug = args.debug
    
    print(f"🌟 Starting Comprehensive Codebase Analysis API")
    print(f"🔗 Server will be available at: http://{args.host}:{args.port}")
    print(f"📖 API Documentation: http://{args.host}:{args.port}/docs")
    print(f"🔍 ReDoc Documentation: http://{args.host}:{args.port}/redoc")
    
    uvicorn.run(
        "api:app" if args.reload else app,
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="debug" if args.debug else "info"
    )

