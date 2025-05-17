"""Tests for the langchain agent extension."""

from unittest.mock import MagicMock, patch

import pytest
from langchain.tools import BaseTool
from langchain_core.messages import SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.graph import CompiledGraph

from codegen.agents.utils import AgentConfig
from codegen.extensions.langchain.agent import (
    create_codebase_agent,
    create_chat_agent,
    create_codebase_inspector_agent,
    create_agent_with_tools,
)


class TestLangchainAgentExtension:
    """Tests for the langchain agent extension."""

    @pytest.fixture
    def mock_codebase(self):
        """Create a mock codebase."""
        codebase = MagicMock()
        codebase.name = "test-repo"
        return codebase

    @pytest.fixture
    def mock_llm(self):
        """Create a mock LLM."""
        llm = MagicMock()
        return llm

    @pytest.fixture
    def mock_graph(self):
        """Create a mock graph."""
        graph = MagicMock(spec=CompiledGraph)
        return graph

    def test_create_codebase_agent(self, mock_codebase, mock_llm, mock_graph):
        """Test creating a codebase agent."""
        with patch("codegen.extensions.langchain.agent.LLM", return_value=mock_llm) as mock_llm_class, \
             patch("codegen.extensions.langchain.agent.create_react_agent", return_value=mock_graph) as mock_create_react_agent:
            
            # Create a codebase agent
            agent = create_codebase_agent(
                codebase=mock_codebase,
                model_provider="anthropic",
                model_name="claude-3-7-sonnet-latest",
                memory=True,
                debug=True
            )
            
            # Check that LLM was created with the correct parameters
            mock_llm_class.assert_called_once_with(
                model_provider="anthropic",
                model_name="claude-3-7-sonnet-latest"
            )
            
            # Check that create_react_agent was called with the correct parameters
            mock_create_react_agent.assert_called_once()
            args, kwargs = mock_create_react_agent.call_args
            assert kwargs["model"] == mock_llm
            assert len(kwargs["tools"]) > 0  # Should have some tools
            assert isinstance(kwargs["system_message"], SystemMessage)
            assert isinstance(kwargs["checkpointer"], MemorySaver)
            assert kwargs["debug"] is True
            
            # Check the returned agent
            assert agent == mock_graph

    def test_create_codebase_agent_with_additional_tools(self, mock_codebase, mock_llm, mock_graph):
        """Test creating a codebase agent with additional tools."""
        with patch("codegen.extensions.langchain.agent.LLM", return_value=mock_llm), \
             patch("codegen.extensions.langchain.agent.create_react_agent", return_value=mock_graph):
            
            # Create a mock tool
            mock_tool = MagicMock(spec=BaseTool)
            mock_tool.get_name.return_value = "custom_tool"
            
            # Create a codebase agent with the additional tool
            agent = create_codebase_agent(
                codebase=mock_codebase,
                additional_tools=[mock_tool]
            )
            
            # Check the returned agent
            assert agent == mock_graph

    def test_create_codebase_agent_with_config(self, mock_codebase, mock_llm, mock_graph):
        """Test creating a codebase agent with a config."""
        with patch("codegen.extensions.langchain.agent.LLM", return_value=mock_llm), \
             patch("codegen.extensions.langchain.agent.create_react_agent", return_value=mock_graph) as mock_create_react_agent:
            
            # Create a config
            config = AgentConfig(keep_first_messages=2, max_messages=50)
            
            # Create a codebase agent with the config
            agent = create_codebase_agent(
                codebase=mock_codebase,
                config=config
            )
            
            # Check that create_react_agent was called with the config
            mock_create_react_agent.assert_called_once()
            args, kwargs = mock_create_react_agent.call_args
            assert kwargs["config"] == config
            
            # Check the returned agent
            assert agent == mock_graph

    def test_create_chat_agent(self, mock_codebase, mock_llm, mock_graph):
        """Test creating a chat agent."""
        with patch("codegen.extensions.langchain.agent.LLM", return_value=mock_llm) as mock_llm_class, \
             patch("codegen.extensions.langchain.agent.create_react_agent", return_value=mock_graph) as mock_create_react_agent:
            
            # Create a chat agent
            agent = create_chat_agent(
                codebase=mock_codebase,
                model_provider="anthropic",
                model_name="claude-3-5-sonnet-latest",
                memory=True,
                debug=True
            )
            
            # Check that LLM was created with the correct parameters
            mock_llm_class.assert_called_once_with(
                model_provider="anthropic",
                model_name="claude-3-5-sonnet-latest"
            )
            
            # Check that create_react_agent was called with the correct parameters
            mock_create_react_agent.assert_called_once()
            args, kwargs = mock_create_react_agent.call_args
            assert kwargs["model"] == mock_llm
            assert len(kwargs["tools"]) > 0  # Should have some tools
            assert isinstance(kwargs["system_message"], SystemMessage)
            assert isinstance(kwargs["checkpointer"], MemorySaver)
            assert kwargs["debug"] is True
            
            # Check the returned agent
            assert agent == mock_graph

    def test_create_codebase_inspector_agent(self, mock_codebase, mock_llm, mock_graph):
        """Test creating a codebase inspector agent."""
        with patch("codegen.extensions.langchain.agent.LLM", return_value=mock_llm) as mock_llm_class, \
             patch("codegen.extensions.langchain.agent.create_react_agent", return_value=mock_graph) as mock_create_react_agent:
            
            # Create a codebase inspector agent
            agent = create_codebase_inspector_agent(
                codebase=mock_codebase,
                model_provider="openai",
                model_name="gpt-4o",
                memory=True,
                debug=True
            )
            
            # Check that LLM was created with the correct parameters
            mock_llm_class.assert_called_once_with(
                model_provider="openai",
                model_name="gpt-4o"
            )
            
            # Check that create_react_agent was called with the correct parameters
            mock_create_react_agent.assert_called_once()
            args, kwargs = mock_create_react_agent.call_args
            assert kwargs["model"] == mock_llm
            assert len(kwargs["tools"]) > 0  # Should have some tools
            assert isinstance(kwargs["system_message"], SystemMessage)
            assert isinstance(kwargs["checkpointer"], MemorySaver)
            assert kwargs["debug"] is True
            
            # Check the returned agent
            assert agent == mock_graph

    def test_create_agent_with_tools(self, mock_llm, mock_graph):
        """Test creating an agent with specific tools."""
        with patch("codegen.extensions.langchain.agent.LLM", return_value=mock_llm) as mock_llm_class, \
             patch("codegen.extensions.langchain.agent.create_react_agent", return_value=mock_graph) as mock_create_react_agent:
            
            # Create mock tools
            mock_tool1 = MagicMock(spec=BaseTool)
            mock_tool1.name = "tool1"
            mock_tool2 = MagicMock(spec=BaseTool)
            mock_tool2.name = "tool2"
            
            # Create an agent with the tools
            agent = create_agent_with_tools(
                tools=[mock_tool1, mock_tool2],
                model_provider="openai",
                model_name="gpt-4o",
                memory=True,
                debug=True
            )
            
            # Check that LLM was created with the correct parameters
            mock_llm_class.assert_called_once_with(
                model_provider="openai",
                model_name="gpt-4o"
            )
            
            # Check that create_react_agent was called with the correct parameters
            mock_create_react_agent.assert_called_once()
            args, kwargs = mock_create_react_agent.call_args
            assert kwargs["model"] == mock_llm
            assert len(kwargs["tools"]) == 2
            assert kwargs["tools"][0] == mock_tool1
            assert kwargs["tools"][1] == mock_tool2
            assert isinstance(kwargs["system_message"], SystemMessage)
            assert isinstance(kwargs["checkpointer"], MemorySaver)
            assert kwargs["debug"] is True
            
            # Check the returned agent
            assert agent == mock_graph

