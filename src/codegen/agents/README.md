# Codegen Agents Module

This module provides interfaces for interacting with AI-powered code generation agents. It includes classes for different agent types and utilities for handling agent messages and state.

## Installation

The Codegen Agent SDK is included as part of the Codegen package. Ensure you have the latest version installed:

```bash
pip install codegen
```

## Agent Types

The module provides three main agent types:

1. **Agent**: Basic API client for interacting with Codegen AI agents via REST API
2. **ChatAgent**: Agent for interactive conversations about a codebase
3. **CodeAgent**: Agent for code generation and analysis with advanced features

## Usage Examples

### Basic Agent

The `Agent` class provides a simple interface for interacting with Codegen AI agents via the REST API:

```python
from codegen.agents import Agent

# Initialize the Agent with your organization ID and API token
agent = Agent(
    token="your_api_token_here",  # Your API authentication token
    org_id=123,  # Your organization ID (optional)
)

# Run an agent with a prompt
job = agent.run("Create a Python function to calculate Fibonacci numbers")

# Check the initial status
print(f"Job ID: {job.id}")
print(f"Status: {job.status}")

# Refresh the job to get updated status
job.refresh()

# Check the updated status
print(f"Updated status: {job.status}")

# Once job is complete, you can access the result
if job.status == "completed":
    print(f"Result: {job.result}")
```

### Chat Agent

The `ChatAgent` class provides an interface for interactive conversations about a codebase:

```python
from codegen import Codebase
from codegen.agents import ChatAgent

# Initialize a codebase
codebase = Codebase("path/to/repo")

# Create a chat agent
agent = ChatAgent(
    codebase=codebase,
    model_provider="anthropic",  # "anthropic" or "openai"
    model_name="claude-3-5-sonnet-latest",
    memory=True,  # Enable conversation memory
)

# Start a conversation
response, thread_id = agent.chat("How can I optimize this code?")
print(response)

# Continue the conversation with the same thread_id
follow_up, thread_id = agent.chat("What about memory usage?", thread_id=thread_id)
print(follow_up)

# Get the chat history for a thread
history = agent.get_chat_history(thread_id)
for message in history:
    print(f"{message.__class__.__name__}: {message.content}")
```

### Code Agent

The `CodeAgent` class provides advanced features for code generation and analysis:

```python
from codegen import Codebase
from codegen.agents import CodeAgent
from codegen.agents.utils import AgentConfig

# Initialize a codebase
codebase = Codebase("path/to/repo")

# Create a code agent with custom configuration
agent_config = AgentConfig(
    keep_first_messages=2,  # Number of initial messages to keep during summarization
    max_messages=50,  # Maximum number of messages before triggering summarization
)

# Create a code agent
agent = CodeAgent(
    codebase=codebase,
    model_provider="anthropic",  # "anthropic" or "openai"
    model_name="claude-3-7-sonnet-latest",
    memory=True,  # Enable conversation memory
    agent_config=agent_config,
    temperature=0.7,  # Control randomness (0-1)
)

# Generate code based on a prompt
result = agent.run("Create a function to parse JSON data")
print(result)

# Generate code based on a prompt with images
image_urls = ["data:image/png;base64,abc123"]  # Base64-encoded image
result = agent.run("Implement this UI design", image_urls=image_urls)
print(result)

# Get the agent's tools
tools = agent.get_tools()
print(f"Available tools: {[tool.name for tool in tools]}")

# Get the agent's state
state = agent.get_state()
print(f"Agent state: {state}")

# Get the agent trace URL for debugging
trace_url = agent.get_agent_trace_url()
print(f"Agent trace URL: {trace_url}")
```

## Message Tracing and Logging

The module includes utilities for tracing and logging agent messages:

```python
from codegen.agents.tracer import MessageStreamTracer
from codegen.agents.data import UserMessage

# Create a custom logger
class CustomLogger:
    def __init__(self):
        self.logs = []
        
    def log(self, data):
        self.logs.append(data)
        print(f"Logged: {data.type} - {data.content[:50]}...")

# Create a tracer with the custom logger
tracer = MessageStreamTracer(logger=CustomLogger())

# Process a message stream (typically from an agent)
def message_stream():
    yield {"messages": [UserMessage(content="Hello")]}
    # More messages...

processed_stream = tracer.process_stream(message_stream())
for chunk in processed_stream:
    # Process the chunk
    pass

# Get all traces
traces = tracer.get_traces()
```

## API Reference

### Agent Class

```python
Agent(token: str, org_id: int | None = None, base_url: str | None = CODEGEN_BASE_API_URL)
```

**Methods:**
- `run(prompt: str) -> AgentTask`: Run an agent with the given prompt
- `get_status() -> dict[str, Any] | None`: Get the status of the current job

### ChatAgent Class

```python
ChatAgent(codebase: "Codebase", model_provider: str = "anthropic", model_name: str = "claude-3-5-sonnet-latest", memory: bool = True, tools: list[BaseTool] | None = None, **kwargs)
```

**Methods:**
- `run(prompt: str, thread_id: str | None = None) -> str`: Run the agent with a prompt
- `chat(prompt: str, thread_id: str | None = None) -> tuple[str, str]`: Chat with the agent, maintaining conversation history
- `get_chat_history(thread_id: str) -> list`: Retrieve the chat history for a specific thread

### CodeAgent Class

```python
CodeAgent(codebase: "Codebase", model_provider: str = "anthropic", model_name: str = "claude-3-7-sonnet-latest", memory: bool = True, tools: list[BaseTool] | None = None, tags: list[str] | None = [], metadata: dict | None = {}, agent_config: AgentConfig | None = None, thread_id: str | None = None, logger: ExternalLogger | None = None, **kwargs)
```

**Methods:**
- `run(prompt: str, image_urls: list[str] | None = None) -> str`: Run the agent with a prompt and optional images
- `get_agent_trace_url() -> str | None`: Get the URL for the most recent agent run in LangSmith
- `get_tools() -> list[BaseTool]`: Get the tools available to the agent
- `get_state() -> dict`: Get the current state of the agent
- `get_tags_metadata() -> tuple[list[str], dict]`: Get the tags and metadata for the agent

### AgentConfig TypedDict

```python
AgentConfig(keep_first_messages: int, max_messages: int)
```

- `keep_first_messages`: Number of initial messages to keep during summarization
- `max_messages`: Maximum number of messages before triggering summarization

## Environment Variables

- `CODEGEN_ORG_ID`: Default organization ID (used if `org_id` is not provided)
- `LANGCHAIN_PROJECT`: Project name for LangSmith tracing (used by CodeAgent)

## Error Handling

Handle potential API errors using standard try/except blocks:

```python
try:
    job = agent.run("Your prompt here")
    job.refresh()
    print(job.status)
except Exception as e:
    print(f"Error: {e}")
```

