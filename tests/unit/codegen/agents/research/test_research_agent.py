import unittest
from unittest.mock import patch, MagicMock

from codegen.agents.research.research_agent import ResearchAgent

class TestResearchAgent(unittest.TestCase):
    """Test cases for the ResearchAgent class."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock Researcher
        self.researcher_patcher = patch('codegen.agents.research.research_agent.Researcher')
        self.mock_researcher_class = self.researcher_patcher.start()
        self.mock_researcher = MagicMock()
        self.mock_researcher_class.return_value = self.mock_researcher
        
        # Mock ContextUnderstanding
        self.context_understanding_patcher = patch('codegen.agents.research.research_agent.ContextUnderstanding')
        self.mock_context_understanding_class = self.context_understanding_patcher.start()
        self.mock_context_understanding = MagicMock()
        self.mock_context_understanding_class.return_value = self.mock_context_understanding
        
        # Mock BaseAgent.__init__
        self.base_agent_patcher = patch('codegen.agents.base.BaseAgent.__init__')
        self.mock_base_agent_init = self.base_agent_patcher.start()
        self.mock_base_agent_init.return_value = None

    def tearDown(self):
        """Tear down test fixtures."""
        self.researcher_patcher.stop()
        self.context_understanding_patcher.stop()
        self.base_agent_patcher.stop()

    def test_init_default_params(self):
        """Test initialization with default parameters."""
        agent = ResearchAgent()
        
        # Check that the base agent was initialized correctly
        self.mock_base_agent_init.assert_called_once_with(
            model_provider="anthropic",
            model_name=None,
            temperature=0.2,
            max_tokens=4000
        )
        
        # Check that the agent properties are set correctly
        self.assertEqual(agent.researcher, self.mock_researcher)
        self.assertEqual(agent.context_understanding, self.mock_context_understanding)

    def test_init_custom_params(self):
        """Test initialization with custom parameters."""
        agent = ResearchAgent(
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
        self.assertEqual(agent.researcher, self.mock_researcher)
        self.assertEqual(agent.context_understanding, self.mock_context_understanding)

    def test_research_default_params(self):
        """Test the research method with default parameters."""
        # Set up mock response
        mock_response = {"results": ["result1", "result2"]}
        self.mock_researcher.research.return_value = mock_response
        
        # Create agent and call research
        agent = ResearchAgent()
        result = agent.research("Test query")
        
        # Check that the researcher was called correctly
        self.mock_researcher.research.assert_called_once_with(
            query="Test query",
            context={},
            max_results=5
        )
        
        # Check the result
        self.assertEqual(result, mock_response)

    def test_research_custom_params(self):
        """Test the research method with custom parameters."""
        # Set up mock response
        mock_response = {"results": ["result1", "result2", "result3"]}
        self.mock_researcher.research.return_value = mock_response
        
        # Create agent and call research
        agent = ResearchAgent()
        context = {"domain": "programming"}
        result = agent.research("Test query", context=context, max_results=3)
        
        # Check that the researcher was called correctly
        self.mock_researcher.research.assert_called_once_with(
            query="Test query",
            context=context,
            max_results=3
        )
        
        # Check the result
        self.assertEqual(result, mock_response)

    def test_analyze_context_default_params(self):
        """Test the analyze_context method with default parameters."""
        # Set up mock response
        mock_response = {"analysis": "This is an analysis"}
        self.mock_context_understanding.analyze.return_value = mock_response
        
        # Create agent and call analyze_context
        agent = ResearchAgent()
        result = agent.analyze_context("Test content")
        
        # Check that the context understanding was called correctly
        self.mock_context_understanding.analyze.assert_called_once_with(
            content="Test content",
            questions=None,
            context={}
        )
        
        # Check the result
        self.assertEqual(result, mock_response)

    def test_analyze_context_custom_params(self):
        """Test the analyze_context method with custom parameters."""
        # Set up mock response
        mock_response = {"analysis": "This is a detailed analysis"}
        self.mock_context_understanding.analyze.return_value = mock_response
        
        # Create agent and call analyze_context
        agent = ResearchAgent()
        questions = ["What is the main topic?", "What are the key points?"]
        context = {"domain": "programming"}
        result = agent.analyze_context("Test content", questions=questions, context=context)
        
        # Check that the context understanding was called correctly
        self.mock_context_understanding.analyze.assert_called_once_with(
            content="Test content",
            questions=questions,
            context=context
        )
        
        # Check the result
        self.assertEqual(result, mock_response)

if __name__ == '__main__':
    unittest.main()
