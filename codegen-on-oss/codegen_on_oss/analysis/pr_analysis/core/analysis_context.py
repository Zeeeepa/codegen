"""
Analysis context for PR analysis.

This module provides the AnalysisContext class, which holds the context for PR analysis.
"""

import logging
from typing import Dict, Any

from codegen_on_oss.analysis.pr_analysis.git.models import Repository, PullRequest

logger = logging.getLogger(__name__)


class AnalysisContext:
    """
    Context for PR analysis.

    This class holds the context for PR analysis, including repository and PR information.

    Attributes:
        repository: Repository object
        pull_request: Pull request object
        config: Analysis configuration
        data: Additional data
    """

    def __init__(
        self, repository: Repository, pull_request: PullRequest, config: Dict[str, Any]
    ):
        """
        Initialize the analysis context.

        Args:
            repository: Repository object
            pull_request: Pull request object
            config: Analysis configuration
        """
        self.repository = repository
        self.pull_request = pull_request
        self.config = config
        self.data = {}

    def set_data(self, key: str, value: Any) -> None:
        """
        Set a data value.

        Args:
            key: Data key
            value: Data value
        """
        self.data[key] = value

    def get_data(self, key: str, default: Any = None) -> Any:
        """
        Get a data value.

        Args:
            key: Data key
            default: Default value if key is not found

        Returns:
            Data value or default
        """
        return self.data.get(key, default)

    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            key: Configuration key
            default: Default value if key is not found

        Returns:
            Configuration value or default
        """
        return self.config.get(key, default)

