"""
Documentation Validation Service for PR Review Agent.
This module provides a service for validating PRs against documentation requirements.
"""
import os
import logging
from typing import Dict, List, Any, Optional
from github import Github
from .documentation_validator import DocumentationValidator
from ..core.config_manager import ConfigManager
logger = logging.getLogger(__name__)
class DocumentationValidationService:
    """
    Service for validating PRs against documentation requirements.
    
    Provides high-level functionality for validating PRs against documentation
    requirements and generating validation reports.
    """
    
    def __init__(self, config: Dict[str, Any], repo_path: str):
        """
        Initialize the documentation validation service.
        
        Args:
            config: Configuration dictionary
            repo_path: Path to the repository
        """
        self.config = config
        self.repo_path = repo_path
        
        # Get GitHub token from config
        github_token = config["github"]["token"]
        
        # Initialize validator
        self.validator = DocumentationValidator(github_token, repo_path)
        
        # Get documentation files from config
        self.doc_files = config["validation"]["documentation"]["files"]
        self.required = config["validation"]["documentation"]["required"]
    
    def validate_pr(self, repo_name: str, pr_number: int) -> Dict[str, Any]:
        """
        Validate a PR against documentation requirements.
        
        Args:
            repo_name: Repository name (owner/repo)
            pr_number: Pull request number
            
        Returns:
            Validation results
        """
        # Check if documentation validation is enabled
        if not self.config["validation"]["documentation"]["enabled"]:
            logger.info("Documentation validation is disabled")
            return {
                "pr_number": pr_number,
                "repo_name": repo_name,
                "validation_enabled": False,
                "passed": True,
                "message": "Documentation validation is disabled"
            }
        
        # Validate PR against documentation requirements
        validation_results = self.validator.validate_pr(
            repo_name=repo_name,
            pr_number=pr_number,
            doc_files=self.doc_files
        )
        
        # Check if validation failed
        if "error" in validation_results:
            logger.error(f"Error validating PR against documentation: {validation_results['error']}")
            
            # If validation is required, fail the PR
            if self.required:
                return {
                    "pr_number": pr_number,
                    "repo_name": repo_name,
                    "validation_enabled": True,
                    "passed": False,
                    "message": f"Error validating PR against documentation: {validation_results['error']}"
                }
            else:
                # If validation is not required, pass the PR with a warning
                return {
                    "pr_number": pr_number,
                    "repo_name": repo_name,
                    "validation_enabled": True,
                    "passed": True,
                    "message": f"Warning: Error validating PR against documentation: {validation_results['error']}"
                }
        
        # Check if validation passed
        validation_passed = validation_results.get("validation_results", {}).get("passed", False)
        
        # If validation is required and failed, fail the PR
        if self.required and not validation_passed:
            return {
                "pr_number": pr_number,
                "repo_name": repo_name,
                "validation_enabled": True,
                "passed": False,
                "message": "PR does not meet documentation requirements",
                "details": validation_results
            }
        
        # If validation is not required or passed, pass the PR
        return {
            "pr_number": pr_number,
            "repo_name": repo_name,
            "validation_enabled": True,
            "passed": True,
            "message": "PR meets documentation requirements" if validation_passed else "PR does not meet documentation requirements, but validation is not required",
            "details": validation_results
        }
    
    def generate_validation_report(self, validation_results: Dict[str, Any]) -> str:
        """
        Generate a human-readable validation report.
        
        Args:
            validation_results: Validation results
            
        Returns:
            Validation report as a string
        """
        if not validation_results.get("validation_enabled", False):
            return "Documentation validation is disabled."
        
        if "error" in validation_results:
            return f"Error validating PR against documentation: {validation_results['error']}"
        
        details = validation_results.get("details", {})
        validation_results_details = details.get("validation_results", {})
        
        matched_requirements = validation_results_details.get("matched_requirements", [])
        unmatched_requirements = validation_results_details.get("unmatched_requirements", [])
        issues = validation_results_details.get("issues", [])
        
        report = []
        report.append("# Documentation Validation Report\n")
        
        if validation_results.get("passed", False):
            report.append("## ✅ Validation Passed\n")
            report.append(validation_results.get("message", "PR meets documentation requirements."))
        else:
            report.append("## ❌ Validation Failed\n")
            report.append(validation_results.get("message", "PR does not meet documentation requirements."))
        
        report.append("\n## Matched Requirements\n")
        if matched_requirements:
            for i, req in enumerate(matched_requirements, 1):
                requirement = req["requirement"]
                report.append(f"{i}. {requirement['text']}")
                report.append(f"   - Source: {requirement.get('source_file', 'unknown')}")
                report.append(f"   - Type: {requirement.get('type', 'unknown')}")
                report.append(f"   - Mentioned in PR: {'Yes' if req.get('mentioned_in_pr', False) else 'No'}")
                report.append(f"   - Addressed in code: {'Yes' if req.get('addressed_in_code', False) else 'No'}")
                report.append("")
        else:
            report.append("No requirements matched.")
        
        report.append("\n## Unmatched Requirements\n")
        if unmatched_requirements:
            for i, req in enumerate(unmatched_requirements, 1):
                requirement = req["requirement"]
                report.append(f"{i}. {requirement['text']}")
                report.append(f"   - Source: {requirement.get('source_file', 'unknown')}")
                report.append(f"   - Type: {requirement.get('type', 'unknown')}")
                report.append("")
        else:
            report.append("No unmatched requirements.")
        
        report.append("\n## Issues\n")
        if issues:
            for i, issue in enumerate(issues, 1):
                report.append(f"{i}. [{issue.get('type', 'issue').upper()}] {issue.get('message', '')}")
                if "details" in issue:
                    report.append("   Details:")
                    for detail in issue["details"]:
                        report.append(f"   - {detail}")
                report.append("")
        else:
            report.append("No issues found.")
        
        return "\n".join(report)
    
    def save_validation_results(self, validation_results: Dict[str, Any], output_dir: str) -> str:
        """
        Save validation results to a file.
        
        Args:
            validation_results: Validation results
            output_dir: Directory to save the results
            
        Returns:
            Path to the saved file
        """
        import json
        import datetime
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename
        pr_number = validation_results.get("pr_number", "unknown")
        repo_name = validation_results.get("repo_name", "unknown").replace("/", "-")
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        
        filename = f"{repo_name}-pr-{pr_number}-doc-validation-{timestamp}.json"
        filepath = os.path.join(output_dir, filename)
        
        # Save results to file
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(validation_results, f, indent=2)
        
        logger.info(f"Validation results saved to {filepath}")
        
        return filepath