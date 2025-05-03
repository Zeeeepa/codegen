"""
Commit Analyzer Module

This module provides functionality for analyzing commits by comparing
the codebase before and after the commit.
"""

import logging
import os
from typing import Dict, List, Optional, Set, Tuple, Any, Union

from codegen import Codebase
from codegen.configs.models.secrets import SecretsConfig

from codegen_on_oss.snapshot.codebase_snapshot import CodebaseSnapshot, SnapshotManager
from codegen_on_oss.analysis.diff_analyzer import DiffAnalyzer

logger = logging.getLogger(__name__)

class CommitAnalyzer:
    """
    A class for analyzing commits by comparing snapshots of the codebase
    before and after the commit.
    """
    
    def __init__(
        self, 
        snapshot_manager: Optional[SnapshotManager] = None,
        github_token: Optional[str] = None
    ):
        """
        Initialize a new CommitAnalyzer.
        
        Args:
            snapshot_manager: Optional SnapshotManager to use for creating and retrieving snapshots
            github_token: Optional GitHub token for accessing private repositories
        """
        self.snapshot_manager = snapshot_manager or SnapshotManager()
        self.github_token = github_token
    
    def analyze_commit(
        self, 
        repo_url: str, 
        base_commit: str, 
        head_commit: str
    ) -> Dict[str, Any]:
        """
        Analyze a commit by comparing the codebase before and after the commit.
        
        Args:
            repo_url: The repository URL or owner/repo string
            base_commit: The base commit SHA (before the changes)
            head_commit: The head commit SHA (after the changes)
            
        Returns:
            A dictionary with analysis results
        """
        # Check if we already have snapshots for these commits
        base_snapshot = self.snapshot_manager.get_snapshot_by_commit(base_commit)
        head_snapshot = self.snapshot_manager.get_snapshot_by_commit(head_commit)
        
        # Create snapshots if they don't exist
        if not base_snapshot:
            logger.info(f"Creating snapshot for base commit {base_commit}")
            base_codebase = self.snapshot_manager.create_codebase_from_repo(
                repo_url, base_commit, self.github_token
            )
            base_snapshot = self.snapshot_manager.create_snapshot(base_codebase, base_commit)
        
        if not head_snapshot:
            logger.info(f"Creating snapshot for head commit {head_commit}")
            head_codebase = self.snapshot_manager.create_codebase_from_repo(
                repo_url, head_commit, self.github_token
            )
            head_snapshot = self.snapshot_manager.create_snapshot(head_codebase, head_commit)
        
        # Analyze the differences between the snapshots
        diff_analyzer = DiffAnalyzer(base_snapshot, head_snapshot)
        
        # Get the analysis results
        summary = diff_analyzer.get_summary()
        high_risk_changes = diff_analyzer.get_high_risk_changes()
        
        # Evaluate the commit quality
        quality_assessment = self._assess_commit_quality(diff_analyzer)
        
        return {
            'summary': summary,
            'high_risk_changes': high_risk_changes,
            'quality_assessment': quality_assessment,
            'base_snapshot_id': base_snapshot.snapshot_id,
            'head_snapshot_id': head_snapshot.snapshot_id
        }
    
    def _assess_commit_quality(self, diff_analyzer: DiffAnalyzer) -> Dict[str, Any]:
        """
        Assess the quality of a commit based on the diff analysis.
        
        Args:
            diff_analyzer: The DiffAnalyzer instance with the analysis results
            
        Returns:
            A dictionary with quality assessment metrics
        """
        summary = diff_analyzer.get_summary()
        high_risk = diff_analyzer.get_high_risk_changes()
        
        # Initialize quality metrics
        quality = {
            'score': 0.0,  # 0.0 to 10.0
            'issues': [],
            'warnings': [],
            'positive_aspects': [],
            'overall_assessment': '',
            'is_properly_implemented': False
        }
        
        # Start with a perfect score and deduct points for issues
        score = 10.0
        
        # Check for high-risk changes
        if high_risk['complexity_increases']:
            num_increases = len(high_risk['complexity_increases'])
            if num_increases > 5:
                score -= 2.0
                quality['issues'].append(f"Significant complexity increases in {num_increases} functions")
            elif num_increases > 0:
                score -= 0.5
                quality['warnings'].append(f"Complexity increases in {num_increases} functions")
        
        if high_risk['core_file_changes']:
            num_core_changes = len(high_risk['core_file_changes'])
            if num_core_changes > 3:
                score -= 1.5
                quality['issues'].append(f"Changes to {num_core_changes} core files with many dependencies")
            elif num_core_changes > 0:
                score -= 0.5
                quality['warnings'].append(f"Changes to {num_core_changes} core files")
        
        if high_risk['interface_changes']:
            num_interface_changes = len(high_risk['interface_changes'])
            if num_interface_changes > 3:
                score -= 1.5
                quality['issues'].append(f"Interface changes to {num_interface_changes} functions")
            elif num_interface_changes > 0:
                score -= 0.5
                quality['warnings'].append(f"Interface changes to {num_interface_changes} functions")
        
        # Check for positive aspects
        if summary['complexity_changes']['decreased'] > summary['complexity_changes']['increased']:
            score += 0.5
            quality['positive_aspects'].append("Overall complexity decreased")
        
        if summary['function_changes']['added'] > 0 and summary['function_changes']['deleted'] == 0:
            score += 0.5
            quality['positive_aspects'].append("Added new functionality without removing existing functions")
        
        # Adjust score based on the size of the commit
        total_changes = (
            summary['file_changes']['added'] + 
            summary['file_changes']['deleted'] + 
            summary['file_changes']['modified']
        )
        
        # Very large commits are often problematic
        if total_changes > 50:
            score -= 1.0
            quality['warnings'].append(f"Very large commit with {total_changes} file changes")
        # Small, focused commits are good
        elif total_changes < 5:
            score += 0.5
            quality['positive_aspects'].append("Small, focused commit")
        
        # Ensure score is within bounds
        score = max(0.0, min(10.0, score))
        quality['score'] = round(score, 1)
        
        # Determine overall assessment
        if score >= 9.0:
            quality['overall_assessment'] = "Excellent"
            quality['is_properly_implemented'] = True
        elif score >= 7.5:
            quality['overall_assessment'] = "Good"
            quality['is_properly_implemented'] = True
        elif score >= 6.0:
            quality['overall_assessment'] = "Satisfactory"
            quality['is_properly_implemented'] = True
        elif score >= 4.0:
            quality['overall_assessment'] = "Needs Improvement"
            quality['is_properly_implemented'] = False
        else:
            quality['overall_assessment'] = "Poor"
            quality['is_properly_implemented'] = False
        
        return quality
    
    def format_analysis_report(self, analysis_results: Dict[str, Any]) -> str:
        """
        Format the analysis results as a human-readable report.
        
        Args:
            analysis_results: The analysis results from analyze_commit
            
        Returns:
            A formatted string with the analysis report
        """
        summary = analysis_results['summary']
        quality = analysis_results['quality_assessment']
        
        report = f"""
Commit Analysis Report
=====================

Quality Score: {quality['score']}/10.0 - {quality['overall_assessment']}
Properly Implemented: {'Yes' if quality['is_properly_implemented'] else 'No'}

Summary:
- Files: {summary['file_changes']['added']} added, {summary['file_changes']['deleted']} deleted, {summary['file_changes']['modified']} modified
- Functions: {summary['function_changes']['added']} added, {summary['function_changes']['deleted']} deleted, {summary['function_changes']['modified']} modified
- Classes: {summary['class_changes']['added']} added, {summary['class_changes']['deleted']} deleted, {summary['class_changes']['modified']} modified
- Complexity: {summary['complexity_changes']['increased']} functions increased, {summary['complexity_changes']['decreased']} decreased
"""
        
        if quality['issues']:
            report += "\nIssues:\n"
            for issue in quality['issues']:
                report += f"- {issue}\n"
        
        if quality['warnings']:
            report += "\nWarnings:\n"
            for warning in quality['warnings']:
                report += f"- {warning}\n"
        
        if quality['positive_aspects']:
            report += "\nPositive Aspects:\n"
            for aspect in quality['positive_aspects']:
                report += f"- {aspect}\n"
        
        # Add high risk changes
        high_risk = analysis_results['high_risk_changes']
        
        if high_risk['complexity_increases']:
            report += "\nSignificant Complexity Increases:\n"
            for item in high_risk['complexity_increases'][:5]:  # Limit to top 5
                report += f"- {item['function']}: {item['original']} → {item['modified']} ({item['delta']:+d}, {item['percent_change']:.1f}%)\n"
            if len(high_risk['complexity_increases']) > 5:
                report += f"  ... and {len(high_risk['complexity_increases']) - 5} more\n"
        
        if high_risk['interface_changes']:
            report += "\nInterface Changes:\n"
            for item in high_risk['interface_changes'][:5]:  # Limit to top 5
                report += f"- {item['function']}: Parameters changed from {item['original_params']} to {item['modified_params']}\n"
            if len(high_risk['interface_changes']) > 5:
                report += f"  ... and {len(high_risk['interface_changes']) - 5} more\n"
        
        # Add conclusion
        if quality['is_properly_implemented']:
            report += "\nConclusion: This commit is properly implemented and has no significant issues.\n"
        else:
            report += "\nConclusion: This commit has issues that should be addressed before merging.\n"
        
        return report
    
    def analyze_pull_request(
        self, 
        repo_url: str, 
        pr_number: int,
        github_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze a pull request by comparing the base and head commits.
        
        Args:
            repo_url: The repository URL or owner/repo string
            pr_number: The pull request number
            github_token: Optional GitHub token for accessing private repositories
            
        Returns:
            A dictionary with analysis results
        """
        from github import Github
        
        # Use the provided token or the instance token
        token = github_token or self.github_token
        if not token:
            raise ValueError("GitHub token is required to analyze pull requests")
        
        # Parse the repo URL to get owner and repo name
        if "/" in repo_url and "github.com" not in repo_url:
            owner, repo_name = repo_url.split("/")
        else:
            # Extract owner/repo from a full GitHub URL
            parts = repo_url.rstrip("/").split("/")
            owner = parts[-2]
            repo_name = parts[-1]
            if repo_name.endswith(".git"):
                repo_name = repo_name[:-4]
        
        # Get the PR details from GitHub
        g = Github(token)
        repo = g.get_repo(f"{owner}/{repo_name}")
        pr = repo.get_pull(pr_number)
        
        # Get the base and head commits
        base_commit = pr.base.sha
        head_commit = pr.head.sha
        
        # Analyze the commits
        return self.analyze_commit(repo_url, base_commit, head_commit)

