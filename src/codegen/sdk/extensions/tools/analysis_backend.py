#!/usr/bin/env python3
"""
Unified Analysis Backend API
Provides comprehensive codebase analysis using Graph-Sitter, AutoGenLib, and LSP diagnostics
"""

import os
import tempfile
import shutil
import subprocess
import traceback
import uuid
import math
import ast
import re
import asyncio
import logging
import networkx as nx
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from collections import defaultdict, Counter
from datetime import datetime
from pathlib import Path

# FastAPI and web framework imports
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Core imports
try:
    from codegen.sdk.core import Codebase
    from codegen.sdk.extensions.tools.graph_sitter_analysis import GraphSitterAnalyzer
    from codegen.sdk.extensions.lsp.lsp_diagnostics import LSPDiagnosticsManager, RuntimeErrorCollector
    from codegen.sdk.extensions.autogenlib.autogenlib_context import (
        get_enhanced_context_for_diagnostic,
        get_autogenlib_context,
        get_graph_sitter_context
    )
    from codegen.sdk.extensions.autogenlib.autogenlib_ai_resolve import (
        resolve_diagnostic_with_ai,
        resolve_runtime_error_with_ai, 
        resolve_ui_error_with_ai,
        resolve_multiple_errors_with_ai, 
        generate_comprehensive_fix_strategy
    )
    from solidlsp.lsp_protocol_handler.lsp_types import Diagnostic, DocumentUri, Range
    from solidlsp.ls_config import Language

    UNIFIED_ANALYSIS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Unified analysis components not available: {e}")
    UNIFIED_ANALYSIS_AVAILABLE = False

logger = logging.getLogger(__name__)

# Pydantic models for API
class AnalyzeRequest(BaseModel):
    repo_url: str = Field(..., description="GitHub repository URL")
    branch: str = Field(default="main", description="Branch to analyze")
    config: Optional[Dict] = Field(default=None, description="Analysis configuration")
    include_deep_analysis: bool = Field(
        default=True, description="Include comprehensive analysis"
    )
    language: str = Field(default="python", description="Programming language")
    include_runtime_monitoring: bool = Field(default=False, description="Include runtime error monitoring")
    runtime_log_path: Optional[str] = Field(default=None, description="Path to runtime log file")
    ui_log_path: Optional[str] = Field(default=None, description="Path to UI error log file")


class ErrorAnalysisResponse(BaseModel):
    total_errors: int
    critical_errors: int
    major_errors: int
    minor_errors: int
    errors_by_category: Dict[str, int]
    detailed_errors: List[Dict[str, Any]]
    error_patterns: List[Dict[str, Any]]
    suggestions: List[Dict[str, Any]]
    runtime_errors: List[Dict[str, Any]]
    ui_errors: List[Dict[str, Any]]
    resolution_recommendations: List[Dict[str, Any]]


class EntrypointAnalysisResponse(BaseModel):
    total_entrypoints: int
    main_entrypoints: List[Dict[str, Any]]
    secondary_entrypoints: List[Dict[str, Any]]
    test_entrypoints: List[Dict[str, Any]]
    api_entrypoints: List[Dict[str, Any]]
    cli_entrypoints: List[Dict[str, Any]]
    entrypoint_graph: Dict[str, Any]
    complexity_metrics: Dict[str, Any]
    dependency_analysis: Dict[str, Any]
    call_flow_analysis: Dict[str, Any]


class FixErrorsRequest(BaseModel):
    analysis_id: str
    max_fixes: int = Field(default=5, description="Maximum number of errors to fix")
    fix_strategy: str = Field(default="individual", description="Fix strategy: individual, batch, or comprehensive")
    include_runtime_errors: bool = Field(default=True, description="Include runtime error fixes")
    include_ui_errors: bool = Field(default=True, description="Include UI error fixes")
    dry_run: bool = Field(default=False, description="Preview fixes without applying")


class DocumentationRequest(BaseModel):
    analysis_id: str
    target_type: str = Field(default="codebase", description="Documentation target: codebase, class, function")
    target_name: Optional[str] = Field(default=None, description="Specific target name")
    output_format: str = Field(default="mdx", description="Output format: mdx, json, html")
    include_private: bool = Field(default=False, description="Include private symbols")
    generate_missing_docstrings: bool = Field(default=True, description="Generate missing docstrings with AI")


class TransformationRequest(BaseModel):
    analysis_id: str
    transformation_type: str
    target_path: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    dry_run: bool = Field(default=True, description="Preview changes without applying")


class VisualizationRequest(BaseModel):
    analysis_id: str
    viz_type: str = Field(..., description="Type of visualization")
    entry_point: Optional[str] = Field(
        default=None, description="Entry point for visualization"
    )
    max_depth: int = Field(default=10, description="Maximum depth for traversal")
    include_external: bool = Field(
        default=False, description="Include external modules"
    )
    filter_patterns: List[str] = Field(
        default_factory=list, description="Filter patterns"
    )


class CodeQualityMetrics(BaseModel):
    complexity_score: float
    maintainability_index: float
    technical_debt_ratio: float
    test_coverage_estimate: float
    documentation_coverage: float
    code_duplication_score: float
    type_coverage: float
    function_metrics: Dict[str, Any]
    class_metrics: Dict[str, Any]
    file_metrics: Dict[str, Any]


