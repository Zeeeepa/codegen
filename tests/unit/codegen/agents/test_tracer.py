"""Tests for the MessageStreamTracer class in the agents module."""

from unittest.mock import MagicMock, patch

import pytest
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain.schema import FunctionMessage as LCFunctionMessage
from langchain_core.messages import ToolMessage as LCToolMessage

from codegen.agents.data import (
    AssistantMessage,
    SystemMessageData,
    ToolMessageData,
    UserMessage,
    FunctionMessageData,
    UnknownMessage,
)
from codegen.agents.tracer import MessageStreamTracer


class TestMessageStreamTracer:
    """Tests for the MessageStreamTracer class."""

    @pytest.fixture
    def tracer(self):
        """Create a MessageStreamTracer instance."""
        return MessageStreamTracer()

    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger."""
        logger = MagicMock()
        logger.log = MagicMock()
        return logger

    @pytest.fixture
    def tracer_with_logger(self, mock_logger):
        """Create a MessageStreamTracer instance with a logger."""
        return MessageStreamTracer(logger=mock_logger)

    def test_init(self, tracer):
        """Test initialization."""
        assert tracer.traces == []
        assert tracer.logger is None

    def test_init_with_logger(self, tracer_with_logger, mock_logger):
        """Test initialization with a logger."""
        assert tracer_with_logger.traces == []
        assert tracer_with_logger.logger == mock_logger

    def test_extract_structured_data_human_message(self, tracer):
        """Test extracting structured data from a HumanMessage."""
        human_message = HumanMessage(content="Hello")
        chunk = {"messages": [human_message]}
        
        result = tracer.extract_structured_data(chunk)
        
        assert isinstance(result, UserMessage)
        assert result.type == "user"
        assert result.content == "Hello"

    def test_extract_structured_data_ai_message(self, tracer):
        """Test extracting structured data from an AIMessage."""
        ai_message = AIMessage(content="Hello, how can I help?")
        chunk = {"messages": [ai_message]}
        
        result = tracer.extract_structured_data(chunk)
        
        assert isinstance(result, AssistantMessage)
        assert result.type == "assistant"
        assert result.content == "Hello, how can I help?"
        assert result.tool_calls == []

    def test_extract_structured_data_ai_message_with_tool_calls(self, tracer):
        """Test extracting structured data from an AIMessage with tool calls."""
        ai_message = AIMessage(
            content="I'll search for that",
            additional_kwargs={
                "tool_calls": [
                    {
                        "id": "call_123",
                        "function": {
                            "name": "search",
                            "arguments": '{"query": "test"}'
                        }
                    }
                ]
            }
        )
        chunk = {"messages": [ai_message]}
        
        result = tracer.extract_structured_data(chunk)
        
        assert isinstance(result, AssistantMessage)
        assert result.type == "assistant"
        assert result.content == "I'll search for that"
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].name == "search"
        assert result.tool_calls[0].arguments == '{"query": "test"}'
        assert result.tool_calls[0].id == "call_123"

    def test_extract_structured_data_ai_message_with_function_call(self, tracer):
        """Test extracting structured data from an AIMessage with function call."""
        ai_message = AIMessage(
            content="I'll search for that",
            additional_kwargs={
                "function_call": {
                    "name": "search",
                    "arguments": '{"query": "test"}'
                }
            }
        )
        chunk = {"messages": [ai_message]}
        
        result = tracer.extract_structured_data(chunk)
        
        assert isinstance(result, AssistantMessage)
        assert result.type == "assistant"
        assert result.content == "I'll search for that"
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].name == "search"
        assert result.tool_calls[0].arguments == '{"query": "test"}'
        assert result.tool_calls[0].id == "function_call_1"  # Default ID

    def test_extract_structured_data_system_message(self, tracer):
        """Test extracting structured data from a SystemMessage."""
        system_message = SystemMessage(content="You are a helpful assistant")
        chunk = {"messages": [system_message]}
        
        result = tracer.extract_structured_data(chunk)
        
        assert isinstance(result, SystemMessageData)
        assert result.type == "system"
        assert result.content == "You are a helpful assistant"

    def test_extract_structured_data_function_message(self, tracer):
        """Test extracting structured data from a FunctionMessage."""
        function_message = LCFunctionMessage(content="Function result", name="test_function")
        chunk = {"messages": [function_message]}
        
        result = tracer.extract_structured_data(chunk)
        
        assert isinstance(result, FunctionMessageData)
        assert result.type == "function"
        assert result.content == "Function result"

    def test_extract_structured_data_tool_message(self, tracer):
        """Test extracting structured data from a ToolMessage."""
        tool_message = LCToolMessage(content="Tool result", tool_call_id="call_123", name="search")
        chunk = {"messages": [tool_message]}
        
        result = tracer.extract_structured_data(chunk)
        
        assert isinstance(result, ToolMessageData)
        assert result.type == "tool"
        assert result.content == "Tool result"
        assert result.tool_name == "search"
        assert result.tool_response == "Tool result"
        assert result.tool_id == "call_123"

    def test_extract_structured_data_unknown_message(self, tracer):
        """Test extracting structured data from an unknown message type."""
        # Create a custom message type that doesn't match any known types
        class CustomMessage:
            def __str__(self):
                return "Custom message content"
        
        custom_message = CustomMessage()
        chunk = {"messages": [custom_message]}
        
        result = tracer.extract_structured_data(chunk)
        
        assert isinstance(result, UnknownMessage)
        assert result.type == "unknown"
        assert result.content == "Custom message content"

    def test_extract_structured_data_empty_chunk(self, tracer):
        """Test extracting structured data from an empty chunk."""
        chunk = {"messages": []}
        
        result = tracer.extract_structured_data(chunk)
        
        assert result is None

    def test_extract_structured_data_no_messages(self, tracer):
        """Test extracting structured data from a chunk with no messages key."""
        chunk = {"other_key": "value"}
        
        result = tracer.extract_structured_data(chunk)
        
        assert result is None

    def test_process_stream(self, tracer):
        """Test processing a stream of messages."""
        # Create a generator that yields chunks
        def message_stream():
            yield {"messages": [HumanMessage(content="Hello")]}
            yield {"messages": [AIMessage(content="Hi there")]}
        
        # Process the stream
        processed_stream = list(tracer.process_stream(message_stream()))
        
        # Check that the original chunks are passed through
        assert len(processed_stream) == 2
        assert processed_stream[0] == {"messages": [HumanMessage(content="Hello")]}
        assert processed_stream[1] == {"messages": [AIMessage(content="Hi there")]}
        
        # Check that traces were collected
        assert len(tracer.traces) == 2
        assert isinstance(tracer.traces[0], UserMessage)
        assert tracer.traces[0].content == "Hello"
        assert isinstance(tracer.traces[1], AssistantMessage)
        assert tracer.traces[1].content == "Hi there"

    def test_process_stream_with_logger(self, tracer_with_logger, mock_logger):
        """Test processing a stream of messages with a logger."""
        # Create a generator that yields chunks
        def message_stream():
            yield {"messages": [HumanMessage(content="Hello")]}
            yield {"messages": [AIMessage(content="Hi there")]}
        
        # Process the stream
        processed_stream = list(tracer_with_logger.process_stream(message_stream()))
        
        # Check that the logger was called for each message
        assert mock_logger.log.call_count == 2
        
        # Check the first call
        first_call_args = mock_logger.log.call_args_list[0][0]
        assert isinstance(first_call_args[0], UserMessage)
        assert first_call_args[0].content == "Hello"
        
        # Check the second call
        second_call_args = mock_logger.log.call_args_list[1][0]
        assert isinstance(second_call_args[0], AssistantMessage)
        assert second_call_args[0].content == "Hi there"

    def test_get_traces(self, tracer):
        """Test getting all collected traces."""
        # Add some traces
        tracer.traces = [
            UserMessage(content="Hello"),
            AssistantMessage(content="Hi there")
        ]
        
        # Get the traces
        traces = tracer.get_traces()
        
        # Check the traces
        assert len(traces) == 2
        assert isinstance(traces[0], UserMessage)
        assert traces[0].content == "Hello"
        assert isinstance(traces[1], AssistantMessage)
        assert traces[1].content == "Hi there"

    def test_clear_traces(self, tracer):
        """Test clearing all traces."""
        # Add some traces
        tracer.traces = [
            UserMessage(content="Hello"),
            AssistantMessage(content="Hi there")
        ]
        
        # Clear the traces
        tracer.clear_traces()
        
        # Check that the traces were cleared
        assert tracer.traces == []

