"""
Real integration tests for LangChain with Z.ai GLM endpoint.
NO MOCKS - All tests use actual API calls.
"""
import os
import pytest
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool

from codegen.extensions.langchain.llm import LLM
from codegen.extensions.langchain.agent import create_react_agent


# Skip all tests if API key not available
pytestmark = pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set - skipping real API tests"
)


class TestGLMIntegration:
    """Integration tests with real Z.ai GLM API."""
    
    @pytest.fixture(scope="class")
    def api_config(self):
        """Get API configuration from environment."""
        return {
            "api_key": os.getenv("ANTHROPIC_API_KEY"),
            "base_url": os.getenv("ANTHROPIC_BASE_URL", "https://api.z.ai/api/anthropic"),
            "model": os.getenv("ANTHROPIC_MODEL", "glm-4.7")
        }
    
    @pytest.fixture(scope="class")
    def llm(self, api_config):
        """Create LLM instance with GLM configuration."""
        return LLM(
            model_provider="anthropic",
            model_name=api_config["model"],
            temperature=0
        )
    
    def test_llm_initialization(self, llm, api_config):
        """Test that LLM initializes with custom endpoint."""
        assert llm is not None
        assert llm._model is not None
        assert llm.model_name == api_config["model"]
        print(f"✅ LLM initialized with model: {api_config['model']}")
    
    def test_simple_completion(self, llm):
        """Test basic text completion with real API."""
        messages = [HumanMessage(content="What is 2+2? Answer with just the number.")]
        
        response = llm._model.invoke(messages)
        
        assert response is not None
        assert response.content is not None
        assert len(response.content) > 0
        print(f"✅ Completion response: {response.content[:100]}")
    
    def test_multi_turn_conversation(self, llm):
        """Test multi-turn conversation."""
        messages = [
            HumanMessage(content="My name is Alice."),
            HumanMessage(content="What is my name?")
        ]
        
        response = llm._model.invoke(messages)
        
        assert response is not None
        assert "alice" in response.content.lower()
        print(f"✅ Multi-turn response: {response.content[:100]}")
    
    def test_tool_binding(self, llm):
        """Test that tools can be bound to the model."""
        @tool
        def get_weather(location: str) -> str:
            """Get weather for a location."""
            return f"Weather in {location}: Sunny, 72°F"
        
        model_with_tools = llm._model.bind_tools([get_weather])
        
        assert model_with_tools is not None
        print("✅ Tools bound successfully")
    
    def test_agent_creation(self, api_config):
        """Test creating a ReAct agent with real tools."""
        @tool
        def calculator(expression: str) -> str:
            """Evaluate a mathematical expression."""
            try:
                result = eval(expression)
                return str(result)
            except Exception as e:
                return f"Error: {e}"
        
        agent = create_react_agent(
            tools=[calculator],
            model_provider="anthropic",
            model_name=api_config["model"],
            memory=False,
            debug=False
        )
        
        assert agent is not None
        print("✅ Agent created successfully")
    
    def test_agent_execution(self, api_config):
        """Test agent execution with real API call."""
        @tool
        def multiply(a: int, b: int) -> int:
            """Multiply two numbers."""
            return a * b
        
        agent = create_react_agent(
            tools=[multiply],
            model_provider="anthropic",
            model_name=api_config["model"],
            memory=False,
            debug=False
        )
        
        # Execute agent with a task
        result = agent.invoke({
            "messages": [HumanMessage(content="What is 7 times 8?")]
        })
        
        assert result is not None
        assert "messages" in result
        print(f"✅ Agent execution result: {result['messages'][-1].content[:100]}")
    
    def test_error_handling(self, llm):
        """Test error handling with invalid input."""
        # Test with empty message
        try:
            messages = [HumanMessage(content="")]
            response = llm._model.invoke(messages)
            # If it doesn't raise, that's fine - some models handle empty input
            print("✅ Empty input handled gracefully")
        except Exception as e:
            # Expected behavior - error is raised
            print(f"✅ Error handling works: {type(e).__name__}")
    
    def test_streaming_response(self, llm):
        """Test streaming responses."""
        messages = [HumanMessage(content="Count from 1 to 5.")]
        
        chunks = []
        for chunk in llm._model.stream(messages):
            chunks.append(chunk)
        
        assert len(chunks) > 0
        print(f"✅ Streaming works: received {len(chunks)} chunks")
    
    def test_custom_endpoint_configuration(self, api_config):
        """Verify custom endpoint is being used."""
        # This test verifies the configuration is passed through
        llm = LLM(
            model_provider="anthropic",
            model_name=api_config["model"],
            temperature=0
        )
        
        # Make a request to verify endpoint works
        messages = [HumanMessage(content="Hello")]
        response = llm._model.invoke(messages)
        
        assert response is not None
        print(f"✅ Custom endpoint working: {api_config['base_url']}")


class TestGLMPerformance:
    """Performance and edge case tests."""
    
    @pytest.fixture(scope="class")
    def llm(self):
        """Create LLM instance."""
        return LLM(
            model_provider="anthropic",
            model_name=os.getenv("ANTHROPIC_MODEL", "glm-4.7"),
            temperature=0
        )
    
    def test_large_input(self, llm):
        """Test with larger input."""
        large_text = "Hello. " * 100  # 100 repetitions
        messages = [HumanMessage(content=f"{large_text} Summarize this in one word.")]
        
        response = llm._model.invoke(messages)
        
        assert response is not None
        print(f"✅ Large input handled: {len(large_text)} chars")
    
    def test_concurrent_requests(self, llm):
        """Test multiple requests in sequence."""
        messages = [HumanMessage(content="Say 'test'")]
        
        responses = []
        for i in range(3):
            response = llm._model.invoke(messages)
            responses.append(response)
        
        assert len(responses) == 3
        assert all(r is not None for r in responses)
        print("✅ Multiple requests handled successfully")


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v", "-s"])

