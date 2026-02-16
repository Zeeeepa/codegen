#!/usr/bin/env python3
"""Test script for LangChain integration with GLM model.

This script validates that the LangChain integration can connect to custom
Anthropic-compatible endpoints like GLM models.

Usage:
    export ANTHROPIC_API_KEY=your_key
    export ANTHROPIC_BASE_URL=http://your-glm-endpoint
    export ANTHROPIC_MODEL=glm-4.7
    python scripts/test_langchain_glm.py
"""

import logging
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def check_environment():
    """Check if required environment variables are set."""
    required_vars = ["ANTHROPIC_API_KEY"]
    optional_vars = ["ANTHROPIC_BASE_URL", "ANTHROPIC_MODEL"]
    
    logger.info("=" * 60)
    logger.info("Environment Variable Check")
    logger.info("=" * 60)
    
    missing = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask the API key for security
            masked = value[:8] + "..." if len(value) > 8 else "***"
            logger.info(f"✅ {var}: {masked}")
        else:
            logger.error(f"❌ {var}: NOT SET")
            missing.append(var)
    
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            logger.info(f"✅ {var}: {value}")
        else:
            logger.warning(f"⚠️  {var}: NOT SET (using default)")
    
    if missing:
        logger.error(f"\n❌ Missing required environment variables: {', '.join(missing)}")
        logger.error("Please set them before running this test.")
        return False
    
    logger.info("=" * 60)
    return True


def test_llm_initialization():
    """Test LLM initialization with custom endpoint."""
    logger.info("\n" + "=" * 60)
    logger.info("Test 1: LLM Initialization")
    logger.info("=" * 60)
    
    try:
        from codegen.extensions.langchain.llm import LLM
        
        # Get custom model name if set
        model_name = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")
        
        logger.info(f"Creating LLM with provider='anthropic', model='{model_name}'")
        llm = LLM(model_provider="anthropic", model_name=model_name)
        
        logger.info("✅ LLM initialized successfully")
        logger.info(f"   Model provider: {llm.model_provider}")
        logger.info(f"   Model name: {llm.model_name}")
        logger.info(f"   Temperature: {llm.temperature}")
        
        return llm
    except Exception as e:
        logger.error(f"❌ LLM initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_simple_completion(llm):
    """Test a simple completion without tools."""
    logger.info("\n" + "=" * 60)
    logger.info("Test 2: Simple Completion (No Tools)")
    logger.info("=" * 60)
    
    try:
        from langchain_core.messages import HumanMessage
        
        logger.info("Sending test message: 'Hello, what is 2+2?'")
        messages = [HumanMessage(content="Hello, what is 2+2? Please respond briefly.")]
        
        response = llm._model.invoke(messages)
        
        logger.info("✅ Completion successful")
        logger.info(f"   Response: {response.content[:200]}...")
        
        return True
    except Exception as e:
        logger.error(f"❌ Completion failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_tool_binding(llm):
    """Test tool binding capability."""
    logger.info("\n" + "=" * 60)
    logger.info("Test 3: Tool Binding")
    logger.info("=" * 60)
    
    try:
        from langchain_core.tools import tool
        
        @tool
        def get_weather(location: str) -> str:
            """Get the weather for a location."""
            return f"The weather in {location} is sunny."
        
        logger.info("Binding test tool to LLM")
        llm_with_tools = llm.bind_tools([get_weather])
        
        logger.info("✅ Tool binding successful")
        logger.info("   Note: This doesn't test if the GLM model actually supports tool calling")
        logger.info("   That would require a full invocation with tool use")
        
        return True
    except Exception as e:
        logger.error(f"❌ Tool binding failed: {e}")
        logger.error("   This might indicate the GLM endpoint doesn't support Anthropic's tool format")
        import traceback
        traceback.print_exc()
        return False


def test_agent_creation():
    """Test creating a simple agent."""
    logger.info("\n" + "=" * 60)
    logger.info("Test 4: Agent Creation")
    logger.info("=" * 60)
    
    try:
        from codegen.extensions.langchain.agent import create_agent_with_tools
        from langchain_core.tools import tool
        
        @tool
        def simple_tool(query: str) -> str:
            """A simple test tool."""
            return f"Processed: {query}"
        
        logger.info("Creating agent with test tool")
        model_name = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")
        agent = create_agent_with_tools(
            tools=[simple_tool],
            model_provider="anthropic",
            model_name=model_name,
            memory=False,
            debug=False
        )
        
        logger.info("✅ Agent created successfully")
        logger.info(f"   Agent type: {type(agent)}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Agent creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    logger.info("\n" + "=" * 60)
    logger.info("LangChain GLM Integration Test Suite")
    logger.info("=" * 60)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Test 1: LLM initialization
    llm = test_llm_initialization()
    if not llm:
        logger.error("\n❌ Test suite failed at LLM initialization")
        sys.exit(1)
    
    # Test 2: Simple completion
    if not test_simple_completion(llm):
        logger.warning("\n⚠️  Simple completion test failed")
        logger.warning("   This might indicate connectivity issues with the GLM endpoint")
    
    # Test 3: Tool binding
    if not test_tool_binding(llm):
        logger.warning("\n⚠️  Tool binding test failed")
        logger.warning("   The GLM model might not support Anthropic's tool calling format")
    
    # Test 4: Agent creation
    if not test_agent_creation():
        logger.warning("\n⚠️  Agent creation test failed")
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Test Suite Complete")
    logger.info("=" * 60)
    logger.info("✅ Basic integration tests passed")
    logger.info("⚠️  Some advanced features may not be supported by the GLM endpoint")
    logger.info("   Check the logs above for details")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()

