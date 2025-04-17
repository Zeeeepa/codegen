"""Base class for tool observations/responses."""

import json
from typing import Any, ClassVar, Optional

from langchain_core.messages import ToolMessage
from pydantic import BaseModel, Field


class Observation(BaseModel):
    """Base class for all tool observations."""

    status: str = Field(
        default="success",
        description="Status of the observation (success/error)",
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if status is error",
    )

    str_template: ClassVar[str] = ""

    def _get_details(self) -> dict[str, Any]:
        """Get details for string template.

        Override in subclasses to provide custom details.
        """
        return {}

    def __str__(self) -> str:
        """Get string representation of the observation."""
        if self.status == "error":
            return f"Error: {self.error}"
        return self.render_as_string()

    def __repr__(self) -> str:
        """Get detailed string representation of the observation."""
        return f"{self.__class__.__name__}({self.model_dump_json()})"

    def render_as_string(self) -> str:
        """Render the observation as a string.

        This is used for string representation and as the content field
        in the ToolMessage. Subclasses can override this to customize
        their string output format.
        """
        return json.dumps(self.model_dump(), indent=2)

    def render(self, tool_call_id: Optional[str] = None) -> ToolMessage | str:
        """Render the observation as a ToolMessage or string.

        Args:
            tool_call_id: Optional[str] = None - If provided, return a ToolMessage.
                If None, return a string representation.

        Returns:
            ToolMessage or str containing the observation content and metadata.
            For error cases, includes error information in artifacts.
        """
        if tool_call_id is None:
            return self.render_as_string()

        # Get content first in case render_as_string has side effects
        content = self.render_as_string()

        if self.status == "error":
            return ToolMessage(
                content=content,
                status=self.status,
                tool_call_id=tool_call_id,
            )

        return ToolMessage(
            content=content,
            status=self.status,
            tool_call_id=tool_call_id,
        )
