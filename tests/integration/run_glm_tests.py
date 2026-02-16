#!/usr/bin/env python3
"""
Simple test runner for GLM integration tests.
Bypasses pytest configuration issues.
"""
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from langchain_core.messages import HumanMessage
from langchain_core.tools import tool

from codegen.extensions.langchain.llm import LLM
from codegen.extensions.langchain.agent import create_react_agent


def check_environment():
    """Check required environment variables."""
    required = ["ANTHROPIC_API_KEY", "ANTHROPIC_BASE_URL", "ANTHROPIC_MODEL"]
    missing = [var for var in required if not os.getenv(var)]
    
    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}")
        return False
    
    print("✅ Environment variables set:")
    print(f"   ANTHROPIC_BASE_URL: {os.getenv('ANTHROPIC_BASE_URL')}")
    print(f"   ANTHROPIC_MODEL: {os.getenv('ANTHROPIC_MODEL')}")
    print(f"   ANTHROPIC_API_KEY: ***{os.getenv('ANTHROPIC_API_KEY')[-10:]}")
    return True


def test_llm_initialization():
    """Test LLM initialization."""
    print("\n" + "="*60)
    print("Test 1: LLM Initialization")
    print("="*60)
    
    try:
        llm = LLM(
            model_provider="anthropic",
            model_name=os.getenv("ANTHROPIC_MODEL"),
            temperature=0
        )
        print(f"✅ LLM initialized successfully")
        print(f"   Model: {llm.model_name}")
        return llm
    except Exception as e:
        print(f"❌ LLM initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_simple_completion(llm):
    """Test simple completion."""
    print("\n" + "="*60)
    print("Test 2: Simple Completion")
    print("="*60)
    
    try:
        messages = [HumanMessage(content="What is 2+2? Answer with just the number.")]
        response = llm._model.invoke(messages)
        
        print(f"✅ Completion successful")
        print(f"   Response: {response.content[:200]}")
        return True
    except Exception as e:
        print(f"❌ Completion failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_multi_turn(llm):
    """Test multi-turn conversation."""
    print("\n" + "="*60)
    print("Test 3: Multi-turn Conversation")
    print("="*60)
    
    try:
        messages = [
            HumanMessage(content="My name is Alice."),
            HumanMessage(content="What is my name?")
        ]
        response = llm._model.invoke(messages)
        
        print(f"✅ Multi-turn successful")
        print(f"   Response: {response.content[:200]}")
        return True
    except Exception as e:
        print(f"❌ Multi-turn failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_tool_binding(llm):
    """Test tool binding."""
    print("\n" + "="*60)
    print("Test 4: Tool Binding")
    print("="*60)
    
    try:
        @tool
        def get_weather(location: str) -> str:
            """Get weather for a location."""
            return f"Weather in {location}: Sunny, 72°F"
        
        model_with_tools = llm._model.bind_tools([get_weather])
        print(f"✅ Tool binding successful")
        return True
    except Exception as e:
        print(f"❌ Tool binding failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_agent_creation():
    """Test agent creation."""
    print("\n" + "="*60)
    print("Test 5: Agent Creation")
    print("="*60)
    
    try:
        from langchain_core.messages import SystemMessage
        
        @tool
        def calculator(expression: str) -> str:
            """Evaluate a mathematical expression."""
            try:
                result = eval(expression)
                return str(result)
            except Exception as e:
                return f"Error: {e}"
        
        # Create LLM instance
        llm = LLM(
            model_provider="anthropic",
            model_name=os.getenv("ANTHROPIC_MODEL"),
            temperature=0
        )
        
        # Create agent with LLM instance
        agent = create_react_agent(
            model=llm,
            tools=[calculator],
            system_message=SystemMessage(content="You are a helpful assistant."),
            checkpointer=None,
            debug=False
        )
        
        print(f"✅ Agent created successfully")
        print(f"   Agent type: {type(agent)}")
        return agent
    except Exception as e:
        print(f"❌ Agent creation failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_agent_execution(agent):
    """Test agent execution."""
    print("\n" + "="*60)
    print("Test 6: Agent Execution")
    print("="*60)
    
    try:
        result = agent.invoke({
            "messages": [HumanMessage(content="What is 7 times 8?")]
        })
        
        print(f"✅ Agent execution successful")
        print(f"   Result: {result['messages'][-1].content[:200]}")
        return True
    except Exception as e:
        print(f"❌ Agent execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_streaming(llm):
    """Test streaming responses."""
    print("\n" + "="*60)
    print("Test 7: Streaming Responses")
    print("="*60)
    
    try:
        messages = [HumanMessage(content="Count from 1 to 5.")]
        
        chunks = []
        for chunk in llm._model.stream(messages):
            chunks.append(chunk)
        
        print(f"✅ Streaming successful")
        print(f"   Received {len(chunks)} chunks")
        return True
    except Exception as e:
        print(f"❌ Streaming failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("LangChain GLM Integration Test Suite")
    print("="*60)
    
    if not check_environment():
        sys.exit(1)
    
    # Test 1: LLM initialization
    llm = test_llm_initialization()
    if not llm:
        print("\n❌ Test suite failed at LLM initialization")
        sys.exit(1)
    
    # Test 2: Simple completion
    test_simple_completion(llm)
    
    # Test 3: Multi-turn
    test_multi_turn(llm)
    
    # Test 4: Tool binding
    test_tool_binding(llm)
    
    # Test 5: Agent creation
    agent = test_agent_creation()
    
    # Test 6: Agent execution (if agent created)
    if agent:
        test_agent_execution(agent)
    
    # Test 7: Streaming
    test_streaming(llm)
    
    # Summary
    print("\n" + "="*60)
    print("Test Suite Complete")
    print("="*60)
    print("✅ All integration tests completed")
    print("   Check output above for individual test results")
    print("="*60)


if __name__ == "__main__":
    main()
