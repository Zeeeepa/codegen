"""
High-Value Agent Services

This module contains the high-value development agents that provide maximum
benefit for CI/CD operations:

- CodegenClaudeAgent: Development tasks with Claude integration
- RepoMasterAgent: Code analysis and repository insights

These agents are powered by Z.AI substrate and coordinated through ROMA
meta-orchestration for optimal development workflow automation.
"""

from .codegen_claude_agent import CodegenClaudeAgent
from .repomaster_agent import RepoMasterAgent

__all__ = [
    "CodegenClaudeAgent",
    "RepoMasterAgent",
]
