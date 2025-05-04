"""
WSL Manager Module

This module provides a unified interface for WSL-related functionality,
including client, server, deployment, and integration components.
"""

import json
import logging
import os
import subprocess
import tempfile
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import requests
import uvicorn
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field

# Import from existing modules
from codegen_on_oss.analysis.consolidated_analyzer import CodeAnalyzer

logger = logging.getLogger(__name__)


class WSLClient:
    """
    Client for interacting with the WSL2 server for code validation,
    repository comparison, and PR analysis.
    """
    
    def __init__(self, base_url: str = "http://localhost:8000", api_key: Optional[str] = None):
        """
        Initialize the WSL client.
        
        Args:
            base_url: Base URL of the WSL server
            api_key: Optional API key for authentication
        """
        self.base_url = base_url
        self.api_key = api_key or os.environ.get("WSL_API_KEY")
        self.headers = {"Content-Type": "application/json"}
        
        if self.api_key:
            self.headers["X-API-Key"] = self.api_key
    
    def analyze_repository(self, repo_path: str) -> Dict[str, Any]:
        """
        Analyze a repository using the WSL server.
        
        Args:
            repo_path: Path to the repository to analyze
            
        Returns:
            Analysis results from the server
        """
        endpoint = f"{self.base_url}/analyze/repository"
        payload = {"repo_path": repo_path}
        
        try:
            response = requests.post(endpoint, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error analyzing repository: {str(e)}")
            return {"error": str(e)}
    
    def compare_repositories(self, base_repo_path: str, head_repo_path: str) -> Dict[str, Any]:
        """
        Compare two repositories using the WSL server.
        
        Args:
            base_repo_path: Path to the base repository
            head_repo_path: Path to the head repository
            
        Returns:
            Comparison results from the server
        """
        endpoint = f"{self.base_url}/analyze/compare"
        payload = {
            "base_repo_path": base_repo_path,
            "head_repo_path": head_repo_path,
        }
        
        try:
            response = requests.post(endpoint, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error comparing repositories: {str(e)}")
            return {"error": str(e)}
    
    def analyze_pr(self, repo_url: str, pr_number: int) -> Dict[str, Any]:
        """
        Analyze a pull request using the WSL server.
        
        Args:
            repo_url: URL of the repository
            pr_number: PR number to analyze
            
        Returns:
            PR analysis results from the server
        """
        endpoint = f"{self.base_url}/analyze/pr"
        payload = {
            "repo_url": repo_url,
            "pr_number": pr_number,
        }
        
        try:
            response = requests.post(endpoint, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error analyzing PR: {str(e)}")
            return {"error": str(e)}
    
    def check_server_status(self) -> Dict[str, Any]:
        """
        Check the status of the WSL server.
        
        Returns:
            Server status information
        """
        endpoint = f"{self.base_url}/status"
        
        try:
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error checking server status: {str(e)}")
            return {"error": str(e), "status": "offline"}


# Server models
class RepositoryAnalysisRequest(BaseModel):
    """Request model for repository analysis."""
    
    repo_path: str = Field(..., description="Path to the repository to analyze")


class RepositoryComparisonRequest(BaseModel):
    """Request model for repository comparison."""
    
    base_repo_path: str = Field(..., description="Path to the base repository")
    head_repo_path: str = Field(..., description="Path to the head repository")


class PRAnalysisRequest(BaseModel):
    """Request model for PR analysis."""
    
    repo_url: str = Field(..., description="URL of the repository")
    pr_number: int = Field(..., description="PR number to analyze")


class WSLServer:
    """
    FastAPI server for WSL2 code validation, repository comparison, and PR analysis.
    """
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8000, api_key: Optional[str] = None):
        """
        Initialize the WSL server.
        
        Args:
            host: Host to bind the server to
            port: Port to bind the server to
            api_key: Optional API key for authentication
        """
        self.host = host
        self.port = port
        self.api_key = api_key or os.environ.get("WSL_API_KEY")
        
        self.app = FastAPI(
            title="WSL Code Analysis Server",
            description="API for code validation, repository comparison, and PR analysis",
            version="1.0.0",
        )
        
        # Set up CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Set up API key authentication
        if self.api_key:
            self.api_key_header = APIKeyHeader(name="X-API-Key")
            
            @self.app.middleware("http")
            async def authenticate(request: Request, call_next):
                if request.url.path == "/status":
                    return await call_next(request)
                
                api_key = request.headers.get("X-API-Key")
                if api_key != self.api_key:
                    return JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={"detail": "Invalid API key"},
                    )
                
                return await call_next(request)
        
        # Set up routes
        self.setup_routes()
    
    def setup_routes(self):
        """Set up the FastAPI routes."""
        
        @self.app.get("/status")
        async def get_status():
            """Get the server status."""
            return {
                "status": "online",
                "version": "1.0.0",
                "api_key_required": bool(self.api_key),
            }
        
        @self.app.post("/analyze/repository")
        async def analyze_repository(request: RepositoryAnalysisRequest):
            """Analyze a repository."""
            try:
                analyzer = CodeAnalyzer(repo_path=request.repo_path)
                
                results = {
                    "summary": analyzer.get_codebase_summary(),
                    "complexity": analyzer.analyze_complexity(),
                    "features": analyzer.analyze_features(),
                    "integrity": analyzer.analyze_code_integrity().to_dict(),
                }
                
                return results
            except Exception as e:
                logger.error(f"Error analyzing repository: {str(e)}")
                logger.error(traceback.format_exc())
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error analyzing repository: {str(e)}",
                )
        
        @self.app.post("/analyze/compare")
        async def compare_repositories(request: RepositoryComparisonRequest):
            """Compare two repositories."""
            try:
                analyzer = CodeAnalyzer()
                
                results = analyzer.analyze_diff(
                    base_path=request.base_repo_path,
                    head_path=request.head_repo_path,
                )
                
                return results
            except Exception as e:
                logger.error(f"Error comparing repositories: {str(e)}")
                logger.error(traceback.format_exc())
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error comparing repositories: {str(e)}",
                )
        
        @self.app.post("/analyze/pr")
        async def analyze_pr(request: PRAnalysisRequest, background_tasks: BackgroundTasks):
            """Analyze a pull request."""
            try:
                # Clone the repository
                with tempfile.TemporaryDirectory() as temp_dir:
                    repo_dir = os.path.join(temp_dir, "repo")
                    
                    # Clone the repository
                    subprocess.run(
                        ["git", "clone", request.repo_url, repo_dir],
                        check=True,
                        capture_output=True,
                    )
                    
                    # Fetch the PR
                    subprocess.run(
                        ["git", "-C", repo_dir, "fetch", "origin", f"pull/{request.pr_number}/head:pr-{request.pr_number}"],
                        check=True,
                        capture_output=True,
                    )
                    
                    # Get the base branch
                    pr_info = subprocess.run(
                        ["git", "-C", repo_dir, "show", f"pr-{request.pr_number}"],
                        check=True,
                        capture_output=True,
                        text=True,
                    )
                    
                    # Extract the base branch from the PR info
                    base_branch = "main"  # Default to main
                    for line in pr_info.stdout.splitlines():
                        if line.startswith("Merge:"):
                            base_branch = line.split()[1]
                            break
                    
                    # Create temporary directories for base and head
                    base_dir = os.path.join(temp_dir, "base")
                    head_dir = os.path.join(temp_dir, "head")
                    
                    os.makedirs(base_dir)
                    os.makedirs(head_dir)
                    
                    # Copy the base branch to base_dir
                    subprocess.run(
                        ["git", "-C", repo_dir, "checkout", base_branch],
                        check=True,
                        capture_output=True,
                    )
                    
                    subprocess.run(
                        ["cp", "-r", f"{repo_dir}/.", base_dir],
                        check=True,
                        capture_output=True,
                    )
                    
                    # Copy the PR branch to head_dir
                    subprocess.run(
                        ["git", "-C", repo_dir, "checkout", f"pr-{request.pr_number}"],
                        check=True,
                        capture_output=True,
                    )
                    
                    subprocess.run(
                        ["cp", "-r", f"{repo_dir}/.", head_dir],
                        check=True,
                        capture_output=True,
                    )
                    
                    # Analyze the diff
                    analyzer = CodeAnalyzer()
                    
                    results = analyzer.analyze_diff(
                        base_path=base_dir,
                        head_path=head_dir,
                    )
                    
                    return results
            except Exception as e:
                logger.error(f"Error analyzing PR: {str(e)}")
                logger.error(traceback.format_exc())
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error analyzing PR: {str(e)}",
                )
    
    def run(self):
        """Run the FastAPI server."""
        uvicorn.run(self.app, host=self.host, port=self.port)


