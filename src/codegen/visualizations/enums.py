from dataclasses import dataclass
from enum import StrEnum


@dataclass(frozen=True)
class VizNode:
    name: str | None = None
    text: str | None = None
    code: str | None = None
    color: str | None = None
    shape: str | None = None
    start_point: tuple | None = None
    emoji: str | None = None
    end_point: tuple | None = None
    file_path: str | None = None
    symbol_name: str | None = None
    # Added fields for enhanced call graph visualization
    description: str | None = None
    module: str | None = None
    is_async: bool | None = None
    is_method: bool | None = None
    is_private: bool | None = None
    parent_class: str | None = None
    parameters: list | None = None
    return_type: str | None = None
    call_count: int | None = None
    complexity: int | None = None


@dataclass(frozen=True)
class VizEdge:
    """Edge data for visualization graphs"""
    name: str | None = None
    source: str | None = None
    target: str | None = None
    color: str | None = None
    style: str | None = None
    weight: int | None = None
    label: str | None = None
    call_type: str | None = None
    file_path: str | None = None
    start_point: tuple | None = None
    end_point: tuple | None = None


@dataclass(frozen=True)
class GraphJson:
    type: str
    data: dict


class GraphType(StrEnum):
    TREE = "tree"
    GRAPH = "graph"


class CallGraphFilterType(StrEnum):
    """Filter types for call graph visualization"""
    DEPTH = "depth"
    MODULE = "module"
    FUNCTION_TYPE = "function_type"
    PRIVACY = "privacy"
    COMPLEXITY = "complexity"
    CALL_COUNT = "call_count"


class CallGraphEdgeType(StrEnum):
    """Edge types for call graph visualization"""
    DIRECT = "direct"
    INDIRECT = "indirect"
    RECURSIVE = "recursive"
    ASYNC = "async"
    CONDITIONAL = "conditional"
    EXTERNAL = "external"

