"""
Codegen Dashboard - A comprehensive Tkinter application for managing Codegen agent runs,
projects, workflows, and AI-powered code analysis.

Features:
- Real-time agent run monitoring and management
- Chat interface with RepoMaster + Z.AI integration
- Project visualization using graph-sitter analysis
- PRD validation and automated follow-up agents
- Validation gates and workflow orchestration
- Agentic observability overlay
"""

__version__ = "1.0.0"
__author__ = "Codegen Team"

from .main import CodegenDashboard

__all__ = ["CodegenDashboard"]
