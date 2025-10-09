"""
ChatKit Widget Definitions
Interactive UI components for streaming
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class WorkflowWidget(BaseModel):
    """Workflow progress widget"""
    type: str = "workflow"
    title: str
    steps: List[Dict[str, Any]] = Field(default_factory=list)
    current_step: int = 0
    status: str = "running"  # running, complete, error


class ProgressWidget(BaseModel):
    """Progress bar widget"""
    type: str = "progress"
    label: str
    progress: int = 0  # 0-100
    message: Optional[str] = None


class CodeWidget(BaseModel):
    """Code display widget"""
    type: str = "code"
    language: str = "python"
    code: str
    title: Optional[str] = None


class MarkdownWidget(BaseModel):
    """Markdown content widget"""
    type: str = "markdown"
    content: str


class ImageWidget(BaseModel):
    """Image display widget"""
    type: str = "image"
    url: str
    alt: Optional[str] = None
    caption: Optional[str] = None


class TableWidget(BaseModel):
    """Data table widget"""
    type: str = "table"
    headers: List[str]
    rows: List[List[Any]]
    title: Optional[str] = None


class AgentTreeWidget(BaseModel):
    """Agent hierarchy tree widget"""
    type: str = "agent_tree"
    root_agent: Dict[str, Any]
    sub_agents: List[Dict[str, Any]] = Field(default_factory=list)


class WorkflowCanvasWidget(BaseModel):
    """Workflow DAG visualization widget"""
    type: str = "workflow_canvas"
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    status: Dict[str, str]  # node_id -> status

