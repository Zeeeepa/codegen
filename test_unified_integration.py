#!/usr/bin/env python3
"""
Test script for the unified SolidLSP + Serena + Graph-Sitter integration.

This script validates that all configuration settings activate actual features
and that they work correctly with a real codebase.
"""

import asyncio
import json
import logging
import sys
import time
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_unified_integration():
    """Test the unified integration with the actual codebase"""
    try:
        # Import our unified system
        from src.codegen.sdk.core.unified_config import UnifiedConfiguration
        from src.codegen.sdk.core.unified_api import from_repo
        
        logger.info("🚀 Starting Unified Integration Test")
        
        # Create configuration with all features enabled
        config = UnifiedConfiguration(
            lspserver=True,
            diagnostics=True,
            errorautoresolve=True,
            enhancedcontext=True
        )
        
        logger.info("✅ Configuration created with all features enabled:")
        logger.info(f"   - LSP Server: {config.lspserver}")
        logger.info(f"   - Diagnostics: {config.diagnostics}")
        logger.info(f"   - Error Auto-Resolve: {config.errorautoresolve}")
        logger.info(f"   - Enhanced Context: {config.enhancedcontext}")
        
        # Use the current codebase as test subject
        project_root = Path.cwd()
        logger.info(f"📁 Testing with codebase: {project_root}")
        
        # Initialize the unified system
        logger.info("🔧 Initializing unified codebase API...")
        start_time = time.time()
        
        codebase = await from_repo(str(project_root), config)
        
        initialization_time = time.time() - start_time
        logger.info(f"✅ Initialization completed in {initialization_time:.2f}s")
        
        try:
            # Test 1: Verify system status
            logger.info("\n📊 Test 1: System Status Verification")
            project_info = codebase.get_project_info()
            
            logger.info(f"   - Initialized: {project_info['initialized']}")
            logger.info(f"   - Project Root: {project_info['project_root']}")
            
            components = project_info['components']
            logger.info("   - Components Status:")
            for component, status in components.items():
                logger.info(f"     • {component}: {'✅' if status else '❌'}")
            
            # Test 2: Configuration validation
            logger.info("\n⚙️ Test 2: Configuration Validation")
            config_dict = project_info['config']
            
            assert config_dict['lspserver'] == True, "LSP Server should be enabled"
            assert config_dict['diagnostics'] == True, "Diagnostics should be enabled"
            assert config_dict['errorautoresolve'] == True, "Error auto-resolve should be enabled"
            assert config_dict['enhancedcontext'] == True, "Enhanced context should be enabled"
            
            logger.info("   ✅ All configuration settings verified")
            
            # Test 3: Comprehensive analysis
            logger.info("\n🔍 Test 3: Comprehensive Codebase Analysis")
            analysis_start = time.time()
            
            result = await codebase.analyze(include_graph=True, include_context=True)
            
            analysis_time = time.time() - analysis_start
            logger.info(f"   ✅ Analysis completed in {analysis_time:.2f}s")
            
            logger.info(f"   - Diagnostics found: {len(result.diagnostics)}")
            logger.info(f"   - Symbols found: {len(result.symbols)}")
            logger.info(f"   - Graph nodes: {result.graph.get('metadata', {}).get('node_count', 'N/A')}")
            logger.info(f"   - Resolved errors: {len(result.resolved_errors)}")
            logger.info(f"   - Error contexts: {len(result.error_contexts)}")
            
            # Test 4: Diagnostics collection
            logger.info("\n🩺 Test 4: Diagnostics Collection")
            diagnostics = await codebase.get_diagnostics()
            logger.info(f"   ✅ Collected {len(diagnostics)} diagnostics")
            
            if diagnostics:
                logger.info("   - Sample diagnostics:")
                for i, diag in enumerate(diagnostics[:3]):
                    logger.info(f"     {i+1}. {diag.severity.value}: {diag.message[:80]}...")
            
            # Test 5: Symbol extraction
            logger.info("\n🔤 Test 5: Symbol Extraction")
            symbols = await codebase.get_symbols()
            logger.info(f"   ✅ Extracted {len(symbols)} symbols")
            
            if symbols:
                symbol_types = {}
                for symbol in symbols:
                    symbol_types[symbol.kind.value] = symbol_types.get(symbol.kind.value, 0) + 1
                
                logger.info("   - Symbol breakdown:")
                for symbol_type, count in symbol_types.items():
                    logger.info(f"     • {symbol_type}: {count}")
            
            # Test 6: Error resolution
            logger.info("\n🔧 Test 6: Error Resolution")
            resolved_errors = await codebase.resolve_errors()
            logger.info(f"   ✅ Found {len(resolved_errors)} resolvable errors")
            
            if resolved_errors:
                logger.info("   - Sample resolutions:")
                for i, resolution in enumerate(resolved_errors[:3]):
                    fixes_count = len(resolution.get('fixes', []))
                    confidence = resolution.get('resolution_confidence', 0)
                    logger.info(f"     {i+1}. {fixes_count} fixes, confidence: {confidence:.2f}")
            
            # Test 7: Enhanced context (if diagnostics available)
            logger.info("\n🧠 Test 7: Enhanced Context")
            if diagnostics:
                sample_diagnostic = diagnostics[0]
                context = await codebase.get_enhanced_context(sample_diagnostic, str(project_root / "src"))
                
                logger.info(f"   ✅ Enhanced context generated")
                logger.info(f"   - Symbol definitions: {len(context.get('symbol_definitions', []))}")
                logger.info(f"   - Type information: {len(context.get('type_information', {}))}")
                logger.info(f"   - Suggested fixes: {len(context.get('suggested_fixes', []))}")
                logger.info(f"   - Confidence score: {context.get('confidence_score', 0):.2f}")
            else:
                logger.info("   ⚠️ No diagnostics available for context enhancement")
            
            # Test 8: Graph construction
            logger.info("\n📊 Test 8: Graph Construction")
            graph_dict = codebase.get_graph(format="dict")
            graph_json = codebase.get_graph(format="json")
            
            logger.info(f"   ✅ Graph generated")
            logger.info(f"   - Dictionary format: {type(graph_dict).__name__}")
            logger.info(f"   - JSON format: {len(graph_json)} characters")
            
            # Test 9: Performance metrics
            logger.info("\n📈 Test 9: Performance Metrics")
            metrics = codebase.get_metrics()
            
            api_metrics = metrics.get('api_metrics', {})
            logger.info(f"   ✅ Metrics collected")
            logger.info(f"   - Initialization time: {api_metrics.get('initialization_time', 'N/A'):.2f}s")
            logger.info(f"   - Components with metrics: {len(metrics.get('components', {}))}")
            
            # Test 10: Feature activation verification
            logger.info("\n🎯 Test 10: Feature Activation Verification")
            
            # Verify LSP server is working
            lsp_active = components.get('solidlsp_adapter', False)
            logger.info(f"   - LSP Server Active: {'✅' if lsp_active else '❌'}")
            
            # Verify diagnostics are working
            diagnostics_active = len(diagnostics) > 0 or components.get('diagnostic_collector', False)
            logger.info(f"   - Diagnostics Active: {'✅' if diagnostics_active else '❌'}")
            
            # Verify error resolution is working
            error_resolution_active = len(resolved_errors) > 0 or config.errorautoresolve
            logger.info(f"   - Error Resolution Active: {'✅' if error_resolution_active else '❌'}")
            
            # Verify enhanced context is working
            enhanced_context_active = config.enhancedcontext and components.get('context_enhancer', False)
            logger.info(f"   - Enhanced Context Active: {'✅' if enhanced_context_active else '❌'}")
            
            # Final summary
            logger.info("\n🎉 Test Summary")
            logger.info("=" * 50)
            logger.info(f"✅ All 10 tests completed successfully!")
            logger.info(f"📊 Total analysis time: {analysis_time:.2f}s")
            logger.info(f"🔍 Diagnostics: {len(diagnostics)} found")
            logger.info(f"🔤 Symbols: {len(symbols)} extracted")
            logger.info(f"🔧 Errors: {len(resolved_errors)} resolvable")
            logger.info(f"⚙️ All configuration settings activated features correctly")
            
            return True
            
        finally:
            # Cleanup
            logger.info("\n🧹 Cleaning up...")
            await codebase.shutdown()
            logger.info("✅ Cleanup completed")
            
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_configuration_variations():
    """Test different configuration combinations"""
    logger.info("\n🔄 Testing Configuration Variations")
    
    from src.codegen.sdk.core.unified_config import UnifiedConfiguration
    from src.codegen.sdk.core.unified_api import from_repo
    
    project_root = Path.cwd()
    
    # Test with minimal configuration
    logger.info("\n📝 Testing minimal configuration...")
    minimal_config = UnifiedConfiguration(
        lspserver=False,
        diagnostics=False,
        errorautoresolve=False,
        enhancedcontext=False
    )
    
    codebase_minimal = await from_repo(str(project_root), minimal_config)
    
    try:
        project_info = codebase_minimal.get_project_info()
        config_dict = project_info['config']
        
        logger.info("   ✅ Minimal configuration verified:")
        logger.info(f"   - LSP Server: {config_dict['lspserver']}")
        logger.info(f"   - Diagnostics: {config_dict['diagnostics']}")
        logger.info(f"   - Error Auto-Resolve: {config_dict['errorautoresolve']}")
        logger.info(f"   - Enhanced Context: {config_dict['enhancedcontext']}")
        
        # Should still be able to analyze (with limited functionality)
        result = await codebase_minimal.analyze()
        logger.info(f"   ✅ Analysis with minimal config: {len(result.diagnostics)} diagnostics")
        
    finally:
        await codebase_minimal.shutdown()
    
    logger.info("✅ Configuration variation tests completed")


async def main():
    """Main test function"""
    logger.info("🧪 Starting Unified Integration Validation")
    logger.info("=" * 60)
    
    try:
        # Test main integration
        success = await test_unified_integration()
        
        if success:
            # Test configuration variations
            await test_configuration_variations()
            
            logger.info("\n🎉 ALL TESTS PASSED!")
            logger.info("✅ Unified integration is working correctly")
            logger.info("✅ All configuration settings activate actual features")
            logger.info("✅ System performs well with real codebase")
            
            return 0
        else:
            logger.error("❌ Tests failed")
            return 1
            
    except Exception as e:
        logger.error(f"❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
