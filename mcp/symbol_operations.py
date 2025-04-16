"""
Symbol Operations Example
This script demonstrates how to use the MCP client to perform symbol operations.
"""
import sys
import os
import json
from pathlib import Path
# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from mcp.client import MCPClient
def main():
    """Run the example."""
    # Create a client
    client = MCPClient()
    
    # Get all symbols in the codebase
    print("Getting all symbols in the codebase...")
    symbols = client.symbols()
    print(f"Found {len(symbols)} symbols")
    
    # Get all functions in the codebase
    print("\nGetting all functions in the codebase...")
    functions = client.functions()
    print(f"Found {len(functions)} functions")
    
    # Get all classes in the codebase
    print("\nGetting all classes in the codebase...")
    classes = client.classes()
    print(f"Found {len(classes)} classes")
    
    # Get a specific symbol
    symbol_name = "MCPServer"  # Example symbol name
    print(f"\nGetting symbol '{symbol_name}'...")
    try:
        symbol = client.get_symbol(symbol_name)
        print(f"Found symbol: {json.dumps(symbol, indent=2)}")
    except Exception as e:
        print(f"Error getting symbol: {str(e)}")
    
    # Check if a symbol exists
    print(f"\nChecking if symbol '{symbol_name}' exists...")
    exists = client.has_symbol(symbol_name)
    print(f"Symbol exists: {exists}")
    
    # Get all symbols matching a pattern
    pattern = "MCP"
    print(f"\nGetting all symbols matching pattern '{pattern}'...")
    matching_symbols = client.get_symbols(pattern)
    print(f"Found {len(matching_symbols)} matching symbols")
    
    # Get all symbols in a file
    file_path = "mcp/protocol.py"
    print(f"\nGetting all symbols in file '{file_path}'...")
    try:
        file_symbols = client.file_symbols(file_path)
        print(f"Found {len(file_symbols)} symbols in file")
    except Exception as e:
        print(f"Error getting file symbols: {str(e)}")
    
    # Get all functions in a file
    print(f"\nGetting all functions in file '{file_path}'...")
    try:
        file_functions = client.file_functions(file_path)
        print(f"Found {len(file_functions)} functions in file")
    except Exception as e:
        print(f"Error getting file functions: {str(e)}")
    
    # Get all classes in a file
    print(f"\nGetting all classes in file '{file_path}'...")
    try:
        file_classes = client.file_classes(file_path)
        print(f"Found {len(file_classes)} classes in file")
    except Exception as e:
        print(f"Error getting file classes: {str(e)}")
if __name__ == "__main__":
    main()