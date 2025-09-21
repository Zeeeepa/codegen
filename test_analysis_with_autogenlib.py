#!/usr/bin/env python3
"""
Test the analysis files using AutoGenLib's AI-powered error resolution
"""

import os
import sys
import traceback

# Add the tools directory to Python path
sys.path.insert(0, '/tmp/Zeeeepa/codegen/tools')
sys.path.insert(0, '/tmp/Zeeeepa/codegen')

print("=== Testing Graph-Sitter Analysis Files with AutoGenLib ===")

# Test 1: Initialize autogenlib with a description
try:
    import autogenlib
    autogenlib.init("Graph-sitter analysis tools for codebase examination", 
                    enable_exception_handler=True, enable_caching=False)
    
    print("✓ AutoGenLib initialized successfully")
    ai_status = autogenlib.check_ai_availability()
    print(f"✓ AI Status: {ai_status}")
    
except Exception as e:
    print(f"✗ AutoGenLib initialization failed: {e}")
    traceback.print_exc()

# Test 2: Try to import and use graph_sitter_analysis with autogenlib handling
print("\n=== Testing graph_sitter_analysis import ===")
try:
    # This should trigger autogenlib to handle missing dependencies
    import graph_sitter_analysis
    print("✓ graph_sitter_analysis imported successfully!")
    
    # Try to use some analysis functions
    if hasattr(graph_sitter_analysis, 'CodebaseAnalyzer'):
        analyzer = graph_sitter_analysis.CodebaseAnalyzer()
        print(f"✓ CodebaseAnalyzer created: {analyzer}")
    else:
        print("? CodebaseAnalyzer not found, but import succeeded")
        
except Exception as e:
    print(f"✗ graph_sitter_analysis import failed: {e}")
    print("AutoGenLib should handle this error...")
    traceback.print_exc()

# Test 3: Try to import and use graph_sitter_backend
print("\n=== Testing graph_sitter_backend import ===")
try:
    import graph_sitter_backend
    print("✓ graph_sitter_backend imported successfully!")
    
    # Try to create a backend instance
    if hasattr(graph_sitter_backend, 'GraphSitterBackend'):
        backend = graph_sitter_backend.GraphSitterBackend()
        print(f"✓ GraphSitterBackend created: {backend}")
    else:
        print("? GraphSitterBackend not found, but import succeeded")
        
except Exception as e:
    print(f"✗ graph_sitter_backend import failed: {e}")
    print("AutoGenLib should handle this error...")
    traceback.print_exc()

# Test 4: Try direct codebase analysis
print("\n=== Testing direct codebase analysis ===")
try:
    from codegen.exports import Codebase, ProgrammingLanguage
    
    # Create a minimal codebase for testing
    codebase = Codebase()
    print(f"✓ Codebase created: {codebase}")
    
    # Test with current directory
    current_dir = "/tmp/Zeeeepa/codegen"
    print(f"✓ Testing with directory: {current_dir}")
    
except Exception as e:
    print(f"✗ Direct codebase analysis failed: {e}")
    print("AutoGenLib should handle this error...")
    traceback.print_exc()

print("\n=== Test Summary ===")
print("AutoGenLib should have intercepted import errors and provided solutions.")
print("Check above for any AI-generated code or suggestions.")
print("=== End Test ===")