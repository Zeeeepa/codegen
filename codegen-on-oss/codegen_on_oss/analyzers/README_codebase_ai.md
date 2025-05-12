# Codebase AI Module

The `codebase_ai.py` module provides AI-powered code analysis and generation capabilities for the Codegen analyzer system. It enables the generation of system prompts, context, and tools for AI models to analyze and generate code.

## Features

- **System Prompt Generation**: Create tailored prompts for AI models to analyze and modify code
- **Context Generation**: Format code and additional information for AI models
- **Tool Definitions**: Define tools for AI models to interact with the codebase
- **Flagging System**: Determine whether code elements should be flagged for modification

## Usage

### Basic Usage

```python
from codegen_on_oss.analyzers.codebase_ai import CodebaseAI, generate_system_prompt, generate_context

# Create a CodebaseAI instance
codebase_ai = CodebaseAI()

# Generate a system prompt
system_prompt = codebase_ai.generate_system_prompt()

# Generate a system prompt with a target
system_prompt = codebase_ai.generate_system_prompt(target=editable_object)

# Generate a system prompt with context
system_prompt = codebase_ai.generate_system_prompt(context=context_object)

# Generate a system prompt with both target and context
system_prompt = codebase_ai.generate_system_prompt(target=editable_object, context=context_object)

# Generate tools for AI models
tools = codebase_ai.generate_tools()
```

### Integration with Analyzers

The `codebase_ai.py` module can be integrated with other analyzers to provide AI-powered analysis capabilities:

```python
from codegen_on_oss.analyzers.codebase_ai import CodebaseAI
from codegen_on_oss.analyzers.codebase_analyzer import CodebaseAnalyzer

class AICodebaseAnalyzer(CodebaseAnalyzer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.codebase_ai = CodebaseAI()

    def analyze_with_ai(self, file):
        # Generate a system prompt for the file
        system_prompt = self.codebase_ai.generate_system_prompt(target=file)

        # Use the system prompt with an AI model
        # ...
```

## API Reference

### Functions

- `generate_system_prompt(target=None, context=None)`: Generate a system prompt for AI-powered code analysis and generation
- `generate_flag_system_prompt(target, context=None)`: Generate a system prompt for determining whether to flag a code element
- `generate_context(context=None)`: Generate a context string for AI models
- `generate_tools()`: Generate a list of tools for AI models
- `generate_flag_tools()`: Generate a list of tools for flagging code elements

### Classes

#### CodebaseAI

The `CodebaseAI` class provides methods for generating system prompts, context, and tools for AI models to analyze and generate code.

##### Methods

- `generate_system_prompt(target=None, context=None)`: Generate a system prompt for AI-powered code analysis and generation
- `generate_flag_system_prompt(target, context=None)`: Generate a system prompt for determining whether to flag a code element
- `generate_context(context=None)`: Generate a context string for AI models
- `generate_tools()`: Generate a list of tools for AI models
- `generate_flag_tools()`: Generate a list of tools for flagging code elements

## Examples

See the `examples/codebase_ai_example.py` file for a complete example of how to use the `codebase_ai.py` module.

## Testing

The `codebase_ai.py` module includes comprehensive tests in the `tests/analyzers/test_codebase_ai.py` file. Run the tests using pytest:

```bash
pytest tests/analyzers/test_codebase_ai.py
```

