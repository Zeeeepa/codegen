"""
Tests for the codegen.agents.utils module.
"""

import pytest
from typing import get_type_hints

from codegen.agents.utils import AgentConfig


class TestAgentConfig:
    """Tests for the AgentConfig class."""

    def test_agent_config_type_hints(self):
        """Test that AgentConfig has the expected type hints."""
        type_hints = get_type_hints(AgentConfig)
        
        # Check that the expected fields are present
        assert "keep_first_messages" in type_hints
        assert "max_messages" in type_hints
        
        # Check that the fields have the correct types
        assert type_hints["keep_first_messages"] == int
        assert type_hints["max_messages"] == int

    def test_agent_config_instantiation(self):
        """Test that AgentConfig can be instantiated with valid values."""
        # Create a valid config
        config: AgentConfig = {
            "keep_first_messages": 5,
            "max_messages": 50
        }
        
        # Check that the values are accessible
        assert config["keep_first_messages"] == 5
        assert config["max_messages"] == 50

    def test_agent_config_partial_instantiation(self):
        """Test that AgentConfig can be instantiated with partial values."""
        # Create a partial config (total=False allows this)
        config: AgentConfig = {
            "keep_first_messages": 5
        }
        
        # Check that the value is accessible
        assert config["keep_first_messages"] == 5
        
        # Check that the other field is not present
        assert "max_messages" not in config

    def test_agent_config_with_additional_fields(self):
        """Test that AgentConfig can include additional fields."""
        # TypedDict with total=False allows additional fields
        config: AgentConfig = {
            "keep_first_messages": 5,
            "max_messages": 50,
            "custom_field": "value"  # type: ignore
        }
        
        # Check that all values are accessible
        assert config["keep_first_messages"] == 5
        assert config["max_messages"] == 50
        assert config["custom_field"] == "value"  # type: ignore

