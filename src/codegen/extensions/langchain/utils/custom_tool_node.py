"""Custom tool execution with truncation detection for LangGraph 1.0."""

from typing import Any, Callable, Optional, Sequence, Union

from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.stores import InMemoryBaseStore
from langchain_core.tools import BaseTool


class CustomToolNode:
    """Tool executor that detects truncated tool calls.
    
    This replaces the removed langgraph.prebuilt.ToolNode with custom
    truncation detection logic for handling max_tokens scenarios.
    """

    def __init__(
        self,
        tools: Sequence[Union[BaseTool, Callable]],
        *,
        name: str = "tools",
        tags: Optional[list[str]] = None,
        handle_tool_errors: Union[bool, Callable[[Exception], str]] = True,
    ) -> None:
        """Initialize the CustomToolNode.
        
        Args:
            tools: List of tools to make available for execution
            name: Name of the node (default: "tools")
            tags: Optional tags for the node
            handle_tool_errors: Whether/how to handle tool errors
        """
        self.tools_by_name = {tool.name if isinstance(tool, BaseTool) else tool.__name__: tool for tool in tools}
        self.name = name
        self.tags = tags or []
        self.handle_tool_errors = handle_tool_errors

    def __call__(self, state: dict[str, Any], config: RunnableConfig) -> dict[str, Any]:
        """Execute tools based on the state.
        
        Args:
            state: Current state containing messages
            config: Runnable configuration with store access
            
        Returns:
            Updated state with tool messages
        """
        messages = state.get("messages", [])
        if not messages:
            return {"messages": []}

        # Get the last message
        last_message = messages[-1]
        
        # Check for truncation before executing tools
        store = config.get("configurable", {}).get("store")
        if isinstance(last_message, AIMessage) and store:
            self._check_truncation(last_message, store)

        # Execute tool calls
        if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
            return {"messages": []}

        tool_messages = []
        for tool_call in last_message.tool_calls:
            tool_name = tool_call.get("name")
            tool = self.tools_by_name.get(tool_name)
            
            if not tool:
                error_msg = f"Tool '{tool_name}' not found. Available tools: {list(self.tools_by_name.keys())}"
                tool_messages.append(
                    ToolMessage(
                        content=error_msg,
                        tool_call_id=tool_call.get("id", ""),
                        name=tool_name,
                    )
                )
                continue

            try:
                # Execute the tool
                if isinstance(tool, BaseTool):
                    result = tool.invoke(tool_call.get("args", {}), config=config)
                else:
                    result = tool(**tool_call.get("args", {}))
                
                tool_messages.append(
                    ToolMessage(
                        content=str(result),
                        tool_call_id=tool_call.get("id", ""),
                        name=tool_name,
                    )
                )
            except Exception as e:
                if self.handle_tool_errors:
                    error_content = self._handle_error(e) if callable(self.handle_tool_errors) else str(e)
                    tool_messages.append(
                        ToolMessage(
                            content=f"Error: {error_content}",
                            tool_call_id=tool_call.get("id", ""),
                            name=tool_name,
                        )
                    )
                else:
                    raise

        return {"messages": tool_messages}

    def _check_truncation(self, message: AIMessage, store: InMemoryBaseStore) -> None:
        """Check if the response was truncated due to max tokens.
        
        Args:
            message: The AI message to check
            store: Store for persisting truncation state
        """
        response_metadata = message.response_metadata
        
        # Check if the stop reason is due to max tokens
        if response_metadata.get("stop_reason") == "max_tokens":
            # Check if the response metadata contains usage information
            if "usage" not in response_metadata or "output_tokens" not in response_metadata["usage"]:
                msg = "Response metadata is missing usage information."
                raise ValueError(msg)

            output_tokens = response_metadata["usage"]["output_tokens"]
            
            # Set flag for create_file tool calls
            for tool_call in message.tool_calls:
                if tool_call.get("name") == "create_file":
                    store.mset([
                        (tool_call["name"], {
                            "max_tokens": output_tokens,
                            "max_tokens_reached": True
                        })
                    ])

    def _handle_error(self, error: Exception) -> str:
        """Handle tool execution errors.
        
        Args:
            error: The exception that occurred
            
        Returns:
            Error message string
        """
        if callable(self.handle_tool_errors):
            return self.handle_tool_errors(error)
        return str(error)
