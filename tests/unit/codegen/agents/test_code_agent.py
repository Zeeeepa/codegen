"""Tests for the CodeAgent class in the agents module."""

from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest
from langchain.tools import BaseTool
from langchain_core.messages import AIMessage, HumanMessage
from langsmith import Client

from codegen.agents.code_agent import CodeAgent
from codegen.agents.loggers import ExternalLogger
from codegen.agents.utils import AgentConfig


class TestCodeAgent:
    """Tests for the CodeAgent class."""

    @pytest.fixture
    def mock_codebase(self):
        """Create a mock codebase."""
        codebase = MagicMock()
        codebase.name = "test-repo"
        return codebase

    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent."""
        agent = MagicMock()
        
        # Mock the stream method to return a generator
        def mock_stream(*args, **kwargs):
            yield {
                "messages": [AIMessage(content="I'll help you with that code")],
                "final_answer": "I've analyzed the code and made improvements."
            }
        agent.stream = mock_stream
        
        # Mock the get_state method
        agent.get_state = MagicMock(return_value={
            "messages": [
                HumanMessage(content="Help me with this code"),
                AIMessage(content="I'll help you with that code")
            ]
        })
        
        # Mock the get_graph method
        mock_graph = MagicMock()
        mock_node = MagicMock()
        mock_tool = MagicMock(spec=BaseTool)
        mock_node.data.tools_by_name = {"tool1": mock_tool}
        mock_graph.nodes = {"tools": mock_node}
        agent.get_graph = MagicMock(return_value=mock_graph)
        
        return agent

    @pytest.fixture
    def mock_langsmith_client(self):
        """Create a mock LangSmith client."""
        client = MagicMock(spec=Client)
        return client

    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger."""
        logger = MagicMock(spec=ExternalLogger)
        return logger

    @pytest.fixture
    def code_agent(self, mock_codebase, mock_agent, mock_langsmith_client):
        """Create a CodeAgent instance with mocked dependencies."""
        with patch("codegen.agents.code_agent.create_codebase_agent", return_value=mock_agent), \
             patch("codegen.agents.code_agent.Client", return_value=mock_langsmith_client), \
             patch("codegen.agents.code_agent.find_and_print_langsmith_run_url"):
            agent = CodeAgent(codebase=mock_codebase)
            return agent

    def test_init(self, code_agent, mock_codebase, mock_agent, mock_langsmith_client):
        """Test initialization of CodeAgent."""
        assert code_agent.codebase == mock_codebase
        assert code_agent.agent == mock_agent
        assert code_agent.langsmith_client == mock_langsmith_client
        assert code_agent.model_name == "claude-3-7-sonnet-latest"  # Default model
        assert isinstance(code_agent.thread_id, str)
        # Verify thread_id is a valid UUID
        UUID(code_agent.thread_id)
        assert code_agent.project_name == "RELACE"  # Default project name
        assert code_agent.run_id is None
        assert code_agent.instance_id is None
        assert code_agent.difficulty is None
        assert code_agent.logger is None
        assert code_agent.tags == ["claude-3-7-sonnet-latest"]  # Default model as tag
        assert code_agent.metadata == {
            "project": "RELACE",
            "model": "claude-3-7-sonnet-latest"
        }

    def test_init_with_custom_parameters(self, mock_codebase):
        """Test initialization with custom parameters."""
        with patch("codegen.agents.code_agent.create_codebase_agent") as mock_create_agent, \
             patch("codegen.agents.code_agent.Client"), \
             patch("codegen.agents.code_agent.find_and_print_langsmith_run_url"):
            
            # Create a mock tool
            mock_tool = MagicMock(spec=BaseTool)
            
            # Create a mock logger
            mock_logger = MagicMock(spec=ExternalLogger)
            
            # Create a mock config
            mock_config = AgentConfig(keep_first_messages=2, max_messages=50)
            
            # Create a CodeAgent with custom parameters
            agent = CodeAgent(
                codebase=mock_codebase,
                model_provider="openai",
                model_name="gpt-4",
                memory=False,
                tools=[mock_tool],
                tags=["test-tag"],
                metadata={"run_id": "run_123", "instance_id": "instance_456", "difficulty": "difficulty_3"},
                agent_config=mock_config,
                thread_id="custom_thread_id",
                logger=mock_logger,
                temperature=0.7
            )
            
            # Check that create_codebase_agent was called with the correct parameters
            mock_create_agent.assert_called_once()
            args, kwargs = mock_create_agent.call_args
            assert kwargs["model_provider"] == "openai"
            assert kwargs["model_name"] == "gpt-4"
            assert kwargs["memory"] == False
            assert kwargs["additional_tools"] == [mock_tool]
            assert kwargs["config"] == mock_config
            assert kwargs["temperature"] == 0.7
            
            # Check the agent's properties
            assert agent.model_name == "gpt-4"
            assert agent.thread_id == "custom_thread_id"
            assert agent.tags == ["test-tag", "gpt-4"]
            assert agent.run_id == "run_123"
            assert agent.instance_id == "instance_456"
            assert agent.difficulty == 3  # Extracted from "difficulty_3"
            assert agent.logger == mock_logger
            assert agent.metadata == {
                "project": "RELACE",
                "model": "gpt-4",
                "run_id": "run_123",
                "instance_id": "instance_456",
                "difficulty": "difficulty_3"
            }

    def test_run(self, code_agent, mock_agent):
        """Test the run method."""
        # Run the agent
        response = code_agent.run("Analyze this code")
        
        # Check that the agent's stream method was called
        mock_agent.stream.assert_called_once()
        
        # Check the response
        assert response == "I've analyzed the code and made improvements."

    def test_run_with_images(self, code_agent, mock_agent):
        """Test the run method with images."""
        # Run the agent with images
        image_urls = ["data:image/png;base64,abc123", "data:image/jpeg;base64,def456"]
        response = code_agent.run("Analyze this code and images", image_urls=image_urls)
        
        # Check that the agent's stream method was called with the correct content
        mock_agent.stream.assert_called_once()
        call_args = mock_agent.stream.call_args
        messages = call_args[0][0]["messages"]
        assert len(messages) == 1
        assert isinstance(messages[0], HumanMessage)
        
        # Check the content of the message
        content = messages[0].content
        assert len(content) == 3  # Text + 2 images
        assert content[0]["type"] == "text"
        assert content[0]["text"] == "Analyze this code and images"
        assert content[1]["type"] == "image_url"
        assert content[1]["image_url"]["url"] == "data:image/png;base64,abc123"
        assert content[2]["type"] == "image_url"
        assert content[2]["image_url"]["url"] == "data:image/jpeg;base64,def456"
        
        # Check the response
        assert response == "I've analyzed the code and made improvements."

    def test_get_agent_trace_url(self, code_agent):
        """Test the get_agent_trace_url method."""
        with patch("codegen.agents.code_agent.find_and_print_langsmith_run_url", return_value="https://smith.langchain.com/runs/123"):
            # Get the agent trace URL
            url = code_agent.get_agent_trace_url()
            
            # Check the URL
            assert url == "https://smith.langchain.com/runs/123"

    def test_get_agent_trace_url_exception(self, code_agent):
        """Test the get_agent_trace_url method when an exception occurs."""
        with patch("codegen.agents.code_agent.find_and_print_langsmith_run_url", side_effect=Exception("Error")):
            # Get the agent trace URL
            url = code_agent.get_agent_trace_url()
            
            # Check that the method returns None when an exception occurs
            assert url is None

    def test_get_tools(self, code_agent, mock_agent):
        """Test the get_tools method."""
        # Get the tools
        tools = code_agent.get_tools()
        
        # Check that the agent's get_graph method was called
        mock_agent.get_graph.assert_called_once()
        
        # Check the tools
        assert len(tools) == 1
        assert tools[0] == mock_agent.get_graph().nodes["tools"].data.tools_by_name["tool1"]

    def test_get_state(self, code_agent, mock_agent):
        """Test the get_state method."""
        # Get the state
        state = code_agent.get_state()
        
        # Check that the agent's get_state method was called with the correct config
        mock_agent.get_state.assert_called_once()
        call_args = mock_agent.get_state.call_args
        assert call_args[0][0] == code_agent.config
        
        # Check the state
        assert state == {
            "messages": [
                HumanMessage(content="Help me with this code"),
                AIMessage(content="I'll help you with that code")
            ]
        }

    def test_get_tags_metadata(self, code_agent):
        """Test the get_tags_metadata method."""
        # Get the tags and metadata
        tags, metadata = code_agent.get_tags_metadata()
        
        # Check the tags
        assert tags == ["claude-3-7-sonnet-latest"]
        
        # Check the metadata
        assert metadata == {
            "project": "RELACE",
            "model": "claude-3-7-sonnet-latest"
        }

    def test_get_tags_metadata_with_swebench_info(self, mock_codebase, mock_agent, mock_langsmith_client):
        """Test the get_tags_metadata method with SWEBench information."""
        with patch("codegen.agents.code_agent.create_codebase_agent", return_value=mock_agent), \
             patch("codegen.agents.code_agent.Client", return_value=mock_langsmith_client), \
             patch("codegen.agents.code_agent.find_and_print_langsmith_run_url"):
            
            # Create a CodeAgent with SWEBench information
            agent = CodeAgent(
                codebase=mock_codebase,
                metadata={
                    "run_id": "run_123",
                    "instance_id": "instance_456",
                    "difficulty": "difficulty_3"
                }
            )
            
            # Get the tags and metadata
            tags, metadata = agent.get_tags_metadata()
            
            # Check the tags
            assert "claude-3-7-sonnet-latest" in tags
            assert "run_123" in tags
            assert "instance_456" in tags
            assert "difficulty_3" in tags
            
            # Check the metadata
            assert metadata["project"] == "RELACE"
            assert metadata["model"] == "claude-3-7-sonnet-latest"
            assert metadata["swebench_run_id"] == "run_123"
            assert metadata["swebench_instance_id"] == "instance_456"
            assert metadata["swebench_difficulty"] == 3

