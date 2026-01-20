"""
CI/CD integration module.

Provides templates and utilities for GitHub Actions, GitLab CI, and Jenkins.
"""

from autoqa.ci.generator import CIProvider, CITemplateGenerator

__all__ = [
    "CIProvider",
    "CITemplateGenerator",
]
