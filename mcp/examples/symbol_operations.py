#!/usr/bin/env python3
"""
Example script demonstrating how to use the MCP client for symbol operations.
"""

import sys
import os
import logging
from typing import List, Dict, Any

# Add the parent directory to the path so we can import the MCP client
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from mcp.client import MCPClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def print_symbols(symbols: List[Dict[str, Any]]) -> None:
    """Print a list of symbols.

    Args:
        symbols (List[Dict[str, Any]]): List of symbols to print.
    """
    for symbol in symbols:
        print(f"- {symbol.get('name')} ({symbol.get('symbol_type')})")


def main() -> None:
    """Run the example."""
    # Initialize the client
    client = MCPClient(host="localhost", port=8000)

    try:
        # Get all symbols in the codebase
        logger.info("Getting all symbols in the codebase...")
        symbols = client.symbols()
        print(f"Found {len(symbols)} symbols:")
        print_symbols(symbols)
        print()

        # Get all functions in the codebase
        logger.info("Getting all functions in the codebase...")
        functions = client.functions()
        print(f"Found {len(functions)} functions:")
        print_symbols(functions)
        print()

        # Get all classes in the codebase
        logger.info("Getting all classes in the codebase...")
        classes = client.classes()
        print(f"Found {len(classes)} classes:")
        print_symbols(classes)
        print()

        # Get a specific symbol
        symbol_name = "ExampleClass"  # Replace with a symbol name in your codebase
        logger.info(f"Getting symbol: {symbol_name}...")
        symbol = client.get_symbol(symbol_name, optional=True)
        if symbol:
            print(f"Found symbol: {symbol.get('name')} ({symbol.get('symbol_type')})")
        else:
            print(f"Symbol {symbol_name} not found.")
        print()

        # Check if a symbol exists
        logger.info(f"Checking if symbol {symbol_name} exists...")
        exists = client.has_symbol(symbol_name)
        print(f"Symbol {symbol_name} exists: {exists}")
        print()

        # Get symbol usages
        if exists:
            logger.info(f"Getting usages of symbol {symbol_name}...")
            usages = client.symbol_usages(symbol_name)
            print(f"Found {len(usages)} usages of {symbol_name}.")
            for usage in usages:
                print(f"- {usage.get('file')}:{usage.get('line')}:{usage.get('column')}")
        print()

        # Rename a symbol (commented out to avoid modifying the codebase)
        # new_name = "NewExampleClass"
        # logger.info(f"Renaming symbol {symbol_name} to {new_name}...")
        # renamed = client.symbol_rename(symbol_name, new_name)
        # print(f"Symbol renamed: {renamed}")
        # print()

        # Move a symbol to another file (commented out to avoid modifying the codebase)
        # target_file = "new_file.py"
        # logger.info(f"Moving symbol {symbol_name} to {target_file}...")
        # moved = client.symbol_move_to_file(symbol_name, target_file)
        # print(f"Symbol moved: {moved}")
        # print()

        # Remove a symbol (commented out to avoid modifying the codebase)
        # logger.info(f"Removing symbol {symbol_name}...")
        # removed = client.symbol_remove(symbol_name)
        # print(f"Symbol removed: {removed}")
        # print()

        logger.info("Example completed successfully.")

    except Exception as e:
        logger.error(f"Error running example: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
