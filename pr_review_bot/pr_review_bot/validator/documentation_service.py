"""
Documentation Validation Service for PR Review Agent.
This module provides a high-level service for validating PR changes against documentation requirements.
"""
import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple

from .documentation_parser import DocumentationParser
from .documentation_validator import DocumentationValidator

logger = logging.getLogger(__name__)

class DocumentationValidationService:
    """
    Service for validating PR changes against documentation requirements.
    
    Coordinates the validation process and provides an easy-to-use interface
    for the PR Review Controller.
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
        
        # Get GitHub token
        self.github_token = config["github"]["token"]
        
        # Get documentation files to validate against
        self.doc_files = config["validation"]["documentation"]["files"]
        
        # Initialize parser and validator
        self.parser = DocumentationParser(repo_path)
        self.validator = DocumentationValidator(self.github_token, repo_path)
    
    def validate_pr(self, repo_name: str, pr_number: int) -> Dict[str, Any]:
        """
        Validate a PR against documentation requirements.
        
        Args:
            repo_name: Repository name (owner/repo)
            pr_number: Pull request number
            
        Returns:
            Validation results
        """
        try:
            logger.info(f"Validating PR #{pr_number} in {repo_name} against documentation requirements")
            
            # Validate PR against documentation requirements
            validation_results = self.validator.validate_pr(repo_name, pr_number, self.doc_files)
            
            # Check if validation passed
            passed = validation_results.get("matched_requirements", []) and not validation_results.get("unmatched_requirements", [])
            validation_results["passed"] = passed
            
            # Log validation results
            if passed:
                logger.info(f"PR #{pr_number} passed documentation validation")
            else:
                logger.warning(f"PR #{pr_number} failed documentation validation")
                logger.warning(f"Unmatched requirements: {len(validation_results.get('unmatched_requirements', []))}")
            
            return validation_results
        
        except Exception as e:
            logger.error(f"Error validating PR against documentation requirements: {e}")
            
            return {
                "passed": False,
                "error": str(e),
                "matched_requirements": [],
                "unmatched_requirements": [],
                "issues": [{"message": f"Error validating PR against documentation requirements: {str(e)}"}]
            }
    
    def generate_validation_report(self, validation_results: Dict[str, Any]) -> str:
        """
        Generate a human-readable validation report.
        
        Args:
            validation_results: Validation results
            
        Returns:
            Validation report as a string
        """
        passed = validation_results.get("passed", False)
        
        report = []
        
        if passed:
            report.append("# ✅ Documentation Validation Passed")
            report.append("PR meets all documentation requirements.")
        else:
            report.append("# ❌ Validation Failed")
            report.append("PR does not meet documentation requirements.")
        
        # Add matched requirements
        matched_requirements = validation_results.get("matched_requirements", [])
        if matched_requirements:
            report.append("\n## Matched Requirements")
            for i, req in enumerate(matched_requirements, 1):
                report.append(f"{i}. {req['text']}")
                report.append(f"   - Source: {req['source']}")
                report.append(f"   - Type: {req['type']}")
                report.append(f"   - Mentioned in PR: {req.get('mentioned_in_pr', 'No')}")
                report.append(f"   - Addressed in code: {req.get('addressed_in_code', 'No')}")
                report.append("")
        
        # Add unmatched requirements
        unmatched_requirements = validation_results.get("unmatched_requirements", [])
        if unmatched_requirements:
            report.append("\n## Unmatched Requirements")
            for i, req in enumerate(unmatched_requirements, 1):
                report.append(f"{i}. {req['text']}")
                report.append(f"   - Source: {req['source']}")
                report.append(f"   - Type: {req['type']}")
                report.append("")
        
        # Add issues
        issues = validation_results.get("issues", [])
        if issues:
            report.append("\n## Issues")
            for i, issue in enumerate(issues, 1):
                report.append(f"{i}. [ERROR] {issue['message']}")
                if "details" in issue:
                    report.append("   Details:")
                    for detail in issue["details"]:
                        report.append(f"   - {detail}")
                report.append("")
        
        return "\n".join(report)
    
    def save_validation_results(self, validation_results: Dict[str, Any], output_dir: str) -> str:
        """
        Save validation results for failed validations.
        
        Args:
            validation_results: Validation results
            output_dir: Directory to save results to
            
        Returns:
            Path to saved results
        """
        try:
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Create filename
            repo_name = validation_results.get("repo_name", "unknown")
            pr_number = validation_results.get("pr_number", "unknown")
            
            repo_slug = repo_name.replace("/", "-")
            filename = f"{repo_slug}-pr-{pr_number}-documentation-validation.json"
            
            # Create file path
            file_path = os.path.join(output_dir, filename)
            
            # Save validation results
            with open(file_path, "w") as f:
                json.dump(validation_results, f, indent=2)
            
            logger.info(f"Saved documentation validation results to {file_path}")
            
            return file_path
        
        except Exception as e:
            logger.error(f"Error saving validation results: {e}")
            return ""
