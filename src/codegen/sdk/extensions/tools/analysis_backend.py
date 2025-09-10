#!/usr/bin/env python3
"""
Production Graph-Sitter Backend API
Provides comprehensive codebase analysis, visualization, and transformation capabilities
using actual graph-sitter library implementation
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
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from collections import defaultdict, Counter
from datetime import datetime
import asyncio
import logging
import networkx as nx
from pathlib import Path

# FastAPI and web framework imports
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Graph-sitter imports (actual implementation)
try:
    from codegen.sdk.core import Codebase
    from codegen.sdk.core.external_module import ExternalModule
    from codegen.sdk.core.symbol import Symbol
    from codegen.sdk.core.file import SourceFile
    from codegen.sdk.core.function import Function
    from codegen.sdk.core.class_definition import Class
    from codegen.sdk.core.statements.statement import Statement
    from codegen.sdk.core.statements.if_block_statement import IfBlockStatement
    from codegen.sdk.core.statements.while_statement import WhileStatement
    from codegen.sdk.core.statements.try_catch_statement import TryCatchStatement
    from codegen.sdk.core.import_resolution import Import
    from codegen.sdk.core.assignment import Assignment
    from codegen.sdk.core.detached_symbols.parameter import Parameter
    from codegen.sdk.extensions.tools.graph_sitter_analysis import GraphSitterAnalyzer
    from codegen.sdk.extensions.lsp.lsp_diagnostics import LSPDiagnosticsManager
    from codegen.sdk.extensions.autogenlib.autogenlib_ai_resolve import (
        resolve_diagnostic_with_ai,
        resolve_runtime_error_with_ai, 
        resolve_ui_error_with_ai,
        resolve_multiple_errors_with_ai, 
        generate_comprehensive_fix_strategy
    )
    from solidlsp.lsp_protocol_handler.lsp_types import Diagnostic, DocumentUri, Range
    from solidlsp.ls_config import Language

    GRAPH_SITTER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: graph-sitter or related modules not available: {e}")
    print("Install with: pip install graph-sitter")
    GRAPH_SITTER_AVAILABLE = False

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


class AnalysisEngine:
    """
    Enhanced analysis engine integrating all Graph-Sitter modules, LSP, and AutoGenLib.
    """

    def __init__(self, codebase: Codebase, language: str):
        self.codebase = codebase
        self.language = language
        self.analyzer = GraphSitterAnalyzer(codebase)
        self.lsp_manager = LSPDiagnosticsManager(codebase, Language(language))
        self.context_cache = {}
        self.insight_cache = {}
        self.visualization_cache = {}

    async def perform_full_analysis(self) -> Dict[str, Any]:
        """Perform comprehensive codebase analysis using all available tools."""
        try:
            # Start LSP server
            self.lsp_manager.start_server()
            
            # 1. Open files in LSP server for diagnostic collection
            logger.info("Opening files in LSP server for diagnostic collection...")
            file_contents = {}
            for file_obj in list(self.codebase.files):
                try:
                    self.lsp_manager.open_file(file_obj.filepath, file_obj.source)
                    file_contents[file_obj.filepath] = file_obj.source
                except Exception as e:
                    logger.warning(f"Could not open file {file_obj.filepath} with LSP: {e}")

            # Give LSP server some time to process files and publish diagnostics
            logger.info("Waiting for LSP server to process files and publish diagnostics (5 seconds)...")
            await asyncio.sleep(5) # Adjust as needed for larger codebases

            # 2. Retrieve Enhanced Diagnostics
            logger.info("Retrieving enhanced diagnostics from LSP server...")
            all_enhanced_diagnostics = self.lsp_manager.get_all_enhanced_diagnostics()

            # 3. Perform Graph-Sitter Analysis
            logger.info("Performing comprehensive Graph-Sitter analysis...")
            codebase_summary = self.analyzer.get_codebase_overview()
            tree_structure = self._build_tree_structure_from_graph_sitter(self.codebase, all_enhanced_diagnostics)
            error_analysis = self._analyze_errors_comprehensive(self.codebase, all_enhanced_diagnostics)
            dead_code_analysis = self.analyzer.find_dead_code()
            entrypoint_analysis = self._analyze_entrypoints_with_graph_sitter_enhanced(self.codebase)
            dependency_graph = self._build_dependency_graph_from_graph_sitter(self.codebase)
            code_quality_metrics = self._calculate_code_quality_metrics(self.codebase)
            architectural_insights = self._analyze_architectural_patterns(self.codebase)
            security_analysis = self._analyze_security_patterns(self.codebase)
            performance_analysis = self._analyze_performance_patterns(self.codebase)
            
            # 4. Get error statistics
            error_statistics = self.lsp_manager.get_error_statistics()
            
            # 5. Generate visualizations
            visualizations = self._generate_default_visualizations()

            analysis = {
                "codebase_summary": codebase_summary,
                "tree_structure": tree_structure,
                "error_analysis": error_analysis,
                "error_statistics": error_statistics,
                "dead_code_analysis": dead_code_analysis,
                "entrypoint_analysis": entrypoint_analysis,
                "dependency_graph": dependency_graph,
                "code_quality_metrics": code_quality_metrics,
                "architectural_insights": architectural_insights,
                "security_analysis": security_analysis,
                "performance_analysis": performance_analysis,
                "visualizations": visualizations,
                "metrics": {
                    "files": len(list(self.codebase.files)),
                    "functions": len(list(self.codebase.functions)),
                    "classes": len(list(self.codebase.classes)),
                    "symbols": len(list(self.codebase.symbols)),
                    "imports": len(list(self.codebase.imports)),
                    "external_modules": len(list(self.codebase.external_modules)),
                },
            }

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing codebase with graph-sitter: {e}")
            logger.error(traceback.format_exc())
            raise Exception(f"Graph-sitter analysis failed: {str(e)}")
        finally:
            self.lsp_manager.shutdown_server() # Ensure LSP server is shut down

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
