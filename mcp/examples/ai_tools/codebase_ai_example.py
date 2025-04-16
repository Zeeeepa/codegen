"""
Example demonstrating the use of the codebase_ai tool in MCP.

This example shows how to use the codebase_ai tool to generate code and analyze existing code.
"""

import json
import sys
from pathlib import Path

# Add the parent directory to the path so we can import the MCP client
sys.path.append(str(Path(__file__).parent.parent.parent))

from mcp.client import MCPClient


def main():
    """Run the codebase_ai example."""
    # Initialize the MCP client
    client = MCPClient()
    
    # Set the API key for AI operations
    # In a real application, you would get this from an environment variable or config file
    api_key = "your-api-key"
    response = client.request("codebase.set_ai_key", {"api_key": api_key})
    if not response.get("success"):
        print(f"Error setting API key: {response.get('error', {}).get('message')}")
        return
    
    print("API key set successfully.")
    
    # Set session options
    response = client.request("codebase.set_session_options", {"max_ai_requests": 20})
    if not response.get("success"):
        print(f"Error setting session options: {response.get('error', {}).get('message')}")
        return
    
    print("Session options set successfully.")
    
    # Example 1: Generate a new function using AI
    print("\nExample 1: Generate a new function")
    prompt = "Create a Python function that validates an email address using regex"
    response = client.request("codebase.ai", {
        "prompt": prompt,
        "model": "gpt-4"  # Optional: specify the model to use
    })
    
    if response.get("success"):
        print("AI response:")
        print(json.dumps(response.get("data"), indent=2))
    else:
        print(f"Error calling AI: {response.get('error', {}).get('message')}")
    
    # Example 2: Analyze existing code with context
    print("\nExample 2: Analyze existing code with context")
    prompt = "Suggest improvements for this function"
    target = {
        "name": "validate_email",
        "type": "function",
        "content": """
def validate_email(email):
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None
"""
    }
    context = {
        "requirements": "Need to handle international domains and ensure security",
        "usage": "This function is used in a user registration form"
    }
    
    response = client.request("codebase.ai", {
        "prompt": prompt,
        "target": target,
        "context": context
    })
    
    if response.get("success"):
        print("AI response:")
        print(json.dumps(response.get("data"), indent=2))
    else:
        print(f"Error calling AI: {response.get('error', {}).get('message')}")
    
    # Get AI client configuration
    print("\nGetting AI client configuration:")
    response = client.request("codebase.ai_client", {})
    if response.get("success"):
        print(json.dumps(response.get("data"), indent=2))
    else:
        print(f"Error getting AI client: {response.get('error', {}).get('message')}")


if __name__ == "__main__":
    main()
