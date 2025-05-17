"""Tests for the data classes in the agents module."""

import pytest
from datetime import UTC, datetime

from codegen.agents.data import (
    BaseMessage,
    UserMessage,
    SystemMessageData,
    ToolCall,
    AssistantMessage,
    ToolMessageData,
    FunctionMessageData,
    UnknownMessage,
)


class TestBaseMessage:
    """Tests for the BaseMessage class."""

    def test_init_with_defaults(self):
        """Test initialization with default values."""
        message = BaseMessage(type="test")
        assert message.type == "test"
        assert message.content == ""
        assert isinstance(message.timestamp, str)
        # Verify timestamp is in ISO format
        datetime.fromisoformat(message.timestamp)

    def test_init_with_custom_values(self):
        """Test initialization with custom values."""
        custom_timestamp = datetime.now(tz=UTC).isoformat()
        message = BaseMessage(type="test", content="Hello", timestamp=custom_timestamp)
        assert message.type == "test"
        assert message.content == "Hello"
        assert message.timestamp == custom_timestamp


class TestUserMessage:
    """Tests for the UserMessage class."""

    def test_init_with_defaults(self):
        """Test initialization with default values."""
        message = UserMessage()
        assert message.type == "user"
        assert message.content == ""
        assert isinstance(message.timestamp, str)

    def test_init_with_content(self):
        """Test initialization with content."""
        message = UserMessage(content="User query")
        assert message.type == "user"
        assert message.content == "User query"


class TestSystemMessageData:
    """Tests for the SystemMessageData class."""

    def test_init_with_defaults(self):
        """Test initialization with default values."""
        message = SystemMessageData()
        assert message.type == "system"
        assert message.content == ""
        assert isinstance(message.timestamp, str)

    def test_init_with_content(self):
        """Test initialization with content."""
        message = SystemMessageData(content="System instruction")
        assert message.type == "system"
        assert message.content == "System instruction"


class TestToolCall:
    """Tests for the ToolCall class."""

    def test_init_with_defaults(self):
        """Test initialization with default values."""
        tool_call = ToolCall()
        assert tool_call.name is None
        assert tool_call.arguments is None
        assert tool_call.id is None

    def test_init_with_values(self):
        """Test initialization with values."""
        tool_call = ToolCall(name="search", arguments='{"query": "test"}', id="call_123")
        assert tool_call.name == "search"
        assert tool_call.arguments == '{"query": "test"}'
        assert tool_call.id == "call_123"


class TestAssistantMessage:
    """Tests for the AssistantMessage class."""

    def test_init_with_defaults(self):
        """Test initialization with default values."""
        message = AssistantMessage()
        assert message.type == "assistant"
        assert message.content == ""
        assert message.tool_calls == []
        assert isinstance(message.timestamp, str)

    def test_init_with_content_and_tool_calls(self):
        """Test initialization with content and tool calls."""
        tool_call = ToolCall(name="search", arguments='{"query": "test"}', id="call_123")
        message = AssistantMessage(content="Assistant response", tool_calls=[tool_call])
        assert message.type == "assistant"
        assert message.content == "Assistant response"
        assert len(message.tool_calls) == 1
        assert message.tool_calls[0].name == "search"
        assert message.tool_calls[0].arguments == '{"query": "test"}'
        assert message.tool_calls[0].id == "call_123"


class TestToolMessageData:
    """Tests for the ToolMessageData class."""

    def test_init_with_defaults(self):
        """Test initialization with default values."""
        message = ToolMessageData()
        assert message.type == "tool"
        assert message.content == ""
        assert message.tool_name is None
        assert message.tool_response is None
        assert message.tool_id is None
        assert message.status is None
        assert isinstance(message.timestamp, str)

    def test_init_with_values(self):
        """Test initialization with values."""
        message = ToolMessageData(
            content="Tool result",
            tool_name="search",
            tool_response="Search results",
            tool_id="call_123",
            status="success"
        )
        assert message.type == "tool"
        assert message.content == "Tool result"
        assert message.tool_name == "search"
        assert message.tool_response == "Search results"
        assert message.tool_id == "call_123"
        assert message.status == "success"


class TestFunctionMessageData:
    """Tests for the FunctionMessageData class."""

    def test_init_with_defaults(self):
        """Test initialization with default values."""
        message = FunctionMessageData()
        assert message.type == "function"
        assert message.content == ""
        assert isinstance(message.timestamp, str)

    def test_init_with_content(self):
        """Test initialization with content."""
        message = FunctionMessageData(content="Function result")
        assert message.type == "function"
        assert message.content == "Function result"


class TestUnknownMessage:
    """Tests for the UnknownMessage class."""

    def test_init_with_defaults(self):
        """Test initialization with default values."""
        message = UnknownMessage()
        assert message.type == "unknown"
        assert message.content == ""
        assert isinstance(message.timestamp, str)

    def test_init_with_content(self):
        """Test initialization with content."""
        message = UnknownMessage(content="Unknown message content")
        assert message.type == "unknown"
        assert message.content == "Unknown message content"

