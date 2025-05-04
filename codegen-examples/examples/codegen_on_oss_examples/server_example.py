"""
Server Example

This script demonstrates how to use the analysis server.
"""

import argparse
import codegen
import json
from typing import Any, Dict

import requests


class CodeAnalysisClient:
    """Client for interacting with the code analysis server."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize a new CodeAnalysisClient.
        
        Args:
            base_url: The base URL of the analysis server
        """
        self.base_url = base_url.rstrip("/")
    
    def analyze_repository(self, repo_url: str) -> Dict[str, Any]:
        """
        Analyze a repository.
        
        Args:
            repo_url: The URL of the repository to analyze
            
        Returns:
            Dict containing the analysis results
        """
        endpoint = f"{self.base_url}/analyze"
        payload = {"repo_url": repo_url}
        
        response = requests.post(endpoint, json=payload)
        response.raise_for_status()
        
        return response.json()
    
    def get_analysis_status(self, analysis_id: str) -> Dict[str, Any]:
        """
        Get the status of an analysis.
        
        Args:
            analysis_id: The ID of the analysis
            
        Returns:
            Dict containing the analysis status
        """
        endpoint = f"{self.base_url}/status/{analysis_id}"
        
        response = requests.get(endpoint)
        response.raise_for_status()
        
        return response.json()
    
    def get_analysis_results(self, analysis_id: str) -> Dict[str, Any]:
        """
        Get the results of an analysis.
        
        Args:
            analysis_id: The ID of the analysis
            
        Returns:
            Dict containing the analysis results
        """
        endpoint = f"{self.base_url}/results/{analysis_id}"
        
        response = requests.get(endpoint)
        response.raise_for_status()
        
        return response.json()


@codegen.function("codegen-on-oss-server-client")
def run(repo_url: str, server_url: str = "http://localhost:8000"):
    """
    Run an analysis using the code analysis server.
    
    This function:
    1. Creates a client for the analysis server
    2. Submits a repository for analysis
    3. Polls for the analysis status
    4. Retrieves and returns the analysis results
    
    Args:
        repo_url: The URL of the repository to analyze
        server_url: The URL of the analysis server
        
    Returns:
        dict: The analysis results
    """
    client = CodeAnalysisClient(server_url)
    
    print(f"Submitting repository {repo_url} for analysis...")
    analysis = client.analyze_repository(repo_url)
    analysis_id = analysis["analysis_id"]
    
    print(f"Analysis ID: {analysis_id}")
    print("Waiting for analysis to complete...")
    
    while True:
        status = client.get_analysis_status(analysis_id)
        if status["status"] == "completed":
            break
        elif status["status"] == "failed":
            raise Exception(f"Analysis failed: {status.get('error', 'Unknown error')}")
        
        print(f"Status: {status['status']}")
        # In a real application, you would add a delay here
    
    print("Analysis complete! Retrieving results...")
    results = client.get_analysis_results(analysis_id)
    
    return results


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Code Analysis Client Example")
    parser.add_argument("--repo", required=True, help="Repository URL to analyze")
    parser.add_argument("--server", default="http://localhost:8000", help="Analysis server URL")
    parser.add_argument("--output", help="Output file for analysis results (JSON)")
    
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    
    results = run(args.repo, args.server)
    
    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to {args.output}")
    else:
        print(json.dumps(results, indent=2))

