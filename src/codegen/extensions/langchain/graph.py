"""Demo implementation of an agent with Codegen tools."""

from typing import TYPE_CHECKING, Annotated, Any, Literal, Optional

import anthropic
import openai
from langchain.tools import BaseTool
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START
from langgraph.graph.message import add_messages
from langgraph.graph.state import CompiledGraph, StateGraph
from langgraph.pregel import RetryPolicy


class GraphState(dict[str, Any]):
    """State of the graph."""

    query: str
    final_answer: str
    messages: Annotated[list[AnyMessage], add_messages]


class AgentGraph:
    """Main graph class for the agent."""

    def __init__(self, model: "LLM", tools: list[BaseTool], system_message: SystemMessage):
        self.model = model.bind_tools(tools)
        self.tools = tools
        self.tools_by_name = {tool.name: tool for tool in self.tools}
        self.system_message = system_message

    # =================================== NODES ====================================

    # Reasoner node
    def reasoner(self, state: GraphState) -> dict[str, Any]:
        new_turn = len(state["messages"]) == 0 or isinstance(state["messages"][-1], AIMessage)
        messages = state["messages"]
        if new_turn:
            query = state["query"]
            messages.append(HumanMessage(content=query))

        result = self.model.invoke([self.system_message, *messages])

        if isinstance(result, AIMessage):
            return {"messages": [*messages, result], "final_answer": result.content}

        return {"messages": [*messages, result]}

    # Tool node
    def tool_node(self, state: GraphState) -> dict[str, Any]:
        """Performs the tool call"""
        result = []
        for tool_call in state["messages"][-1].tool_calls:
            tool = self.tools_by_name[tool_call["name"]]
            observation = tool.invoke(tool_call["args"])
            result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))
        return {"messages": result}

    # =================================== EDGE CONDITIONS ====================================
    def should_continue(self, state: GraphState) -> Literal["tools", END]:
        messages = state["messages"]
        last_message = messages[-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return END

    # =================================== COMPILE GRAPH ====================================
    def create(self, checkpointer: Optional[MemorySaver] = None, debug: bool = False) -> CompiledGraph:
        """Create and compile the graph."""
        builder = StateGraph(GraphState)

        # the retry policy has an initial interval, a backoff factor, and a max interval of controlling the
        # amount of time between retries
        retry_policy = RetryPolicy(retry_on=[anthropic.RateLimitError, openai.RateLimitError], max_attempts=10)

        # Add nodes
        builder.add_node("reasoner", self.reasoner, retry=retry_policy)
        builder.add_node("tools", self.tool_node, retry=retry_policy)

        # Add edges
        builder.add_edge(START, "reasoner")
        builder.add_edge("tools", "reasoner")
        builder.add_conditional_edges(
            "reasoner",
            self.should_continue,
        )

        return builder.compile(checkpointer=checkpointer, debug=debug)


def create_react_agent(
    model: "LLM",
    tools: list[BaseTool],
    system_message: SystemMessage,
    checkpointer: Optional[MemorySaver] = None,
    debug: bool = False,
) -> CompiledGraph:
    """Create a reactive agent graph."""
    graph = AgentGraph(model, tools, system_message)
    return graph.create(checkpointer=checkpointer, debug=debug)


if TYPE_CHECKING:
    from codegen.extensions.langchain.llm import LLM
