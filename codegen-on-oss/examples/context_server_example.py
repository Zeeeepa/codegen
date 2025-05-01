#!/usr/bin/env python
"""
Example script demonstrating how to use the CodeContextRetrievalServer.
"""

import json
import requests
import sys
import time


def main():
    """
    Main function to demonstrate the CodeContextRetrievalServer.
    """
    # Check if a repository name was provided
    if len(sys.argv) < 2:
        print("Usage: python context_server_example.py <repo_full_name> [commit]")
        sys.exit(1)

    repo_full_name = sys.argv[1]
    commit = sys.argv[2] if len(sys.argv) > 2 else None

    # Server URL
    server_url = "http://localhost:8000"

    print(f"Using CodeContextRetrievalServer at {server_url}")
    print(f"Repository: {repo_full_name}")
    print(f"Commit: {commit or 'latest'}")

    # Check if server is running
    try:
        response = requests.get(server_url)
        if response.status_code != 200:
            print(f"Server returned status code {response.status_code}")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print(f"Could not connect to server at {server_url}")
        print("Make sure the server is running with: cgparse serve")
        sys.exit(1)

    # Analyze repository
    print("\nAnalyzing repository...")
    response = requests.post(
        f"{server_url}/analyze",
        json={
            "repo_full_name": repo_full_name,
            "commit": commit,
        },
    )
    
    if response.status_code != 200:
        print(f"Error analyzing repository: {response.text}")
        sys.exit(1)
        
    analysis_results = response.json()
    print("Analysis complete!")
    print(json.dumps(analysis_results, indent=2))

    # Create a snapshot
    print("\nCreating snapshot...")
    response = requests.post(
        f"{server_url}/snapshot/create",
        json={
            "repo_full_name": repo_full_name,
            "commit": commit,
        },
    )
    
    if response.status_code != 200:
        print(f"Error creating snapshot: {response.text}")
        sys.exit(1)
        
    snapshot_id = response.json()["snapshot_id"]
    print(f"Snapshot created with ID: {snapshot_id}")

    # List snapshots
    print("\nListing snapshots...")
    response = requests.get(
        f"{server_url}/snapshot/list",
        params={"repo_name": repo_full_name},
    )
    
    if response.status_code != 200:
        print(f"Error listing snapshots: {response.text}")
    else:
        snapshots = response.json()["snapshots"]
        print(f"Found {len(snapshots)} snapshots:")
        for snapshot in snapshots:
            print(f"  - {snapshot['snapshot_id']} ({snapshot['last_modified']})")

    # Run an agent
    print("\nRunning agent...")
    response = requests.post(
        f"{server_url}/agent/run",
        json={
            "repo_full_name": repo_full_name,
            "commit": commit,
            "prompt": "Analyze this codebase and summarize its structure.",
            "metadata": {"example": "true"},
        },
    )
    
    if response.status_code != 200:
        print(f"Error running agent: {response.text}")
    else:
        agent_result = response.json()
        print("Agent run complete!")
        if "edited_files" in agent_result:
            print(f"Edited files: {agent_result['edited_files']}")


if __name__ == "__main__":
    main()

