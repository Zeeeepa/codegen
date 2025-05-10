"""
WSL2 Command-Line Interface

This module provides a command-line interface for deploying the WSL2 server
and interacting with it for code validation, repository comparison, and PR analysis.
"""

import argparse
import json
import logging
import sys

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


def validate_command(args):
    """
    Validate a codebase.

    Args:
        args: Command-line arguments
    """
    client = WSLClient(
        base_url=args.server,
        api_key=args.api_key,
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
        help="Output file to save results to",
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
        help="Output file to save results to",
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
        help="Output file to save results to",
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
