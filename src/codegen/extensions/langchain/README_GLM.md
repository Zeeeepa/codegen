# Using GLM Models with LangChain Integration

This guide explains how to use GLM (or other Anthropic-compatible) models with the Codegen LangChain integration.

## Overview

The LangChain integration now supports custom Anthropic-compatible endpoints, allowing you to use alternative models like GLM that implement the Anthropic API format.

## Configuration

### Environment Variables

Set the following environment variables to use a custom endpoint:

```bash
# Required: Your API key for the custom endpoint
export ANTHROPIC_API_KEY=your_api_key_here

# Required: The base URL of your custom endpoint
export ANTHROPIC_BASE_URL=http://your-glm-endpoint/v1

# Optional: Custom model name (if different from default)
export ANTHROPIC_MODEL=glm-4.7
```

### Using .env File

Alternatively, create a `.env` file in your project root:

```env
ANTHROPIC_API_KEY=your_api_key_here
ANTHROPIC_BASE_URL=http://your-glm-endpoint/v1
ANTHROPIC_MODEL=glm-4.7
```

## Usage

Once configured, use the LangChain integration as normal:

```python
from codegen.extensions.langchain.llm import LLM
from codegen.extensions.langchain.agent import create_agent_with_tools

# Create LLM instance - will automatically use custom endpoint
llm = LLM(
    model_provider="anthropic",
    model_name="glm-4.7"  # Or use ANTHROPIC_MODEL env var
)

# Create an agent
agent = create_agent_with_tools(
    tools=[...],
    model_provider="anthropic",
    model_name="glm-4.7"
)
```

## Testing

A test script is provided to validate your configuration:

```bash
# Set environment variables
export ANTHROPIC_API_KEY=your_key
export ANTHROPIC_BASE_URL=http://your-endpoint
export ANTHROPIC_MODEL=glm-4.7

# Run the test script
python scripts/test_langchain_glm.py
```

The test script will:
1. ✅ Verify environment variables are set
2. ✅ Test LLM initialization
3. ✅ Test simple completion (no tools)
4. ✅ Test tool binding capability
5. ✅ Test agent creation

## Compatibility Notes

### What Works
- ✅ Basic text completion
- ✅ LLM initialization with custom endpoints
- ✅ Agent creation

### What Might Not Work
- ⚠️ **Tool calling**: GLM models may not fully support Anthropic's tool calling format
- ⚠️ **Streaming**: Streaming responses may behave differently
- ⚠️ **Advanced features**: Some Anthropic-specific features may not be available

### Troubleshooting

#### Connection Errors
If you see connection errors:
1. Verify `ANTHROPIC_BASE_URL` is correct and accessible
2. Check that the endpoint is running
3. Ensure your API key is valid

#### Tool Calling Issues
If tool calling doesn't work:
1. The GLM model may not support Anthropic's tool format
2. Try using the agent without tools first
3. Check GLM documentation for tool calling support

#### Model Not Found
If you see "model not found" errors:
1. Verify `ANTHROPIC_MODEL` matches the model name on your endpoint
2. Check that the model is available on your GLM instance

## Logging

The integration includes logging for debugging:

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.INFO)

# You'll see messages like:
# INFO - Using custom Anthropic endpoint: http://your-endpoint
# INFO - Using custom Anthropic model: glm-4.7
```

## Example: Complete Setup

```python
import os
from codegen.extensions.langchain.llm import LLM
from codegen.extensions.langchain.agent import create_codebase_agent
from codegen import Codebase

# Set environment variables (or use .env file)
os.environ["ANTHROPIC_API_KEY"] = "your_key"
os.environ["ANTHROPIC_BASE_URL"] = "http://your-glm-endpoint/v1"
os.environ["ANTHROPIC_MODEL"] = "glm-4.7"

# Create a codebase instance
codebase = Codebase.from_path("/path/to/your/code")

# Create an agent with GLM model
agent = create_codebase_agent(
    codebase=codebase,
    model_provider="anthropic",
    model_name="glm-4.7",
    memory=True,
    debug=True
)

# Use the agent
result = agent.invoke({
    "messages": [{"role": "user", "content": "Analyze this codebase"}]
})
```

## Support

For issues or questions:
1. Check the test script output for diagnostic information
2. Enable debug logging to see detailed connection info
3. Verify your GLM endpoint is Anthropic-compatible
4. Consult GLM documentation for model-specific limitations

