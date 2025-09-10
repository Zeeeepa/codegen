#!/usr/bin/env python3
"""
Direct Import Test Script
Tests the refactored modules directly without full codegen package dependencies
"""

import os
import sys
import traceback
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_direct_imports():
    """Test direct imports of our refactored modules."""
    logger.info("🔍 Testing direct imports of refactored modules...")
    
    results = {}
    
    # Test 1: LSP Diagnostics Module
    logger.info("Testing LSP diagnostics module...")
    try:
        # Add the specific path to sys.path
        lsp_path = Path(__file__).parent / "src" / "codegen" / "sdk" / "extensions" / "lsp"
        sys.path.insert(0, str(lsp_path))
        
        # Try to compile the file directly
        import py_compile
        lsp_file = lsp_path / "lsp_diagnostics.py"
        py_compile.compile(str(lsp_file), doraise=True)
        logger.info("✅ LSP diagnostics module compiles successfully")
        results["lsp_diagnostics"] = "COMPILE_OK"
        
        # Check for specific imports that might be problematic
        with open(lsp_file, 'r') as f:
            content = f.read()
            if "from codegen.sdk.core import Codebase" in content:
                logger.info("✅ Found correct codegen.sdk.core import")
            if "from solidlsp" in content:
                logger.info("✅ Found solidlsp imports")
                
    except Exception as e:
        logger.error(f"❌ LSP diagnostics module failed: {e}")
        results["lsp_diagnostics"] = f"ERROR: {e}"
    
    # Test 2: AutoGenLib Context Module
    logger.info("Testing AutoGenLib context module...")
    try:
        autogenlib_path = Path(__file__).parent / "src" / "codegen" / "sdk" / "extensions" / "autogenlib"
        context_file = autogenlib_path / "autogenlib_context.py"
        py_compile.compile(str(context_file), doraise=True)
        logger.info("✅ AutoGenLib context module compiles successfully")
        results["autogenlib_context"] = "COMPILE_OK"
        
        # Check imports
        with open(context_file, 'r') as f:
            content = f.read()
            if "from codegen.sdk.core import Codebase" in content:
                logger.info("✅ Found correct codegen.sdk.core import")
                
    except Exception as e:
        logger.error(f"❌ AutoGenLib context module failed: {e}")
        results["autogenlib_context"] = f"ERROR: {e}"
    
    # Test 3: AutoGenLib AI Resolve Module
    logger.info("Testing AutoGenLib AI resolve module...")
    try:
        ai_resolve_file = autogenlib_path / "autogenlib_ai_resolve.py"
        py_compile.compile(str(ai_resolve_file), doraise=True)
        logger.info("✅ AutoGenLib AI resolve module compiles successfully")
        results["autogenlib_ai_resolve"] = "COMPILE_OK"
        
    except Exception as e:
        logger.error(f"❌ AutoGenLib AI resolve module failed: {e}")
        results["autogenlib_ai_resolve"] = f"ERROR: {e}"
    
    # Test 4: Graph-Sitter Analysis Module
    logger.info("Testing Graph-Sitter analysis module...")
    try:
        tools_path = Path(__file__).parent / "src" / "codegen" / "sdk" / "extensions" / "tools"
        analysis_file = tools_path / "graph_sitter_analysis.py"
        py_compile.compile(str(analysis_file), doraise=True)
        logger.info("✅ Graph-Sitter analysis module compiles successfully")
        results["graph_sitter_analysis"] = "COMPILE_OK"
        
        # Check for updated imports
        with open(analysis_file, 'r') as f:
            content = f.read()
            if "from codegen.sdk.core import Codebase" in content:
                logger.info("✅ Found correct codegen.sdk.core import")
            if "from graph_sitter import" not in content or "from graph_sitter.core" not in content:
                logger.info("✅ Old graph_sitter imports have been updated")
                
    except Exception as e:
        logger.error(f"❌ Graph-Sitter analysis module failed: {e}")
        results["graph_sitter_analysis"] = f"ERROR: {e}"
    
    # Test 5: Analysis Backend Module
    logger.info("Testing Analysis backend module...")
    try:
        backend_file = tools_path / "analysis_backend.py"
        py_compile.compile(str(backend_file), doraise=True)
        logger.info("✅ Analysis backend module compiles successfully")
        results["analysis_backend"] = "COMPILE_OK"
        
        # Check for updated imports
        with open(backend_file, 'r') as f:
            content = f.read()
            if "from codegen.sdk.core import Codebase" in content:
                logger.info("✅ Found correct codegen.sdk.core import")
            if "class AnalysisEngine" in content:
                logger.info("✅ Found AnalysisEngine class")
                
    except Exception as e:
        logger.error(f"❌ Analysis backend module failed: {e}")
        results["analysis_backend"] = f"ERROR: {e}"
    
    return results

