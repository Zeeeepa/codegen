import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import uuid

from codegen.agents.planning.planning_agent import PlanningAgent
from codegen.agents.planning.planning import PlanManager, PlanStepStatus
from codegen.agents.planning.flow import PlanningFlow

class TestPlanningAgent(unittest.TestCase):
    """Test cases for the PlanningAgent class."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock PlanManager
        self.plan_manager_patcher = patch('codegen.agents.planning.planning_agent.PlanManager')
        self.mock_plan_manager_class = self.plan_manager_patcher.start()
        self.mock_plan_manager = MagicMock()
        self.mock_plan_manager_class.return_value = self.mock_plan_manager
        
        # Mock PlanningTool
        self.planning_tool_patcher = patch('codegen.agents.planning.planning_agent.PlanningTool')
        self.mock_planning_tool_class = self.planning_tool_patcher.start()
        self.mock_planning_tool = MagicMock()
        self.mock_planning_tool_class.return_value = self.mock_planning_tool
        
        # Mock PlanningFlow
        self.planning_flow_patcher = patch('codegen.agents.planning.planning_agent.PlanningFlow')
        self.mock_planning_flow_class = self.planning_flow_patcher.start()
        self.mock_planning_flow = MagicMock()
        self.mock_planning_flow_class.return_value = self.mock_planning_flow
        
        # Mock BaseAgent.__init__
        self.base_agent_patcher = patch('codegen.agents.base.BaseAgent.__init__')
        self.mock_base_agent_init = self.base_agent_patcher.start()
        self.mock_base_agent_init.return_value = None

    def tearDown(self):
        """Tear down test fixtures."""
        self.plan_manager_patcher.stop()
        self.planning_tool_patcher.stop()
        self.planning_flow_patcher.stop()
        self.base_agent_patcher.stop()

    def test_init_default_params(self):
        """Test initialization with default parameters."""
        agent = PlanningAgent()
        
        # Check that the base agent was initialized correctly
        self.mock_base_agent_init.assert_called_once_with(
            model_provider="anthropic",
            model_name="claude-3-5-sonnet-latest",
            memory=True
        )
        
        # Check that the agent properties are set correctly
        self.assertEqual(agent.max_iterations, 10)
        self.assertEqual(agent.message_history, {})
        self.assertEqual(agent.plan_manager, self.mock_plan_manager)
        self.assertEqual(agent.planning_tool, self.mock_planning_tool)
        self.assertEqual(agent.flows, {})

    def test_init_custom_params(self):
        """Test initialization with custom parameters."""
        agent = PlanningAgent(
            model_provider="openai",
            model_name="gpt-4o",
            memory=False,
            max_iterations=5,
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
        self.assertEqual(agent.max_iterations, 5)

    @patch('uuid.uuid4')
    async def test_run_new_thread(self, mock_uuid):
        """Test the run method with a new thread."""
        # Set up mocks
        mock_uuid.return_value = uuid.UUID('12345678-1234-5678-1234-567812345678')
        self.mock_planning_flow.execute = AsyncMock(return_value="Test response")
        
        # Create agent and run
        agent = PlanningAgent()
        response = await agent.run("Test prompt")
        
        # Check that the flow was created and executed correctly
        self.mock_planning_flow_class.assert_called_once_with(
            agents={"default": agent},
            planning_tool=self.mock_planning_tool,
            plan_id="plan_12345678-1234-5678-1234-567812345678"
        )
        self.mock_planning_flow.execute.assert_called_once_with("Test prompt")
        
        # Check that the message history was updated
        self.assertEqual(len(agent.message_history["12345678-1234-5678-1234-567812345678"]), 2)
        self.assertEqual(agent.message_history["12345678-1234-5678-1234-567812345678"][0]["role"], "user")
        self.assertEqual(agent.message_history["12345678-1234-5678-1234-567812345678"][0]["content"], "Test prompt")
        self.assertEqual(agent.message_history["12345678-1234-5678-1234-567812345678"][1]["role"], "assistant")
        self.assertEqual(agent.message_history["12345678-1234-5678-1234-567812345678"][1]["content"], "Test response")
        
        # Check the result
        self.assertEqual(response, "Test response")

    async def test_run_existing_thread(self):
        """Test the run method with an existing thread."""
        # Set up existing thread
        agent = PlanningAgent()
        agent.message_history["existing-thread"] = [{"role": "user", "content": "Previous prompt"}]
        agent.flows["existing-thread"] = self.mock_planning_flow
        
        # Set up mock response
        self.mock_planning_flow.execute = AsyncMock(return_value="Test response")
        
        # Run with existing thread
        response = await agent.run("Test prompt", thread_id="existing-thread")
        
        # Check that the flow was executed correctly
        self.mock_planning_flow.execute.assert_called_once_with("Test prompt")
        
        # Check that the message history was updated
        self.assertEqual(len(agent.message_history["existing-thread"]), 2)
        self.assertEqual(agent.message_history["existing-thread"][1]["role"], "assistant")
        self.assertEqual(agent.message_history["existing-thread"][1]["content"], "Test response")
        
        # Check the result
        self.assertEqual(response, "Test response")

    def test_get_chat_history(self):
        """Test the get_chat_history method."""
        # Set up message history
        agent = PlanningAgent()
        agent.message_history["test-thread"] = [{"role": "user", "content": "Test prompt"}]
        
        # Get chat history
        history = agent.get_chat_history("test-thread")
        
        # Check the result
        self.assertEqual(history, [{"role": "user", "content": "Test prompt"}])

    def test_get_chat_history_empty(self):
        """Test the get_chat_history method with an empty history."""
        # Create agent
        agent = PlanningAgent()
        
        # Get chat history for non-existent thread
        history = agent.get_chat_history("non-existent-thread")
        
        # Check the result
        self.assertEqual(history, [])

    def test_get_plan(self):
        """Test the get_plan method."""
        # Set up mock plan
        mock_plan = {"steps": ["step1", "step2"]}
        self.mock_planning_tool.plans = {"plan_test-thread": mock_plan}
        
        # Set up flow
        agent = PlanningAgent()
        mock_flow = MagicMock()
        mock_flow.active_plan_id = "plan_test-thread"
        agent.flows["test-thread"] = mock_flow
        
        # Get plan
        plan = agent.get_plan("test-thread")
        
        # Check the result
        self.assertEqual(plan, mock_plan)

    def test_get_plan_no_flow(self):
        """Test the get_plan method when no flow exists."""
        # Create agent
        agent = PlanningAgent()
        
        # Get plan for non-existent thread
        plan = agent.get_plan("non-existent-thread")
        
        # Check the result
        self.assertIsNone(plan)

    def test_get_plan_no_plan_id(self):
        """Test the get_plan method when no plan ID exists."""
        # Set up flow without plan ID
        agent = PlanningAgent()
        mock_flow = MagicMock()
        mock_flow.active_plan_id = None
        agent.flows["test-thread"] = mock_flow
        
        # Get plan
        plan = agent.get_plan("test-thread")
        
        # Check the result
        self.assertIsNone(plan)

    def test_get_plan_invalid_plan_id(self):
        """Test the get_plan method with an invalid plan ID."""
        # Set up flow with invalid plan ID
        agent = PlanningAgent()
        mock_flow = MagicMock()
        mock_flow.active_plan_id = "invalid-plan-id"
        agent.flows["test-thread"] = mock_flow
        
        # Set up empty plans
        self.mock_planning_tool.plans = {}
        
        # Get plan
        plan = agent.get_plan("test-thread")
        
        # Check the result
        self.assertIsNone(plan)

if __name__ == '__main__':
    unittest.main()
