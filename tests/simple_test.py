#!/usr/bin/env python3
"""
Simple test script to verify the structure of the visualization files.

This script checks that the visualization files exist and have the expected structure.
"""

import os
import sys

# Define the paths to the visualization files
visualization_manager_path = os.path.join('src', 'codegen', 'visualizations', 'visualization_manager.py')
viz_utils_path = os.path.join('src', 'codegen', 'visualizations', 'viz_utils.py')
enums_path = os.path.join('src', 'codegen', 'visualizations', 'enums.py')
docs_path = os.path.join('docs', 'visualization_features.md')
examples_path = os.path.join('examples', 'enhanced_visualizations.py')

# Check that the files exist
for path in [visualization_manager_path, viz_utils_path, enums_path, docs_path, examples_path]:
    if not os.path.exists(path):
        print(f"Error: {path} does not exist")
        sys.exit(1)
    print(f"Found {path}")

# Check the content of the files
with open(enums_path, 'r') as f:
    enums_content = f.read()
    if 'INHERITANCE' not in enums_content:
        print(f"Error: {enums_path} does not contain INHERITANCE")
        sys.exit(1)
    if 'CALL_GRAPH' not in enums_content:
        print(f"Error: {enums_path} does not contain CALL_GRAPH")
        sys.exit(1)
    if 'DEPENDENCY_GRAPH' not in enums_content:
        print(f"Error: {enums_path} does not contain DEPENDENCY_GRAPH")
        sys.exit(1)
    if 'MODULE_DEPENDENCIES' not in enums_content:
        print(f"Error: {enums_path} does not contain MODULE_DEPENDENCIES")
        sys.exit(1)
    print(f"Verified {enums_path} content")

with open(viz_utils_path, 'r') as f:
    viz_utils_content = f.read()
    if 'create_inheritance_graph' not in viz_utils_content:
        print(f"Error: {viz_utils_path} does not contain create_inheritance_graph")
        sys.exit(1)
    if 'create_call_graph' not in viz_utils_content:
        print(f"Error: {viz_utils_path} does not contain create_call_graph")
        sys.exit(1)
    if 'create_dependency_graph' not in viz_utils_content:
        print(f"Error: {viz_utils_path} does not contain create_dependency_graph")
        sys.exit(1)
    if 'create_module_dependency_graph' not in viz_utils_content:
        print(f"Error: {viz_utils_path} does not contain create_module_dependency_graph")
        sys.exit(1)
    print(f"Verified {viz_utils_path} content")

with open(visualization_manager_path, 'r') as f:
    visualization_manager_content = f.read()
    if 'visualize_inheritance_hierarchy' not in visualization_manager_content:
        print(f"Error: {visualization_manager_path} does not contain visualize_inheritance_hierarchy")
        sys.exit(1)
    if 'visualize_call_graph' not in visualization_manager_content:
        print(f"Error: {visualization_manager_path} does not contain visualize_call_graph")
        sys.exit(1)
    if 'visualize_dependency_graph' not in visualization_manager_content:
        print(f"Error: {visualization_manager_path} does not contain visualize_dependency_graph")
        sys.exit(1)
    if 'visualize_module_dependencies' not in visualization_manager_content:
        print(f"Error: {visualization_manager_path} does not contain visualize_module_dependencies")
        sys.exit(1)
    print(f"Verified {visualization_manager_path} content")

print("All tests passed!")

