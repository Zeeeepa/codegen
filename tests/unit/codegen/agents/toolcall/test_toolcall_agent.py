import unittest
from unittest.mock import patch, MagicMock
import uuid

from codegen.agents.toolcall.toolcall_agent import ToolCallAgent, Tool

class TestToolCallAgent(unittest.TestCase):
    """Test cases for the ToolCallAgent class."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock BaseAgent.__init__
        self.base_agent_patcher = patch('codegen.agents.base.BaseAgent.__init__')
        self.mock_base_agent_init = self.base_agent_patcher.start()
        self.mock_base_agent_init.return_value = None
        
        # Create mock tools
        self.mock_tool_func = MagicMock(return_value="Tool result")
        self.mock_tool = Tool(
            name="test_tool",
            description="A test tool",
            func=self.mock_tool_func
        )

    def tearDown(self):
        """Tear down test fixtures."""
        self.base_agent_patcher.stop()

    def test_tool_init(self):
        """Test initialization of Tool class."""
        tool = Tool(
            name="test_tool",
            description="A test tool",
            func=self.mock_tool_func
        )
        
        self.assertEqual(tool.name, "test_tool")
        self.assertEqual(tool.description, "A test tool")
        self.assertEqual(tool.func, self.mock_tool_func)

    def test_tool_call(self):
        """Test calling a Tool."""
        tool = Tool(
            name="test_tool",
            description="A test tool",
            func=self.mock_tool_func
        )
        
        result = tool("arg1", arg2="value")
        
        self.mock_tool_func.assert_called_once_with("arg1", arg2="value")
        self.assertEqual(result, "Tool result")

    def test_init_default_params(self):
        """Test initialization with default parameters."""
        tools = [self.mock_tool]
        agent = ToolCallAgent(tools)
        
        # Check that the base agent was initialized correctly
        self.mock_base_agent_init.assert_called_once_with(
            model_provider="anthropic",
            model_name="claude-3-5-sonnet-latest",
            memory=True
        )
        
        # Check that the agent properties are set correctly
        self.assertEqual(agent.tools, {"test_tool": self.mock_tool})
        self.assertEqual(agent.message_history, {})

    def test_init_custom_params(self):
        """Test initialization with custom parameters."""
        tools = [self.mock_tool]
        agent = ToolCallAgent(
            tools=tools,
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
        self.assertEqual(agent.tools, {"test_tool": self.mock_tool})

    @patch('uuid.uuid4')
    def test_run_new_thread(self, mock_uuid):
        """Test the run method with a new thread."""
        # Set up mocks
        mock_uuid.return_value = uuid.UUID('12345678-1234-5678-1234-567812345678')
        
        # Create agent and run
        agent = ToolCallAgent([self.mock_tool])
        result = agent.run("Test prompt")
        
        # Check that the message history was updated
        self.assertEqual(len(agent.message_history["12345678-1234-5678-1234-567812345678"]), 2)
        self.assertEqual(agent.message_history["12345678-1234-5678-1234-567812345678"][0]["role"], "user")
        self.assertEqual(agent.message_history["12345678-1234-5678-1234-567812345678"][0]["content"], "Test prompt")
        self.assertEqual(agent.message_history["12345678-1234-5678-1234-567812345678"][1]["role"], "assistant")
        
        # Check the result (this is a placeholder in the current implementation)
        self.assertIn("ToolCall Agent would process: Test prompt", result)

    def test_run_existing_thread(self):
        """Test the run method with an existing thread."""
        # Set up existing thread
        agent = ToolCallAgent([self.mock_tool])
        agent.message_history["existing-thread"] = [{"role": "user", "content": "Previous prompt"}]
        
        # Run with existing thread
        result = agent.run("Test prompt", thread_id="existing-thread")
        
        # Check that the message history was updated
        self.assertEqual(len(agent.message_history["existing-thread"]), 2)
        self.assertEqual(agent.message_history["existing-thread"][1]["role"], "assistant")
        
        # Check the result (this is a placeholder in the current implementation)
        self.assertIn("ToolCall Agent would process: Test prompt", result)

    def test_get_chat_history(self):
        """Test the get_chat_history method."""
        # Set up message history
        agent = ToolCallAgent([self.mock_tool])
        agent.message_history["test-thread"] = [{"role": "user", "content": "Test prompt"}]
        
        # Get chat history
        history = agent.get_chat_history("test-thread")
        
        # Check the result
        self.assertEqual(history, [{"role": "user", "content": "Test prompt"}])

    def test_get_chat_history_empty(self):
        """Test the get_chat_history method with an empty history."""
        # Create agent
        agent = ToolCallAgent([self.mock_tool])
        
        # Get chat history for non-existent thread
        history = agent.get_chat_history("non-existent-thread")
        
        # Check the result
        self.assertEqual(history, [])

    def test_add_tool(self):
        """Test the add_tool method."""
        # Create agent
        agent = ToolCallAgent([])
        
        # Add a tool
        agent.add_tool(self.mock_tool)
        
        # Check that the tool was added
        self.assertEqual(agent.tools, {"test_tool": self.mock_tool})

    def test_remove_tool(self):
        """Test the remove_tool method."""
        # Create agent with a tool
        agent = ToolCallAgent([self.mock_tool])
        
        # Remove the tool
        agent.remove_tool("test_tool")
        
        # Check that the tool was removed
        self.assertEqual(agent.tools, {})

    def test_remove_nonexistent_tool(self):
        """Test removing a tool that doesn't exist."""
        # Create agent with a tool
        agent = ToolCallAgent([self.mock_tool])
        
        # Remove a non-existent tool
        agent.remove_tool("non_existent_tool")
        
        # Check that the tools are unchanged
        self.assertEqual(agent.tools, {"test_tool": self.mock_tool})

if __name__ == '__main__':
    unittest.main()
