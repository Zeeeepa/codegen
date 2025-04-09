import unittest
from unittest.mock import patch, MagicMock
import uuid

from codegen.agents.base import BaseAgent

class TestBaseAgent(unittest.TestCase):
    """Test cases for the BaseAgent class."""

    def test_init(self):
        """Test initialization of BaseAgent."""
        # Create a concrete subclass for testing
        class ConcreteAgent(BaseAgent):
            def run(self, prompt, thread_id=None):
                return "Test response"
            
            def get_chat_history(self, thread_id):
                return []
        
        # Test with default parameters
        agent = ConcreteAgent()
        self.assertEqual(agent.model_provider, "anthropic")
        self.assertEqual(agent.model_name, "claude-3-5-sonnet-latest")
        self.assertTrue(agent.memory)
        self.assertEqual(agent.config, {})
        
        # Test with custom parameters
        agent = ConcreteAgent(
            model_provider="openai",
            model_name="gpt-4o",
            memory=False,
            temperature=0.7,
            max_tokens=2000
        )
        self.assertEqual(agent.model_provider, "openai")
        self.assertEqual(agent.model_name, "gpt-4o")
        self.assertFalse(agent.memory)
        self.assertEqual(agent.config, {"temperature": 0.7, "max_tokens": 2000})

    @patch('uuid.uuid4')
    def test_generate(self, mock_uuid):
        """Test generate method."""
        # Create a concrete subclass for testing
        class ConcreteAgent(BaseAgent):
            def run(self, prompt, thread_id=None):
                return f"Response to: {prompt} (thread: {thread_id})"
            
            def get_chat_history(self, thread_id):
                return []
        
        # Mock uuid4 to return a predictable value
        mock_uuid.return_value = uuid.UUID('12345678-1234-5678-1234-567812345678')
        
        agent = ConcreteAgent()
        response = agent.generate("Test prompt")
        
        # Since generate is synchronous in our implementation despite being defined as async
        self.assertEqual(response, "Response to: Test prompt (thread: 12345678-1234-5678-1234-567812345678)")

    @patch('uuid.uuid4')
    @patch('builtins.print')
    def test_chat(self, mock_print, mock_uuid):
        """Test chat method."""
        # Create a concrete subclass for testing
        class ConcreteAgent(BaseAgent):
            def run(self, prompt, thread_id=None):
                return f"Response to: {prompt} (thread: {thread_id})"
            
            def get_chat_history(self, thread_id):
                return []
        
        # Mock uuid4 to return a predictable value
        mock_uuid.return_value = uuid.UUID('12345678-1234-5678-1234-567812345678')
        
        agent = ConcreteAgent()
        
        # Test with new thread
        response, thread_id = agent.chat("Test prompt")
        self.assertEqual(response, "Response to: Test prompt (thread: 12345678-1234-5678-1234-567812345678)")
        self.assertEqual(thread_id, "12345678-1234-5678-1234-567812345678")
        mock_print.assert_called_with("Starting new chat thread: 12345678-1234-5678-1234-567812345678")
        
        # Test with existing thread
        mock_print.reset_mock()
        response, thread_id = agent.chat("Follow-up prompt", thread_id="existing-thread")
        self.assertEqual(response, "Response to: Follow-up prompt (thread: existing-thread)")
        self.assertEqual(thread_id, "existing-thread")
        mock_print.assert_called_with("Continuing chat thread: existing-thread")

if __name__ == '__main__':
    unittest.main()
