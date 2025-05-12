#!/usr/bin/env python3
"""
Example usage of the codebase_ai module.

This example demonstrates how to use the codebase_ai module to generate
system prompts, context, and tools for AI-powered code analysis and generation.
"""

import logging
import os
import sys

# Add the parent directory to the path so we can import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from codegen_on_oss.analyzers.codebase_ai import CodebaseAI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class SimpleEditable:
    """A simple implementation of the Editable interface for demonstration."""

    def __init__(self, source_code):
        """Initialize with source code."""
        self._source = source_code

    @property
    def extended_source(self):
        """Get the extended source code."""
        return self._source


def main():
    """Run the example."""
    logger.info("Running codebase_ai example")

    # Create a CodebaseAI instance
    codebase_ai = CodebaseAI()

    # Create a simple editable with some Python code
    code = """
def calculate_sum(a, b):
    return a + b

def calculate_product(a, b):
    return a * b
"""
    editable = SimpleEditable(code)

    # Generate a system prompt with the editable as the target
    system_prompt = codebase_ai.generate_system_prompt(editable)
    logger.info("Generated system prompt:")
    print(f"\n{'-' * 80}\n{system_prompt}\n{'-' * 80}\n")

    # Generate context with additional information
    additional_context = {
        "requirements": "The code should handle edge cases and validate inputs.",
        "examples": [
            "calculate_sum(1, 2) should return 3",
            "calculate_product(3, 4) should return 12",
        ],
    }
    context_string = codebase_ai.generate_context(additional_context)
    logger.info("Generated context:")
    print(f"\n{'-' * 80}\n{context_string}\n{'-' * 80}\n")

    # Generate a system prompt with both target and context
    full_prompt = codebase_ai.generate_system_prompt(editable, additional_context)
    logger.info("Generated full prompt:")
    print(f"\n{'-' * 80}\n{full_prompt}\n{'-' * 80}\n")

    # Generate tools
    tools = codebase_ai.generate_tools()
    logger.info(f"Generated {len(tools)} tools")
    for tool in tools:
        print(f"Tool: {tool['function']['name']}")
        print(f"Description: {tool['function']['description']}")
        print()

    logger.info("Example completed successfully")


if __name__ == "__main__":
    main()
