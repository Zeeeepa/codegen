from typing import Dict, List, Optional, Union

from langchain.schema import AIMessage as LCAIMessage
from langchain.schema import HumanMessage as LCHumanMessage
from langchain.schema import FunctionMessage as LCFunctionMessage
from langchain.schema import SystemMessage as LCSystemMessage
from langchain_core.messages import ToolMessage as LCToolMessage

from codegen.agents.data import AssistantMessage, BaseMessage, FunctionMessageData, SystemMessageData, ToolCall, ToolMessageData, UnknownMessage, UserMessage
from codegen.agents.loggers import ExternalLogger


class MessageStreamTracer:
    """Tracer for message streams."""

    def __init__(self, external_logger: Optional[ExternalLogger] = None):
        """Initialize a MessageStreamTracer."""
        self.messages: List[BaseMessage] = []
        self.external_logger = external_logger

    def add_message(self, message: BaseMessage) -> None:
        """Add a message to the tracer."""
        self.messages.append(message)
        if self.external_logger:
            self.external_logger.log_message(message)

    def add_langchain_message(self, message: Union[LCSystemMessage, LCHumanMessage, LCAIMessage, LCFunctionMessage, LCToolMessage]) -> None:
        """Add a langchain message to the tracer."""
        if isinstance(message, LCSystemMessage):
            self.add_message(SystemMessageData(content=message.content))
        elif isinstance(message, LCHumanMessage):
            self.add_message(UserMessage(content=message.content))
        elif isinstance(message, LCAIMessage):
            if hasattr(message, "tool_calls") and message.tool_calls:
                tool_calls = []
                for tool_call in message.tool_calls:
                    tool_calls.append(
                        ToolCall(
                            name=tool_call.get("name", ""),
                            args=tool_call.get("args", {}),
                        )
                    )
                self.add_message(
                    AssistantMessage(
                        content=message.content,
                        tool_calls=tool_calls,
                    )
                )
            else:
                self.add_message(AssistantMessage(content=message.content))
        elif isinstance(message, LCFunctionMessage):
            self.add_message(
                FunctionMessageData(
                    name=message.name,
                    content=message.content,
                )
            )
        elif isinstance(message, LCToolMessage):
            self.add_message(
                ToolMessageData(
                    tool_call_id=message.tool_call_id,
                    name=message.name,
                    content=message.content,
                )
            )
        else:
            self.add_message(UnknownMessage(content=str(message)))

    def get_messages(self) -> List[BaseMessage]:
        """Get all messages in the tracer."""
        return self.messages

    def get_message_dicts(self) -> List[Dict]:
        """Get all messages in the tracer as dicts."""
        return [message.dict() for message in self.messages]

    def clear(self) -> None:
        """Clear all messages in the tracer."""
        self.messages = []
