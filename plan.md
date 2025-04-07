# Codegen Codebase Restructuring Plan

## Current Structure Analysis

After analyzing the codegen codebase, I've identified several issues with the current organization:

1. **Duplicate Functionality**: There are similar implementations in both `agents` and `extensions` directories (e.g., planning, reflection).
2. **Inconsistent Import Patterns**: Some modules import from `codegen.agents` while others import from `codegen.extensions`.
3. **Unclear Boundaries**: The distinction between what belongs in `agents` vs `extensions` is not well-defined.
4. **Circular Dependencies**: Some modules in `extensions` depend on `agents` and vice versa.
5. **Scattered Tools**: Tools are spread across multiple directories with overlapping functionality.

## Core Issues

1. The `agents` directory contains agent implementations but also includes planning and PR review functionality that could be considered extensions.
2. The `extensions` directory contains a mix of tools, utilities, and integrations without clear organization.
3. The `langchain` extension imports from `agents`, creating circular dependencies.
4. Similar functionality exists in both directories (e.g., planning in both `agents/planning` and `extensions/planning`).

## Proposed Structure

I propose reorganizing the codebase with the following structure:

```
src/codegen/
├── agents/                  # Core agent implementations
│   ├── base.py              # Base agent classes and interfaces
│   ├── chat_agent.py        # Chat-based agent implementation
│   ├── code_agent.py        # Code-focused agent implementation
│   ├── mcp_agent.py         # MCP agent implementation
│   └── toolcall_agent.py    # Tool-calling agent implementation
│
├── core/                    # Core functionality used across the codebase
│   ├── config.py            # Configuration utilities
│   ├── logging.py           # Logging utilities
│   ├── types.py             # Shared type definitions
│   └── utils.py             # General utilities
│
├── extensions/              # Extensions to core functionality
│   ├── attribution/         # Code attribution functionality
│   ├── events/              # Event handling (GitHub, Linear, Slack)
│   ├── github/              # GitHub integration
│   ├── graph/               # Graph-based code analysis
│   ├── index/               # Code indexing
│   ├── linear/              # Linear integration
│   ├── lsp/                 # Language Server Protocol implementation
│   ├── mcp/                 # MCP integration
│   ├── slack/               # Slack integration
│   └── swebench/            # SWE benchmarking
│
├── frameworks/              # Integration with external frameworks
│   ├── langchain/           # LangChain integration
│   └── langgraph/           # LangGraph integration
│
├── services/                # Higher-level services built on core components
│   ├── planning/            # Planning functionality
│   ├── reflection/          # Reflection and self-improvement
│   ├── research/            # Code research and analysis
│   └── pr_review/           # PR review functionality
│
└── tools/                   # All tools in one place
    ├── bash.py              # Bash command execution
    ├── code/                # Code manipulation tools
    │   ├── create_file.py
    │   ├── delete_file.py
    │   ├── edit_file.py
    │   ├── rename_file.py
    │   └── view_file.py
    ├── github/              # GitHub-specific tools
    ├── linear/              # Linear-specific tools
    ├── search/              # Search tools
    │   ├── ripgrep.py
    │   ├── semantic_search.py
    │   └── search_files.py
    └── websearch/           # Web search tools
```

## Migration Strategy

1. **Create New Structure**: Set up the new directory structure without modifying existing code.
2. **Move Core Components**: Move core components to their new locations, updating imports.
3. **Consolidate Duplicates**: Identify and merge duplicate functionality.
4. **Update Imports**: Update all import statements to reflect the new structure.
5. **Test Thoroughly**: Ensure all functionality works as expected after restructuring.

## Specific Changes

### 1. Consolidate Planning Functionality

Currently, planning exists in both:
- `src/codegen/agents/planning/`
- `src/codegen/extensions/planning/`

Proposal: Move all planning functionality to `src/codegen/services/planning/` and ensure a single, consistent implementation.

### 2. Consolidate Reflection Functionality

Currently, reflection exists in both:
- `src/codegen/agents/` (via tracer.py)
- `src/codegen/extensions/reflection/`

Proposal: Move all reflection functionality to `src/codegen/services/reflection/`.

### 3. Move LangChain Integration

Currently, LangChain integration is in `src/codegen/extensions/langchain/` but imports from `codegen.agents`.

Proposal: Move to `src/codegen/frameworks/langchain/` and refactor to remove circular dependencies.

### 4. Consolidate Tools

Currently, tools are scattered across:
- `src/codegen/extensions/tools/`
- Various agent implementations

Proposal: Move all tools to `src/codegen/tools/` organized by functionality.

### 5. Clarify Agent Boundaries

Currently, the distinction between agents and extensions is unclear.

Proposal: 
- `agents/`: Only core agent implementations and interfaces
- `services/`: Higher-level functionality built on agents
- `tools/`: All tools used by agents
- `extensions/`: Integrations with external systems

## Benefits

1. **Clear Separation of Concerns**: Each directory has a well-defined purpose.
2. **Reduced Duplication**: Similar functionality is consolidated.
3. **Simplified Imports**: More consistent import patterns.
4. **Easier Maintenance**: Related code is grouped together.
5. **Better Scalability**: Structure can accommodate future growth.

## Implementation Plan

1. Create the new directory structure
2. Move files to their new locations one module at a time
3. Update imports in moved files
4. Update imports in dependent files
5. Test each module after migration
6. Remove empty directories from the old structure

This restructuring will make the codebase more maintainable, reduce duplication, and provide a clearer organization for future development.
