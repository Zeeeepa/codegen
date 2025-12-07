"""Multi-agent council orchestration for Codegen.

This module provides a council-based approach where multiple agents with different
models collaborate to solve complex problems through:
1. Parallel generation of candidate responses
2. Peer ranking and evaluation
3. Synthesis of final answer
"""

from .models import AgentConfig, CouncilConfig, CouncilResult
from .orchestrator import CouncilOrchestrator

__all__ = [
    "AgentConfig",
    "CouncilConfig",
    "CouncilResult",
    "CouncilOrchestrator",
]

