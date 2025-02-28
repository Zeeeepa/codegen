from enum import Enum

from codegen.extensions.graph.types import Node, Relation


class NodeLabel(Enum):
    CLASS = "Class"
    METHOD = "Method"
    FUNCTION = "Func"


class RelationLabel(Enum):
    DEFINES = "DEFINES"
    INHERITS_FROM = "INHERITS_FROM"
    CALLS = "CALLS"


class SimpleGraph:
    """Basic graph implementation using sets of nodes and relations."""

    def __init__(self):
        self.nodes: dict[str, Node] = {}
        self.relations: set[Relation] = set()
        self.existing_relations: set[str] = set()

    def add_node(self, node: Node) -> None:
        """Add a node to the graph."""
        self.nodes[node.id] = node

    def add_relation(self, relation: Relation) -> None:
        """Add a relation to the graph."""
        related_nodes = f"{relation.source_id}->{relation.label}->{relation.target_id}"
        if relation.source_id in self.nodes and relation.target_id in self.nodes and related_nodes not in self.existing_relations:
            self.relations.add(relation)
            self.existing_relations.add(related_nodes)
