from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal


# Base dataclass for all message types
@dataclass
class BaseMessage:
    """Base class for all message types."""

    type: str
    timestamp: str = field(default_factory=lambda: datetime.now(tz=UTC).isoformat())
    content: str = ""


@dataclass
class UserMessage(BaseMessage):
    """Represents a message from the user."""

    type: Literal["user"] = field(default="user")


@dataclass
class SystemMessageData(BaseMessage):
    """Represents a system message."""

    type: Literal["system"] = field(default="system")


@dataclass
class ToolCall:
    """Represents a tool call within an assistant message."""

    name: str | None = None
    arguments: str | None = None
    id: str | None = None


@dataclass
class AssistantMessage(BaseMessage):
    """Represents a message from the assistant."""

    type: Literal["assistant"] = field(default="assistant")
    tool_calls: list[ToolCall] = field(default_factory=list)


@dataclass
class ToolMessageData(BaseMessage):
    """Represents a tool response message."""

    type: Literal["tool"] = field(default="tool")
    tool_name: str | None = None
    tool_response: str | None = None
    tool_id: str | None = None
    status: str | None = None


@dataclass
class FunctionMessageData(BaseMessage):
    """Represents a function message."""

    type: Literal["function"] = field(default="function")


@dataclass
class UnknownMessage(BaseMessage):
    """Represents an unknown message type."""

    type: Literal["unknown"] = field(default="unknown")


type AgentRunMessage = UserMessage | SystemMessageData | AssistantMessage | ToolMessageData | FunctionMessageData | UnknownMessage
