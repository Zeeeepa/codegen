# Codegen Agents

This guide demonstrates how to build intelligent code agents that can analyze and manipulate codebases.

## Basic Usage

The following example shows how to create and run a :



Your  must be set in your env.

The default implementation uses  for the model but this can be changed through the  and  arguments.



If using a non-default model provider, make sure to set the appropriate API key (e.g.,  for OpenAI models) in your env.

## Available Agents

Codegen provides several specialized agents for different tasks:

### CodeAgent

The  is designed for code analysis and manipulation. It can understand, modify, and generate code across various programming languages.



### ChatAgent

The  provides conversational capabilities, allowing for natural language interactions about code.



### PRReviewAgent

The  specializes in reviewing pull requests, providing feedback on code quality, potential issues, and suggesting improvements.



### PlanningAgent

The  helps with project planning, breaking down complex tasks into manageable steps.



### ReflectionAgent

The  can analyze its own outputs and improve them based on feedback.



### ResearchAgent

The  specializes in gathering and analyzing information from various sources.



### MCPAgent

The  (Multi-Context Processing Agent) can handle multiple contexts simultaneously, making it ideal for complex tasks that require understanding different parts of a codebase.



### ToolCallAgent

The  provides a framework for using tools to perform specific tasks.



## Available Tools

The agents come with a comprehensive set of tools for code analysis and manipulation:



Each tool provides specific capabilities:

- : View contents and metadata of files
- : Make intelligent edits to files
- : Analyze symbol dependencies and usages
- : Move symbols between files with import handling
- : Make regex-based replacement editing on files
- : List directory contents
- : Search for files and symbols
- : Create new files
- : Delete files
- : Rename files
- : Edit files

## Extensions

### GitHub Integration

The agents include tools for GitHub operations like PR management. Set up GitHub access with:



Import the GitHub tools:



These tools enable:
- Creating pull requests
- Viewing PR contents and diffs
- Adding general PR comments
- Adding inline review comments

### Linear Integration

The agents can interact with Linear for issue tracking and project management. To use Linear tools, set the following environment variables:



Import and use the Linear tools:



These tools allow the agents to:
- Create and search issues
- Get issue details and comments
- Add comments to issues
- View team information

## Adding Custom Tools

You can extend the agents with custom tools:


