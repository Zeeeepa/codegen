"""Consistent spinner styles for the CLI."""

from codegen.cli.rich.types import SpinnerConfig
from dataclasses import dataclass

from rich.status import Status


def create_spinner(text: str) -> Status:
    """Create a spinner with consistent styling.

    Args:
        text: The text to show next to the spinner

    Returns:
        A rich Status object with consistent styling

    """
    config = SpinnerConfig(text)
    return Status(f"[{config.style}]{config.text}", spinner=config.spinner, spinner_style=config.spinner_style)
