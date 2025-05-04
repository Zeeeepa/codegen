#!/usr/bin/env python3
"""
Command-line interface for the codegen-on-oss system.
"""

import argparse
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional

from codegen_on_oss.analysis import CodeAnalyzer
from codegen_on_oss.snapshot import CodebaseSnapshot, PRReviewer, PRTaskManager
from codegen_on_oss.wsl import WSLClient, WSLDeployment, WSLIntegration

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def analyze_command(args):
    """
    Handle the analyze command.
    
    Args:
        args: Command-line arguments
    """
    analyzer = CodeAnalyzer(repo_path=args.repo_path)
    
    if args.summary:
        result = analyzer.get_codebase_summary()
    elif args.complexity:
        result = analyzer.analyze_complexity(file_path=args.file_path)
    elif args.features:
        result = analyzer.analyze_features()
    elif args.integrity:
        result = analyzer.analyze_code_integrity().to_dict()
    else:
        # Default to summary
        result = analyzer.get_codebase_summary()
    
    print(json.dumps(result, indent=2))


def snapshot_command(args):
    """
    Handle the snapshot command.
    
    Args:
        args: Command-line arguments
    """
    snapshot = CodebaseSnapshot(repo_path=args.repo_path, snapshot_dir=args.snapshot_dir)
    
    if args.action == "create":
        result = snapshot.create_snapshot(name=args.name)
    elif args.action == "list":
        result = snapshot.list_snapshots()
    elif args.action == "get":
        result = snapshot.get_snapshot(args.snapshot_id)
    elif args.action == "delete":
        result = snapshot.delete_snapshot(args.snapshot_id)
    elif args.action == "compare":
        result = snapshot.compare_snapshots(args.snapshot_id_1, args.snapshot_id_2)
    else:
        result = {"error": f"Unknown action: {args.action}"}
    
    print(json.dumps(result, indent=2))


def pr_command(args):
    """
    Handle the PR command.
    
    Args:
        args: Command-line arguments
    """
    if args.action == "review":
        reviewer = PRReviewer(
            repo_url=args.repo_url,
            pr_number=args.pr_number,
            snapshot_dir=args.snapshot_dir,
        )
        result = reviewer.review_pr()
    elif args.action == "task":
        task_manager = PRTaskManager(
            repo_url=args.repo_url,
            snapshot_dir=args.snapshot_dir,
        )
        
        if args.task_action == "create":
            result = task_manager.create_pr_task(
                pr_number=args.pr_number,
                task_type=args.task_type,
                task_data=json.loads(args.task_data),
            )
        elif args.task_action == "list":
            result = task_manager.list_pr_tasks(pr_number=args.pr_number)
        elif args.task_action == "get":
            result = task_manager.get_pr_task(args.task_id)
        elif args.task_action == "update":
            result = task_manager.update_pr_task_status(args.task_id, args.status)
        elif args.task_action == "delete":
            result = task_manager.delete_pr_task(args.task_id)
        else:
            result = {"error": f"Unknown task action: {args.task_action}"}
    else:
        result = {"error": f"Unknown action: {args.action}"}
    
    print(json.dumps(result, indent=2))


