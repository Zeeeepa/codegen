"""Project management module for Codegen CLI."""

from .main import project_app, register_project_command
from .dashboard import run_project_dashboard

__all__ = ["project_app", "register_project_command", "run_project_dashboard"]

