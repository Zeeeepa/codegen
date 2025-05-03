"""
Server Example

This script demonstrates how to use the analysis server.
"""

import argparse
import json
from typing import Any, Dict, Optional

import requests


class CodeAnalysisClient:
    """Client for interacting with the code analysis server."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize a new CodeAnalysisClient.

        Args:
            base_url: Base URL of the analysis server
        """
        self.base_url = base_url

    def analyze_repo(self, repo_url: str) -> Dict[str, Any]:
        """
        Analyze a repository.

        Args:
            repo_url: URL of the repository to analyze

        Returns:
            Analysis results
        """
        response = requests.post(
            f"{self.base_url}/analyze_repo", json={"repo_url": repo_url}
        )
        response.raise_for_status()
        return response.json()

    def analyze_file(self, repo_url: str, file_path: str) -> Dict[str, Any]:
        """
        Analyze a specific file in a repository.

        Args:
            repo_url: URL of the repository
            file_path: Path to the file to analyze

        Returns:
            Analysis results
        """
        response = requests.post(
            f"{self.base_url}/analyze_file",
            json={"repo_url": repo_url, "file_path": file_path},
        )
        response.raise_for_status()
        return response.json()


class CodeAnalysisServer:
    """Server for analyzing code."""

    def __init__(self, host: str = "localhost", port: int = 8000):
        """
        Initialize a new CodeAnalysisServer.

        Args:
            host: Host to run the server on
            port: Port to run the server on
        """
        self.host = host
        self.port = port

    def start(self) -> None:
        """Start the analysis server."""
        from codegen_on_oss.analysis.server import run_server

        run_server(host=self.host, port=self.port)


def analyze_repository(
    repo_url: str, server_url: str = "http://localhost:8000"
) -> None:
    """
    Analyze a repository and print the results.

    Args:
        repo_url: URL of the repository to analyze
        server_url: URL of the analysis server
    """
    client = CodeAnalysisClient(server_url)

    print(f"Analyzing repository: {repo_url}")
    results = client.analyze_repo(repo_url)

    print("\nAnalysis Results:")
    print(json.dumps(results, indent=2))


def analyze_file(
    repo_url: str, file_path: str, server_url: str = "http://localhost:8000"
) -> None:
    """
    Analyze a specific file in a repository and print the results.

    Args:
        repo_url: URL of the repository
        file_path: Path to the file to analyze
        server_url: URL of the analysis server
    """
    client = CodeAnalysisClient(server_url)

    print(f"Analyzing file: {file_path} in repository {repo_url}")
    results = client.analyze_file(repo_url, file_path)

    print("\nAnalysis Results:")
    print(json.dumps(results, indent=2))


def main() -> None:
    """Main function to run the example."""
    parser = argparse.ArgumentParser(description="Code Analysis Server Example")

    parser.add_argument(
        "--start-server", action="store_true", help="Start the analysis server"
    )

    parser.add_argument("--host", default="localhost", help="Host to run the server on")

    parser.add_argument(
        "--port", type=int, default=8000, help="Port to run the server on"
    )

    parser.add_argument("--analyze-repo", help="URL of the repository to analyze")

    parser.add_argument(
        "--analyze-file",
        nargs=2,
        metavar=("REPO_URL", "FILE_PATH"),
        help="Analyze a specific file in a repository",
    )

    parser.add_argument(
        "--server-url",
        default="http://localhost:8000",
        help="URL of the analysis server",
    )

    args = parser.parse_args()

    if args.start_server:
        server = CodeAnalysisServer(args.host, args.port)
        print(f"Starting analysis server on {args.host}:{args.port}")
        server.start()
    elif args.analyze_repo:
        analyze_repository(args.analyze_repo, args.server_url)
    elif args.analyze_file:
        repo_url, file_path = args.analyze_file
        analyze_file(repo_url, file_path, args.server_url)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
