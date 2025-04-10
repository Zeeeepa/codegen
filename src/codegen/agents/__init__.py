"""
Agent framework for codegen.

This module provides a collection of agent implementations for various tasks.
"""

from codegen.agents.base import BaseAgent
from codegen.agents.chat.chat_agent import ChatAgent
from codegen.agents.code.code_agent import CodeAgent
from codegen.agents.issue_solver.agent import IssueSolverAgent
from codegen.agents.mcp.mcp_agent import MCPAgent
from codegen.agents.planning.planning_agent import PlanningAgent
from codegen.agents.pr_review.pr_review_agent import PRReviewAgent
from codegen.agents.reflection.reflection_agent import ReflectionAgent
from codegen.agents.research.research_agent import ResearchAgent
from codegen.agents.toolcall.toolcall_agent import Tool, ToolCallAgent

__all__ = [
    "BaseAgent",
    "ChatAgent",
    "CodeAgent",
    "IssueSolverAgent",
    "MCPAgent",
    "PlanningAgent",
    "PRReviewAgent",
    "ReflectionAgent",
    "ResearchAgent",
    "Tool",
    "ToolCallAgent",
]
