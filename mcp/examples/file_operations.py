"""
File Operations Example
This script demonstrates how to use the MCP client to perform file operations.
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
    
    # View a file
    file_path = "mcp/client.py"
    print(f"Viewing file '{file_path}'...")
    file_data = client.view_file(file_path)
    print(f"File exists: {file_data.get('exists', False)}")
    print(f"Line count: {file_data.get('line_count', 0)}")
    
    # Create a new file
    new_file_path = "mcp/examples/temp_file.txt"
    print(f"\nCreating file '{new_file_path}'...")
    create_result = client.create_file(new_file_path, "This is a test file.")
    print(f"File creation success: {create_result.get('success', False)}")
    
    # Edit the file
    print(f"\nEditing file '{new_file_path}'...")
    edit_result = client.edit_file(new_file_path, "This is an edited test file.")
    print(f"File edit success: {edit_result.get('success', False)}")
    
    # Rename the file
    renamed_file_path = "mcp/examples/renamed_temp_file.txt"
    print(f"\nRenaming file from '{new_file_path}' to '{renamed_file_path}'...")
    rename_result = client.rename_file(new_file_path, renamed_file_path)
    print(f"File rename success: {rename_result.get('success', False)}")
    
    # Delete the file
    print(f"\nDeleting file '{renamed_file_path}'...")
    delete_result = client.delete_file(renamed_file_path)
    print(f"File deletion success: {delete_result.get('success', False)}")

if __name__ == "__main__":
    main()
