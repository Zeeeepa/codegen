"""
Enhanced Analysis Server Example

This script demonstrates how to use the enhanced analysis server for PR validation
and codebase analysis.
"""

import argparse
import json
import logging
import requests
from typing import Dict, List, Optional, Any
from pathlib import Path


class ProjectManager:
    """Manages projects for the enhanced analysis server."""
    
    def __init__(self, server_url: str = "http://localhost:8000"):
        """
        Initialize a new ProjectManager.
        
        Args:
            server_url: URL of the analysis server
        """
        self.server_url = server_url
    
    def register_project(self, project_url: str, project_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Register a project with the analysis server.
        
        Args:
            project_url: URL of the project repository
            project_name: Optional name for the project
            
        Returns:
            A dictionary with the registration result
        """
        if not project_name:
            project_name = project_url.split("/")[-1]
        
        data = {
            "url": project_url,
            "name": project_name
        }
        
        response = requests.post(
            f"{self.server_url}/api/projects/register",
            json=data
        )
        
        return response.json()


class WebhookHandler:
    """Handles webhooks for the enhanced analysis server."""
    
    def __init__(self, server_url: str = "http://localhost:8000"):
        """
        Initialize a new WebhookHandler.
        
        Args:
            server_url: URL of the analysis server
        """
        self.server_url = server_url
    
    def register_webhook(
        self,
        project_id: str,
        webhook_url: str,
        events: List[str]
    ) -> Dict[str, Any]:
        """
        Register a webhook with the analysis server.
        
        Args:
            project_id: ID of the project
            webhook_url: URL to send webhook events to
            events: List of events to trigger the webhook
            
        Returns:
            A dictionary with the registration result
        """
        data = {
            "project_id": project_id,
            "webhook_url": webhook_url,
            "events": events
        }
        
        response = requests.post(
            f"{self.server_url}/api/webhooks/register",
            json=data
        )
        
        return response.json()
    
    def trigger_webhook(
        self,
        project_id: str,
        event: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Trigger a webhook event.
        
        Args:
            project_id: ID of the project
            event: Event type
            payload: Event payload
            
        Returns:
            A dictionary with the trigger result
        """
        data = {
            "project_id": project_id,
            "event": event,
            "payload": payload
        }
        
        response = requests.post(
            f"{self.server_url}/api/webhooks/trigger",
            json=data
        )
        
        return response.json()


class FeatureAnalyzer:
    """Analyzes features in a codebase."""
    
    def __init__(self, server_url: str = "http://localhost:8000"):
        """
        Initialize a new FeatureAnalyzer.
        
        Args:
            server_url: URL of the analysis server
        """
        self.server_url = server_url
    
    def analyze_feature(
        self,
        project_id: str,
        feature_path: str
    ) -> Dict[str, Any]:
        """
        Analyze a feature in a project.
        
        Args:
            project_id: ID of the project
            feature_path: Path to the feature to analyze
            
        Returns:
            A dictionary with the analysis result
        """
        data = {
            "project_id": project_id,
            "feature_path": feature_path
        }
        
        response = requests.post(
            f"{self.server_url}/api/features/analyze",
            json=data
        )
        
        return response.json()
    
    def analyze_function(
        self,
        project_id: str,
        function_name: str
    ) -> Dict[str, Any]:
        """
        Analyze a function in a project.
        
        Args:
            project_id: ID of the project
            function_name: Name of the function to analyze
            
        Returns:
            A dictionary with the analysis result
        """
        data = {
            "project_id": project_id,
            "function_name": function_name
        }
        
        response = requests.post(
            f"{self.server_url}/api/functions/analyze",
            json=data
        )
        
        return response.json()


class PRValidator:
    """Validates pull requests."""
    
    def __init__(self, server_url: str = "http://localhost:8000"):
        """
        Initialize a new PRValidator.
        
        Args:
            server_url: URL of the analysis server
        """
        self.server_url = server_url
    
    def validate_pr(
        self,
        project_id: str,
        pr_number: int
    ) -> Dict[str, Any]:
        """
        Validate a pull request.
        
        Args:
            project_id: ID of the project
            pr_number: Number of the pull request
            
        Returns:
            A dictionary with the validation result
        """
        data = {
            "project_id": project_id,
            "pr_number": pr_number
        }
        
        response = requests.post(
            f"{self.server_url}/api/prs/validate",
            json=data
        )
        
        return response.json()


def main():
    """Main function to run the example."""
    parser = argparse.ArgumentParser(description="Enhanced Analysis Server Example")
    
    parser.add_argument(
        "--start-server",
        action="store_true",
        help="Start the enhanced analysis server"
    )
    
    parser.add_argument(
        "--register-project",
        type=str,
        help="Register a project with the server"
    )
    
    parser.add_argument(
        "--project-name",
        type=str,
        help="Name for the project"
    )
    
    parser.add_argument(
        "--pr-validation",
        type=str,
        help="Repository URL for PR validation"
    )
    
    parser.add_argument(
        "--pr-number",
        type=int,
        help="PR number for validation"
    )
    
    parser.add_argument(
        "--analyze-feature",
        type=str,
        help="Repository URL for feature analysis"
    )
    
    parser.add_argument(
        "--feature-path",
        type=str,
        help="Path to the feature to analyze"
    )
    
    args = parser.parse_args()
    
    if args.start_server:
        print("Starting enhanced analysis server...")
        # Import here to avoid circular imports
        from codegen_on_oss.analysis.server import run_server
        run_server()
    
    if args.register_project:
        print(f"Registering project: {args.register_project}")
        project_manager = ProjectManager()
        result = project_manager.register_project(
            args.register_project,
            args.project_name
        )
        print(json.dumps(result, indent=2))
    
    if args.pr_validation and args.pr_number:
        print(f"Validating PR #{args.pr_number} for {args.pr_validation}")
        # First register the project if not already registered
        project_manager = ProjectManager()
        project_result = project_manager.register_project(args.pr_validation)
        
        # Then validate the PR
        pr_validator = PRValidator()
        result = pr_validator.validate_pr(
            project_result["project_id"],
            args.pr_number
        )
        print(json.dumps(result, indent=2))
    
    if args.analyze_feature and args.feature_path:
        print(f"Analyzing feature: {args.feature_path} in {args.analyze_feature}")
        # First register the project if not already registered
        project_manager = ProjectManager()
        project_result = project_manager.register_project(args.analyze_feature)
        
        # Then analyze the feature
        feature_analyzer = FeatureAnalyzer()
        result = feature_analyzer.analyze_feature(
            project_result["project_id"],
            args.feature_path
        )
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
