# Codegen Agents

This directory contains a collection of intelligent agents designed to perform various tasks related to code analysis, generation, and manipulation.

## Available Agents

### CodeAgent

This agent analyzes and manipulates codebases with powerful code viewing and manipulation tools.

```python
from codegen import CodeAgent, Codebase

# Grab a repo from Github
codebase = Codebase.from_repo('fastapi/fastapi')

# Create a code agent with read/write codebase access
agent = CodeAgent(codebase)

# Run the agent with a prompt
agent.run("Tell me about this repo")
```

The agent has access to powerful code viewing and manipulation tools powered by Codegen, including:
• `ViewFileTool`: View contents and metadata of files
• `SemanticEditTool`: Make intelligent edits to files
• `RevealSymbolTool`: Analyze symbol dependencies and usages
• `MoveSymbolTool`: Move symbols between files with import handling
• `ReplacementEditTool`: Make regex-based replacement editing on files
• `ListDirectoryTool`: List directory contents
• `SearchTool`: Search for files and symbols
• `CreateFileTool`: Create new files
• `DeleteFileTool`: Delete files
• `RenameFileTool`: Rename files
• `EditFileTool`: Edit files

View the full code for the default tools and agent implementation in our [examples repository](https://github.com/codegen-sh/codegen-sdk/tree/develop/src/codegen/extensions/langchain/tools)

#### Basic Usage

The following example shows how to create and run a `CodeAgent`:

```python
from codegen import CodeAgent, Codebase

# Grab a repo from Github
codebase = Codebase.from_repo('fastapi/fastapi')

# Create a code agent with read/write codebase access
agent = CodeAgent(codebase)

# Run the agent with a prompt
agent.run("Tell me about this repo")
```

Your `ANTHROPIC_API_KEY` must be set in your env.
The default implementation uses `anthropic/claude-3-5-sonnet-latest` for the model but this can be changed through the `model_provider` and `model_name` arguments.

```python
agent = CodeAgent(
    codebase=codebase,
    model_provider="openai",
    model_name="gpt-4o",
)
```

If using a non-default model provider, make sure to set the appropriate API key (e.g., `OPENAI_API_KEY` for OpenAI models) in your env.

#### Available Tools

The agent comes with a comprehensive set of tools for code analysis and manipulation. Here are some key tools:

```python
from codegen.extensions.langchain.tools import (
    CreateFileTool,
    DeleteFileTool,
    EditFileTool,
    ListDirectoryTool,
    MoveSymbolTool,
    RenameFileTool,
    ReplacementEditTool,
    RevealSymbolTool,
    SearchTool,
    SemanticEditTool,
    ViewFileTool,
)
```

View the full set of [tools on Github](https://github.com/codegen-sh/codegen-sdk/blob/develop/src/codegen/extensions/langchain/tools.py)

### ChatAgent

The ChatAgent provides conversational capabilities for interacting with users and answering questions.

```python
from codegen import ChatAgent

# Create a chat agent
agent = ChatAgent()

# Run the agent with a prompt
response = agent.run("What are the best practices for writing clean code?")
print(response)
```

The ChatAgent is designed for natural language interactions and can:
• Answer programming questions
• Explain code concepts
• Provide guidance on best practices
• Assist with debugging issues
• Generate code snippets based on requirements

#### Basic Usage

```python
from codegen import ChatAgent

# Create a chat agent with custom model
agent = ChatAgent(
    model_provider="anthropic",
    model_name="claude-3-5-sonnet-latest"
)

# Run the agent with a prompt
response = agent.run("Explain the concept of dependency injection")
print(response)
```

### PlanningAgent

The PlanningAgent helps break down complex tasks into manageable steps and create execution plans.

```python
from codegen import PlanningAgent, Codebase

# Create a planning agent
agent = PlanningAgent()

# Generate a plan for implementing a feature
plan = agent.run("Create a user authentication system with login, registration, and password reset")
print(plan)
```

The PlanningAgent can:
• Break down complex tasks into steps
• Identify dependencies between tasks
• Estimate effort for each task
• Suggest implementation approaches
• Create a structured execution plan

#### Basic Usage

```python
from codegen import PlanningAgent, Codebase

# Create a planning agent with a codebase for context
codebase = Codebase.from_repo('my-org/my-repo')
agent = PlanningAgent(codebase=codebase)

# Generate a plan with codebase context
plan = agent.run("Refactor the authentication system to use JWT tokens")
print(plan)
```

### PRReviewAgent

The PRReviewAgent analyzes pull requests and provides code review feedback.

```python
from codegen import PRReviewAgent
from codegen.extensions.github.types.events.pull_request import PullRequestEvent

# Create a PR review agent
agent = PRReviewAgent()

# Review a pull request
pr_event = PullRequestEvent(pr_number=123, repo="owner/repo")
review = agent.run(pr_event)
print(review)
```

The PRReviewAgent can:
• Analyze code changes in pull requests
• Identify potential bugs and issues
• Suggest improvements and optimizations
• Check for adherence to coding standards
• Provide constructive feedback

#### Basic Usage

```python
from codegen import PRReviewAgent, Codebase
from codegen.extensions.github.types.events.pull_request import PullRequestEvent

# Create a PR review agent with GitHub integration
agent = PRReviewAgent(
    github_token="your_github_token"
)

# Review a pull request
pr_event = PullRequestEvent(pr_number=123, repo="owner/repo")
review = agent.run(pr_event)
```

### MCPAgent

The MCPAgent (Master Control Program Agent) orchestrates multiple agents to solve complex problems.

```python
from codegen import MCPAgent, CodeAgent, PlanningAgent

# Create component agents
code_agent = CodeAgent(codebase)
planning_agent = PlanningAgent()

# Create MCP agent to orchestrate them
agent = MCPAgent(agents=[code_agent, planning_agent])

# Run the MCP agent with a complex task
result = agent.run("Implement a new feature for user profile management")
```

The MCPAgent can:
• Coordinate multiple specialized agents
• Delegate subtasks to appropriate agents
• Synthesize results from different agents
• Handle complex multi-step workflows
• Manage context and state across agents

#### Basic Usage

```python
from codegen import MCPAgent, CodeAgent, ChatAgent, PlanningAgent

# Create component agents
code_agent = CodeAgent(codebase)
chat_agent = ChatAgent()
planning_agent = PlanningAgent()

# Create MCP agent with custom configuration
agent = MCPAgent(
    agents=[code_agent, chat_agent, planning_agent],
    orchestration_strategy="sequential"
)

# Run the MCP agent
result = agent.run("Analyze the codebase, create a plan for implementing a new API, and generate the code")
```

### ToolCallAgent

The ToolCallAgent provides a framework for using tools to accomplish tasks.

```python
from codegen import ToolCallAgent, Tool
from pydantic import BaseModel, Field

# Define a custom tool
class CalculatorInput(BaseModel):
    expression: str = Field(..., description="Math expression to evaluate")

class CalculatorTool(Tool):
    name = "calculator"
    description = "Evaluates mathematical expressions"
    input_schema = CalculatorInput

    def _run(self, expression: str) -> str:
        return str(eval(expression))

# Create a tool call agent with custom tools
agent = ToolCallAgent(tools=[CalculatorTool()])

# Run the agent with a prompt
result = agent.run("Calculate 2 + 2 * 3")
print(result)
```

The ToolCallAgent can:
• Use a variety of tools to accomplish tasks
• Select appropriate tools based on the task
• Parse and validate tool inputs
• Handle tool execution and error recovery
• Combine results from multiple tool calls

#### Basic Usage

```python
from codegen import ToolCallAgent
from codegen.extensions.langchain.tools import SearchTool, ViewFileTool

# Create a tool call agent with standard tools
agent = ToolCallAgent(
    tools=[SearchTool(), ViewFileTool()],
    model_provider="anthropic",
    model_name="claude-3-5-sonnet-latest"
)

# Run the agent with a prompt
result = agent.run("Find all files containing the word 'authentication' and show their content")
```

### ReflectionAgent

The ReflectionAgent analyzes its own reasoning and improves its problem-solving approach.

```python
from codegen import ReflectionAgent

# Create a reflection agent
agent = ReflectionAgent()

# Run the agent with a complex problem
solution = agent.run("Design a scalable architecture for a real-time chat application")
print(solution)
```

The ReflectionAgent can:
• Analyze its own reasoning process
• Identify flaws in its approach
• Consider alternative solutions
• Improve its problem-solving strategy
• Provide more robust and well-reasoned solutions

#### Basic Usage

```python
from codegen import ReflectionAgent

# Create a reflection agent with custom configuration
agent = ReflectionAgent(
    reflection_depth=3,
    model_provider="anthropic",
    model_name="claude-3-5-sonnet-latest"
)

# Run the agent with a prompt
solution = agent.run("Optimize a database query that's performing poorly")
```

### ResearchAgent

The ResearchAgent gathers and synthesizes information to answer complex questions.

```python
from codegen import ResearchAgent

# Create a research agent
agent = ResearchAgent()

# Run the agent with a research question
research = agent.run("What are the latest advancements in transformer models?")
print(research)
```

The ResearchAgent can:
• Search for relevant information
• Analyze and synthesize findings
• Evaluate source credibility
• Identify key insights and patterns
• Present comprehensive research results

#### Basic Usage

```python
from codegen import ResearchAgent

# Create a research agent with custom configuration
agent = ResearchAgent(
    search_depth=5,
    model_provider="anthropic",
    model_name="claude-3-5-sonnet-latest"
)

# Run the agent with a research question
research = agent.run("Compare different approaches to implementing microservices")
```

## Extensions

### GitHub Integration

Many agents include tools for GitHub operations like PR management. Set up GitHub access with:

```python
CODEGEN_SECRETS__GITHUB_TOKEN="..."
```

Import the GitHub tools:

```python
from codegen.extensions.langchain.tools import (
    GithubCreatePRTool,
    GithubViewPRTool,
    GithubCreatePRCommentTool,
    GithubCreatePRReviewCommentTool
)
```

These tools enable:
• Creating pull requests
• Viewing PR contents and diffs
• Adding general PR comments
• Adding inline review comments

View all Github tools on [Github](https://github.com/codegen-sh/codegen-sdk/blob/develop/src/codegen/extensions/langchain/tools.py)

### Linear Integration

Agents can interact with Linear for issue tracking and project management. To use Linear tools, set the following environment variables:

```
LINEAR_ACCESS_TOKEN="..."
LINEAR_TEAM_ID="..."
LINEAR_SIGNING_SECRET="..."
```

Import and use the Linear tools:

```python
from codegen.extensions.langchain.tools import (
    LinearGetIssueTool,
    LinearGetIssueCommentsTool,
    LinearCommentOnIssueTool,
    LinearSearchIssuesTool,
    LinearCreateIssueTool,
    LinearGetTeamsTool
)
```

These tools allow the agent to:
• Create and search issues
• Get issue details and comments
• Add comments to issues
• View team information

View all Linear tools on [Github](https://github.com/codegen-sh/codegen-sdk/blob/develop/src/codegen/extensions/langchain/tools.py)

## Adding Custom Tools

You can extend agents with custom tools:

```python
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from codegen import CodeAgent

class CustomToolInput(BaseModel):
    """Input schema for custom tool."""
    param: str = Field(..., description="Parameter description")

class CustomCodeTool(BaseTool):
    """A custom tool for the code agent."""
    name = "custom_tool"
    description = "Description of what the tool does"
    args_schema = CustomToolInput

    def _run(self, param: str) -> str:
        # Tool implementation
        return f"Processed {param}"

# Add custom tool to agent
tools.append(CustomCodeTool())
agent = CodeAgent(codebase, tools=tools, model_name="claude-3-5-sonnet-latest")
```
