"""
Planning implementation for codegen.

This module provides planning capabilities for agents.
"""

import time
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from uuid import uuid4

class PlanStepStatus(str, Enum):
    """Status of a plan step."""
    
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    
    @classmethod
    def get_all_statuses(cls) -> list[str]:
        """Return a list of all status values"""
        return [status.value for status in cls]
    
    @classmethod
    def get_active_statuses(cls) -> list[str]:
        """Return a list of values representing active statuses (not started or in progress)"""
        return [cls.NOT_STARTED.value, cls.IN_PROGRESS.value]

    @classmethod
    def get_status_marks(cls) -> Dict[str, str]:
        """Return a mapping of statuses to their marker symbols"""
        return {
            cls.COMPLETED.value: "[✓]",
            cls.IN_PROGRESS.value: "[→]",
            cls.BLOCKED.value: "[!]",
            cls.NOT_STARTED.value: "[ ]",
        }