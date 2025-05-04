#!/usr/bin/env python3
"""
WSL2 Server CLI

This script provides a command-line interface for deploying, managing,
and interacting with the WSL2 server for code validation.

Example usage:
    # Deploy the server
    python -m codegen_on_oss.scripts.wsl_server_cli deploy

    # Check server status
    python -m codegen_on_oss.scripts.wsl_server_cli status

    # Stop the server
    python -m codegen_on_oss.scripts.wsl_server_cli stop

    # Validate a codebase
    python -m codegen_on_oss.scripts.wsl_server_cli validate --repo https://github.com/user/repo

    # Compare repositories
    python -m codegen_on_oss.scripts.wsl_server_cli compare --base-repo https://github.com/user/repo1 --head-repo https://github.com/user/repo2

    # Analyze a PR
    python -m codegen_on_oss.scripts.wsl_server_cli analyze-pr --repo https://github.com/user/repo --pr-number 123
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

from codegen_on_oss.analysis.wsl_client import WSLClient
from codegen_on_oss.analysis.wsl_deployment import WSLDeployment

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def deploy_command(args):
    """
    Deploy the WSL2 server.

    Args:
        args: Command-line arguments
    """
    deployment = WSLDeployment(
        wsl_distro=args.distro,
        port=args.port,
        api_key=args.api_key,
        use_docker=args.docker,
        use_ctrlplane=args.ctrlplane,
        log_level=args.log_level,
        timeout=args.timeout,
    )

    # Check if WSL is installed
    if not deployment.check_wsl_installed():
        logger.error("WSL is not installed. Please install WSL first.")
        sys.exit(1)

    # Check if the specified distribution is installed
    if not deployment.check_distro_installed():
        logger.error(f"WSL distribution '{args.distro}' is not installed.")
        logger.info("Please install it using: wsl --install -d Ubuntu")
        sys.exit(1)

    # Install dependencies
    logger.info("Installing dependencies...")
    if not deployment.install_dependencies():
        logger.error("Failed to install dependencies.")
        sys.exit(1)

    # Deploy server
    logger.info("Deploying server...")
    if not deployment.deploy_server():
        logger.error("Failed to deploy server.")
        sys.exit(1)

    logger.info(f"Server deployed successfully on port {args.port}.")
    logger.info(f"You can access the server at: http://localhost:{args.port}")


def stop_command(args):
    """
    Stop the WSL2 server.

    Args:
        args: Command-line arguments
    """
    deployment = WSLDeployment(
        wsl_distro=args.distro,
        port=args.port,
        api_key=args.api_key,
        use_docker=args.docker,
        use_ctrlplane=args.ctrlplane,
    )

    # Stop server
    logger.info("Stopping server...")
    if not deployment.stop_server():
        logger.error("Failed to stop server.")
        sys.exit(1)

    logger.info("Server stopped successfully.")


def status_command(args):
    """
    Check the status of the WSL2 server.

    Args:
        args: Command-line arguments
    """
    deployment = WSLDeployment(
        wsl_distro=args.distro,
        port=args.port,
        api_key=args.api_key,
        use_docker=args.docker,
        use_ctrlplane=args.ctrlplane,
    )

    # Get server status
    status = deployment.get_server_status()

    # Print status
    print("\nWSL2 Server Status:")
    print(f"Deployment Type: {status['deployment_type']}")
    print(f"WSL Distribution: {status['wsl_distro']}")
    print(f"Port: {status['port']}")
    print(f"Status: {status['status']}")
    print(f"Uptime: {status['uptime']}")

    # Print logs if requested
    if args.logs:
        print("\nServer Logs:")
        print(status["logs"])

    # Also check server health if it's running
    if status["status"] == "running":
        try:
            client = WSLClient(
                base_url=f"http://localhost:{args.port}",
                api_key=args.api_key,
                timeout=args.timeout,
            )
            health = client.health_check()
            print("\nServer Health:")
            for key, value in health.items():
                print(f"{key}: {value}")
        except Exception as e:
            print(f"\nFailed to check server health: {str(e)}")


def validate_command(args):
    """
    Validate a codebase.

    Args:
        args: Command-line arguments
    """
    client = WSLClient(
        base_url=args.server,
        api_key=args.api_key,
        timeout=args.timeout,
    )

    # Check server health
    try:
        health = client.health_check()
        logger.info(f"Server health: {health['status']}")
    except Exception as e:
        logger.error(f"Failed to connect to server: {str(e)}")
        sys.exit(1)

    # Validate codebase
    logger.info(f"Validating codebase: {args.repo_url}")
    try:
        results = client.validate_codebase(
            repo_url=args.repo_url,
            branch=args.branch,
            categories=args.categories.split(",") if args.categories else None,
            github_token=args.github_token,
            include_metrics=args.include_metrics,
            timeout=args.timeout,
        )

        # Format results
        if args.format == "json":
            output = json.dumps(results, indent=2)
        elif args.format == "markdown":
            output = client.format_validation_results_markdown(results)
        else:
            output = str(results)

        # Save results to file if specified
        if args.output:
            client.save_results_to_file(results, args.output)
            logger.info(f"Results saved to: {args.output}")

        # Save markdown to file if specified
        if args.markdown:
            client.save_markdown_to_file(
                client.format_validation_results_markdown(results),
                args.markdown,
            )
            logger.info(f"Markdown report saved to: {args.markdown}")

        # Print results
        print(output)

    except Exception as e:
        logger.error(f"Failed to validate codebase: {str(e)}")
        sys.exit(1)


def compare_command(args):
    """
    Compare two repositories or branches.

    Args:
        args: Command-line arguments
    """
    client = WSLClient(
        base_url=args.server,
        api_key=args.api_key,
        timeout=args.timeout,
    )

    # Check server health
    try:
        health = client.health_check()
        logger.info(f"Server health: {health['status']}")
    except Exception as e:
        logger.error(f"Failed to connect to server: {str(e)}")
        sys.exit(1)

    # Compare repositories
    logger.info(f"Comparing repositories: {args.base_repo_url} vs {args.head_repo_url}")
    try:
        results = client.compare_repositories(
            base_repo_url=args.base_repo_url,
            head_repo_url=args.head_repo_url,
            base_branch=args.base_branch,
            head_branch=args.head_branch,
            github_token=args.github_token,
            include_detailed_diff=args.include_detailed_diff,
            diff_file_paths=args.diff_file_paths.split(",") if args.diff_file_paths else None,
            timeout=args.timeout,
        )

        # Format results
        if args.format == "json":
            output = json.dumps(results, indent=2)
        elif args.format == "markdown":
            output = client.format_comparison_results_markdown(results)
        else:
            output = str(results)

        # Save results to file if specified
        if args.output:
            client.save_results_to_file(results, args.output)
            logger.info(f"Results saved to: {args.output}")

        # Save markdown to file if specified
        if args.markdown:
            client.save_markdown_to_file(
                client.format_comparison_results_markdown(results),
                args.markdown,
            )
            logger.info(f"Markdown report saved to: {args.markdown}")

        # Print results
        print(output)

    except Exception as e:
        logger.error(f"Failed to compare repositories: {str(e)}")
        sys.exit(1)


def analyze_pr_command(args):
    """
    Analyze a pull request.

    Args:
        args: Command-line arguments
    """
    client = WSLClient(
        base_url=args.server,
        api_key=args.api_key,
        timeout=args.timeout,
    )

    # Check server health
    try:
        health = client.health_check()
        logger.info(f"Server health: {health['status']}")
    except Exception as e:
        logger.error(f"Failed to connect to server: {str(e)}")
        sys.exit(1)

    # Analyze pull request
    logger.info(f"Analyzing pull request: {args.repo_url}#{args.pr_number}")
    try:
        results = client.analyze_pr(
            repo_url=args.repo_url,
            pr_number=args.pr_number,
            github_token=args.github_token,
            detailed=args.detailed,
            post_comment=args.post_comment,
            include_diff_analysis=args.include_diff_analysis,
            timeout=args.timeout,
        )

        # Format results
        if args.format == "json":
            output = json.dumps(results, indent=2)
        elif args.format == "markdown":
            output = client.format_pr_analysis_markdown(results)
        else:
            output = str(results)

        # Save results to file if specified
        if args.output:
            client.save_results_to_file(results, args.output)
            logger.info(f"Results saved to: {args.output}")

        # Save markdown to file if specified
        if args.markdown:
            client.save_markdown_to_file(
                client.format_pr_analysis_markdown(results),
                args.markdown,
            )
            logger.info(f"Markdown report saved to: {args.markdown}")

        # Print results
        print(output)

    except Exception as e:
        logger.error(f"Failed to analyze pull request: {str(e)}")
        sys.exit(1)


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="WSL2 Command-Line Interface for Code Validation",
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Deploy command
    deploy_parser = subparsers.add_parser("deploy", help="Deploy the WSL2 server")
    deploy_parser.add_argument(
        "--distro",
        default="Ubuntu",
        help="WSL distribution to use",
    )
    deploy_parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to expose the server on",
    )
    deploy_parser.add_argument(
        "--api-key",
        help="API key for authentication",
    )
    deploy_parser.add_argument(
        "--docker",
        action="store_true",
        help="Use Docker for deployment",
    )
    deploy_parser.add_argument(
        "--ctrlplane",
        action="store_true",
        help="Use ctrlplane for orchestration",
    )
    deploy_parser.add_argument(
        "--log-level",
        choices=["debug", "info", "warning", "error"],
        default="info",
        help="Log level for the server",
    )
    deploy_parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Command execution timeout in seconds",
    )
    deploy_parser.set_defaults(func=deploy_command)

    # Stop command
    stop_parser = subparsers.add_parser("stop", help="Stop the WSL2 server")
    stop_parser.add_argument(
        "--distro",
        default="Ubuntu",
        help="WSL distribution to use",
    )
    stop_parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port the server is running on",
    )
    stop_parser.add_argument(
        "--api-key",
        help="API key for authentication",
    )
    stop_parser.add_argument(
        "--docker",
        action="store_true",
        help="Server was deployed using Docker",
    )
    stop_parser.add_argument(
        "--ctrlplane",
        action="store_true",
        help="Server was deployed using ctrlplane",
    )
    stop_parser.set_defaults(func=stop_command)

    # Status command
    status_parser = subparsers.add_parser("status", help="Check the status of the WSL2 server")
    status_parser.add_argument(
        "--distro",
        default="Ubuntu",
        help="WSL distribution to use",
    )
    status_parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port the server is running on",
    )
    status_parser.add_argument(
        "--api-key",
        help="API key for authentication",
    )
    status_parser.add_argument(
        "--docker",
        action="store_true",
        help="Server was deployed using Docker",
    )
    status_parser.add_argument(
        "--ctrlplane",
        action="store_true",
        help="Server was deployed using ctrlplane",
    )
    status_parser.add_argument(
        "--logs",
        action="store_true",
        help="Show server logs",
    )
    status_parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="Request timeout in seconds",
    )
    status_parser.set_defaults(func=status_command)

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate a codebase")
    validate_parser.add_argument(
        "repo_url",
        help="URL of the repository to validate",
    )
    validate_parser.add_argument(
        "--branch",
        default="main",
        help="Branch to validate",
    )
    validate_parser.add_argument(
        "--categories",
        help="Comma-separated list of categories to validate",
    )
    validate_parser.add_argument(
        "--github-token",
        help="GitHub token for authentication",
    )
    validate_parser.add_argument(
        "--include-metrics",
        action="store_true",
        help="Include detailed metrics in the response",
    )
    validate_parser.add_argument(
        "--server",
        default="http://localhost:8000",
        help="URL of the WSL2 server",
    )
    validate_parser.add_argument(
        "--api-key",
        help="API key for authentication",
    )
    validate_parser.add_argument(
        "--format",
        choices=["json", "markdown", "text"],
        default="text",
        help="Output format",
    )
    validate_parser.add_argument(
        "--output",
        help="Output file to save results to (JSON)",
    )
    validate_parser.add_argument(
        "--markdown",
        help="Output file to save markdown report to",
    )
    validate_parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Request timeout in seconds",
    )
    validate_parser.set_defaults(func=validate_command)

    # Compare command
    compare_parser = subparsers.add_parser("compare", help="Compare two repositories or branches")
    compare_parser.add_argument(
        "base_repo_url",
        help="URL of the base repository",
    )
    compare_parser.add_argument(
        "head_repo_url",
        help="URL of the head repository",
    )
    compare_parser.add_argument(
        "--base-branch",
        default="main",
        help="Base branch",
    )
    compare_parser.add_argument(
        "--head-branch",
        default="main",
        help="Head branch",
    )
    compare_parser.add_argument(
        "--github-token",
        help="GitHub token for authentication",
    )
    compare_parser.add_argument(
        "--include-detailed-diff",
        action="store_true",
        help="Include detailed diffs in the response",
    )
    compare_parser.add_argument(
        "--diff-file-paths",
        help="Comma-separated list of file paths to include in the detailed diff",
    )
    compare_parser.add_argument(
        "--server",
        default="http://localhost:8000",
        help="URL of the WSL2 server",
    )
    compare_parser.add_argument(
        "--api-key",
        help="API key for authentication",
    )
    compare_parser.add_argument(
        "--format",
        choices=["json", "markdown", "text"],
        default="text",
        help="Output format",
    )
    compare_parser.add_argument(
        "--output",
        help="Output file to save results to (JSON)",
    )
    compare_parser.add_argument(
        "--markdown",
        help="Output file to save markdown report to",
    )
    compare_parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Request timeout in seconds",
    )
    compare_parser.set_defaults(func=compare_command)

    # Analyze PR command
    analyze_pr_parser = subparsers.add_parser("analyze-pr", help="Analyze a pull request")
    analyze_pr_parser.add_argument(
        "repo_url",
        help="URL of the repository",
    )
    analyze_pr_parser.add_argument(
        "pr_number",
        type=int,
        help="PR number to analyze",
    )
    analyze_pr_parser.add_argument(
        "--github-token",
        help="GitHub token for authentication",
    )
    analyze_pr_parser.add_argument(
        "--detailed",
        action="store_true",
        default=True,
        help="Perform detailed analysis",
    )
    analyze_pr_parser.add_argument(
        "--post-comment",
        action="store_true",
        help="Post a comment with the analysis results",
    )
    analyze_pr_parser.add_argument(
        "--include-diff-analysis",
        action="store_true",
        help="Include diff analysis in the response",
    )
    analyze_pr_parser.add_argument(
        "--server",
        default="http://localhost:8000",
        help="URL of the WSL2 server",
    )
    analyze_pr_parser.add_argument(
        "--api-key",
        help="API key for authentication",
    )
    analyze_pr_parser.add_argument(
        "--format",
        choices=["json", "markdown", "text"],
        default="text",
        help="Output format",
    )
    analyze_pr_parser.add_argument(
        "--output",
        help="Output file to save results to (JSON)",
    )
    analyze_pr_parser.add_argument(
        "--markdown",
        help="Output file to save markdown report to",
    )
    analyze_pr_parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Request timeout in seconds",
    )
    analyze_pr_parser.set_defaults(func=analyze_pr_command)

    # Parse arguments
    args = parser.parse_args()

    # Run command
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

