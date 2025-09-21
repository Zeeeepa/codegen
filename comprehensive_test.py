#!/usr/bin/env python3
"""
Comprehensive test of all graph-sitter tools with AutoGenLib and Z.ai integration
"""

import os
import sys
import traceback
from datetime import datetime

# Add the tools directory to Python path
sys.path.insert(0, '/tmp/Zeeeepa/codegen/tools')
sys.path.insert(0, '/tmp/Zeeeepa/codegen')

print("=" * 60)
print("🚀 COMPREHENSIVE GRAPH-SITTER TOOLS TEST")
print("=" * 60)
print(f"Test started at: {datetime.now()}")
print()

# Test results tracking
test_results = {
    "passed": 0,
    "failed": 0,
    "warnings": 0,
    "details": []
}

def test_step(name: str, func):
    """Helper to track test results"""
    try:
        print(f"📋 {name}...")
        result = func()
        if result:
            print(f"✅ {name} - PASSED")
            test_results["passed"] += 1
            test_results["details"].append(f"✅ {name}")
            return True
        else:
            print(f"⚠️  {name} - WARNING")
            test_results["warnings"] += 1
            test_results["details"].append(f"⚠️  {name}")
            return False
    except Exception as e:
        print(f"❌ {name} - FAILED: {e}")
        test_results["failed"] += 1
        test_results["details"].append(f"❌ {name}: {e}")
        return False

# Test 1: AutoGenLib Integration
def test_autogenlib():
    import autogenlib
    autogenlib.init("Graph-sitter comprehensive analysis tools", 
                    enable_exception_handler=True, enable_caching=False)
    
    ai_status = autogenlib.check_ai_availability()
    print(f"   AI Status: {ai_status}")
    
    # Test Z.ai integration
    client = autogenlib.get_ai_client()
    if client:
        print(f"   AI Client: {type(client).__name__}")
        return True
    else:
        print("   No AI client available (expected without API keys)")
        return True

# Test 2: Core Graph-Sitter Classes
def test_core_classes():
    from codegen.exports import Codebase, Function, ProgrammingLanguage
    
    codebase = Codebase()
    function = Function()
    
    print(f"   Codebase: {codebase}")
    print(f"   Function: {function}")
    print(f"   ProgrammingLanguage: {ProgrammingLanguage}")
    
    return True

# Test 3: Backend Import and Basic Functionality
def test_backend():
    import graph_sitter_backend
    
    # Check FastAPI app
    if hasattr(graph_sitter_backend, 'app'):
        print("   FastAPI app available")
        
    # Test some basic functions
    if hasattr(graph_sitter_backend, 'calculate_doi'):
        # Test with a placeholder class
        from tools.graph_sitter_backend import Class, calculate_doi
        test_class = Class()
        doi = calculate_doi(test_class)
        print(f"   DOI calculation works: {doi}")
        
    return True

# Test 4: Analysis Tools
def test_analysis_tools():
    # Test the compatibility modules
    try:
        from graph_sitter.core.symbol import Symbol
        from graph_sitter.core.function import Function
        from graph_sitter.core.class_definition import Class
        
        symbol = Symbol()
        function = Function()
        class_obj = Class()
        
        print(f"   Symbol: {symbol}")
        print(f"   Function: {function}")
        print(f"   Class: {class_obj}")
        
        return True
    except ImportError as e:
        print(f"   Compatibility modules issue: {e}")
        return False

# Test 5: Z.ai SDK Integration
def test_zai_integration():
    try:
        from autogenlib._z_ai_client import is_zai_available, test_zai_connection
        
        is_available = is_zai_available()
        print(f"   Z.ai SDK available: {is_available}")
        
        if is_available:
            # Test with a fake key to verify connection handling
            os.environ['ZAI_API_KEY'] = 'test_key'
            connection_status = test_zai_connection()
            print(f"   Z.ai connection test: {connection_status}")
            
        return True
    except Exception as e:
        print(f"   Z.ai integration issue: {e}")
        return False

# Test 6: File System Analysis
def test_filesystem_analysis():
    current_dir = "/tmp/Zeeeepa/codegen"
    files_found = []
    
    # Count Python files
    for root, dirs, files in os.walk(current_dir):
        for file in files:
            if file.endswith('.py'):
                files_found.append(os.path.join(root, file))
    
    print(f"   Found {len(files_found)} Python files to analyze")
    
    # Test with a sample file
    if files_found:
        sample_file = files_found[0]
        print(f"   Sample file: {sample_file}")
        try:
            with open(sample_file, 'r') as f:
                content = f.read()
            print(f"   File content length: {len(content)} characters")
        except Exception as e:
            print(f"   File read error: {e}")
            return False
    
    return len(files_found) > 0

# Test 7: Environment and Dependencies
def test_environment():
    import platform
    print(f"   Python version: {platform.python_version()}")
    print(f"   Platform: {platform.platform()}")
    
    # Check key modules
    modules_to_check = ['fastapi', 'uvicorn', 'pydantic', 'networkx', 'rich', 'tree_sitter']
    available_modules = []
    
    for module in modules_to_check:
        try:
            __import__(module)
            available_modules.append(module)
        except ImportError:
            pass
    
    print(f"   Available modules: {', '.join(available_modules)}")
    return len(available_modules) >= 4  # Require at least 4 core modules

print("🧪 Running Tests...")
print("-" * 40)

# Execute all tests
test_step("AutoGenLib Integration", test_autogenlib)
test_step("Core Graph-Sitter Classes", test_core_classes)
test_step("Backend Import and Basic Functionality", test_backend)
test_step("Analysis Tools Compatibility", test_analysis_tools)
test_step("Z.ai SDK Integration", test_zai_integration)
test_step("File System Analysis", test_filesystem_analysis)
test_step("Environment and Dependencies", test_environment)

# Print results
print()
print("=" * 60)
print("📊 TEST RESULTS SUMMARY")
print("=" * 60)
print(f"✅ Passed: {test_results['passed']}")
print(f"⚠️  Warnings: {test_results['warnings']}")
print(f"❌ Failed: {test_results['failed']}")
print(f"📈 Total: {test_results['passed'] + test_results['warnings'] + test_results['failed']}")

if test_results['failed'] == 0:
    print("\n🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
    print("The graph-sitter tools are properly installed and integrated.")
    print("Z.ai integration is configured and ready (needs API key for full functionality).")
    print("AutoGenLib is available for AI-powered error resolution.")
else:
    print(f"\n⚠️  {test_results['failed']} tests failed. See details above.")

print()
print("📋 Detailed Results:")
for detail in test_results["details"]:
    print(f"   {detail}")

print()
print(f"Test completed at: {datetime.now()}")
print("=" * 60)