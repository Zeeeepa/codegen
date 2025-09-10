#!/usr/bin/env python3
"""
Unified Analysis Engine
Integrates Graph-Sitter, AutoGenLib, and LSP diagnostics for comprehensive codebase analysis
"""

import os
import sys
import argparse
import asyncio
import logging
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Core imports
from codegen.sdk.core import Codebase

# Import unified analysis components
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
    resolve_multiple_errors_with_ai
)

# LSP imports
try:
    from solidlsp.ls_config import Language
    from solidlsp.lsp_protocol_handler.lsp_types import Diagnostic
    LSP_AVAILABLE = True
except ImportError:
    LSP_AVAILABLE = False
    print("Warning: SolidLSP not available. LSP diagnostics will be disabled.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class UnifiedAnalysisEngine:
    """
    Unified analysis engine that combines:
    - Graph-Sitter analysis (comprehensive codebase analysis)
    - AutoGenLib context (AI-driven context enrichment)
    - LSP diagnostics (real-time error detection)
    """
    
    def __init__(self, codebase_path: str, language: str = "python"):
        self.codebase_path = Path(codebase_path)
        self.language = language
        
        # Initialize core components
        logger.info(f"Initializing codebase from: {codebase_path}")
        self.codebase = Codebase(self.codebase_path)
        
        # Initialize Graph-Sitter analyzer
        logger.info("Initializing Graph-Sitter analyzer...")
        self.graph_sitter = GraphSitterAnalyzer(self.codebase)
        
        # Initialize LSP diagnostics manager
        if LSP_AVAILABLE:
            logger.info("Initializing LSP diagnostics manager...")
            self.lsp_manager = LSPDiagnosticsManager(self.codebase, Language(language.upper()))
            self.runtime_collector = RuntimeErrorCollector(self.codebase)
        else:
            self.lsp_manager = None
            self.runtime_collector = None
        
        # Analysis results cache
        self.analysis_cache = {}
        
    async def perform_comprehensive_analysis(self, 
                                           include_lsp: bool = True,
                                           include_runtime_monitoring: bool = False,
                                           runtime_log_path: Optional[str] = None,
                                           ui_log_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform comprehensive unified analysis combining all components.
        """
        logger.info("🚀 Starting comprehensive unified analysis...")
        
        analysis_results = {
            "timestamp": datetime.now().isoformat(),
            "codebase_path": str(self.codebase_path),
            "language": self.language,
            "components_used": []
        }
        
        # 1. Graph-Sitter Analysis
        logger.info("📊 Performing Graph-Sitter analysis...")
        try:
            gs_results = await self._perform_graph_sitter_analysis()
            analysis_results["graph_sitter"] = gs_results
            analysis_results["components_used"].append("graph_sitter")
            logger.info("✅ Graph-Sitter analysis completed")
        except Exception as e:
            logger.error(f"❌ Graph-Sitter analysis failed: {e}")
            analysis_results["graph_sitter"] = {"error": str(e)}
        
        # 2. LSP Diagnostics Analysis
        if include_lsp and self.lsp_manager:
            logger.info("🔍 Performing LSP diagnostics analysis...")
            try:
                lsp_results = await self._perform_lsp_analysis(
                    runtime_log_path=runtime_log_path,
                    ui_log_path=ui_log_path
                )
                analysis_results["lsp_diagnostics"] = lsp_results
                analysis_results["components_used"].append("lsp_diagnostics")
                logger.info("✅ LSP diagnostics analysis completed")
            except Exception as e:
                logger.error(f"❌ LSP diagnostics analysis failed: {e}")
                analysis_results["lsp_diagnostics"] = {"error": str(e)}
        
        # 3. Runtime Error Collection
        if include_runtime_monitoring and self.runtime_collector:
            logger.info("⚡ Collecting runtime errors...")
            try:
                runtime_results = self._collect_runtime_errors(
                    runtime_log_path=runtime_log_path,
                    ui_log_path=ui_log_path
                )
                analysis_results["runtime_errors"] = runtime_results
                analysis_results["components_used"].append("runtime_monitoring")
                logger.info("✅ Runtime error collection completed")
            except Exception as e:
                logger.error(f"❌ Runtime error collection failed: {e}")
                analysis_results["runtime_errors"] = {"error": str(e)}
        
        # 4. Unified Error Context Analysis
        if "lsp_diagnostics" in analysis_results and "graph_sitter" in analysis_results:
            logger.info("🔗 Performing unified error context analysis...")
            try:
                unified_results = await self._perform_unified_error_analysis(
                    analysis_results["lsp_diagnostics"],
                    analysis_results["graph_sitter"]
                )
                analysis_results["unified_error_analysis"] = unified_results
                analysis_results["components_used"].append("unified_error_analysis")
                logger.info("✅ Unified error context analysis completed")
            except Exception as e:
                logger.error(f"❌ Unified error context analysis failed: {e}")
                analysis_results["unified_error_analysis"] = {"error": str(e)}
        
        # 5. Generate Summary
        analysis_results["summary"] = self._generate_analysis_summary(analysis_results)
        
        logger.info("🎉 Comprehensive unified analysis completed!")
        return analysis_results
    
    async def _perform_graph_sitter_analysis(self) -> Dict[str, Any]:
        """Perform comprehensive Graph-Sitter analysis."""
        results = {}
        
        # Codebase overview
        results["codebase_overview"] = self.graph_sitter.get_codebase_overview()
        
        # Dead code analysis
        results["dead_code"] = self.graph_sitter.find_dead_code()
        
        # Entrypoint analysis
        results["entrypoints"] = self.graph_sitter._identify_entrypoints()
        
        # Complexity analysis
        results["complexity"] = {
            "overview": self.graph_sitter._get_complexity_overview(),
            "hotspots": self.graph_sitter._identify_complexity_hotspots()
        }
        
        # Documentation analysis
        results["documentation"] = self.graph_sitter.generate_docstrings_for_undocumented()
        
        # Architecture analysis
        results["architecture"] = {
            "patterns": self.graph_sitter._analyze_architectural_patterns(),
            "dependencies": self.graph_sitter._analyze_dependency_patterns(),
            "modularity": self.graph_sitter._analyze_modularity()
        }
        
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
        
        # Enrich diagnostics with Graph-Sitter context
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
            import re
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
    
    def save_results(self, results: Dict[str, Any], output_path: str):
        """Save analysis results to file."""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Analysis results saved to: {output_file}")


async def main():
    """Main entry point for the unified analysis engine."""
    parser = argparse.ArgumentParser(description="Unified Codebase Analysis Engine")
    parser.add_argument("--local", type=str, help="Path to local codebase")
    parser.add_argument("--url", type=str, help="GitHub repository name (owner/repo)")
    parser.add_argument("--language", type=str, default="python", help="Programming language")
    parser.add_argument("--output", type=str, default="analysis_results.json", help="Output file path")
    parser.add_argument("--include-lsp", action="store_true", default=True, help="Include LSP diagnostics")
    parser.add_argument("--include-runtime", action="store_true", help="Include runtime error monitoring")
    parser.add_argument("--runtime-log", type=str, help="Path to runtime log file")
    parser.add_argument("--ui-log", type=str, help="Path to UI error log file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Determine codebase path
    if args.local:
        codebase_path = args.local
    elif args.url:
        # For GitHub URLs, we'd need to clone the repo first
        # For now, just use the URL as a path (assuming it's already cloned)
        codebase_path = args.url
    else:
        print("Error: Must specify either --local or --url")
        sys.exit(1)
    
    if not Path(codebase_path).exists():
        print(f"Error: Codebase path does not exist: {codebase_path}")
        sys.exit(1)
    
    try:
        # Initialize analysis engine
        engine = UnifiedAnalysisEngine(codebase_path, args.language)
        
        # Perform comprehensive analysis
        results = await engine.perform_comprehensive_analysis(
            include_lsp=args.include_lsp,
            include_runtime_monitoring=args.include_runtime,
            runtime_log_path=args.runtime_log,
            ui_log_path=args.ui_log
        )
        
        # Save results
        engine.save_results(results, args.output)
        
        # Print summary
        summary = results.get("summary", {})
        print("\n" + "="*60)
        print("🎯 UNIFIED ANALYSIS SUMMARY")
        print("="*60)
        print(f"📊 Codebase Metrics:")
        metrics = summary.get("codebase_metrics", {})
        for key, value in metrics.items():
            print(f"   {key.capitalize()}: {value}")
        
        print(f"\n🔍 Error Summary:")
        error_summary = summary.get("error_summary", {})
        for key, value in error_summary.items():
            print(f"   {key.capitalize()}: {value}")
        
        print(f"\n💯 Health Score: {summary.get('health_score', 0):.1f}/100")
        
        print(f"\n📋 Top Recommendations:")
        for i, rec in enumerate(summary.get("recommendations", [])[:3], 1):
            print(f"   {i}. {rec}")
        
        print(f"\n📄 Full results saved to: {args.output}")
        print("="*60)
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

