"""
Example demonstrating the use of the reflection tool in MCP.

This example shows how to use the reflection tool to organize thoughts,
identify knowledge gaps, and create a strategic plan.
"""

import json
import sys
from pathlib import Path

# Add the parent directory to the path so we can import the MCP client
sys.path.append(str(Path(__file__).parent.parent.parent))

from mcp.client import MCPClient


def main():
    """Run the reflection example."""
    # Initialize the MCP client
    client = MCPClient()
    
    # Example 1: Basic reflection
    print("\nExample 1: Basic reflection")
    
    context_summary = "Refactoring a large legacy codebase with poor test coverage"
    findings_so_far = """
    - The codebase has over 100,000 lines of code
    - Test coverage is less than 20%
    - There are many circular dependencies
    - Documentation is outdated or missing
    - Several critical bugs have been reported in production
    """
    
    response = client.request("reflection", {
        "context_summary": context_summary,
        "findings_so_far": findings_so_far
    })
    
    if response.get("success"):
        print("Reflection response:")
        print(json.dumps(response.get("data"), indent=2))
    else:
        print(f"Error during reflection: {response.get('error', {}).get('message')}")
    
    # Example 2: Reflection with challenges and focus
    print("\nExample 2: Reflection with challenges and focus")
    
    context_summary = "Implementing a new authentication system"
    findings_so_far = """
    - Current system uses basic username/password
    - Need to support multi-factor authentication
    - Must maintain backward compatibility
    - Several third-party integrations depend on the current system
    """
    current_challenges = """
    - How to handle the transition period?
    - What's the best way to test the new system?
    - How to communicate changes to users?
    """
    reflection_focus = "architecture"
    
    response = client.request("reflection", {
        "context_summary": context_summary,
        "findings_so_far": findings_so_far,
        "current_challenges": current_challenges,
        "reflection_focus": reflection_focus
    })
    
    if response.get("success"):
        print("Reflection response:")
        print(json.dumps(response.get("data"), indent=2))
    else:
        print(f"Error during reflection: {response.get('error', {}).get('message')}")


if __name__ == "__main__":
    main()
