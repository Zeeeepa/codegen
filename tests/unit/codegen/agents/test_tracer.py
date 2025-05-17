"""
Tests for the codegen.agents.tracer module.
"""

import pytest
from unittest.mock import MagicMock, patch
from typing import Generator

from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain.schema import FunctionMessage as LCFunctionMessage
from langchain_core.messages import ToolMessage as LCToolMessage

from codegen.agents.tracer import MessageStreamTracer
from codegen.agents.data import (
    AssistantMessage, 
    BaseMessage, 
    FunctionMessageData, 
    SystemMessageData, 
    ToolMessageData, 
    UserMessage
)
from codegen.agents.loggers import ExternalLogger


class TestMessageStreamTracer:
    """Tests for the MessageStreamTracer class."""

    @pytest.fixture
    def tracer(self):
        """Create a MessageStreamTracer instance for testing."""
        return MessageStreamTracer()

    @pytest.fixture
    def mock_logger(self):
        """Create a mock ExternalLogger for testing."""
        logger = MagicMock(spec=ExternalLogger)
        return logger

    @pytest.fixture
    def tracer_with_logger(self, mock_logger):
        """Create a MessageStreamTracer with a mock logger."""
        return MessageStreamTracer(logger=mock_logger)

    def test_init(self, tracer):
        """Test initialization of MessageStreamTracer."""
        assert tracer.traces == []
        assert tracer.logger is None

    def test_init_with_logger(self, tracer_with_logger, mock_logger):
        """Test initialization of MessageStreamTracer with a logger."""
        assert tracer_with_logger.traces == []
        assert tracer_with_logger.logger == mock_logger

    def test_get_traces(self, tracer):
        """Test get_traces method."""
        assert tracer.get_traces() == []
        
        # Add a trace
        tracer.traces.append(UserMessage(type="user", content="Hello"))
        assert len(tracer.get_traces()) == 1
        assert isinstance(tracer.get_traces()[0], UserMessage)

    def test_clear_traces(self, tracer):
        """Test clear_traces method."""
        # Add a trace
        tracer.traces.append(UserMessage(type="user", content="Hello"))
        assert len(tracer.get_traces()) == 1
        
        # Clear traces
        tracer.clear_traces()
        assert tracer.get_traces() == []

    def test_get_message_type_human(self, tracer):
        """Test _get_message_type with HumanMessage."""
        message = HumanMessage(content="Hello")
        assert tracer._get_message_type(message) == "user"

    def test_get_message_type_ai(self, tracer):
        """Test _get_message_type with AIMessage."""
        message = AIMessage(content="Hello")
        assert tracer._get_message_type(message) == "assistant"

    def test_get_message_type_system(self, tracer):
        """Test _get_message_type with SystemMessage."""
        message = SystemMessage(content="Hello")
        assert tracer._get_message_type(message) == "system"

    def test_get_message_type_function(self, tracer):
        """Test _get_message_type with FunctionMessage."""
        message = LCFunctionMessage(content="Hello", name="test_function")
        assert tracer._get_message_type(message) == "function"

    def test_get_message_type_tool(self, tracer):
        """Test _get_message_type with ToolMessage."""
        message = LCToolMessage(content="Hello", tool_call_id="123")
        assert tracer._get_message_type(message) == "tool"

    def test_get_message_type_custom(self, tracer):
        """Test _get_message_type with custom message type."""
        message = MagicMock()
        message.type = "custom"
        assert tracer._get_message_type(message) == "custom"

    def test_get_message_type_unknown(self, tracer):
        """Test _get_message_type with unknown message type."""
        message = MagicMock()
        delattr(message, "type")
        assert tracer._get_message_type(message) == "unknown"

    def test_get_message_content_direct(self, tracer):
        """Test _get_message_content with direct content attribute."""
        message = MagicMock()
        message.content = "Hello"
        assert tracer._get_message_content(message) == "Hello"

    def test_get_message_content_nested(self, tracer):
        """Test _get_message_content with nested content attribute."""
        message = MagicMock()
        message.message = MagicMock()
        message.message.content = "Hello"
        assert tracer._get_message_content(message) == "Hello"

    def test_get_message_content_fallback(self, tracer):
        """Test _get_message_content with fallback to string representation."""
        message = MagicMock()
        delattr(message, "content")
        message.__str__.return_value = "Hello"
        assert tracer._get_message_content(message) == "Hello"

    def test_extract_tool_calls_from_additional_kwargs(self, tracer):
        """Test _extract_tool_calls with tool_calls in additional_kwargs."""
        message = MagicMock()
        message.additional_kwargs = {
            "tool_calls": [
                {
                    "function": {"name": "test_tool", "arguments": '{"arg": "value"}'},
                    "id": "tool_1"
                }
            ]
        }
        tool_calls = tracer._extract_tool_calls(message)
        assert len(tool_calls) == 1
        assert tool_calls[0]["name"] == "test_tool"
        assert tool_calls[0]["arguments"] == '{"arg": "value"}'
        assert tool_calls[0]["id"] == "tool_1"

    def test_extract_tool_calls_from_function_call(self, tracer):
        """Test _extract_tool_calls with function_call in additional_kwargs."""
        message = MagicMock()
        message.additional_kwargs = {
            "function_call": {
                "name": "test_function",
                "arguments": '{"arg": "value"}'
            }
        }
        tool_calls = tracer._extract_tool_calls(message)
        assert len(tool_calls) == 1
        assert tool_calls[0]["name"] == "test_function"
        assert tool_calls[0]["arguments"] == '{"arg": "value"}'
        assert tool_calls[0]["id"] == "function_call_1"

    def test_extract_tool_calls_empty(self, tracer):
        """Test _extract_tool_calls with no tool calls."""
        message = MagicMock()
        message.additional_kwargs = {}
        tool_calls = tracer._extract_tool_calls(message)
        assert tool_calls == []

    def test_extract_structured_data_user_message(self, tracer):
        """Test extract_structured_data with a user message."""
        message = HumanMessage(content="Hello")
        chunk = {"messages": [message]}
        result = tracer.extract_structured_data(chunk)
        assert isinstance(result, UserMessage)
        assert result.type == "user"
        assert result.content == "Hello"

    def test_extract_structured_data_system_message(self, tracer):
        """Test extract_structured_data with a system message."""
        message = SystemMessage(content="System instruction")
        chunk = {"messages": [message]}
        result = tracer.extract_structured_data(chunk)
        assert isinstance(result, SystemMessageData)
        assert result.type == "system"
        assert result.content == "System instruction"

    def test_extract_structured_data_assistant_message(self, tracer):
        """Test extract_structured_data with an assistant message."""
        message = AIMessage(content="Assistant response")
        chunk = {"messages": [message]}
        result = tracer.extract_structured_data(chunk)
        assert isinstance(result, AssistantMessage)
        assert result.type == "assistant"
        assert result.content == "Assistant response"
        assert result.tool_calls == []

    def test_extract_structured_data_assistant_message_with_tool_calls(self, tracer):
        """Test extract_structured_data with an assistant message with tool calls."""
        message = AIMessage(
            content="Assistant response",
            additional_kwargs={
                "tool_calls": [
                    {
                        "function": {"name": "test_tool", "arguments": '{"arg": "value"}'},
                        "id": "tool_1"
                    }
                ]
            }
        )
        chunk = {"messages": [message]}
        result = tracer.extract_structured_data(chunk)
        assert isinstance(result, AssistantMessage)
        assert result.type == "assistant"
        assert result.content == "Assistant response"
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].name == "test_tool"
        assert result.tool_calls[0].arguments == '{"arg": "value"}'
        assert result.tool_calls[0].id == "tool_1"

    def test_extract_structured_data_tool_message(self, tracer):
        """Test extract_structured_data with a tool message."""
        message = LCToolMessage(content="Tool response", tool_call_id="tool_1")
        chunk = {"messages": [message]}
        result = tracer.extract_structured_data(chunk)
        assert isinstance(result, ToolMessageData)
        assert result.type == "tool"
        assert result.content == "Tool response"
        assert result.tool_id == "tool_1"

    def test_extract_structured_data_function_message(self, tracer):
        """Test extract_structured_data with a function message."""
        message = LCFunctionMessage(content="Function result", name="test_function")
        chunk = {"messages": [message]}
        result = tracer.extract_structured_data(chunk)
        assert isinstance(result, FunctionMessageData)
        assert result.type == "function"
        assert result.content == "Function result"

    def test_extract_structured_data_empty_chunk(self, tracer):
        """Test extract_structured_data with an empty chunk."""
        chunk = {}
        result = tracer.extract_structured_data(chunk)
        assert result is None

    def test_extract_structured_data_empty_messages(self, tracer):
        """Test extract_structured_data with empty messages."""
        chunk = {"messages": []}
        result = tracer.extract_structured_data(chunk)
        assert result is None

    def test_extract_structured_data_alternative_format(self, tracer):
        """Test extract_structured_data with an alternative format."""
        message = HumanMessage(content="Hello")
        chunk = {"alternative_key": [message]}
        result = tracer.extract_structured_data(chunk)
        assert isinstance(result, UserMessage)
        assert result.type == "user"
        assert result.content == "Hello"

    def test_process_stream(self, tracer_with_logger, mock_logger):
        """Test process_stream method."""
        # Create a mock message stream
        message1 = {"messages": [HumanMessage(content="Hello")]}
        message2 = {"messages": [AIMessage(content="Hi there")]}
        
        def mock_stream():
            yield message1
            yield message2
        
        # Process the stream
        processed_stream = tracer_with_logger.process_stream(mock_stream())
        
        # Collect the processed messages
        processed_messages = list(processed_stream)
        
        # Check that the original messages were passed through
        assert processed_messages == [message1, message2]
        
        # Check that traces were collected
        traces = tracer_with_logger.get_traces()
        assert len(traces) == 2
        assert isinstance(traces[0], UserMessage)
        assert traces[0].content == "Hello"
        assert isinstance(traces[1], AssistantMessage)
        assert traces[1].content == "Hi there"
        
        # Check that the logger was called
        assert mock_logger.log.call_count == 2
        mock_logger.log.assert_any_call(traces[0])
        mock_logger.log.assert_any_call(traces[1])

