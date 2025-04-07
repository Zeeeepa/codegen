"""
Agent framework for agentgen.

This module provides a collection of agent implementations for various tasks.
"""

from agentgen.agents.base import BaseAgent
from agentgen.agents.mcp_agent import MCPAgent
from agentgen.agents.planning_agent import PlanningAgent
from agentgen.agents.toolcall_agent import Tool, ToolCallAgent

__all__ = [
    "BaseAgent",
    "MCPAgent",
    "PlanningAgent",
    "Tool",
    "ToolCallAgent",
]