def wsl_command(args):
    """
    Handle the WSL command.
    
    Args:
        args: Command-line arguments
    """
    if args.action == "client":
        client = WSLClient(base_url=args.server_url, api_key=args.api_key)
        
        if args.client_action == "analyze":
            result = client.analyze_repository(args.repo_path)
        elif args.client_action == "compare":
            result = client.compare_repositories(args.base_repo_path, args.head_repo_path)
        elif args.client_action == "pr":
            result = client.analyze_pr(args.repo_url, args.pr_number)
        elif args.client_action == "status":
            result = client.check_server_status()
        else:
            result = {"error": f"Unknown client action: {args.client_action}"}
    elif args.action == "deploy":
        if args.deploy_action == "local":
            WSLDeployment.deploy_local(host=args.host, port=args.port, api_key=args.api_key)
            return
        elif args.deploy_action == "docker":
            WSLDeployment.deploy_docker(image_name=args.image_name, tag=args.tag)
            return
        elif args.deploy_action == "ctrlplane":
            WSLDeployment.deploy_ctrlplane(name=args.name, region=args.region)
            return
        else:
            result = {"error": f"Unknown deploy action: {args.deploy_action}"}
    elif args.action == "integration":
        if args.integration_action == "hooks":
            WSLIntegration.setup_git_hooks(args.repo_path, args.server_url, args.api_key)
            result = {"status": "success", "message": "Git hooks set up"}
        elif args.integration_action == "actions":
            WSLIntegration.setup_github_actions(args.repo_path, args.server_url, args.api_key)
            result = {"status": "success", "message": "GitHub Actions workflow set up"}
        else:
            result = {"error": f"Unknown integration action: {args.integration_action}"}
    else:
        result = {"error": f"Unknown action: {args.action}"}
    
    print(json.dumps(result, indent=2))


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="Codegen-on-OSS CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a repository")
    analyze_parser.add_argument("--repo-path", required=True, help="Path to the repository")
    analyze_parser.add_argument("--file-path", help="Path to a specific file to analyze")
    analyze_parser.add_argument("--summary", action="store_true", help="Get a summary of the codebase")
    analyze_parser.add_argument("--complexity", action="store_true", help="Analyze code complexity")
    analyze_parser.add_argument("--features", action="store_true", help="Analyze code features")
    analyze_parser.add_argument("--integrity", action="store_true", help="Analyze code integrity")
    analyze_parser.set_defaults(func=analyze_command)
    
    # Snapshot command
    snapshot_parser = subparsers.add_parser("snapshot", help="Manage codebase snapshots")
    snapshot_parser.add_argument("action", choices=["create", "list", "get", "delete", "compare"], help="Action to perform")
    snapshot_parser.add_argument("--repo-path", help="Path to the repository")
    snapshot_parser.add_argument("--snapshot-dir", help="Directory to store snapshots in")
    snapshot_parser.add_argument("--name", help="Name for the snapshot")
    snapshot_parser.add_argument("--snapshot-id", help="ID of the snapshot")
    snapshot_parser.add_argument("--snapshot-id-1", help="ID of the first snapshot for comparison")
    snapshot_parser.add_argument("--snapshot-id-2", help="ID of the second snapshot for comparison")
    snapshot_parser.set_defaults(func=snapshot_command)
    
    # PR command
    pr_parser = subparsers.add_parser("pr", help="Manage pull requests")
    pr_parser.add_argument("action", choices=["review", "task"], help="Action to perform")
    pr_parser.add_argument("--repo-url", help="URL of the repository")
    pr_parser.add_argument("--pr-number", type=int, help="PR number")
    pr_parser.add_argument("--snapshot-dir", help="Directory to store snapshots in")
    
    # PR task subcommand
    pr_task_parser = pr_parser.add_argument_group("task")
    pr_task_parser.add_argument("--task-action", choices=["create", "list", "get", "update", "delete"], help="Task action to perform")
    pr_task_parser.add_argument("--task-type", help="Type of task (e.g., 'review', 'fix', 'test')")
    pr_task_parser.add_argument("--task-data", help="Task-specific data (JSON string)")
    pr_task_parser.add_argument("--task-id", help="ID of the task")
    pr_task_parser.add_argument("--status", help="New status for the task")
    
    pr_parser.set_defaults(func=pr_command)
    
    # WSL command
    wsl_parser = subparsers.add_parser("wsl", help="Manage WSL integration")
    wsl_parser.add_argument("action", choices=["client", "deploy", "integration"], help="Action to perform")
    
    # WSL client subcommand
    wsl_client_parser = wsl_parser.add_argument_group("client")
    wsl_client_parser.add_argument("--client-action", choices=["analyze", "compare", "pr", "status"], help="Client action to perform")
    wsl_client_parser.add_argument("--repo-path", help="Path to the repository")
    wsl_client_parser.add_argument("--base-repo-path", help="Path to the base repository")
    wsl_client_parser.add_argument("--head-repo-path", help="Path to the head repository")
    wsl_client_parser.add_argument("--repo-url", help="URL of the repository")
    wsl_client_parser.add_argument("--pr-number", type=int, help="PR number")
    wsl_client_parser.add_argument("--server-url", default="http://localhost:8000", help="URL of the WSL server")
    wsl_client_parser.add_argument("--api-key", help="API key for authentication")
    
    # WSL deploy subcommand
    wsl_deploy_parser = wsl_parser.add_argument_group("deploy")
    wsl_deploy_parser.add_argument("--deploy-action", choices=["local", "docker", "ctrlplane"], help="Deploy action to perform")
    wsl_deploy_parser.add_argument("--host", default="0.0.0.0", help="Host to bind the server to")
    wsl_deploy_parser.add_argument("--port", type=int, default=8000, help="Port to bind the server to")
    wsl_deploy_parser.add_argument("--api-key", help="API key for authentication")
    wsl_deploy_parser.add_argument("--image-name", default="wsl-server", help="Name of the Docker image")
    wsl_deploy_parser.add_argument("--tag", default="latest", help="Tag for the Docker image")
    wsl_deploy_parser.add_argument("--name", default="wsl-server", help="Name of the deployment")
    wsl_deploy_parser.add_argument("--region", default="us-west-2", help="AWS region for the deployment")
    
    # WSL integration subcommand
    wsl_integration_parser = wsl_parser.add_argument_group("integration")
    wsl_integration_parser.add_argument("--integration-action", choices=["hooks", "actions"], help="Integration action to perform")
    wsl_integration_parser.add_argument("--repo-path", help="Path to the repository")
    wsl_integration_parser.add_argument("--server-url", default="http://localhost:8000", help="URL of the WSL server")
    wsl_integration_parser.add_argument("--api-key", help="API key for authentication")
    
    wsl_parser.set_defaults(func=wsl_command)
    
    args = parser.parse_args()
    
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)
    
    args.func(args)


if __name__ == "__main__":
    main()
