"""Demo implementation of an agent with Codegen tools."""

from typing import TYPE_CHECKING, Any

from langchain.tools import BaseTool
from langchain_core.messages import SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.graph import CompiledGraph

from codegen.agents.utils import AgentConfig
from codegen.extensions.langchain.llm import LLM
from codegen.extensions.langchain.prompts import REASONER_SYSTEM_MESSAGE
from codegen.extensions.langchain.tools import (
    CreateFileTool,
    DeleteFileTool,
    GlobalReplacementEditTool,
    ListDirectoryTool,
    MoveSymbolTool,
    ReflectionTool,
    RelaceEditTool,
    RenameFileTool,
    ReplacementEditTool,
    RevealSymbolTool,
    SearchFilesByNameTool,
    SearchTool,
    # SemanticEditTool,
    ViewFileTool,
    RipGrepSearchTool,
    MoveFileTool,
    CommitChangesTool,
)

from .graph import create_react_agent

if TYPE_CHECKING:
    from codegen import Codebase


def create_codebase_agent(
    codebase,
    model_provider=None,
    model_name=None,
    memory=False,
    additional_tools=None,
    **kwargs,
):
    """
    Create a codebase agent with the given codebase and model.

    Args:
        codebase (Codebase): The codebase to use
        model_provider (str, optional): The model provider to use. Defaults to None.
        model_name (str, optional): The model name to use. Defaults to None.
        memory (bool, optional): Whether to use memory. Defaults to False.
        additional_tools (list, optional): Additional tools to add. Defaults to None.
        **kwargs: Additional arguments to pass to the model

    Returns:
        Agent: The created agent
    """
    llm = LLM(model_provider=model_provider, model_name=model_name, **kwargs)

    # Initialize default tools
    tools = [
        ViewFileTool(codebase),
        ListDirectoryTool(codebase),
        RipGrepSearchTool(codebase),
        EditFileTool(codebase),
        CreateFileTool(codebase),
        DeleteFileTool(codebase),
        RenameFileTool(codebase),
        MoveFileTool(codebase),
        CommitChangesTool(codebase),
        ReflectionTool(codebase),
        SearchFilesByNameTool(codebase),
        GlobalReplacementEditTool(codebase),
    ]

    if additional_tools:
        # Get names of additional tools
        additional_names = {t.get_name() for t in additional_tools}
        # Keep only tools that don't have matching names in additional_tools
        tools = [t for t in tools if t.get_name() not in additional_names]
        tools.extend(additional_tools)

    memory = MemorySaver() if memory else None

    return create_react_agent(model=llm, tools=tools, system_message=SystemMessage(REASONER_SYSTEM_MESSAGE), checkpointer=memory, debug=False, config=None)


def create_chat_agent(
    codebase,
    model_provider=None,
    model_name=None,
    memory=False,
    additional_tools=None,
    **kwargs,
):
    """
    Create a chat agent with the given codebase and model.

    Args:
        codebase (Codebase): The codebase to use
        model_provider (str, optional): The model provider to use. Defaults to None.
        model_name (str, optional): The model name to use. Defaults to None.
        memory (bool, optional): Whether to use memory. Defaults to False.
        additional_tools (list, optional): Additional tools to add. Defaults to None.
        **kwargs: Additional arguments to pass to the model

    Returns:
        Agent: The created agent
    """
    llm = LLM(model_provider=model_provider, model_name=model_name, **kwargs)

    # Initialize default tools
    tools = [
        ViewFileTool(codebase),
        ListDirectoryTool(codebase),
        SearchTool(codebase),
        CreateFileTool(codebase),
        DeleteFileTool(codebase),
        RenameFileTool(codebase),
        MoveSymbolTool(codebase),
        RevealSymbolTool(codebase),
        RelaceEditTool(codebase),
    ]

    if additional_tools:
        # Get names of additional tools
        additional_names = {t.get_name() for t in additional_tools}
        # Keep only tools that don't have matching names in additional_tools
        tools = [t for t in tools if t.get_name() not in additional_names]
        tools.extend(additional_tools)

    memory = MemorySaver() if memory else None

    return create_react_agent(model=llm, tools=tools, system_message=SystemMessage(REASONER_SYSTEM_MESSAGE), checkpointer=memory, debug=False, config=None)


def create_codebase_inspector_agent(
    codebase,
    model_provider=None,
    model_name=None,
    memory=False,
    additional_tools=None,
    **kwargs,
):
    """
    Create an inspector agent with read-only codebase tools.

    Args:
        codebase (Codebase): The codebase to use
        model_provider (str, optional): The model provider to use. Defaults to None.
        model_name (str, optional): The model name to use. Defaults to None.
        memory (bool, optional): Whether to use memory. Defaults to False.
        additional_tools (list, optional): Additional tools to add. Defaults to None.
        **kwargs: Additional arguments to pass to the model

    Returns:
        Agent: The created agent
    """
    llm = LLM(model_provider=model_provider, model_name=model_name, **kwargs)

    # Initialize default tools
    tools = [
        ViewFileTool(codebase),
        ListDirectoryTool(codebase),
        SearchTool(codebase),
        DeleteFileTool(codebase),
        RevealSymbolTool(codebase),
    ]

    memory = MemorySaver() if memory else None

    return create_react_agent(model=llm, tools=tools, system_message=SystemMessage(REASONER_SYSTEM_MESSAGE), checkpointer=memory, debug=False, config=None)


def create_agent_with_tools(
    tools,
    model_provider=None,
    model_name=None,
    memory=False,
    additional_tools=None,
    **kwargs,
):
    """
    Create an agent with a specific set of tools.

    Args:
        tools (list): List of tools to provide to the agent
        model_provider (str, optional): The model provider to use. Defaults to None.
        model_name (str, optional): The model name to use. Defaults to None.
        memory (bool, optional): Whether to use memory. Defaults to False.
        additional_tools (list, optional): Additional tools to add. Defaults to None.
        **kwargs: Additional arguments to pass to the model

    Returns:
        Agent: The created agent
    """
    llm = LLM(model_provider=model_provider, model_name=model_name, **kwargs)

    memory = MemorySaver() if memory else None

    return create_react_agent(model=llm, tools=tools, system_message=SystemMessage(REASONER_SYSTEM_MESSAGE), checkpointer=memory, debug=False, config=None)