class WSLDeployment:
    """
    Utility for deploying the WSL server to various environments.
    """
    
    @staticmethod
    def deploy_local(host: str = "0.0.0.0", port: int = 8000, api_key: Optional[str] = None):
        """
        Deploy the WSL server locally.
        
        Args:
            host: Host to bind the server to
            port: Port to bind the server to
            api_key: Optional API key for authentication
        """
        server = WSLServer(host=host, port=port, api_key=api_key)
        server.run()
    
    @staticmethod
    def deploy_docker(image_name: str = "wsl-server", tag: str = "latest"):
        """
        Deploy the WSL server as a Docker container.
        
        Args:
            image_name: Name of the Docker image
            tag: Tag for the Docker image
        """
        # Create a temporary Dockerfile
        with tempfile.NamedTemporaryFile(suffix=".dockerfile") as f:
            f.write(
                b"""
                FROM python:3.9-slim
                
                WORKDIR /app
                
                COPY . /app/
                
                RUN pip install --no-cache-dir -r requirements.txt
                
                EXPOSE 8000
                
                CMD ["python", "-m", "codegen_on_oss.scripts.run_wsl_server"]
                """
            )
            f.flush()
            
            # Build the Docker image
            subprocess.run(
                ["docker", "build", "-f", f.name, "-t", f"{image_name}:{tag}", "."],
                check=True,
            )
        
        logger.info(f"Docker image built: {image_name}:{tag}")
        logger.info(f"Run with: docker run -p 8000:8000 -e WSL_API_KEY=your_key {image_name}:{tag}")
    
    @staticmethod
    def deploy_ctrlplane(name: str = "wsl-server", region: str = "us-west-2"):
        """
        Deploy the WSL server to ctrlplane.
        
        Args:
            name: Name of the deployment
            region: AWS region for the deployment
        """
        try:
            # Check if ctrlplane is installed
            subprocess.run(["ctrlplane", "--version"], check=True, capture_output=True)
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.error("ctrlplane is not installed. Please install it first.")
            return
        
        # Create a temporary deployment file
        with tempfile.NamedTemporaryFile(suffix=".yaml") as f:
            f.write(
                f"""
                name: {name}
                region: {region}
                
                services:
                  - name: wsl-server
                    image: wsl-server:latest
                    ports:
                      - 8000:8000
                    environment:
                      - WSL_API_KEY=${WSL_API_KEY}
                """.encode()
            )
            f.flush()
            
            # Deploy to ctrlplane
            subprocess.run(
                ["ctrlplane", "deploy", "-f", f.name],
                check=True,
            )
        
        logger.info(f"Deployed to ctrlplane: {name} in {region}")


