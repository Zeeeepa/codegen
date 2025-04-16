"""
Base model for MCP.

This module defines the base model class that all other models inherit from.
"""

from typing import Any, Dict, Optional


class BaseModel:
    """Base model class for all MCP models."""

    def __init__(self, **kwargs):
        """Initialize the base model with arbitrary attributes."""
        for key, value in kwargs.items():
            setattr(self, key, value)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary representation.

        Returns:
            Dict[str, Any]: Dictionary representation of the model.
        """
        return {
            key: value
            for key, value in self.__dict__.items()
            if not key.startswith("_") and not callable(value)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseModel":
        """Create a model instance from a dictionary.

        Args:
            data (Dict[str, Any]): Dictionary containing model data.

        Returns:
            BaseModel: New model instance.
        """
        return cls(**data)

    def __repr__(self) -> str:
        """Return a string representation of the model.

        Returns:
            str: String representation.
        """
        attrs = ", ".join(f"{k}={v!r}" for k, v in self.to_dict().items())
        return f"{self.__class__.__name__}({attrs})"
