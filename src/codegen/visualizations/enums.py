from codegen.visualizations.types import VizNode
from codegen.visualizations.types import GraphJson
from dataclasses import dataclass
from enum import StrEnum


class GraphType(StrEnum):
    TREE = "tree"
    GRAPH = "graph"
