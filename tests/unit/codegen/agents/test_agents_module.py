"""Integration tests for the agents module as a whole."""

from unittest.mock import MagicMock, patch

import pytest

from codegen.agents import Agent, ChatAgent, CodeAgent
from codegen.agents.data import (
    UserMessage,
    SystemMessageData,
    AssistantMessage,
    ToolMessageData,
)
from codegen.agents.tracer import MessageStreamTracer
from codegen.agents.utils import AgentConfig


class TestAgentsModule:
    """Integration tests for the agents module."""

    @pytest.fixture
    def mock_codebase(self):
        """Create a mock codebase."""
        codebase = MagicMock()
        codebase.name = "test-repo"
        return codebase

    def test_module_imports(self):
        """Test that all module imports work correctly."""
        # Verify that the main classes are imported correctly
        assert Agent.__name__ == "Agent"
        assert ChatAgent.__name__ == "ChatAgent"
        assert CodeAgent.__name__ == "CodeAgent"

    def test_agent_creation(self):
        """Test creating an Agent instance."""
        with patch("codegen.agents.agent.ApiClient"), \
             patch("codegen.agents.agent.AgentsApi"), \
             patch("codegen.agents.agent.Configuration"):
            
            # Create an Agent
            agent = Agent(token="test-token", org_id=42)
            
            # Check the agent's properties
            assert agent.token == "test-token"
            assert agent.org_id == 42
            assert agent.current_job is None

    def test_chat_agent_creation(self, mock_codebase):
        """Test creating a ChatAgent instance."""
        with patch("codegen.agents.chat_agent.create_chat_agent"):
            
            # Create a ChatAgent
            agent = ChatAgent(
                codebase=mock_codebase,
                model_provider="anthropic",
                model_name="claude-3-5-sonnet-latest",
                memory=True,
                temperature=0.7
            )
            
            # Check the agent's properties
            assert agent.codebase == mock_codebase

    def test_code_agent_creation(self, mock_codebase):
        """Test creating a CodeAgent instance."""
        with patch("codegen.agents.code_agent.create_codebase_agent"), \
             patch("codegen.agents.code_agent.Client"), \
             patch("codegen.agents.code_agent.find_and_print_langsmith_run_url"):
            
            # Create a CodeAgent
            agent = CodeAgent(
                codebase=mock_codebase,
                model_provider="anthropic",
                model_name="claude-3-7-sonnet-latest",
                memory=True,
                temperature=0.7
            )
            
            # Check the agent's properties
            assert agent.codebase == mock_codebase
            assert agent.model_name == "claude-3-7-sonnet-latest"
            assert isinstance(agent.thread_id, str)

    def test_agent_config(self):
        """Test creating and using an AgentConfig."""
        # Create an AgentConfig
        config = AgentConfig(keep_first_messages=2, max_messages=50)
        
        # Check the config's properties
        assert config["keep_first_messages"] == 2
        assert config["max_messages"] == 50

    def test_message_data_classes(self):
        """Test creating and using message data classes."""
        # Create message instances
        user_message = UserMessage(content="Hello")
        system_message = SystemMessageData(content="You are a helpful assistant")
        assistant_message = AssistantMessage(content="How can I help you?")
        tool_message = ToolMessageData(
            content="Tool result",
            tool_name="search",
            tool_response="Search results",
            tool_id="call_123",
            status="success"
        )
        
        # Check the message properties
        assert user_message.type == "user"
        assert user_message.content == "Hello"
        
        assert system_message.type == "system"
        assert system_message.content == "You are a helpful assistant"
        
        assert assistant_message.type == "assistant"
        assert assistant_message.content == "How can I help you?"
        assert assistant_message.tool_calls == []
        
        assert tool_message.type == "tool"
        assert tool_message.content == "Tool result"
        assert tool_message.tool_name == "search"
        assert tool_message.tool_response == "Search results"
        assert tool_message.tool_id == "call_123"
        assert tool_message.status == "success"

    def test_message_stream_tracer(self):
        """Test creating and using a MessageStreamTracer."""
        # Create a tracer
        tracer = MessageStreamTracer()
        
        # Check the tracer's properties
        assert tracer.traces == []
        assert tracer.logger is None
        
        # Create a mock logger
        mock_logger = MagicMock()
        mock_logger.log = MagicMock()
        
        # Create a tracer with a logger
        tracer_with_logger = MessageStreamTracer(logger=mock_logger)
        
        # Check the tracer's properties
        assert tracer_with_logger.traces == []
        assert tracer_with_logger.logger == mock_logger

