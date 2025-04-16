# AI Tools Examples

This directory contains examples demonstrating how to use the AI tools in the MCP (Model-Code-Protocol) framework.

## Available Examples

### 1. Codebase AI

The `codebase_ai_example.py` file demonstrates how to use the `codebase.ai` tool to:

- Generate new code based on a prompt
- Analyze existing code with additional context
- Configure AI settings

To run the example:

```bash
python codebase_ai_example.py
```

Note: You'll need to set a valid API key in the example code before running it.

### 2. Reflection

The `reflection_example.py` file demonstrates how to use the `reflection` tool to:

- Organize thoughts and findings
- Identify knowledge gaps
- Create a strategic plan for complex problems
- Focus reflection on specific aspects of a problem

To run the example:

```bash
python reflection_example.py
```

## AI Tools Overview

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

## Best Practices

When using AI tools:

1. **Provide clear prompts**: Be specific about what you want the AI to do
2. **Include relevant context**: The more context you provide, the better the results
3. **Review generated code**: Always review and test AI-generated code before using it in production
4. **Use reflection for complex problems**: Break down complex problems using the reflection tool before diving into implementation
