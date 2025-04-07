"""
Agent framework for codegen.

This module provides a collection of agent implementations for various tasks.
"""

from codegen.agents.base import BaseAgent
from codegen.agents.mcp_agent import MCPAgent
from codegen.agents.planning_agent import PlanningAgent
from codegen.agents.toolcall_agent import Tool, ToolCallAgent

__all__ = [
    "BaseAgent",
    "MCPAgent",
    "PlanningAgent",
    "Tool",
    "ToolCallAgent",
]