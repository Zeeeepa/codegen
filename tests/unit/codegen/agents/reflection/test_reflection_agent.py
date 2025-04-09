import unittest
from unittest.mock import patch, MagicMock

from codegen.agents.reflection.reflection_agent import ReflectionAgent

class TestReflectionAgent(unittest.TestCase):
    """Test cases for the ReflectionAgent class."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock Reflector
        self.reflector_patcher = patch('codegen.agents.reflection.reflection_agent.Reflector')
        self.mock_reflector_class = self.reflector_patcher.start()
        self.mock_reflector = MagicMock()
        self.mock_reflector_class.return_value = self.mock_reflector
        
        # Mock BaseAgent.__init__
        self.base_agent_patcher = patch('codegen.agents.base.BaseAgent.__init__')
        self.mock_base_agent_init = self.base_agent_patcher.start()
        self.mock_base_agent_init.return_value = None

    def tearDown(self):
        """Tear down test fixtures."""
        self.reflector_patcher.stop()
        self.base_agent_patcher.stop()

    def test_init_default_params(self):
        """Test initialization with default parameters."""
        agent = ReflectionAgent()
        
        # Check that the base agent was initialized correctly
        self.mock_base_agent_init.assert_called_once_with(
            model_provider="anthropic",
            model_name=None,
            temperature=0.2,
            max_tokens=4000
        )
        
        # Check that the agent properties are set correctly
        self.assertEqual(agent.reflector, self.mock_reflector)

    def test_init_custom_params(self):
        """Test initialization with custom parameters."""
        agent = ReflectionAgent(
            model_provider="openai",
            model_name="gpt-4o",
            temperature=0.7,
            max_tokens=2000
        )
        
        # Check that the base agent was initialized correctly
        self.mock_base_agent_init.assert_called_once_with(
            model_provider="openai",
            model_name="gpt-4o",
            temperature=0.7,
            max_tokens=2000
        )
        
        # Check that the agent properties are set correctly
        self.assertEqual(agent.reflector, self.mock_reflector)

    def test_reflect_default_params(self):
        """Test the reflect method with default parameters."""
        # Set up mock response
        mock_response = {"score": 0.8, "feedback": "Good job!"}
        self.mock_reflector.reflect.return_value = mock_response
        
        # Create agent and call reflect
        agent = ReflectionAgent()
        result = agent.reflect("Test content")
        
        # Check that the reflector was called correctly
        self.mock_reflector.reflect.assert_called_once_with(
            content="Test content",
            criteria=None,
            context={}
        )
        
        # Check the result
        self.assertEqual(result, mock_response)

    def test_reflect_custom_params(self):
        """Test the reflect method with custom parameters."""
        # Set up mock response
        mock_response = {"score": 0.9, "feedback": "Excellent!"}
        self.mock_reflector.reflect.return_value = mock_response
        
        # Create agent and call reflect
        agent = ReflectionAgent()
        criteria = ["clarity", "correctness"]
        context = {"domain": "programming"}
        result = agent.reflect("Test content", criteria=criteria, context=context)
        
        # Check that the reflector was called correctly
        self.mock_reflector.reflect.assert_called_once_with(
            content="Test content",
            criteria=criteria,
            context=context
        )
        
        # Check the result
        self.assertEqual(result, mock_response)

    def test_improve_default_params(self):
        """Test the improve method with default parameters."""
        # Set up mock response
        self.mock_reflector.improve.return_value = "Improved content"
        
        # Create agent and call improve
        agent = ReflectionAgent()
        result = agent.improve("Test content", "Add more details")
        
        # Check that the reflector was called correctly
        self.mock_reflector.improve.assert_called_once_with(
            content="Test content",
            feedback="Add more details",
            context={}
        )
        
        # Check the result
        self.assertEqual(result, "Improved content")

    def test_improve_custom_params(self):
        """Test the improve method with custom parameters."""
        # Set up mock response
        self.mock_reflector.improve.return_value = "Improved content with context"
        
        # Create agent and call improve
        agent = ReflectionAgent()
        context = {"domain": "programming"}
        result = agent.improve("Test content", "Add more details", context=context)
        
        # Check that the reflector was called correctly
        self.mock_reflector.improve.assert_called_once_with(
            content="Test content",
            feedback="Add more details",
            context=context
        )
        
        # Check the result
        self.assertEqual(result, "Improved content with context")

if __name__ == '__main__':
    unittest.main()
