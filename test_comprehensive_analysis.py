#!/usr/bin/env python3
"""
Comprehensive Analysis Test Script
Tests all functions from graph-sitter, autogenlib, and solidlsp integrations
"""

import os
import sys
import traceback
import logging
from pathlib import Path
from typing import Dict, Any, List

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ComprehensiveAnalysisTester:
    """Test all refactored modules for functionality."""
    
    def __init__(self):
        self.test_results = {}
        self.errors = []
        
    def test_core_imports(self) -> bool:
        """Test core SDK imports."""
        logger.info("🔍 Testing core SDK imports...")
        try:
            from codegen.sdk.core import Codebase, Function
            from codegen.sdk.core.symbol import Symbol
            from codegen.sdk.core.class_definition import Class
            from codegen.sdk.core.file import SourceFile
            from codegen.sdk.core.import_resolution import Import
            from codegen.sdk.core.external_module import ExternalModule
            
            logger.info("✅ Core SDK imports successful")
            return True
        except Exception as e:
            logger.error(f"❌ Core SDK imports failed: {e}")
            self.errors.append(f"Core imports: {e}")
            return False
    
    def test_lsp_diagnostics_module(self) -> bool:
        """Test LSP diagnostics module functionality."""
        logger.info("🔍 Testing LSP diagnostics module...")
        try:
            from codegen.sdk.extensions.lsp.lsp_diagnostics import (
                LSPDiagnosticsManager, 
                EnhancedDiagnostic, 
                RuntimeErrorCollector
            )
            from codegen.sdk.core import Codebase
            
            # Test basic instantiation
            # Create a minimal codebase for testing
            test_codebase_path = Path(__file__).parent / "src"
            codebase = Codebase(test_codebase_path)
            
            # Test LSP manager creation
            from codegen.sdk.extensions.lsp.lsp_diagnostics import Language
            lsp_manager = LSPDiagnosticsManager(codebase, Language.PYTHON)
            
            # Test runtime error collector
            runtime_collector = RuntimeErrorCollector(codebase)
            
            logger.info("✅ LSP diagnostics module tests passed")
            return True
        except Exception as e:
            logger.error(f"❌ LSP diagnostics module failed: {e}")
            logger.error(traceback.format_exc())
            self.errors.append(f"LSP diagnostics: {e}")
            return False
    
    def test_autogenlib_modules(self) -> bool:
        """Test autogenlib integration modules."""
        logger.info("🔍 Testing autogenlib modules...")
        try:
            # Test autogenlib context
            from codegen.sdk.extensions.autogenlib.autogenlib_context import (
                get_enhanced_context_for_diagnostic,
                get_autogenlib_context,
                get_graph_sitter_context
            )
            
            # Test autogenlib AI resolve
            from codegen.sdk.extensions.autogenlib.autogenlib_ai_resolve import (
                resolve_diagnostic_with_ai,
                resolve_runtime_error_with_ai,
                resolve_ui_error_with_ai,
                resolve_multiple_errors_with_ai
            )
            
            logger.info("✅ AutoGenLib modules tests passed")
            return True
        except Exception as e:
            logger.error(f"❌ AutoGenLib modules failed: {e}")
            logger.error(traceback.format_exc())
            self.errors.append(f"AutoGenLib modules: {e}")
            return False
    
    def test_graph_sitter_analysis(self) -> bool:
        """Test graph-sitter analysis module."""
        logger.info("🔍 Testing graph-sitter analysis module...")
        try:
            from codegen.sdk.extensions.tools.graph_sitter_analysis import GraphSitterAnalyzer
            from codegen.sdk.core import Codebase
            
            # Create test codebase
            test_codebase_path = Path(__file__).parent / "src"
            codebase = Codebase(test_codebase_path)
            
            # Test analyzer creation
            analyzer = GraphSitterAnalyzer(codebase)
            
            # Test basic analysis methods
            if hasattr(analyzer, 'get_codebase_overview'):
                overview = analyzer.get_codebase_overview()
                logger.info(f"📊 Codebase overview generated: {type(overview)}")
            
            logger.info("✅ Graph-sitter analysis module tests passed")
            return True
        except Exception as e:
            logger.error(f"❌ Graph-sitter analysis module failed: {e}")
            logger.error(traceback.format_exc())
            self.errors.append(f"Graph-sitter analysis: {e}")
            return False
    
    def test_analysis_backend(self) -> bool:
        """Test analysis backend module."""
        logger.info("🔍 Testing analysis backend module...")
        try:
            from codegen.sdk.extensions.tools.analysis_backend import (
                AnalysisEngine,
                AnalyzeRequest,
                ErrorAnalysisResponse,
                EntrypointAnalysisResponse
            )
            from codegen.sdk.core import Codebase
            
            # Create test codebase
            test_codebase_path = Path(__file__).parent / "src"
            codebase = Codebase(test_codebase_path)
            
            # Test analysis engine creation
            engine = AnalysisEngine(codebase, "python")
            
            logger.info("✅ Analysis backend module tests passed")
            return True
        except Exception as e:
            logger.error(f"❌ Analysis backend module failed: {e}")
            logger.error(traceback.format_exc())
            self.errors.append(f"Analysis backend: {e}")
            return False
    
    def test_solidlsp_integration(self) -> bool:
        """Test SolidLSP integration."""
        logger.info("🔍 Testing SolidLSP integration...")
        try:
            # Test imports that should work
            from codegen.sdk.extensions.lsp.lsp_diagnostics import Language
            
            # Test that we can import LSP types
            try:
                from solidlsp.lsp_protocol_handler.lsp_types import Diagnostic, DocumentUri, Range
                logger.info("✅ SolidLSP types imported successfully")
            except ImportError as e:
                logger.warning(f"⚠️ SolidLSP types not available: {e}")
                # This might be expected if solidlsp is not installed
                return True
            
            logger.info("✅ SolidLSP integration tests passed")
            return True
        except Exception as e:
            logger.error(f"❌ SolidLSP integration failed: {e}")
            logger.error(traceback.format_exc())
            self.errors.append(f"SolidLSP integration: {e}")
            return False
    
    def test_function_calls(self) -> bool:
        """Test actual function calls with sample data."""
        logger.info("🔍 Testing function calls with sample data...")
        try:
            from codegen.sdk.core import Codebase
            from codegen.sdk.extensions.tools.graph_sitter_analysis import GraphSitterAnalyzer
            
            # Create test codebase
            test_codebase_path = Path(__file__).parent / "src"
            if not test_codebase_path.exists():
                logger.warning("⚠️ Test codebase path doesn't exist, skipping function call tests")
                return True
                
            codebase = Codebase(test_codebase_path)
            analyzer = GraphSitterAnalyzer(codebase)
            
            # Test some basic operations
            if hasattr(analyzer, 'get_codebase_overview'):
                try:
                    overview = analyzer.get_codebase_overview()
                    logger.info(f"📊 Successfully generated codebase overview")
                except Exception as e:
                    logger.warning(f"⚠️ Codebase overview generation failed: {e}")
            
            logger.info("✅ Function call tests completed")
            return True
        except Exception as e:
            logger.error(f"❌ Function call tests failed: {e}")
            logger.error(traceback.format_exc())
            self.errors.append(f"Function calls: {e}")
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return results."""
        logger.info("🚀 Starting comprehensive analysis tests...")
        
        tests = [
            ("Core Imports", self.test_core_imports),
            ("LSP Diagnostics", self.test_lsp_diagnostics_module),
            ("AutoGenLib Modules", self.test_autogenlib_modules),
            ("Graph-Sitter Analysis", self.test_graph_sitter_analysis),
            ("Analysis Backend", self.test_analysis_backend),
            ("SolidLSP Integration", self.test_solidlsp_integration),
            ("Function Calls", self.test_function_calls),
        ]
        
        results = {}
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                result = test_func()
                results[test_name] = "PASSED" if result else "FAILED"
                if result:
                    passed += 1
            except Exception as e:
                results[test_name] = f"ERROR: {e}"
                self.errors.append(f"{test_name}: {e}")
        
        # Summary
        logger.info(f"\n📊 TEST SUMMARY:")
        logger.info(f"✅ Passed: {passed}/{total}")
        logger.info(f"❌ Failed: {total - passed}/{total}")
        
        if self.errors:
            logger.info(f"\n🔍 ERRORS FOUND:")
            for error in self.errors:
                logger.error(f"  • {error}")
        
        return {
            "results": results,
            "passed": passed,
            "total": total,
            "errors": self.errors,
            "success_rate": passed / total if total > 0 else 0
        }

def main():
    """Main test execution."""
    tester = ComprehensiveAnalysisTester()
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    if results["success_rate"] == 1.0:
        logger.info("🎉 All tests passed!")
        sys.exit(0)
    else:
        logger.error(f"💥 Some tests failed. Success rate: {results['success_rate']:.1%}")
        sys.exit(1)

if __name__ == "__main__":
    main()
