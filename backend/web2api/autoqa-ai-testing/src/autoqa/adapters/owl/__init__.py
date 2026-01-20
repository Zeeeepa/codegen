"""
Owl-Browser SDK adapter for AutoQA/Web2API.

Provides a unified interface to all 157 Owl-Browser commands with
consistent error handling, retries, and telemetry.
"""

from autoqa.adapters.owl.browser_adapter import OwlBrowserAdapter

__all__ = ["OwlBrowserAdapter"]
