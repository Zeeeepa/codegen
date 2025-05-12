#!/usr/bin/env python3
"""
Visualization Examples

This script demonstrates how to use the visualization capabilities of the codegen-on-oss
package to generate various visualizations of code structure and analysis.
"""

import os
import sys
import logging

# Add the parent directory to the path to import the package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from codegen_on_oss.analyzers.visualization.codebase_visualizer import CodebaseVisualizer
from codegen_on_oss.analyzers.visualization.visualizer import VisualizationConfig, OutputFormat

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def main():
    """
    Main function to demonstrate visualization capabilities.
    """
    # Create a visualization config
    config = VisualizationConfig(
        output_format=OutputFormat.PNG,
        output_directory="visualization_output",
        max_depth=5,
        ignore_external=True,
        ignore_tests=True,
    )

    # Create a visualizer
    visualizer = CodebaseVisualizer(config=config)

    # Example 1: Call Graph from Node
    logger.info("Generating call graph from node visualization...")
    result = visualizer.visualize_call_graph_from_node(
        function_name="main",  # Replace with an actual function name in your codebase
        max_depth=3,
        graph_external_modules=False,
    )
    logger.info(f"Call graph visualization saved to: {result}")

    # Example 2: Call Graph Filter
    logger.info("Generating filtered call graph visualization...")
    result = visualizer.visualize_call_graph_filter(
        class_name="CodebaseVisualizer",  # Replace with an actual class name in your codebase
        method_filters=["visualize", "visualize_call_graph", "visualize_dead_code"],
        skip_test_files=True,
        max_depth=3,
    )
    logger.info(f"Filtered call graph visualization saved to: {result}")

    # Example 3: Call Paths Between Nodes
    logger.info("Generating call paths visualization...")
    result = visualizer.visualize_call_paths_between_nodes(
        start_func_name="main",  # Replace with an actual function name in your codebase
        end_func_name="visualize",  # Replace with an actual function name in your codebase
        max_depth=5,
    )
    logger.info(f"Call paths visualization saved to: {result}")

    # Example 4: Dead Code Graph
    logger.info("Generating dead code visualization...")
    result = visualizer.visualize_dead_code_graph(
        skip_test_files=True,
        skip_decorated=True,
    )
    logger.info(f"Dead code visualization saved to: {result}")


if __name__ == "__main__":
    main()

