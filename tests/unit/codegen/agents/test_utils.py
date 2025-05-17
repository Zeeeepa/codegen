"""Tests for the utils module in the agents package."""

import pytest

from codegen.agents.utils import AgentConfig


class TestAgentConfig:
    """Tests for the AgentConfig TypedDict."""

    def test_agent_config_creation(self):
        """Test creating an AgentConfig instance."""
        # Create a minimal AgentConfig
        config = AgentConfig(keep_first_messages=1, max_messages=100)
        
        # Check the values
        assert config["keep_first_messages"] == 1
        assert config["max_messages"] == 100

    def test_agent_config_with_partial_fields(self):
        """Test creating an AgentConfig with only some fields."""
        # Create a config with only keep_first_messages
        config = AgentConfig(keep_first_messages=2)
        
        # Check the value
        assert config["keep_first_messages"] == 2
        
        # Check that max_messages is not present
        with pytest.raises(KeyError):
            config["max_messages"]

    def test_agent_config_with_additional_fields(self):
        """Test that AgentConfig can include additional fields."""
        # Create a config with an additional field
        config = AgentConfig(keep_first_messages=1, max_messages=100, custom_field="value")
        
        # Check the values
        assert config["keep_first_messages"] == 1
        assert config["max_messages"] == 100
        assert config["custom_field"] == "value"

    def test_agent_config_usage_in_function(self):
        """Test using AgentConfig as a function parameter type hint."""
        # Define a function that takes an AgentConfig
        def process_config(config: AgentConfig) -> int:
            return config.get("max_messages", 0)
        
        # Create a config
        config = AgentConfig(keep_first_messages=1, max_messages=50)
        
        # Use the function
        result = process_config(config)
        
        # Check the result
        assert result == 50
        
        # Test with a config missing the field
        config = AgentConfig(keep_first_messages=1)
        result = process_config(config)
        assert result == 0

