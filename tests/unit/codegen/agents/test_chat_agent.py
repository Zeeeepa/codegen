"""Tests for the ChatAgent class in the agents module."""

from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage

from codegen.agents.chat_agent import ChatAgent


class TestChatAgent:
    """Tests for the ChatAgent class."""

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
                "messages": [AIMessage(content="Hello, I'm an AI assistant")],
                "final_answer": "Hello, I'm an AI assistant"
            }
        agent.stream = mock_stream
        return agent

    @pytest.fixture
    def chat_agent(self, mock_codebase, mock_agent):
        """Create a ChatAgent instance with mocked dependencies."""
        with patch("codegen.agents.chat_agent.create_chat_agent", return_value=mock_agent):
            agent = ChatAgent(codebase=mock_codebase)
            return agent

    def test_init(self, chat_agent, mock_codebase, mock_agent):
        """Test initialization of ChatAgent."""
        assert chat_agent.codebase == mock_codebase
        assert chat_agent.agent == mock_agent

    def test_init_with_custom_parameters(self, mock_codebase):
        """Test initialization with custom parameters."""
        with patch("codegen.agents.chat_agent.create_chat_agent") as mock_create_agent:
            # Create a ChatAgent with custom parameters
            ChatAgent(
                codebase=mock_codebase,
                model_provider="openai",
                model_name="gpt-4",
                memory=False,
                tools=[MagicMock()],
                temperature=0.7
            )
            
            # Check that create_chat_agent was called with the correct parameters
            mock_create_agent.assert_called_once()
            args, kwargs = mock_create_agent.call_args
            assert kwargs["model_provider"] == "openai"
            assert kwargs["model_name"] == "gpt-4"
            assert kwargs["memory"] == False
            assert len(kwargs["additional_tools"]) == 1
            assert kwargs["temperature"] == 0.7

    def test_run(self, chat_agent, mock_agent):
        """Test the run method."""
        # Run the agent
        response = chat_agent.run("Hello")
        
        # Check that the agent's stream method was called
        mock_agent.stream.assert_called_once()
        
        # Check the response
        assert response == "Hello, I'm an AI assistant"

    def test_run_with_thread_id(self, chat_agent, mock_agent):
        """Test the run method with a thread ID."""
        # Run the agent with a thread ID
        response = chat_agent.run("Hello", thread_id="thread_123")
        
        # Check that the agent's stream method was called with the thread ID
        mock_agent.stream.assert_called_once()
        call_args = mock_agent.stream.call_args
        assert call_args[1]["config"]["configurable"]["thread_id"] == "thread_123"
        
        # Check the response
        assert response == "Hello, I'm an AI assistant"

    def test_chat(self, chat_agent):
        """Test the chat method."""
        # Mock the run method
        chat_agent.run = MagicMock(return_value="Hello, I'm an AI assistant")
        
        # Chat with the agent
        response, thread_id = chat_agent.chat("Hello")
        
        # Check that the run method was called
        chat_agent.run.assert_called_once_with("Hello", thread_id=thread_id)
        
        # Check the response
        assert response == "Hello, I'm an AI assistant"
        assert isinstance(thread_id, str)

    def test_chat_with_thread_id(self, chat_agent):
        """Test the chat method with a thread ID."""
        # Mock the run method
        chat_agent.run = MagicMock(return_value="Hello, I'm an AI assistant")
        
        # Chat with the agent using a specific thread ID
        response, returned_thread_id = chat_agent.chat("Hello", thread_id="thread_123")
        
        # Check that the run method was called with the thread ID
        chat_agent.run.assert_called_once_with("Hello", thread_id="thread_123")
        
        # Check the response and thread ID
        assert response == "Hello, I'm an AI assistant"
        assert returned_thread_id == "thread_123"

    def test_get_chat_history(self, chat_agent, mock_agent):
        """Test the get_chat_history method."""
        # Mock the agent's get_state method
        mock_agent.get_state = MagicMock(return_value={
            "messages": [
                AIMessage(content="Hello, I'm an AI assistant")
            ]
        })
        
        # Get the chat history
        history = chat_agent.get_chat_history("thread_123")
        
        # Check that the agent's get_state method was called with the thread ID
        mock_agent.get_state.assert_called_once_with({"configurable": {"thread_id": "thread_123"}})
        
        # Check the history
        assert len(history) == 1
        assert isinstance(history[0], AIMessage)
        assert history[0].content == "Hello, I'm an AI assistant"

    def test_get_chat_history_no_state(self, chat_agent, mock_agent):
        """Test the get_chat_history method when there is no state."""
        # Mock the agent's get_state method to return None
        mock_agent.get_state = MagicMock(return_value=None)
        
        # Get the chat history
        history = chat_agent.get_chat_history("thread_123")
        
        # Check that the agent's get_state method was called with the thread ID
        mock_agent.get_state.assert_called_once_with({"configurable": {"thread_id": "thread_123"}})
        
        # Check the history
        assert history == []

    def test_get_chat_history_no_messages(self, chat_agent, mock_agent):
        """Test the get_chat_history method when there are no messages in the state."""
        # Mock the agent's get_state method to return a state without messages
        mock_agent.get_state = MagicMock(return_value={"other_key": "value"})
        
        # Get the chat history
        history = chat_agent.get_chat_history("thread_123")
        
        # Check that the agent's get_state method was called with the thread ID
        mock_agent.get_state.assert_called_once_with({"configurable": {"thread_id": "thread_123"}})
        
        # Check the history
        assert history == []