def check_import_consistency():
    """Check that all import statements are consistent across modules."""
    logger.info("🔍 Checking import consistency...")
    
    files_to_check = [
        "src/codegen/sdk/extensions/lsp/lsp_diagnostics.py",
        "src/codegen/sdk/extensions/autogenlib/autogenlib_context.py", 
        "src/codegen/sdk/extensions/autogenlib/autogenlib_ai_resolve.py",
        "src/codegen/sdk/extensions/tools/graph_sitter_analysis.py",
        "src/codegen/sdk/extensions/tools/analysis_backend.py"
    ]
    
    import_patterns = {
        "old_graph_sitter": ["from graph_sitter import", "from graph_sitter.core", "from graph_sitter.codebase"],
        "new_codegen_sdk": ["from codegen.sdk.core import", "from codegen.sdk.core."],
        "solidlsp": ["from solidlsp"],
        "autogenlib": ["from autogenlib"]
    }
    
    consistency_results = {}
    
    for file_path in files_to_check:
        full_path = Path(__file__).parent / file_path
        if not full_path.exists():
            logger.warning(f"⚠️ File not found: {file_path}")
            continue
            
        logger.info(f"Checking {file_path}...")
        
        with open(full_path, 'r') as f:
            content = f.read()
            
        file_results = {}
        for pattern_name, patterns in import_patterns.items():
            count = sum(content.count(pattern) for pattern in patterns)
            file_results[pattern_name] = count
            
        consistency_results[file_path] = file_results
        
        # Log findings
        if file_results["old_graph_sitter"] > 0:
            logger.warning(f"⚠️ Found {file_results['old_graph_sitter']} old graph_sitter imports in {file_path}")
        if file_results["new_codegen_sdk"] > 0:
            logger.info(f"✅ Found {file_results['new_codegen_sdk']} new codegen.sdk imports in {file_path}")
    
    return consistency_results

def main():
    """Main test execution."""
    logger.info("🚀 Starting direct import analysis...")
    
    # Test direct imports
    import_results = test_direct_imports()
    
    # Check import consistency
    consistency_results = check_import_consistency()
    
    # Summary
    logger.info("\n📊 DIRECT IMPORT TEST SUMMARY:")
    passed = sum(1 for result in import_results.values() if result == "COMPILE_OK")
    total = len(import_results)
    
    for module, result in import_results.items():
        status = "✅" if result == "COMPILE_OK" else "❌"
        logger.info(f"{status} {module}: {result}")
    
    logger.info(f"\n✅ Passed: {passed}/{total}")
    logger.info(f"❌ Failed: {total - passed}/{total}")
    
    # Import consistency summary
    logger.info("\n📊 IMPORT CONSISTENCY SUMMARY:")
    total_old_imports = sum(
        file_data.get("old_graph_sitter", 0) for file_data in consistency_results.values()
    )
    total_new_imports = sum(
        file_data.get("new_codegen_sdk", 0) for file_data in consistency_results.values()
    )
    
    logger.info(f"🔄 Migration status: {total_old_imports} old imports, {total_new_imports} new imports")
    
    if total_old_imports == 0:
        logger.info("🎉 All imports have been successfully migrated!")
    else:
        logger.warning(f"⚠️ {total_old_imports} old imports still need to be updated")
    
    # Exit code
    if passed == total and total_old_imports == 0:
        logger.info("🎉 All tests passed and imports are consistent!")
        return 0
    else:
        logger.error("💥 Some issues found")
        return 1

if __name__ == "__main__":
    sys.exit(main())
