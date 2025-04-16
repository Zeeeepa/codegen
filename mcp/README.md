# Codegen MCP (Model-Controller-Protocol) Server

This module provides a standardized interface for AI models to interact with codebases. It implements a set of operations for manipulating symbols, functions, classes, imports, and AI-related functionality.

## Architecture

The MCP server follows a Model-Controller-Protocol architecture:

- **Models**: Data structures representing code elements (Symbol, Function, Class, Import, etc.)
- **Controllers**: Business logic for operations on code elements
- **Protocol**: Request/response handling and routing

## Features

The MCP server provides the following operations:

### Symbol Operations

- Get symbols by name or pattern
- Check if a symbol exists
- Get all symbols, functions, classes, imports, etc.
- Get symbol usages
- Move symbols between files
- Rename symbols
- Remove symbols

### Function Operations

- Get/set function return types
- Get/modify function parameters
- Check if a function is async
- Get/add function decorators
- Get function calls
- Generate/set function docstrings
- Rename local variables
- Get function call sites and dependencies

### Class Operations

- Get class methods, properties, and attributes
- Check if a class is abstract
- Get parent class names
- Check if a class is a subclass of another
- Add/remove methods and attributes
- Convert a class to a protocol

### Import Operations

- Get import sources
- Update import sources
- Remove imports
- Rename imports

### AI Operations

- Set AI API keys
- Configure AI session options
- Call AI with prompts and context
- Get AI client configuration
- Use reflection to organize thoughts and plan next steps

## Usage

### Starting the Server

```bash
python -m mcp.server --host localhost --port 8000 --repo /path/to/your/repo
```

### Using the Client

```python
from mcp.client import MCPClient

# Initialize the client
client = MCPClient(host="localhost", port=8000)

# Get all symbols in the codebase
symbols = client.symbols()

# Get a specific symbol
symbol = client.get_symbol("MyClass")

# Rename a symbol
client.symbol_rename("old_name", "new_name")

# Call AI to generate code
response = client.ai("Generate a function to calculate factorial", 
                    target={"name": "math_utils.py"})

# Use reflection to organize thoughts and plan next steps
reflection = client.reflection(
    context_summary="Refactoring a large codebase",
    findings_so_far="Found many circular dependencies",
    current_challenges="How to break dependencies safely?",
    reflection_focus="architecture"
)
```

## AI Tools

The MCP server provides powerful AI tools to assist with code generation, analysis, and planning:

### Codebase AI

The `codebase.ai` tool provides the following capabilities:

- Code generation based on natural language prompts
- Code analysis and improvement suggestions
- Contextual modifications to existing code
- Documentation generation

Parameters:
- `prompt`: The instruction or query for the AI
- `target` (optional): The code to modify or analyze
- `context` (optional): Additional information to help the AI understand the task
- `model` (optional): The specific AI model to use

### Reflection

The `reflection` tool helps organize thoughts and plan next steps when working on complex problems. It's particularly useful for:

- Consolidating information from multiple sources
- Identifying knowledge gaps
- Creating a strategic plan
- Breaking down complex problems into manageable steps

Parameters:
- `context_summary`: Summary of the current context and problem being solved
- `findings_so_far`: Key information and insights gathered so far
- `current_challenges` (optional): Current obstacles or questions that need to be addressed
- `reflection_focus` (optional): Specific aspect to focus reflection on (e.g., 'architecture', 'performance', 'next steps')

See the [AI Tools Examples](examples/ai_tools/) for detailed usage examples.

## API Reference

See the docstrings in the code for detailed API documentation.

## License

This project is licensed under the same license as the Codegen project.
