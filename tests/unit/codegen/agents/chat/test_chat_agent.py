import unittest
from unittest.mock import patch, MagicMock
import uuid

from codegen.agents.chat.chat_agent import ChatAgent

class TestChatAgent(unittest.TestCase):
    """Test cases for the ChatAgent class."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock codebase
        self.mock_codebase = MagicMock()
        
        # Mock create_chat_agent
        self.agent_patcher = patch('codegen.agents.chat.chat_agent.create_chat_agent')
        self.mock_create_agent = self.agent_patcher.start()
        self.mock_agent = MagicMock()
        self.mock_create_agent.return_value = self.mock_agent

    def tearDown(self):
        """Tear down test fixtures."""
        self.agent_patcher.stop()

    def test_init_default_params(self):
        """Test initialization with default parameters."""
        agent = ChatAgent(self.mock_codebase)
        
        # Check that the agent was created with the right parameters
        self.mock_create_agent.assert_called_once_with(
            self.mock_codebase,
            model_provider="anthropic",
            model_name="claude-3-5-sonnet-latest",
            memory=True,
            additional_tools=None
        )
        
        # Check that the agent properties are set correctly
        self.assertEqual(agent.codebase, self.mock_codebase)
        self.assertEqual(agent.agent, self.mock_agent)

    def test_init_custom_params(self):
        """Test initialization with custom parameters."""
        mock_tools = [MagicMock()]
        
        agent = ChatAgent(
            codebase=self.mock_codebase,
            model_provider="openai",
            model_name="gpt-4o",
            memory=False,
            tools=mock_tools,
            temperature=0.7,
            max_tokens=2000
        )
        
        # Check that the agent was created with the right parameters
        self.mock_create_agent.assert_called_once_with(
            self.mock_codebase,
            model_provider="openai",
            model_name="gpt-4o",
            memory=False,
            additional_tools=mock_tools,
            temperature=0.7,
            max_tokens=2000
        )
        
        # Check that the agent properties are set correctly
        self.assertEqual(agent.codebase, self.mock_codebase)
        self.assertEqual(agent.agent, self.mock_agent)

    @patch('uuid.uuid4')
    @patch('builtins.print')
    def test_run(self, mock_print, mock_uuid):
        """Test the run method."""
        # Set up mocks
        mock_uuid.return_value = uuid.UUID('12345678-1234-5678-1234-567812345678')
        
        # Set up stream values
        mock_stream = MagicMock()
        self.mock_agent.stream.return_value = mock_stream
        
        # Set up message
        mock_message = MagicMock()
        mock_s = {"messages": [mock_message], "final_answer": "Final response"}
        mock_stream.__iter__.return_value = [mock_s]
        
        # Create agent and run
        agent = ChatAgent(self.mock_codebase)
        result = agent.run("Test prompt")
        
        # Check that the agent was called correctly
        self.mock_agent.stream.assert_called_once_with(
            {"query": "Test prompt"},
            config={"configurable": {"thread_id": "12345678-1234-5678-1234-567812345678"}},
            stream_mode="values"
        )
        
        # Check the result
        self.assertEqual(result, "Final response")

    @patch('uuid.uuid4')
    @patch('builtins.print')
    def test_chat_new_thread(self, mock_print, mock_uuid):
        """Test the chat method with a new thread."""
        # Set up mocks
        mock_uuid.return_value = uuid.UUID('12345678-1234-5678-1234-567812345678')
        
        # Set up run method to return a response
        agent = ChatAgent(self.mock_codebase)
        agent.run = MagicMock(return_value="Test response")
        
        # Call chat with a new thread
        response, thread_id = agent.chat("Test prompt")
        
        # Check that run was called correctly
        agent.run.assert_called_once_with("Test prompt", thread_id="12345678-1234-5678-1234-567812345678")
        
        # Check the result
        self.assertEqual(response, "Test response")
        self.assertEqual(thread_id, "12345678-1234-5678-1234-567812345678")
        mock_print.assert_called_with("Starting new chat thread: 12345678-1234-5678-1234-567812345678")

    @patch('builtins.print')
    def test_chat_existing_thread(self, mock_print):
        """Test the chat method with an existing thread."""
        # Set up run method to return a response
        agent = ChatAgent(self.mock_codebase)
        agent.run = MagicMock(return_value="Test response")
        
        # Call chat with an existing thread
        response, thread_id = agent.chat("Test prompt", thread_id="existing-thread")
        
        # Check that run was called correctly
        agent.run.assert_called_once_with("Test prompt", thread_id="existing-thread")
        
        # Check the result
        self.assertEqual(response, "Test response")
        self.assertEqual(thread_id, "existing-thread")
        mock_print.assert_called_with("Continuing chat thread: existing-thread")

    def test_get_chat_history(self):
        """Test the get_chat_history method."""
        # Set up mock state
        mock_state = {"messages": ["message1", "message2"]}
        self.mock_agent.get_state.return_value = mock_state
        
        # Create agent and get chat history
        agent = ChatAgent(self.mock_codebase)
        history = agent.get_chat_history("test-thread")
        
        # Check that the agent was called correctly
        self.mock_agent.get_state.assert_called_once_with({"configurable": {"thread_id": "test-thread"}})
        
        # Check the result
        self.assertEqual(history, ["message1", "message2"])

    def test_get_chat_history_no_state(self):
        """Test the get_chat_history method when no state is available."""
        # Set up mock state
        self.mock_agent.get_state.return_value = None
        
        # Create agent and get chat history
        agent = ChatAgent(self.mock_codebase)
        history = agent.get_chat_history("test-thread")
        
        # Check that the agent was called correctly
        self.mock_agent.get_state.assert_called_once_with({"configurable": {"thread_id": "test-thread"}})
        
        # Check the result
        self.assertEqual(history, [])

    def test_get_chat_history_no_messages(self):
        """Test the get_chat_history method when no messages are in the state."""
        # Set up mock state
        mock_state = {"other_key": "value"}
        self.mock_agent.get_state.return_value = mock_state
        
        # Create agent and get chat history
        agent = ChatAgent(self.mock_codebase)
        history = agent.get_chat_history("test-thread")
        
        # Check that the agent was called correctly
        self.mock_agent.get_state.assert_called_once_with({"configurable": {"thread_id": "test-thread"}})
        
        # Check the result
        self.assertEqual(history, [])

if __name__ == '__main__':
    unittest.main()
