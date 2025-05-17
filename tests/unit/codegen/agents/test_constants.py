"""Tests for the constants module in the agents package."""

import pytest

from codegen.agents.constants import CODEGEN_BASE_API_URL


class TestConstants:
    """Tests for the constants in the agents package."""

    def test_codegen_base_api_url(self):
        """Test the CODEGEN_BASE_API_URL constant."""
        assert CODEGEN_BASE_API_URL == "https://codegen-sh--rest-api.modal.run"
        assert isinstance(CODEGEN_BASE_API_URL, str)