class WSLIntegration:
    """
    Integration utilities for the WSL system.
    """
    
    @staticmethod
    def setup_git_hooks(repo_path: str, server_url: str, api_key: Optional[str] = None):
        """
        Set up Git hooks to automatically analyze code on commit and PR.
        
        Args:
            repo_path: Path to the repository
            server_url: URL of the WSL server
            api_key: Optional API key for authentication
        """
        hooks_dir = os.path.join(repo_path, ".git", "hooks")
        
        # Create pre-commit hook
        pre_commit_path = os.path.join(hooks_dir, "pre-commit")
        with open(pre_commit_path, "w") as f:
            f.write(
                f"""#!/bin/bash
                
                # WSL pre-commit hook
                echo "Running WSL code analysis..."
                
                # Get the current branch
                BRANCH=$(git rev-parse --abbrev-ref HEAD)
                
                # Run the analysis
                curl -X POST "{server_url}/analyze/repository" \\
                    -H "Content-Type: application/json" \\
                    -H "X-API-Key: {api_key or ''}" \\
                    -d '{{"repo_path": "{repo_path}"}}' \\
                    -o /tmp/wsl-analysis.json
                
                # Check for critical issues
                CRITICAL_ISSUES=$(jq '.integrity.issues | map(select(.severity == "error")) | length' /tmp/wsl-analysis.json)
                
                if [ "$CRITICAL_ISSUES" -gt 0 ]; then
                    echo "Error: Found $CRITICAL_ISSUES critical issues. Please fix them before committing."
                    jq '.integrity.issues | map(select(.severity == "error"))' /tmp/wsl-analysis.json
                    exit 1
                fi
                
                echo "WSL analysis completed successfully."
                exit 0
                """
            )
        
        # Make the hook executable
        os.chmod(pre_commit_path, 0o755)
        
        logger.info(f"Git hooks set up in {repo_path}")
    
    @staticmethod
    def setup_github_actions(repo_path: str, server_url: str, api_key: Optional[str] = None):
        """
        Set up GitHub Actions to automatically analyze code on push and PR.
        
        Args:
            repo_path: Path to the repository
            server_url: URL of the WSL server
            api_key: Optional API key for authentication
        """
        actions_dir = os.path.join(repo_path, ".github", "workflows")
        os.makedirs(actions_dir, exist_ok=True)
        
        # Create GitHub Actions workflow
        workflow_path = os.path.join(actions_dir, "wsl-analysis.yml")
        with open(workflow_path, "w") as f:
            f.write(
                f"""name: WSL Code Analysis

                on:
                  push:
                    branches: [ main, master, develop ]
                  pull_request:
                    branches: [ main, master, develop ]
                
                jobs:
                  analyze:
                    runs-on: ubuntu-latest
                    
                    steps:
                    - uses: actions/checkout@v2
                      with:
                        fetch-depth: 0
                    
                    - name: Set up Python
                      uses: actions/setup-python@v2
                      with:
                        python-version: '3.9'
                    
                    - name: Install dependencies
                      run: |
                        python -m pip install --upgrade pip
                        pip install requests
                    
                    - name: Run WSL analysis
                      env:
                        WSL_API_KEY: {api_key or '${{ secrets.WSL_API_KEY }}'}
                      run: |
                        if [ "${{ github.event_name }}" == "pull_request" ]; then
                          # For PR events
                          python -c "
                          import requests
                          import json
                          import os
                          
                          response = requests.post(
                              '{server_url}/analyze/pr',
                              headers={{
                                  'Content-Type': 'application/json',
                                  'X-API-Key': os.environ.get('WSL_API_KEY', '')
                              }},
                              json={{
                                  'repo_url': '${{ github.repository }}',
                                  'pr_number': ${{ github.event.pull_request.number }}
                              }}
                          )
                          
                          result = response.json()
                          print(json.dumps(result, indent=2))
                          
                          # Check for critical issues
                          critical_issues = sum(1 for issue in result.get('integrity', {}).get('issues', []) if issue.get('severity') == 'error')
                          
                          if critical_issues > 0:
                              print(f'Error: Found {{critical_issues}} critical issues.')
                              exit(1)
                          "
                        else
                          # For push events
                          python -c "
                          import requests
                          import json
                          import os
                          
                          response = requests.post(
                              '{server_url}/analyze/repository',
                              headers={{
                                  'Content-Type': 'application/json',
                                  'X-API-Key': os.environ.get('WSL_API_KEY', '')
                              }},
                              json={{
                                  'repo_path': '${{ github.workspace }}'
                              }}
                          )
                          
                          result = response.json()
                          print(json.dumps(result, indent=2))
                          
                          # Check for critical issues
                          critical_issues = sum(1 for issue in result.get('integrity', {}).get('issues', []) if issue.get('severity') == 'error')
                          
                          if critical_issues > 0:
                              print(f'Error: Found {{critical_issues}} critical issues.')
                              exit(1)
                          "
                        fi
                """
            )
        
        logger.info(f"GitHub Actions workflow set up in {repo_path}")


