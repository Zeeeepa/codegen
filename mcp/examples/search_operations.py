"""
Search Operations Example
This script demonstrates how to use the MCP client to perform search operations.
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
    
    # Search using ripgrep
    print("Searching for 'MCP' using ripgrep...")
    results = client.ripgrep_search("MCP")
    print(f"Found {results.get('total_results', 0)} results")
    
    # Search for files by name
    print("\nSearching for files with 'controller' in the name...")
    file_results = client.search_files_by_name("controller")
    print(f"Found {file_results.get('total_results', 0)} files")
    
    # Semantic search
    print("\nPerforming semantic search for 'handle client requests'...")
    semantic_results = client.semantic_search("handle client requests")
    print(f"Found {semantic_results.get('total_results', 0)} semantic matches")

if __name__ == "__main__":
    main()
