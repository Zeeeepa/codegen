"""
Compatibility layer for agentgen imports.
This file redirects imports from agentgen to codegen.
"""

from codegen.extensions.tools.observation import Observation

# Re-export the Observation class
__all__ = ["Observation"]