def run_wsl_cli():
    """
    Command-line interface for the WSL system.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="WSL Code Analysis System")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Server command
    server_parser = subparsers.add_parser("server", help="Run the WSL server")
    server_parser.add_argument("--host", default="0.0.0.0", help="Host to bind the server to")
    server_parser.add_argument("--port", type=int, default=8000, help="Port to bind the server to")
    server_parser.add_argument("--api-key", help="API key for authentication")
    
    # Client commands
    client_parser = subparsers.add_parser("client", help="Run WSL client commands")
    client_subparsers = client_parser.add_subparsers(dest="client_command", help="Client command to run")
    
    # Analyze repository
    analyze_parser = client_subparsers.add_parser("analyze", help="Analyze a repository")
    analyze_parser.add_argument("repo_path", help="Path to the repository to analyze")
    analyze_parser.add_argument("--server-url", default="http://localhost:8000", help="URL of the WSL server")
    analyze_parser.add_argument("--api-key", help="API key for authentication")
    
    # Compare repositories
    compare_parser = client_subparsers.add_parser("compare", help="Compare two repositories")
    compare_parser.add_argument("base_repo_path", help="Path to the base repository")
    compare_parser.add_argument("head_repo_path", help="Path to the head repository")
    compare_parser.add_argument("--server-url", default="http://localhost:8000", help="URL of the WSL server")
    compare_parser.add_argument("--api-key", help="API key for authentication")
    
    # Analyze PR
    pr_parser = client_subparsers.add_parser("pr", help="Analyze a pull request")
    pr_parser.add_argument("repo_url", help="URL of the repository")
    pr_parser.add_argument("pr_number", type=int, help="PR number to analyze")
    pr_parser.add_argument("--server-url", default="http://localhost:8000", help="URL of the WSL server")
    pr_parser.add_argument("--api-key", help="API key for authentication")
    
    # Deployment commands
    deploy_parser = subparsers.add_parser("deploy", help="Deploy the WSL server")
    deploy_subparsers = deploy_parser.add_subparsers(dest="deploy_command", help="Deployment command to run")
    
    # Deploy locally
    local_parser = deploy_subparsers.add_parser("local", help="Deploy the WSL server locally")
    local_parser.add_argument("--host", default="0.0.0.0", help="Host to bind the server to")
    local_parser.add_argument("--port", type=int, default=8000, help="Port to bind the server to")
    local_parser.add_argument("--api-key", help="API key for authentication")
    
    # Deploy to Docker
    docker_parser = deploy_subparsers.add_parser("docker", help="Deploy the WSL server to Docker")
    docker_parser.add_argument("--image-name", default="wsl-server", help="Name of the Docker image")
    docker_parser.add_argument("--tag", default="latest", help="Tag for the Docker image")
    
    # Deploy to ctrlplane
    ctrlplane_parser = deploy_subparsers.add_parser("ctrlplane", help="Deploy the WSL server to ctrlplane")
    ctrlplane_parser.add_argument("--name", default="wsl-server", help="Name of the deployment")
    ctrlplane_parser.add_argument("--region", default="us-west-2", help="AWS region for the deployment")
    
    # Integration commands
    integration_parser = subparsers.add_parser("integration", help="Set up integrations")
    integration_subparsers = integration_parser.add_subparsers(dest="integration_command", help="Integration command to run")
    
    # Set up Git hooks
    hooks_parser = integration_subparsers.add_parser("hooks", help="Set up Git hooks")
    hooks_parser.add_argument("repo_path", help="Path to the repository")
    hooks_parser.add_argument("--server-url", default="http://localhost:8000", help="URL of the WSL server")
    hooks_parser.add_argument("--api-key", help="API key for authentication")
    
    # Set up GitHub Actions
    actions_parser = integration_subparsers.add_parser("actions", help="Set up GitHub Actions")
    actions_parser.add_argument("repo_path", help="Path to the repository")
    actions_parser.add_argument("--server-url", default="http://localhost:8000", help="URL of the WSL server")
    actions_parser.add_argument("--api-key", help="API key for authentication")
    
    args = parser.parse_args()
    
    # Handle commands
    if args.command == "server":
        WSLDeployment.deploy_local(host=args.host, port=args.port, api_key=args.api_key)
    elif args.command == "client":
        if args.client_command == "analyze":
            client = WSLClient(base_url=args.server_url, api_key=args.api_key)
            result = client.analyze_repository(args.repo_path)
            print(json.dumps(result, indent=2))
        elif args.client_command == "compare":
            client = WSLClient(base_url=args.server_url, api_key=args.api_key)
            result = client.compare_repositories(args.base_repo_path, args.head_repo_path)
            print(json.dumps(result, indent=2))
        elif args.client_command == "pr":
            client = WSLClient(base_url=args.server_url, api_key=args.api_key)
            result = client.analyze_pr(args.repo_url, args.pr_number)
            print(json.dumps(result, indent=2))
        else:
            parser.print_help()
    elif args.command == "deploy":
        if args.deploy_command == "local":
            WSLDeployment.deploy_local(host=args.host, port=args.port, api_key=args.api_key)
        elif args.deploy_command == "docker":
            WSLDeployment.deploy_docker(image_name=args.image_name, tag=args.tag)
        elif args.deploy_command == "ctrlplane":
            WSLDeployment.deploy_ctrlplane(name=args.name, region=args.region)
        else:
            parser.print_help()
    elif args.command == "integration":
        if args.integration_command == "hooks":
            WSLIntegration.setup_git_hooks(args.repo_path, args.server_url, args.api_key)
        elif args.integration_command == "actions":
            WSLIntegration.setup_github_actions(args.repo_path, args.server_url, args.api_key)
        else:
            parser.print_help()
    else:
        parser.print_help()


if __name__ == "__main__":
    run_wsl_cli()

