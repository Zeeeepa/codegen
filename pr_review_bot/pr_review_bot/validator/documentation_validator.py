"""
Documentation Validator for PR Review Agent.
This module provides functionality for validating PR changes against documentation
requirements.
"""
import os
import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from github import Github, PullRequest, Repository
from .documentation_parser import DocumentationParser
logger = logging.getLogger(__name__)
class DocumentationValidator:
    """
    Validator for checking PR changes against documentation requirements.
    
    Validates that PR changes comply with requirements and specifications
    defined in documentation files.
    """
    
    def __init__(self, github_token: str, repo_path: str):
        """
        Initialize the documentation validator.
        
        Args:
            github_token: GitHub API token
            repo_path: Path to the repository
        """
        self.github = Github(github_token)
        self.repo_path = repo_path
        self.parser = DocumentationParser(repo_path)
    
    def validate_pr(self, repo_name: str, pr_number: int, doc_files: List[str]) -> Dict[str, Any]:
        """
        Validate a PR against documentation requirements.
        
        Args:
            repo_name: Repository name (owner/repo)
            pr_number: Pull request number
            doc_files: List of documentation files to validate against
            
        Returns:
            Validation results
        """
        try:
            # Get repository and PR
            repo = self.github.get_repo(repo_name)
            pr = repo.get_pull(pr_number)
            
            # Extract requirements from documentation files
            requirements = self.parser.extract_requirements(doc_files)
            
            # Get PR details
            pr_files = list(pr.get_files())
            pr_diff = pr.get_patch()
            pr_title = pr.title
            pr_body = pr.body or ""
            
            # Validate PR against requirements
            validation_results = self._validate_against_requirements(
                requirements=requirements,
                pr_files=pr_files,
                pr_diff=pr_diff,
                pr_title=pr_title,
                pr_body=pr_body
            )
            
            return {
                "pr_number": pr_number,
                "repo_name": repo_name,
                "documentation_files": doc_files,
                "requirements_count": len(requirements),
                "validation_results": validation_results
            }
        
        except Exception as e:
            logger.error(f"Error validating PR against documentation: {e}")
            return {
                "pr_number": pr_number,
                "repo_name": repo_name,
                "documentation_files": doc_files,
                "error": str(e)
            }
    
    def _validate_against_requirements(
        self,
        requirements: List[Dict[str, Any]],
        pr_files: List[Any],
        pr_diff: str,
        pr_title: str,
        pr_body: str
    ) -> Dict[str, Any]:
        """
        Validate PR changes against extracted requirements.
        
        Args:
            requirements: List of requirements extracted from documentation
            pr_files: List of files changed in the PR
            pr_diff: PR diff content
            pr_title: PR title
            pr_body: PR body
            
        Returns:
            Validation results
        """
        results = {
            "passed": True,
            "matched_requirements": [],
            "unmatched_requirements": [],
            "issues": []
        }
        
        # If no requirements found, consider it passed
        if not requirements:
            results["issues"].append({
                "type": "warning",
                "message": "No requirements found in documentation files"
            })
            return results
        
        # Check each requirement
        for req in requirements:
            req_text = req["text"].lower()
            req_type = req["type"]
            source_file = req.get("source_file", "unknown")
            
            # Check if requirement is mentioned in PR title or body
            mentioned_in_pr = (
                req_text in pr_title.lower() or
                req_text in pr_body.lower()
            )
            
            # Check if requirement is addressed in code changes
            addressed_in_code = False
            
            # Look for keywords in the diff
            keywords = self._extract_keywords(req_text)
            for keyword in keywords:
                if keyword in pr_diff.lower():
                    addressed_in_code = True
                    break
            
            # Determine if requirement is matched
            if mentioned_in_pr or addressed_in_code:
                results["matched_requirements"].append({
                    "requirement": req,
                    "mentioned_in_pr": mentioned_in_pr,
                    "addressed_in_code": addressed_in_code
                })
            else:
                results["unmatched_requirements"].append({
                    "requirement": req
                })
        
        # Determine overall result
        if results["unmatched_requirements"]:
            results["passed"] = False
            results["issues"].append({
                "type": "error",
                "message": f"{len(results['unmatched_requirements'])} requirements not addressed in the PR",
                "details": [req["requirement"]["text"] for req in results["unmatched_requirements"]]
            })
        
        return results
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract keywords from a requirement text.
        
        Args:
            text: Requirement text
            
        Returns:
            List of keywords
        """
        # Remove common words and keep only significant terms
        common_words = {
            "the", "a", "an", "and", "or", "but", "if", "then", "else", "when",
            "at", "from", "to", "in", "on", "by", "for", "with", "about", "against",
            "between", "into", "through", "during", "before", "after", "above", "below",
            "up", "down", "out", "off", "over", "under", "again", "further", "then",
            "once", "here", "there", "all", "any", "both", "each", "few", "more",
            "most", "other", "some", "such", "no", "nor", "not", "only", "own",
            "same", "so", "than", "too", "very", "can", "will", "just", "should",
            "now", "must", "shall", "need", "may", "might", "could", "would"
        }
        
        # Split text into words and filter out common words
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [word for word in words if word not in common_words and len(word) > 2]
        
        return keywords