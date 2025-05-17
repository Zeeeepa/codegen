"""Unit tests for the CLI API endpoints."""

from unittest.mock import patch

import pytest

from codegen.cli.api.endpoints import (
    CREATE_ENDPOINT,
    DEPLOY_ENDPOINT,
    DOCS_ENDPOINT,
    EXPERT_ENDPOINT,
    IDENTIFY_ENDPOINT,
    IMPROVE_ENDPOINT,
    LOOKUP_ENDPOINT,
    PR_LOOKUP_ENDPOINT,
    RUN_ENDPOINT,
    RUN_ON_PR_ENDPOINT,
    CODEGEN_SYSTEM_PROMPT_URL,
)
from codegen.cli.api.modal import MODAL_PREFIX
from codegen.cli.env.enums import Environment


class TestEndpoints:
    """Tests for the CLI API endpoints."""

    def test_endpoints_format(self):
        """Test that endpoints have the correct format."""
        # All endpoints should start with https:// and include the MODAL_PREFIX
        endpoints = [
            RUN_ENDPOINT,
            DOCS_ENDPOINT,
            EXPERT_ENDPOINT,
            IDENTIFY_ENDPOINT,
            CREATE_ENDPOINT,
            DEPLOY_ENDPOINT,
            LOOKUP_ENDPOINT,
            RUN_ON_PR_ENDPOINT,
            PR_LOOKUP_ENDPOINT,
            IMPROVE_ENDPOINT,
        ]

        for endpoint in endpoints:
            assert endpoint.startswith(f"https://{MODAL_PREFIX}--")
            assert endpoint.endswith(".modal.run")

    def test_system_prompt_url(self):
        """Test that the system prompt URL is valid."""
        assert CODEGEN_SYSTEM_PROMPT_URL.startswith("https://gist.githubusercontent.com/")

    @patch("codegen.cli.api.modal.global_env")
    def test_modal_prefix_production(self, mock_global_env):
        """Test that the MODAL_PREFIX is correct in production."""
        # Set up the mock
        mock_global_env.ENV = Environment.PRODUCTION
        mock_global_env.MODAL_ENVIRONMENT = None

        # Import the module again to recalculate MODAL_PREFIX
        from importlib import reload
        from codegen.cli.api import modal as modal_module

        reload(modal_module)

        # Check the result
        assert modal_module.MODAL_PREFIX == "codegen-sh"

    @patch("codegen.cli.api.modal.global_env")
    def test_modal_prefix_staging(self, mock_global_env):
        """Test that the MODAL_PREFIX is correct in staging."""
        # Set up the mock
        mock_global_env.ENV = Environment.STAGING
        mock_global_env.MODAL_ENVIRONMENT = None

        # Import the module again to recalculate MODAL_PREFIX
        from importlib import reload
        from codegen.cli.api import modal as modal_module

        reload(modal_module)

        # Check the result
        assert modal_module.MODAL_PREFIX == "codegen-sh-staging"

    @patch("codegen.cli.api.modal.global_env")
    def test_modal_prefix_develop(self, mock_global_env):
        """Test that the MODAL_PREFIX is correct in develop."""
        # Set up the mock
        mock_global_env.ENV = Environment.DEVELOP
        mock_global_env.MODAL_ENVIRONMENT = None

        # Import the module again to recalculate MODAL_PREFIX
        from importlib import reload
        from codegen.cli.api import modal as modal_module

        reload(modal_module)

        # Check the result
        assert modal_module.MODAL_PREFIX == "codegen-sh-develop"

    @patch("codegen.cli.api.modal.global_env")
    def test_modal_prefix_develop_with_environment(self, mock_global_env):
        """Test that the MODAL_PREFIX is correct in develop with a custom environment."""
        # Set up the mock
        mock_global_env.ENV = Environment.DEVELOP
        mock_global_env.MODAL_ENVIRONMENT = "test"

        # Import the module again to recalculate MODAL_PREFIX
        from importlib import reload
        from codegen.cli.api import modal as modal_module

        reload(modal_module)

        # Check the result
        assert modal_module.MODAL_PREFIX == "codegen-sh-develop-test"

    @patch("codegen.cli.api.modal.global_env")
    def test_modal_prefix_invalid_environment(self, mock_global_env):
        """Test that an invalid environment raises an error."""
        # Set up the mock
        mock_global_env.ENV = "invalid"
        mock_global_env.MODAL_ENVIRONMENT = None

        # Import the module again to recalculate MODAL_PREFIX
        from importlib import reload
        from codegen.cli.api import modal as modal_module

        # Check that an error is raised
        with pytest.raises(ValueError, match="Invalid environment: invalid"):
            reload(modal_module)

