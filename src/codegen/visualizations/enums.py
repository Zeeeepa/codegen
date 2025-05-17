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


@dataclass(frozen=True)
class GraphJson:
    type: str
    data: dict


class GraphType(StrEnum):
    TREE = "tree"
    GRAPH = "graph"


class ElementType(StrEnum):
    """Types of elements that can be selected in the visualization UI."""
    SYMBOL = "symbol"
    FILE = "file"
    FUNCTION = "function"
    CLASS = "class"


@dataclass(frozen=True)
class SelectedElement:
    """Represents an element selected in the visualization UI."""
    type: ElementType
    id: str
    name: str
    methods: list[str] | None = None
    related_elements: list[str] | None = None
