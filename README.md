# Codegen SDK

A powerful Python SDK to interact with intelligent code generation agents, providing comprehensive code analysis and manipulation capabilities.

## Features

The Codegen SDK provides a rich set of features for code analysis and manipulation:

### 1. Code Analysis

- Static code analysis for Python and TypeScript
- Symbol tree analysis (functions, classes, variables)
- Import/Export analysis
- Dependency and usage tracking
- Type inference and checking

### 2. Code Manipulation

- Programmatic code editing and refactoring
- Symbol renaming and moving
- Import management
- Code generation with AI assistance
- Automated code transformations (codemods)

### 3. AI Integration

- Integration with LLMs for code generation and analysis
- Context-aware code suggestions
- Documentation generation
- Code quality improvements

### 4. Extensions and Integrations

- GitHub integration for PR analysis and creation
- Linear integration for issue tracking
- Slack integration for notifications and chat
- MCP (Model Context Protocol) support
- Visualization tools for code analysis

### 5. CLI Tools

- Interactive code exploration
- Codemod execution
- Project initialization
- Notebook integration

## Installation

1. Install the Codegen SDK:

```bash
pip install codegen-sdk
```

2. Initialize a project:

```bash
codegen init
```

## Usage

### Basic Code Analysis

```python
from codegen import Codebase

# Load a codebase
codebase = Codebase("path/to/your/code")

# Analyze functions
for function in codebase.functions:
    print(f"Function: {function.name}")
    print(f"  Parameters: {[p.name for p in function.parameters]}")
    print(f"  Return type: {function.return_type}")
    print(f"  Call sites: {len(list(function.call_sites))}")
```

### Code Manipulation

```python
# Find a function
function = codebase.get_function("process_data")

# Rename the function
function.rename("process_data_v2")

# Add a parameter
function.add_parameter("debug", "bool = False")

# Add a docstring
function.set_docstring("Process data with optional debug mode")

# Commit changes
codebase.commit("Update process_data function")
```

### AI-Assisted Code Generation

```python
# Set your OpenAI API key
codebase.set_ai_key("your-openai-api-key")

# Generate a test for a function
function = codebase.get_function("calculate_total")
test_code = codebase.ai(
    f"Write a pytest test for the function {function.name}",
    target=function
)

# Create a new test file
test_file = codebase.create_file(f"tests/test_{function.file.stem}.py")
test_file.write(test_code)
```

## Documentation

For full documentation, visit [docs.codegen.com](https://docs.codegen.com).

## Examples

Check out the [codegen-examples](https://github.com/Zeeeepa/codegen-examples) repository for more examples and use cases.

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

MIT

