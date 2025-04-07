"""
Flow management for planning in codegen.

This module provides flow control for executing plans.
"""

import json
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Callable

from codegen.agents.base import BaseAgent
from codegen.agents.planning.planning import PlanStepStatus
from codegen.agents.planning.tools import PlanningTool

class Flow(ABC):
    """Base class for flow control in planning."""

    def __init__(self, name: str):
        """Initialize a Flow.

        Args:
            name: Name of the flow
        """
        self.name = name
        self.steps = []
        self.current_step = 0
        self.state = {}

    @abstractmethod
    def next(self) -> Optional[Dict[str, Any]]:
        """Move to the next step in the flow.

        Returns:
            The next step or None if the flow is complete
        """
        pass

    @abstractmethod
    def add_step(self, step: Dict[str, Any]) -> None:
        """Add a step to the flow.

        Args:
            step: The step to add
        """
        pass

    def reset(self) -> None:
        """Reset the flow to the beginning."""
        self.current_step = 0
        self.state = {}

    def get_state(self) -> Dict[str, Any]:
        """Get the current state of the flow.

        Returns:
            The current state
        """
        return self.state

    def set_state(self, state: Dict[str, Any]) -> None:
        """Set the state of the flow.

        Args:
            state: The state to set
        """
        self.state = state