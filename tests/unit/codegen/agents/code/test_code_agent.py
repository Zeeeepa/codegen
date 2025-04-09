import unittest
from unittest.mock import patch, MagicMock, ANY
import os
import uuid

from codegen.agents.code.code_agent import CodeAgent

class TestCodeAgent(unittest.TestCase):
    """Test cases for the CodeAgent class."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock codebase
        self.mock_codebase = MagicMock()
        self.mock_file = MagicMock()
        self.mock_file.filepath = "test.py"
        self.mock_file.content = "def test():\n    return True"
        self.mock_file.language = "python"
        self.mock_codebase.files.return_value = [self.mock_file]
        
        # Mock environment variables
        self.env_patcher = patch.dict(os.environ, {"LANGCHAIN_PROJECT": "TEST_PROJECT"})
        self.env_patcher.start()
        
        # Mock LangSmith client
        self.langsmith_patcher = patch('langsmith.Client')
        self.mock_langsmith = self.langsmith_patcher.start()
        
        # Mock create_codebase_agent
        self.agent_patcher = patch('codegen.agents.code.code_agent.create_codebase_agent')
        self.mock_create_agent = self.agent_patcher.start()
        self.mock_agent = MagicMock()
        self.mock_create_agent.return_value = self.mock_agent

    def tearDown(self):
        """Tear down test fixtures."""
        self.env_patcher.stop()
        self.langsmith_patcher.stop()
        self.agent_patcher.stop()

    def test_init_default_params(self):
        """Test initialization with default parameters."""
        agent = CodeAgent(self.mock_codebase)
        
        # Check that the agent was created with the right parameters
        self.mock_create_agent.assert_called_once_with(
            self.mock_codebase,
            model_provider="anthropic",
            model_name="claude-3-7-sonnet-latest",
            memory=True,
            additional_tools=None,
            config=None
        )
        
        # Check that the agent properties are set correctly
        self.assertEqual(agent.codebase, self.mock_codebase)
        self.assertEqual(agent.model_name, "claude-3-7-sonnet-latest")
        self.assertEqual(agent.project_name, "TEST_PROJECT")
        self.assertIsNotNone(agent.thread_id)
        self.assertIsNone(agent.run_id)
        self.assertIsNone(agent.instance_id)
        self.assertIsNone(agent.difficulty)
        self.assertIsNotNone(agent.tags)
        self.assertIn("claude-3-7-sonnet-latest", agent.tags)
        self.assertEqual(agent.metadata["project"], "TEST_PROJECT")
        self.assertEqual(agent.metadata["model"], "claude-3-7-sonnet-latest")
        self.assertIsNotNone(agent.codebase_stats)

    def test_init_custom_params(self):
        """Test initialization with custom parameters."""
        mock_tools = [MagicMock()]
        mock_config = MagicMock()
        mock_logger = MagicMock()
        
        agent = CodeAgent(
            codebase=self.mock_codebase,
            model_provider="openai",
            model_name="gpt-4o",
            memory=False,
            tools=mock_tools,
            tags=["test-tag"],
            metadata={"custom": "value"},
            agent_config=mock_config,
            thread_id="test-thread",
            logger=mock_logger,
            temperature=0.7,
            analyze_codebase=False
        )
        
        # Check that the agent was created with the right parameters
        self.mock_create_agent.assert_called_once_with(
            self.mock_codebase,
            model_provider="openai",
            model_name="gpt-4o",
            memory=False,
            additional_tools=mock_tools,
            config=mock_config,
            temperature=0.7
        )
        
        # Check that the agent properties are set correctly
        self.assertEqual(agent.codebase, self.mock_codebase)
        self.assertEqual(agent.model_name, "gpt-4o")
        self.assertEqual(agent.thread_id, "test-thread")
        self.assertEqual(agent.logger, mock_logger)
        self.assertIn("test-tag", agent.tags)
        self.assertIn("gpt-4o", agent.tags)
        self.assertEqual(agent.metadata["custom"], "value")
        self.assertIsNone(agent.codebase_stats)

    def test_analyze_codebase(self):
        """Test the _analyze_codebase method."""
        agent = CodeAgent(self.mock_codebase)
        stats = agent._analyze_codebase()
        
        # Check that the stats are calculated correctly
        self.assertEqual(stats["file_count"], 1)
        self.assertEqual(stats["language_distribution"]["python"], 1)
        self.assertEqual(stats["total_lines"], 2)
        self.assertEqual(stats["file_types"][".py"], 1)
        self.assertEqual(stats["largest_files"][0][0], "test.py")
        self.assertEqual(stats["largest_files"][0][1], 2)

    @patch('uuid.uuid4')
    @patch('codegen.agents.code.code_agent.MessageStreamTracer')
    @patch('codegen.extensions.langchain.utils.get_langsmith_url.find_and_print_langsmith_run_url')
    def test_run(self, mock_find_url, mock_tracer_class, mock_uuid):
        """Test the run method."""
        # Set up mocks
        mock_uuid.return_value = uuid.UUID('12345678-1234-5678-1234-567812345678')
        mock_tracer = MagicMock()
        mock_tracer_class.return_value = mock_tracer
        
        # Set up stream values
        mock_stream = MagicMock()
        self.mock_agent.stream.return_value = mock_stream
        
        # Set up traced stream
        mock_message = MagicMock()
        mock_message.content = [{"text": "Test response"}]
        mock_s = {"messages": [mock_message], "final_answer": "Final response"}
        mock_tracer.process_stream.return_value = [mock_s]
        
        # Create agent and run
        agent = CodeAgent(self.mock_codebase)
        result = agent.run("Test prompt")
        
        # Check that the agent was called correctly
        self.mock_agent.stream.assert_called_once()
        mock_tracer.process_stream.assert_called_once_with(mock_stream)
        mock_find_url.assert_called_once()
        
        # Check the result
        self.assertEqual(result, "Final response")

    def test_get_tools(self):
        """Test the get_tools method."""
        # Set up mock tools
        mock_tools = {"tool1": MagicMock(), "tool2": MagicMock()}
        mock_node = MagicMock()
        mock_node.data.tools_by_name = mock_tools
        self.mock_agent.get_graph.return_value.nodes = {"tools": mock_node}
        
        # Create agent and get tools
        agent = CodeAgent(self.mock_codebase)
        tools = agent.get_tools()
        
        # Check the result
        self.assertEqual(len(tools), 2)
        self.assertIn(mock_tools["tool1"], tools)
        self.assertIn(mock_tools["tool2"], tools)

    def test_get_state(self):
        """Test the get_state method."""
        # Set up mock state
        mock_state = {"key": "value"}
        self.mock_agent.get_state.return_value = mock_state
        
        # Create agent and get state
        agent = CodeAgent(self.mock_codebase)
        state = agent.get_state()
        
        # Check that the agent was called correctly
        self.mock_agent.get_state.assert_called_once()
        
        # Check the result
        self.assertEqual(state, mock_state)

    def test_get_tags_metadata(self):
        """Test the get_tags_metadata method."""
        # Create agent with SWEBench metadata
        agent = CodeAgent(
            self.mock_codebase,
            metadata={
                "run_id": "test-run",
                "instance_id": "test-instance",
                "difficulty": "difficulty_3"
            }
        )
        
        # Get tags and metadata
        tags, metadata = agent.get_tags_metadata()
        
        # Check tags
        self.assertIn("claude-3-7-sonnet-latest", tags)
        self.assertIn("test-run", tags)
        self.assertIn("test-instance", tags)
        self.assertIn("difficulty_3", tags)
        
        # Check metadata
        self.assertEqual(metadata["project"], "TEST_PROJECT")
        self.assertEqual(metadata["model"], "claude-3-7-sonnet-latest")
        self.assertEqual(metadata["swebench_run_id"], "test-run")
        self.assertEqual(metadata["swebench_instance_id"], "test-instance")
        self.assertEqual(metadata["swebench_difficulty"], 3)

    def test_get_codebase_stats(self):
        """Test the get_codebase_stats method."""
        # Create agent without analyzing codebase
        agent = CodeAgent(self.mock_codebase, analyze_codebase=False)
        self.assertIsNone(agent.codebase_stats)
        
        # Get stats (should trigger analysis)
        stats = agent.get_codebase_stats()
        
        # Check that stats were calculated
        self.assertIsNotNone(stats)
        self.assertEqual(stats["file_count"], 1)
        self.assertEqual(agent.codebase_stats, stats)

if __name__ == '__main__':
    unittest.main()