class UnifiedAnalysisEngine:
    """
    Unified analysis engine that properly integrates:
    - GraphSitterAnalyzer (comprehensive codebase analysis)
    - LSPDiagnosticsManager (real-time error detection)
    - RuntimeErrorCollector (runtime error monitoring)
    - AutoGenLib context functions (AI-driven context enrichment)
    """

    def __init__(self, codebase: Codebase, language: str = "python"):
        self.codebase = codebase
        self.language = language
        
        # Initialize core components
        self.graph_sitter = GraphSitterAnalyzer(codebase)
        self.lsp_manager = LSPDiagnosticsManager(codebase, Language(language.upper()))
        self.runtime_collector = RuntimeErrorCollector(codebase)
        
        # Caches
        self.analysis_cache = {}
        self.context_cache = {}
        self.visualization_cache = {}

    async def perform_full_analysis(self, 
                                  include_lsp: bool = True,
                                  include_runtime_monitoring: bool = False,
                                  runtime_log_path: Optional[str] = None,
                                  ui_log_path: Optional[str] = None) -> Dict[str, Any]:
        """Perform comprehensive unified analysis using all available tools."""
        logger.info("🚀 Starting comprehensive unified analysis...")
        
        analysis_results = {
            "timestamp": datetime.now().isoformat(),
            "codebase_path": str(self.codebase.root),
            "language": self.language,
            "components_used": []
        }
        
        try:
            # 1. Graph-Sitter Analysis (using the actual GraphSitterAnalyzer)
            logger.info("📊 Performing Graph-Sitter analysis...")
            gs_results = await self._perform_graph_sitter_analysis()
            analysis_results["graph_sitter"] = gs_results
            analysis_results["components_used"].append("graph_sitter")
            logger.info("✅ Graph-Sitter analysis completed")
            
            # 2. LSP Diagnostics Analysis
            if include_lsp:
                logger.info("🔍 Performing LSP diagnostics analysis...")
                lsp_results = await self._perform_lsp_analysis(
                    runtime_log_path=runtime_log_path,
                    ui_log_path=ui_log_path
                )
                analysis_results["lsp_diagnostics"] = lsp_results
                analysis_results["components_used"].append("lsp_diagnostics")
                logger.info("✅ LSP diagnostics analysis completed")
            
            # 3. Runtime Error Collection
            if include_runtime_monitoring:
                logger.info("⚡ Collecting runtime errors...")
                runtime_results = self._collect_runtime_errors(
                    runtime_log_path=runtime_log_path,
                    ui_log_path=ui_log_path
                )
                analysis_results["runtime_errors"] = runtime_results
                analysis_results["components_used"].append("runtime_monitoring")
                logger.info("✅ Runtime error collection completed")
            
            # 4. Unified Error Context Analysis
            if "lsp_diagnostics" in analysis_results and "graph_sitter" in analysis_results:
                logger.info("🔗 Performing unified error context analysis...")
                unified_results = await self._perform_unified_error_analysis(
                    analysis_results["lsp_diagnostics"],
                    analysis_results["graph_sitter"]
                )
                analysis_results["unified_error_analysis"] = unified_results
                analysis_results["components_used"].append("unified_error_analysis")
                logger.info("✅ Unified error context analysis completed")
            
            # 5. Generate Summary
            analysis_results["summary"] = self._generate_analysis_summary(analysis_results)
            
            logger.info("🎉 Comprehensive unified analysis completed!")
            return analysis_results
            
        except Exception as e:
            logger.error(f"Error in unified analysis: {e}")
            logger.error(traceback.format_exc())
            raise Exception(f"Unified analysis failed: {str(e)}")
    
    async def _perform_graph_sitter_analysis(self) -> Dict[str, Any]:
        """Perform comprehensive Graph-Sitter analysis using GraphSitterAnalyzer."""
        results = {}
        
        # Use the actual GraphSitterAnalyzer methods
        results["codebase_overview"] = self.graph_sitter.get_codebase_overview()
        results["dead_code"] = self.graph_sitter.find_dead_code()
        results["documentation_analysis"] = self.graph_sitter.generate_docstrings_for_undocumented()
        
        # Get detailed analysis for key files
        results["file_details"] = {}
        for file_obj in list(self.codebase.files)[:10]:  # Limit to first 10 files
            try:
                file_details = self.graph_sitter.get_file_details(file_obj.filepath)
                results["file_details"][file_obj.filepath] = file_details
            except Exception as e:
                logger.warning(f"Could not analyze file {file_obj.filepath}: {e}")
        
        # Get function and class details for key symbols
        results["symbol_analysis"] = {
            "functions": {},
            "classes": {}
        }
        
        # Analyze top functions
        for func in list(self.codebase.functions)[:5]:  # Top 5 functions
            try:
                func_details = self.graph_sitter.get_function_details(func.name, func.file.filepath if func.file else None)
                results["symbol_analysis"]["functions"][func.name] = func_details
            except Exception as e:
                logger.warning(f"Could not analyze function {func.name}: {e}")
        
        # Analyze top classes
        for cls in list(self.codebase.classes)[:5]:  # Top 5 classes
            try:
                class_details = self.graph_sitter.get_class_details(cls.name, cls.file.filepath if cls.file else None)
                results["symbol_analysis"]["classes"][cls.name] = class_details
            except Exception as e:
                logger.warning(f"Could not analyze class {cls.name}: {e}")
        
        return results
    
    async def _perform_lsp_analysis(self, 
                                  runtime_log_path: Optional[str] = None,
                                  ui_log_path: Optional[str] = None) -> Dict[str, Any]:
        """Perform LSP diagnostics analysis."""
        results = {}
        
        # Start LSP server
        self.lsp_manager.start_server()
        
        try:
            # Open all files in LSP server
            logger.info("Opening files in LSP server...")
            for file_obj in self.codebase.files:
                try:
                    self.lsp_manager.open_file(file_obj.filepath, file_obj.source)
                except Exception as e:
                    logger.warning(f"Could not open file {file_obj.filepath}: {e}")
            
            # Wait for LSP processing
            await asyncio.sleep(3)
            
            # Get enhanced diagnostics
            enhanced_diagnostics = self.lsp_manager.get_all_enhanced_diagnostics(
                runtime_log_path=runtime_log_path,
                ui_log_path=ui_log_path
            )
            
            results["enhanced_diagnostics"] = enhanced_diagnostics
            results["error_statistics"] = self.lsp_manager.get_error_statistics()
            results["diagnostic_count"] = len(enhanced_diagnostics)
            
            # Categorize diagnostics
            results["categorized_diagnostics"] = self._categorize_diagnostics(enhanced_diagnostics)
            
        finally:
            # Shutdown LSP server
            self.lsp_manager.shutdown_server()
        
        return results
    
    def _collect_runtime_errors(self, 
                               runtime_log_path: Optional[str] = None,
                               ui_log_path: Optional[str] = None) -> Dict[str, Any]:
        """Collect runtime errors from various sources."""
        results = {}
        
        # Python runtime errors
        python_errors = self.runtime_collector.collect_python_runtime_errors(runtime_log_path)
        results["python_runtime_errors"] = python_errors
        
        # UI interaction errors
        ui_errors = self.runtime_collector.collect_ui_interaction_errors(ui_log_path)
        results["ui_errors"] = ui_errors
        
        # Network errors
        network_errors = self.runtime_collector.collect_network_errors()
        results["network_errors"] = network_errors
        
        # Summary
        results["summary"] = {
            "total_runtime_errors": len(python_errors),
            "total_ui_errors": len(ui_errors),
            "total_network_errors": len(network_errors),
            "total_errors": len(python_errors) + len(ui_errors) + len(network_errors)
        }
        
        return results
    
    async def _perform_unified_error_analysis(self, 
                                            lsp_results: Dict[str, Any],
                                            gs_results: Dict[str, Any]) -> Dict[str, Any]:
        """Perform unified error analysis combining LSP and Graph-Sitter data."""
        results = {}
        
        enhanced_diagnostics = lsp_results.get("enhanced_diagnostics", [])
        
        # Enrich diagnostics with Graph-Sitter context and AutoGenLib context
        enriched_diagnostics = []
        for enhanced_diag in enhanced_diagnostics:
            try:
                # Get AutoGenLib context
                autogenlib_context = get_enhanced_context_for_diagnostic(enhanced_diag)
                
                # Get Graph-Sitter context for the symbol
                diag = enhanced_diag["diagnostic"]
                file_path = enhanced_diag["relative_file_path"]
                
                # Try to extract symbol name from diagnostic
                symbol_name = self._extract_symbol_from_diagnostic(diag)
                if symbol_name:
                    gs_context = get_graph_sitter_context(self.codebase, symbol_name, file_path)
                else:
                    gs_context = {}
                
                # Combine contexts
                enriched_diag = {
                    **enhanced_diag,
                    "autogenlib_context": autogenlib_context,
                    "graph_sitter_symbol_context": gs_context,
                    "unified_context": {
                        "has_autogenlib_context": bool(autogenlib_context),
                        "has_graph_sitter_context": bool(gs_context),
                        "context_completeness": self._calculate_context_completeness(
                            enhanced_diag, autogenlib_context, gs_context
                        )
                    }
                }
                
                enriched_diagnostics.append(enriched_diag)
                
            except Exception as e:
                logger.warning(f"Failed to enrich diagnostic: {e}")
                enriched_diagnostics.append(enhanced_diag)
        
        results["enriched_diagnostics"] = enriched_diagnostics
        results["enrichment_statistics"] = self._calculate_enrichment_statistics(enriched_diagnostics)
        
        # Error resolution recommendations
        results["resolution_recommendations"] = await self._generate_resolution_recommendations(
            enriched_diagnostics
        )
        
        return results
    
    def _categorize_diagnostics(self, enhanced_diagnostics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Categorize diagnostics by type, severity, and patterns."""
        categories = {
            "by_severity": {"error": 0, "warning": 0, "info": 0, "hint": 0},
            "by_category": {},
            "by_file": {},
            "patterns": []
        }
        
        for enhanced_diag in enhanced_diagnostics:
            diag = enhanced_diag["diagnostic"]
            file_path = enhanced_diag["relative_file_path"]
            
            # By severity
            severity = diag.severity.name.lower() if diag.severity else "unknown"
            categories["by_severity"][severity] = categories["by_severity"].get(severity, 0) + 1
            
            # By category (using diagnostic code)
            category = diag.code if diag.code else "uncategorized"
            categories["by_category"][category] = categories["by_category"].get(category, 0) + 1
            
            # By file
            categories["by_file"][file_path] = categories["by_file"].get(file_path, 0) + 1
        
        return categories
    
    def _extract_symbol_from_diagnostic(self, diagnostic: Diagnostic) -> Optional[str]:
        """Extract symbol name from diagnostic message."""
        message = diagnostic.message
        
        # Common patterns for extracting symbol names
        patterns = [
            r"'([^']+)' is not defined",
            r"name '([^']+)' is not defined",
            r"undefined name '([^']+)'",
            r"'([^']+)' object has no attribute",
            r"module '([^']+)' has no attribute",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                return match.group(1)
        
        return None
    
    def _calculate_context_completeness(self, 
                                      enhanced_diag: Dict[str, Any],
                                      autogenlib_context: Dict[str, Any],
                                      gs_context: Dict[str, Any]) -> float:
        """Calculate how complete the context is for error resolution."""
        completeness_score = 0.0
        
        # Base diagnostic context (always present)
        completeness_score += 0.2
        
        # Enhanced diagnostic context
        if enhanced_diag.get("graph_sitter_context"):
            completeness_score += 0.2
        
        # AutoGenLib context
        if autogenlib_context:
            completeness_score += 0.3
        
        # Graph-Sitter symbol context
        if gs_context and not gs_context.get("error"):
            completeness_score += 0.3
        
        return min(completeness_score, 1.0)
    
    def _calculate_enrichment_statistics(self, enriched_diagnostics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate statistics about context enrichment."""
        total = len(enriched_diagnostics)
        if total == 0:
            return {"total": 0}
        
        with_autogenlib = sum(1 for d in enriched_diagnostics if d.get("autogenlib_context"))
        with_gs_context = sum(1 for d in enriched_diagnostics if d.get("graph_sitter_symbol_context"))
        fully_enriched = sum(1 for d in enriched_diagnostics 
                           if d.get("unified_context", {}).get("context_completeness", 0) >= 0.8)
        
        return {
            "total": total,
            "with_autogenlib_context": with_autogenlib,
            "with_graph_sitter_context": with_gs_context,
            "fully_enriched": fully_enriched,
            "enrichment_rate": {
                "autogenlib": with_autogenlib / total,
                "graph_sitter": with_gs_context / total,
                "fully_enriched": fully_enriched / total
            }
        }
    
    async def _generate_resolution_recommendations(self, 
                                                 enriched_diagnostics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate AI-powered resolution recommendations."""
        recommendations = {
            "individual_fixes": [],
            "batch_fixes": [],
            "comprehensive_strategy": None
        }
        
        # Individual fixes for high-priority errors
        high_priority_diagnostics = [
            d for d in enriched_diagnostics 
            if d["diagnostic"].severity and d["diagnostic"].severity.value <= 2  # Error or Warning
        ][:5]  # Limit to top 5
        
        for enhanced_diag in high_priority_diagnostics:
            try:
                fix_recommendation = resolve_diagnostic_with_ai(enhanced_diag, self.codebase)
                recommendations["individual_fixes"].append({
                    "diagnostic": enhanced_diag,
                    "recommendation": fix_recommendation
                })
            except Exception as e:
                logger.warning(f"Failed to generate fix recommendation: {e}")
        
        # Batch fixes for similar errors
        if len(enriched_diagnostics) > 1:
            try:
                batch_recommendation = resolve_multiple_errors_with_ai(
                    enriched_diagnostics[:10], self.codebase, max_fixes=5
                )
                recommendations["batch_fixes"] = batch_recommendation
            except Exception as e:
                logger.warning(f"Failed to generate batch recommendations: {e}")
        
        return recommendations
    
    def _generate_analysis_summary(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a comprehensive summary of the analysis."""
        summary = {
            "timestamp": analysis_results["timestamp"],
            "components_analyzed": analysis_results["components_used"],
            "codebase_metrics": {},
            "error_summary": {},
            "recommendations": [],
            "health_score": 0.0
        }
        
        # Codebase metrics from Graph-Sitter
        if "graph_sitter" in analysis_results:
            gs_data = analysis_results["graph_sitter"]
            if "codebase_overview" in gs_data:
                overview = gs_data["codebase_overview"]
                summary["codebase_metrics"] = {
                    "files": overview.get("files_count", 0),
                    "functions": overview.get("functions_count", 0),
                    "classes": overview.get("classes_count", 0),
                    "symbols": overview.get("symbols_count", 0),
                    "imports": overview.get("imports_count", 0),
                    "external_modules": overview.get("external_modules_count", 0)
                }
        
        # Error summary from LSP
        if "lsp_diagnostics" in analysis_results:
            lsp_data = analysis_results["lsp_diagnostics"]
            if "error_statistics" in lsp_data:
                summary["error_summary"] = lsp_data["error_statistics"]
        
        # Health score calculation
        summary["health_score"] = self._calculate_health_score(analysis_results)
        
        # Top recommendations
        if "unified_error_analysis" in analysis_results:
            unified_data = analysis_results["unified_error_analysis"]
            if "resolution_recommendations" in unified_data:
                recommendations = unified_data["resolution_recommendations"]
                summary["recommendations"] = [
                    "Fix high-priority errors identified by LSP",
                    "Address dead code identified by Graph-Sitter",
                    "Improve documentation coverage",
                    "Reduce complexity in identified hotspots"
                ]
        
        return summary
    
    def _calculate_health_score(self, analysis_results: Dict[str, Any]) -> float:
        """Calculate overall codebase health score (0-100)."""
        score = 100.0
        
        # Deduct for errors
        if "lsp_diagnostics" in analysis_results:
            error_stats = analysis_results["lsp_diagnostics"].get("error_statistics", {})
            critical_errors = error_stats.get("critical", 0)
            major_errors = error_stats.get("major", 0)
            minor_errors = error_stats.get("minor", 0)
            
            score -= critical_errors * 10  # -10 per critical error
            score -= major_errors * 5      # -5 per major error
            score -= minor_errors * 1      # -1 per minor error
        
        # Deduct for dead code
        if "graph_sitter" in analysis_results:
            dead_code = analysis_results["graph_sitter"].get("dead_code", {})
            dead_functions = len(dead_code.get("unused_functions", []))
            dead_classes = len(dead_code.get("unused_classes", []))
            
            score -= dead_functions * 2    # -2 per dead function
            score -= dead_classes * 3      # -3 per dead class
        
        # Ensure score is between 0 and 100
        return max(0.0, min(100.0, score))

    def _analyze_errors_comprehensive(self, codebase: Codebase, enhanced_diagnostics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Enhanced comprehensive error analysis using Graph-sitter APIs and LSP diagnostics."""
        errors = {
            "total": 0,
            "critical": 0,
            "major": 0,
            "minor": 0,
            "by_category": defaultdict(int), # Use defaultdict for easier counting
            "detailed_errors": [],
            "error_patterns": [],
            "suggestions": [],
            "resolution_recommendations": [],
            "runtime_errors": [],
            "ui_errors": []
        }

        # Integrate enhanced LSP diagnostics
        for enhanced_diag in enhanced_diagnostics:
            diag = enhanced_diag["diagnostic"]
            
            # Categorize by runtime context
            if enhanced_diag["runtime_context"]["related_runtime_errors"]:
                errors["runtime_errors"].extend(enhanced_diag["runtime_context"]["related_runtime_errors"])
            
            if enhanced_diag["ui_interaction_context"]["related_ui_errors"]:
                errors["ui_errors"].extend(enhanced_diag["ui_interaction_context"]["related_ui_errors"])
            
            error_entry = {
                "severity": diag.severity.name.lower() if diag.severity else "unknown",
                "category": diag.code if diag.code else "lsp_diagnostic",
                "file": enhanced_diag["relative_file_path"],
                "symbol": diag.source,
                "line": diag.range.line + 1,
                "message": diag.message,
                "context": enhanced_diag, # Store the full enhanced diagnostic
                "suggestion": "Review comprehensive context and apply AI-generated fix.",
                "resolution_method": "ai_resolution_enhanced",
                "confidence": enhanced_diag["graph_sitter_context"].get("resolution_context", {}).get("resolution_confidence", 0.5),
                "automated_fix_available": enhanced_diag["graph_sitter_context"].get("resolution_context", {}).get("automated_fix_available", False)
            }
            errors["detailed_errors"].append(error_entry)
            errors["by_category"][error_entry["category"]] += 1
            
            # Categorize by severity
            if diag.severity:
                if diag.severity.value == 1:  # Error
                    errors["critical"] += 1
                elif diag.severity.value == 2:  # Warning
                    errors["major"] += 1
                else:  # Info, Hint
                    errors["minor"] += 1
            else:
                errors["minor"] += 1
            errors["total"] += 1

        # Add Graph-Sitter specific analysis (e.g., dead code, circular imports, missing docstrings)
        # Missing docstrings
        for func in codebase.functions:
            if not hasattr(func, 'docstring') or not func.docstring:
                error_entry = {
                    "severity": "minor",
                    "category": "missing_docstrings",
                    "file": func.filepath,
                    "symbol": func.name,
                    "line": func.start_point.line + 1 if hasattr(func, 'start_point') else 0,
                    "message": "Missing docstring",
                    "context": f"Function '{func.name}' has no documentation",
                    "suggestion": f'Add docstring: """Brief description of {func.name}."""',
                    "resolution_method": "generate_docstring",
                    "automated_fix_available": True,
                    "confidence": 0.8
                }
                errors["detailed_errors"].append(error_entry)
                errors["by_category"]["missing_docstrings"] += 1
                errors["minor"] += 1
                errors["total"] += 1

        # Unused imports
        for file_obj in codebase.files:
            for imp in file_obj.imports:
                if not hasattr(imp, 'usages') or len(imp.usages) == 0:
                    error_entry = {
                        "severity": "minor",
                        "category": "unused_imports",
                        "file": file_obj.filepath,
                        "symbol": imp.name,
                        "line": imp.start_point.line + 1 if hasattr(imp, 'start_point') else 0,
                        "message": "Unused import",
                        "context": f"Import '{imp.name}' is not used",
                        "suggestion": "Remove unused import",
                        "resolution_method": "remove_unused_imports",
                        "automated_fix_available": True,
                        "confidence": 0.9
                    }
                    errors["detailed_errors"].append(error_entry)
                    errors["by_category"]["unused_imports"] += 1
                    errors["minor"] += 1
                    errors["total"] += 1

        # Circular imports
        import_graph = nx.DiGraph()
        for file_obj in codebase.files:
            import_graph.add_node(file_obj.filepath)
            for imp in file_obj.imports:
                if hasattr(imp, "from_file") and imp.from_file:
                    import_graph.add_edge(file_obj.filepath, imp.from_file.filepath)

        cycles = list(nx.simple_cycles(import_graph))
        for cycle in cycles:
            for file_path in cycle:
                error_entry = {
                    "severity": "critical",
                    "category": "circular_imports",
                    "file": file_path,
                    "symbol": "imports",
                    "line": 1,
                    "message": "Circular import detected",
                    "context": f"File is part of circular import: {' -> '.join(cycle)}",
                    "suggestion": "Refactor to remove circular dependency",
                    "resolution_method": "refactor_circular_imports",
                    "automated_fix_available": False,
                    "confidence": 0.3
                }
                errors["detailed_errors"].append(error_entry)
                errors["by_category"]["circular_imports"] += 1
                errors["critical"] += 1
                errors["total"] += 1

        # Generate enhanced error patterns
        errors["error_patterns"] = self._analyze_error_patterns_enhanced(errors["detailed_errors"])

        # Generate resolution recommendations
        errors["resolution_recommendations"] = self._generate_resolution_recommendations(errors)

        return errors

    def _generate_default_visualizations(self) -> Dict[str, Any]:
        """Generate default visualizations for the codebase."""
        visualizations = {}
        
        try:
            # Get main entry points for visualization
            entrypoints = self.analyzer._identify_entrypoints()
            
            if entrypoints["functions"]:
                main_func = entrypoints["functions"][0]
                
                # Create blast radius visualization
                blast_radius = self.analyzer.create_blast_radius_visualization(
                    main_func["name"], 
                    filepath=main_func["file"]
                )
                visualizations["blast_radius"] = blast_radius
                
                # Create call trace visualization
                call_trace = self.analyzer.create_call_trace_visualization(
                    main_func["name"],
                    filepath=main_func["file"]
                )
                visualizations["call_trace"] = call_trace
            
            if entrypoints["classes"]:
                main_class = entrypoints["classes"][0]
                
                # Create method relationships visualization
                method_relationships = self.analyzer.create_method_relationships_visualization(
                    main_class["name"],
                    filepath=main_class["file"]
                )
                visualizations["method_relationships"] = method_relationships
            
        except Exception as e:
            logger.warning(f"Error generating default visualizations: {e}")
            visualizations["error"] = str(e)
        
        return visualizations

    def _build_tree_structure_from_graph_sitter(self, codebase: Codebase, all_enhanced_diagnostics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build hierarchical tree structure from graph-sitter codebase with integrated LSP errors"""
        root = {
            "name": "root",
            "type": "directory",
            "path": "",
            "children": [],
            "errors": {"critical": 0, "major": 0, "minor": 0},
            "isEntrypoint": False,
            "metrics": {
                "complexity_score": 0,
                "maintainability_index": 0,
                "lines_of_code": 0,
            },
        }

        # Group files by directory
        dir_structure = defaultdict(lambda: {"files": [], "subdirs": {}})

        for file_obj in codebase.files:
            try:
                # Get enhanced diagnostics for this file
                file_enhanced_diagnostics = [d for d in all_enhanced_diagnostics if d["relative_file_path"] == file_obj.filepath]

                file_node = {
                    "name": file_obj.name,
                    "type": "file",
                    "path": file_obj.filepath,
                    "children": [],
                    "errors": self._detect_file_errors_enhanced(file_obj, file_enhanced_diagnostics),
                    "isEntrypoint": self._is_entrypoint_file(file_obj),
                    "metrics": {
                        "lines": len(file_obj.source.splitlines())
                        if hasattr(file_obj, "source")
                        else 0,
                        "functions": len(list(file_obj.functions)),
                        "classes": len(list(file_obj.classes)),
                        "imports": len(list(file_obj.imports)),
                        "symbols": len(list(getattr(file_obj, "symbols", []))),
                        "complexity_score": self._calculate_file_complexity(file_obj),
                        "maintainability_index": self._calculate_maintainability_index(file_obj),
                        "documentation_coverage": self._calculate_file_doc_coverage(file_obj)
                    },
                }

                # Add functions as children with comprehensive metrics
                for func in file_obj.functions:
                    try:
                        func_node = {
                            "name": func.name,
                            "type": "function",
                            "path": f"{file_obj.filepath}::{func.name}",
                            "children": [],
                            "errors": self._detect_function_errors_enhanced(func, file_enhanced_diagnostics),
                            "isEntrypoint": self._is_entrypoint_function(func),
                            "metrics": {
                                "parameters": self._get_function_parameters_details(func),
                                "return_type": self._get_function_return_type_details(func),
                                "local_variables": self._get_function_local_variables_details(func),
                                "usages": len(list(func.usages)),
                                "call_sites": len(list(func.function_calls)),
                                "dependencies": len(list(func.dependencies)),
                                "complexity_score": self._calculate_function_complexity(func),
                                "has_docstring": bool(getattr(func, "docstring", None)),
                                "is_async": getattr(func, "is_async", False)
                            },
                        }
                        file_node["children"].append(func_node)
                    except Exception as e:
                        logger.warning(f"Error processing function {func.name}: {e}")

                # Add classes as children with comprehensive metrics
                for cls in file_obj.classes:
                    try:
                        class_node = {
                            "name": cls.name,
                            "type": "class",
                            "path": f"{file_obj.filepath}::{cls.name}",
                            "children": [],
                            "errors": self._detect_class_errors_enhanced(cls, file_enhanced_diagnostics),
                            "isEntrypoint": self._is_entrypoint_class(cls),
                            "metrics": {
                                "methods": len(list(cls.methods)),
                                "attributes": len(list(cls.attributes)),
                                "usages": len(list(cls.usages)),
                                "superclasses": len(list(cls.superclasses)),
                                "subclasses": len(list(cls.subclasses)),
                                "dependencies": len(list(cls.dependencies)),
                                "inheritance_depth": self._calculate_doi(cls),
                                "complexity_score": self._calculate_class_complexity(cls),
                                "has_docstring": bool(getattr(cls, "docstring", None))
                            },
                        }

                        # Add methods as children with enhanced metrics
                        for method in cls.methods:
                            try:
                                method_node = {
                                    "name": method.name,
                                    "type": "method",
                                    "path": f"{file_obj.filepath}::{cls.name}::{method.name}",
                                    "children": [],
                                    "errors": self._detect_function_errors_enhanced(
                                        method, file_enhanced_diagnostics
                                    ),
                                    "isEntrypoint": False,
                                    "metrics": {
                                        "parameters": self._get_function_parameters_details(method),
                                        "return_type": self._get_function_return_type_details(method),
                                        "local_variables": self._get_function_local_variables_details(method),
                                        "usages": len(list(method.usages)),
                                        "parent_class": cls.name,
                                        "complexity_score": self._calculate_function_complexity(method),
                                        "is_public": not method.name.startswith("_"),
                                        "has_docstring": bool(getattr(method, "docstring", None))
                                    },
                                }
                                class_node["children"].append(method_node)
                            except Exception as e:
                                logger.warning(
                                    f"Error processing method {method.name}: {e}"
                                )

                        file_node["children"].append(class_node)
                    except Exception as e:
                        logger.warning(f"Error processing class {cls.name}: {e}")

                # Add to directory structure
                path_parts = file_obj.filepath.split(os.sep)
                current_dir_level = dir_structure
                for part in path_parts[:-1]:
                    if part not in current_dir_level:
                        current_dir_level[part] = {"files": [], "subdirs": {}}
                    current_dir_level = current_dir_level[part]["subdirs"]
                
                # Add file to the final directory level
                final_dir = path_parts[-2] if len(path_parts) > 1 else ""
                if final_dir not in current_dir_level:
                    current_dir_level[final_dir] = {"files": [], "subdirs": {}}
                current_dir_level[final_dir]["files"].append(file_node)

            except Exception as e:
                logger.warning(f"Error processing file {file_obj.filepath}: {e}")

        # Convert to hierarchical structure
        root["children"] = self._build_directory_nodes_recursive(dir_structure, "")
        return root

    # Helper methods - stub implementations that can be expanded
    def _detect_file_errors_enhanced(self, file_obj: SourceFile, enhanced_diagnostics: List[Dict[str, Any]]) -> Dict[str, int]:
        """Detect errors in a file using enhanced diagnostics."""
        errors = {"critical": 0, "major": 0, "minor": 0}
        for enhanced_diag in enhanced_diagnostics:
            diag = enhanced_diag["diagnostic"]
            if diag.severity:
                if diag.severity.value == 1:  # Error
                    errors["critical"] += 1
                elif diag.severity.value == 2:  # Warning
                    errors["major"] += 1
                else:  # Info, Hint
                    errors["minor"] += 1
        return errors

    def _detect_function_errors_enhanced(self, func: Function, enhanced_diagnostics: List[Dict[str, Any]]) -> Dict[str, int]:
        """Detect errors in a function using enhanced diagnostics."""
        return {"critical": 0, "major": 0, "minor": 0}

    def _detect_class_errors_enhanced(self, cls: Class, enhanced_diagnostics: List[Dict[str, Any]]) -> Dict[str, int]:
        """Detect errors in a class using enhanced diagnostics."""
        return {"critical": 0, "major": 0, "minor": 0}

    def _is_entrypoint_file(self, file_obj: SourceFile) -> bool:
        """Check if a file is an entry point."""
        return file_obj.name in ["main.py", "__main__.py", "app.py", "server.py"]

    def _is_entrypoint_function(self, func: Function) -> bool:
        """Check if a function is an entry point."""
        return func.name in ["main", "run", "start", "app"]

    def _is_entrypoint_class(self, cls: Class) -> bool:
        """Check if a class is an entry point."""
        return cls.name in ["App", "Application", "Server", "Main"]

    def _calculate_file_complexity(self, file_obj: SourceFile) -> float:
        """Calculate complexity score for a file."""
        return len(list(file_obj.functions)) * 0.5 + len(list(file_obj.classes)) * 1.0

    def _calculate_maintainability_index(self, file_obj: SourceFile) -> float:
        """Calculate maintainability index for a file."""
        return 100.0 - self._calculate_file_complexity(file_obj)

    def _calculate_file_doc_coverage(self, file_obj: SourceFile) -> float:
        """Calculate documentation coverage for a file."""
        total_items = len(list(file_obj.functions)) + len(list(file_obj.classes))
        if total_items == 0:
            return 1.0
        documented = sum(1 for func in file_obj.functions if getattr(func, 'docstring', None))
        documented += sum(1 for cls in file_obj.classes if getattr(cls, 'docstring', None))
        return documented / total_items

    def _calculate_function_complexity(self, func: Function) -> float:
        """Calculate complexity score for a function."""
        return len(list(func.function_calls)) * 0.1 + len(list(func.dependencies)) * 0.2

    def _calculate_class_complexity(self, cls: Class) -> float:
        """Calculate complexity score for a class."""
        return len(list(cls.methods)) * 0.5 + len(list(cls.attributes)) * 0.2

    def _calculate_doi(self, cls: Class) -> int:
        """Calculate depth of inheritance for a class."""
        return len(list(cls.superclasses))

    def _get_function_parameters_details(self, func: Function) -> List[Dict[str, Any]]:
        """Get detailed parameter information for a function."""
        return [{"name": param.name, "type": getattr(param, 'type', 'Any')} for param in func.parameters]

    def _get_function_return_type_details(self, func: Function) -> Dict[str, Any]:
        """Get detailed return type information for a function."""
        return {"type": getattr(func, 'return_type', 'Any')}

    def _get_function_local_variables_details(self, func: Function) -> List[Dict[str, Any]]:
        """Get detailed local variable information for a function."""
        return []  # Stub implementation

    def _build_directory_nodes_recursive(self, dir_structure: Dict, path: str) -> List[Dict[str, Any]]:
        """Build directory nodes recursively."""
        nodes = []
        for name, content in dir_structure.items():
            if content["files"]:
                nodes.extend(content["files"])
            if content["subdirs"]:
                subdir_nodes = self._build_directory_nodes_recursive(content["subdirs"], f"{path}/{name}")
                nodes.extend(subdir_nodes)
        return nodes

    def _analyze_error_patterns_enhanced(self, detailed_errors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze error patterns from detailed errors."""
        patterns = []
        error_counts = Counter(error["category"] for error in detailed_errors)
        for category, count in error_counts.most_common():
            patterns.append({
                "pattern": category,
                "count": count,
                "severity": "high" if count > 10 else "medium" if count > 5 else "low"
            })
        return patterns

    def _generate_resolution_recommendations(self, errors: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate resolution recommendations based on error analysis."""
        recommendations = []
        for category, count in errors["by_category"].items():
            if count > 0:
                recommendations.append({
                    "category": category,
                    "count": count,
                    "recommendation": f"Address {count} {category} issues",
                    "priority": "high" if count > 10 else "medium"
                })
        return recommendations

    def _analyze_entrypoints_with_graph_sitter_enhanced(self, codebase: Codebase) -> Dict[str, Any]:
        """Analyze entry points using Graph-Sitter."""
        return self.analyzer._identify_entrypoints()

    def _build_dependency_graph_from_graph_sitter(self, codebase: Codebase) -> Dict[str, Any]:
        """Build dependency graph from Graph-Sitter codebase."""
        return {"nodes": [], "edges": [], "metrics": {}}

    def _calculate_code_quality_metrics(self, codebase: Codebase) -> Dict[str, Any]:
        """Calculate comprehensive code quality metrics."""
        return {
            "complexity_score": 0.0,
            "maintainability_index": 100.0,
            "technical_debt_ratio": 0.0,
            "test_coverage_estimate": 0.0,
            "documentation_coverage": 0.0,
            "code_duplication_score": 0.0,
            "type_coverage": 0.0,
            "function_metrics": {},
            "class_metrics": {},
            "file_metrics": {}
        }

    def _analyze_architectural_patterns(self, codebase: Codebase) -> Dict[str, Any]:
        """Analyze architectural patterns in the codebase."""
        return {"patterns": [], "recommendations": []}

    def _analyze_security_patterns(self, codebase: Codebase) -> Dict[str, Any]:
        """Analyze security patterns and vulnerabilities."""
        return {"vulnerabilities": [], "recommendations": []}

    def _analyze_performance_patterns(self, codebase: Codebase) -> Dict[str, Any]:
        """Analyze performance patterns and bottlenecks."""
        return {"bottlenecks": [], "recommendations": []}


# FastAPI Application
app = FastAPI(
    title="Unified Analysis Backend API",
    description="Comprehensive codebase analysis using Graph-Sitter, AutoGenLib, and LSP diagnostics",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global analysis engines cache
analysis_engines: Dict[str, UnifiedAnalysisEngine] = {}


@app.post("/analyze", response_model=Dict[str, Any])
async def analyze_codebase(request: AnalyzeRequest, background_tasks: BackgroundTasks):
    """Perform comprehensive unified codebase analysis."""
    if not UNIFIED_ANALYSIS_AVAILABLE:
        raise HTTPException(status_code=500, detail="Unified analysis components not available")
    
    analysis_id = str(uuid.uuid4())
    
    try:
        # Create temporary directory for codebase
        temp_dir = tempfile.mkdtemp()
        
        # Clone repository if URL provided
        if request.repo_url.startswith(('http://', 'https://', 'git@')):
            logger.info(f"Cloning repository: {request.repo_url}")
            subprocess.run([
                'git', 'clone', '--depth', '1', '--branch', request.branch,
                request.repo_url, temp_dir
            ], check=True)
            codebase_path = temp_dir
        else:
            # Assume it's a local path
            codebase_path = request.repo_url
        
        # Initialize codebase and analysis engine
        codebase = Codebase(codebase_path)
        engine = UnifiedAnalysisEngine(codebase, request.language)
        
        # Store engine for later use
        analysis_engines[analysis_id] = engine
        
        # Perform analysis
        results = await engine.perform_full_analysis(
            include_lsp=True,
            include_runtime_monitoring=request.include_runtime_monitoring,
            runtime_log_path=request.runtime_log_path,
            ui_log_path=request.ui_log_path
        )
        
        # Add analysis metadata
        results["analysis_id"] = analysis_id
        results["request_config"] = request.dict()
        
        # Schedule cleanup
        background_tasks.add_task(cleanup_temp_directory, temp_dir)
        
        return results
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/analysis/{analysis_id}/visualizations")
async def get_visualizations(analysis_id: str, request: VisualizationRequest):
    """Generate visualizations for analyzed codebase."""
    if analysis_id not in analysis_engines:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    engine = analysis_engines[analysis_id]
    
    try:
        if request.viz_type == "blast_radius":
            if not request.entry_point:
                raise HTTPException(status_code=400, detail="Entry point required for blast radius visualization")
            
            result = engine.graph_sitter.create_blast_radius_visualization(
                request.entry_point, 
                max_depth=request.max_depth
            )
            
        elif request.viz_type == "call_trace":
            if not request.entry_point:
                raise HTTPException(status_code=400, detail="Entry point required for call trace visualization")
            
            result = engine.graph_sitter.create_call_trace_visualization(
                request.entry_point,
                max_depth=request.max_depth
            )
            
        elif request.viz_type == "dependency_trace":
            if not request.entry_point:
                raise HTTPException(status_code=400, detail="Entry point required for dependency trace visualization")
            
            result = engine.graph_sitter.create_dependency_trace_visualization(
                request.entry_point,
                max_depth=request.max_depth
            )
            
        elif request.viz_type == "method_relationships":
            if not request.entry_point:
                raise HTTPException(status_code=400, detail="Class name required for method relationships visualization")
            
            result = engine.graph_sitter.create_method_relationships_visualization(
                request.entry_point
            )
            
        else:
            raise HTTPException(status_code=400, detail=f"Unknown visualization type: {request.viz_type}")
        
        return result
        
    except Exception as e:
        logger.error(f"Visualization generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Visualization generation failed: {str(e)}")


@app.post("/analysis/{analysis_id}/fix-errors")
async def fix_errors(analysis_id: str, request: FixErrorsRequest):
    """Generate AI-powered error fixes."""
    if analysis_id not in analysis_engines:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    engine = analysis_engines[analysis_id]
    
    try:
        # Get enhanced diagnostics from LSP
        enhanced_diagnostics = engine.lsp_manager.get_all_enhanced_diagnostics()
        
        if request.fix_strategy == "individual":
            # Individual fixes
            fixes = []
            for enhanced_diag in enhanced_diagnostics[:request.max_fixes]:
                try:
                    fix = resolve_diagnostic_with_ai(enhanced_diag, engine.codebase)
                    fixes.append({
                        "diagnostic": enhanced_diag,
                        "fix": fix,
                        "applied": not request.dry_run
                    })
                except Exception as e:
                    logger.warning(f"Failed to generate fix: {e}")
            
            return {"fixes": fixes, "strategy": "individual"}
            
        elif request.fix_strategy == "batch":
            # Batch fixes
            batch_fixes = resolve_multiple_errors_with_ai(
                enhanced_diagnostics[:request.max_fixes], 
                engine.codebase, 
                max_fixes=request.max_fixes
            )
            return {"fixes": batch_fixes, "strategy": "batch"}
            
        elif request.fix_strategy == "comprehensive":
            # Comprehensive strategy
            strategy = generate_comprehensive_fix_strategy(
                enhanced_diagnostics, 
                engine.codebase
            )
            return {"strategy": strategy, "fixes": []}
            
        else:
            raise HTTPException(status_code=400, detail=f"Unknown fix strategy: {request.fix_strategy}")
        
    except Exception as e:
        logger.error(f"Error fixing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Error fixing failed: {str(e)}")


@app.get("/analysis/{analysis_id}/documentation")
async def generate_documentation(analysis_id: str, request: DocumentationRequest):
    """Generate documentation for analyzed codebase."""
    if analysis_id not in analysis_engines:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    engine = analysis_engines[analysis_id]
    
    try:
        if request.target_type == "codebase":
            # Generate comprehensive documentation
            docs = engine.graph_sitter.generate_structured_docs()
            return {"documentation": docs, "format": request.output_format}
            
        elif request.target_type == "class" and request.target_name:
            # Generate class-specific documentation
            class_details = engine.graph_sitter.get_class_details(request.target_name)
            return {"documentation": class_details, "format": request.output_format}
            
        elif request.target_type == "function" and request.target_name:
            # Generate function-specific documentation
            func_details = engine.graph_sitter.get_function_details(request.target_name)
            return {"documentation": func_details, "format": request.output_format}
            
        else:
            raise HTTPException(status_code=400, detail="Invalid documentation request")
        
    except Exception as e:
        logger.error(f"Documentation generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Documentation generation failed: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "unified_analysis_available": UNIFIED_ANALYSIS_AVAILABLE,
        "timestamp": datetime.now().isoformat()
    }


def cleanup_temp_directory(temp_dir: str):
    """Clean up temporary directory."""
    try:
        shutil.rmtree(temp_dir)
        logger.info(f"Cleaned up temporary directory: {temp_dir}")
    except Exception as e:
        logger.warning(f"Failed to clean up temporary directory {temp_dir}: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
