"""Langchain tools for workspace operations."""

from langchain_core.tools.base import BaseTool

from codegen.extensions.langchain.tools import (
    CreateFileTool,
    DeleteFileTool,
    EditFileTool,
    ListDirectoryTool,
    RevealSymbolTool,
    RipGrepTool,
    SemanticEditTool,
    ViewFileTool,
)

__all__ = [
    # Tools
    "CreateFileTool",
    "DeleteFileTool",
    "EditFileTool",
    "ListDirectoryTool",
    "RevealSymbolTool",
    "RipGrepTool",
    "SemanticEditTool",
    "ViewFileTool",
    # Helper functions
    "create_codebase_agent",
    "create_chat_agent",
    "create_codebase_inspector_agent",
]


def get_workspace_tools(codebase: Codebase) -> list[BaseTool]:
    """Get all tools for working with a codebase."""
    return [
        ViewFileTool(codebase),
        ListDirectoryTool(codebase),
        RipGrepTool(codebase),
        EditFileTool(codebase),
        CreateFileTool(codebase),
        DeleteFileTool(codebase),
    ]
