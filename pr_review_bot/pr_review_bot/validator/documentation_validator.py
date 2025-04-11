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
            requirements = self._extract_requirements(doc_files)
            
            # Get PR details
            pr_title = pr.title
            pr_body = pr.body or ""
            pr_files = [f.filename for f in pr.get_files()]
            
            # Get PR diff
            pr_diff = self._get_pr_diff(repo, pr)
            
            # Validate PR against requirements
            validation_results = self._validate_against_requirements(
                requirements=requirements,
                pr_title=pr_title,
                pr_body=pr_body,
                pr_files=pr_files,
                pr_diff=pr_diff
            )
            
            # Add PR details to results
            validation_results["repo_name"] = repo_name
            validation_results["pr_number"] = pr_number
            validation_results["pr_title"] = pr_title
            validation_results["pr_files"] = pr_files
            
            return validation_results
        
        except Exception as e:
            logger.error(f"Error validating PR against documentation requirements: {e}")
            
            return {
                "repo_name": repo_name,
                "pr_number": pr_number,
                "error": str(e),
                "matched_requirements": [],
                "unmatched_requirements": [],
                "issues": [{"message": f"Error validating PR against documentation requirements: {str(e)}"}]
            }
    
    def _extract_requirements(self, doc_files: List[str]) -> List[Dict[str, Any]]:
        """
        Extract requirements from documentation files.
        
        Args:
            doc_files: List of documentation files to extract requirements from
            
        Returns:
            List of requirements
        """
        requirements = []
        
        for file_path in doc_files:
            try:
                # Parse documentation file
                parsed = self.parser.parse_file(file_path)
                
                # Check if parsing was successful
                if "error" in parsed:
                    logger.warning(f"Error parsing documentation file {file_path}: {parsed['error']}")
                    continue
                
                # Add requirements to list
                if "requirements" in parsed:
                    requirements.extend(parsed["requirements"])
            
            except Exception as e:
                logger.error(f"Error extracting requirements from {file_path}: {e}")
        
        return requirements
    
    def _get_pr_diff(self, repo: Repository, pr: PullRequest) -> str:
        """
        Get the diff of a PR.
        
        Args:
            repo: GitHub repository
            pr: GitHub pull request
            
        Returns:
            PR diff as a string
        """
        # Get PR diff
        diff = pr.get_files()
        
        # Combine diffs
        combined_diff = ""
        for file in diff:
            combined_diff += f"diff --git a/{file.filename} b/{file.filename}\n"
            combined_diff += f"--- a/{file.filename}\n"
            combined_diff += f"+++ b/{file.filename}\n"
            combined_diff += file.patch + "\n\n"
        
        return combined_diff
    
    def _validate_against_requirements(
        self,
        requirements: List[Dict[str, Any]],
        pr_title: str,
        pr_body: str,
        pr_files: List[str],
        pr_diff: str
    ) -> Dict[str, Any]:
        """
        Validate PR against requirements.
        
        Args:
            requirements: List of requirements
            pr_title: PR title
            pr_body: PR body
            pr_files: List of PR files
            pr_diff: PR diff
            
        Returns:
            Validation results
        """
        matched_requirements = []
        unmatched_requirements = []
        issues = []
        
        # Combine PR title and body for text search
        pr_text = f"{pr_title}\n{pr_body}".lower()
        
        # Check each requirement
        for req in requirements:
            # Get requirement text and keywords
            req_text = req["text"].lower()
            req_keywords = req.get("keywords", [])
            
            # Check if requirement is mentioned in PR title or body
            mentioned_in_pr = any(keyword.lower() in pr_text for keyword in req_keywords)
            
            # Check if requirement is addressed in code changes
            addressed_in_code = self._is_requirement_addressed_in_code(req, pr_diff)
            
            # If requirement is mentioned in PR or addressed in code, consider it matched
            if mentioned_in_pr or addressed_in_code:
                req_copy = req.copy()
                req_copy["mentioned_in_pr"] = "Yes" if mentioned_in_pr else "No"
                req_copy["addressed_in_code"] = "Yes" if addressed_in_code else "No"
                matched_requirements.append(req_copy)
            else:
                unmatched_requirements.append(req)
        
        # Check if any requirements are unmatched
        if unmatched_requirements:
            issues.append({
                "message": f"{len(unmatched_requirements)} requirements not addressed in the PR",
                "details": [f"- {req['text']}" for req in unmatched_requirements]
            })
        
        return {
            "matched_requirements": matched_requirements,
            "unmatched_requirements": unmatched_requirements,
            "issues": issues
        }
    
    def _is_requirement_addressed_in_code(self, requirement: Dict[str, Any], pr_diff: str) -> bool:
        """
        Check if a requirement is addressed in code changes.
        
        Args:
            requirement: Requirement to check
            pr_diff: PR diff
            
        Returns:
            True if requirement is addressed in code changes, False otherwise
        """
        # Get requirement text and keywords
        req_text = requirement["text"].lower()
        req_keywords = requirement.get("keywords", [])
        
        # Check if any keywords are in the diff
        for keyword in req_keywords:
            if keyword.lower() in pr_diff.lower():
                return True
        
        # Check for related code patterns
        if "api" in req_text and ("api" in pr_diff.lower() or "endpoint" in pr_diff.lower()):
            return True
        
        if "database" in req_text and ("database" in pr_diff.lower() or "db" in pr_diff.lower() or "sql" in pr_diff.lower()):
            return True
        
        if "user interface" in req_text and ("ui" in pr_diff.lower() or "interface" in pr_diff.lower() or "component" in pr_diff.lower()):
            return True
        
        if "performance" in req_text and ("performance" in pr_diff.lower() or "optimize" in pr_diff.lower() or "speed" in pr_diff.lower()):
            return True
        
        if "security" in req_text and ("security" in pr_diff.lower() or "auth" in pr_diff.lower() or "permission" in pr_diff.lower()):
            return True
        
        # Check for code changes related to the requirement
        # This is a simple heuristic and can be improved
        words = re.findall(r'\b\w+\b', req_text)
        significant_words = [word for word in words if len(word) > 3 and word.lower() not in ["must", "should", "shall", "will", "the", "and", "that", "this", "with", "for", "have", "not"]]
        
        for word in significant_words:
            if word.lower() in pr_diff.lower():
                return True
        
        return False
