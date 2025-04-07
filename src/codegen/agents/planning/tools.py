"""
Planning tools for codegen.

This module provides tools for planning and plan management.
"""

from typing import Any, Dict, List, Optional, Union

from codegen.agents.planning.planning import Plan, PlanStep, PlanStepStatus, PlanManager
from codegen.agents.toolcall_agent import Tool

class PlanningTool:
    """Tool for planning and plan management."""
    
    name: str = "planning"
    description: str = "A planning tool that allows the agent to create and manage plans for solving complex tasks."
    
    def __init__(self):
        """Initialize PlanningTool."""
        self.plans = {}  # Dictionary to store plans by plan_id
        self._current_plan_id = None  # Track the current active plan