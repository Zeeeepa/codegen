"""
GitHub Package

This package provides GitHub integration for PR analysis.
"""

from .models import PullRequestContext, PRPartContext, FileChange, PRDiff
from .pr_client import GitHubClient

# Export all GitHub components
__all__ = [
    'PullRequestContext',
    'PRPartContext',
    'FileChange',
    'PRDiff',
    'GitHubClient',
]

