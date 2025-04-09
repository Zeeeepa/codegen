import unittest
from unittest.mock import patch, MagicMock
import uuid

from codegen.agents.mcp.mcp_agent import MCPAgent

class TestMCPAgent(unittest.TestCase):
    """Test cases for the MCPAgent class."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock BaseAgent.__init__
        self.base_agent_patcher = patch('codegen.agents.base.BaseAgent.__init__')
        self.mock_base_agent_init = self.base_agent_patcher.start()
        self.mock_base_agent_init.return_value = None

    def tearDown(self):
        """Tear down test fixtures."""
        self.base_agent_patcher.stop()

    def test_init_default_params(self):
        """Test initialization with default parameters."""
        agent = MCPAgent("http://localhost:8000")
        
        # Check that the base agent was initialized correctly
        self.mock_base_agent_init.assert_called_once_with(
            model_provider="anthropic",
            model_name="claude-3-5-sonnet-latest",
            memory=True
        )
        
        # Check that the agent properties are set correctly
        self.assertEqual(agent.mcp_server_url, "http://localhost:8000")
        self.assertEqual(agent.message_history, {})

    def test_init_custom_params(self):
        """Test initialization with custom parameters."""
        agent = MCPAgent(
            mcp_server_url="http://example.com:8000",
            model_provider="openai",
            model_name="gpt-4o",
            memory=False,
            temperature=0.7,
            max_tokens=2000
        )
        
        # Check that the base agent was initialized correctly
        self.mock_base_agent_init.assert_called_once_with(
            model_provider="openai",
            model_name="gpt-4o",
            memory=False,
            temperature=0.7,
            max_tokens=2000
        )
        
        # Check that the agent properties are set correctly
        self.assertEqual(agent.mcp_server_url, "http://example.com:8000")

    @patch('uuid.uuid4')
    def test_run_new_thread(self, mock_uuid):
        """Test the run method with a new thread."""
        # Set up mocks
        mock_uuid.return_value = uuid.UUID('12345678-1234-5678-1234-567812345678')
        
        # Create agent and run
        agent = MCPAgent("http://localhost:8000")
        result = agent.run("Test prompt")
        
        # Check that the message history was updated
        self.assertEqual(len(agent.message_history["12345678-1234-5678-1234-567812345678"]), 2)
        self.assertEqual(agent.message_history["12345678-1234-5678-1234-567812345678"][0]["role"], "user")
        self.assertEqual(agent.message_history["12345678-1234-5678-1234-567812345678"][0]["content"], "Test prompt")
        self.assertEqual(agent.message_history["12345678-1234-5678-1234-567812345678"][1]["role"], "assistant")
        
        # Check the result (this is a placeholder in the current implementation)
        self.assertIn("MCP Agent response to: Test prompt", result)

    def test_run_existing_thread(self):
        """Test the run method with an existing thread."""
        # Set up existing thread
        agent = MCPAgent("http://localhost:8000")
        agent.message_history["existing-thread"] = [{"role": "user", "content": "Previous prompt"}]
        
        # Run with existing thread
        result = agent.run("Test prompt", thread_id="existing-thread")
        
        # Check that the message history was updated
        self.assertEqual(len(agent.message_history["existing-thread"]), 2)
        self.assertEqual(agent.message_history["existing-thread"][1]["role"], "assistant")
        
        # Check the result (this is a placeholder in the current implementation)
        self.assertIn("MCP Agent response to: Test prompt", result)

    def test_get_chat_history(self):
        """Test the get_chat_history method."""
        # Set up message history
        agent = MCPAgent("http://localhost:8000")
        agent.message_history["test-thread"] = [{"role": "user", "content": "Test prompt"}]
        
        # Get chat history
        history = agent.get_chat_history("test-thread")
        
        # Check the result
        self.assertEqual(history, [{"role": "user", "content": "Test prompt"}])

    def test_get_chat_history_empty(self):
        """Test the get_chat_history method with an empty history."""
        # Create agent
        agent = MCPAgent("http://localhost:8000")
        
        # Get chat history for non-existent thread
        history = agent.get_chat_history("non-existent-thread")
        
        # Check the result
        self.assertEqual(history, [])

if __name__ == '__main__':
    unittest.main()
