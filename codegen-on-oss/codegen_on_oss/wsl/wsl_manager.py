"""
WSL Manager Module

This module provides a unified interface for WSL-related functionality,
including client, server, deployment, and integration components.
"""

import json
import logging
import os
import traceback
from typing import Any, Dict, Optional

import requests
import uvicorn
from fastapi import FastAPI, HTTPException, Request, status
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
                        if [ "${{{{ github.event_name }}}}" == "pull_request" ]; then
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
                                  'repo_url': '${{{{ github.repository }}}}',
                                  'pr_number': ${{{{ github.event.pull_request.number }}}}
                              }}
                          )
                          
                          result = response.json()
                          print(json.dumps(result, indent=2))
                          
                          # Check for critical issues
                          critical_issues = sum(1 for issue in result.get('integrity', {{}}).get('issues', []) if issue.get('severity') == 'error')
                          
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
                                  'repo_path': '${{{{ github.workspace }}}}'
                              }}
                          )
                          
                          result = response.json()
                          print(json.dumps(result, indent=2))
                          
                          # Check for critical issues
                          critical_issues = sum(1 for issue in result.get('integrity', {{}}).get('issues', []) if issue.get('severity') == 'error')
                          
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
    client_subparsers = client_parser.add_subparsers(
        dest="client_command", help="Client command to run"
    )
    
    # Analyze repository
    analyze_parser = client_subparsers.add_parser("analyze", help="Analyze a repository")
    analyze_parser.add_argument("repo_path", help="Path to the repository to analyze")
    analyze_parser.add_argument(
        "--server-url", 
        default="http://localhost:8000", 
        help="URL of the WSL server"
    )
    analyze_parser.add_argument("--api-key", help="API key for authentication")
    
    # Parse arguments and run the appropriate command
    args = parser.parse_args()
    
    if args.command == "server":
        WSLDeployment.deploy_local(host=args.host, port=args.port, api_key=args.api_key)
    elif args.command == "client" and args.client_command == "analyze":
        client = WSLClient(base_url=args.server_url, api_key=args.api_key)
        results = client.analyze_repository(args.repo_path)
        print(json.dumps(results, indent=2))
    else:
        parser.print_help()
