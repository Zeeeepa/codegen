import uuid
from dataclasses import dataclass, field


@dataclass(kw_only=True)
class Relation(BaseNode):
    """Simple relation class connecting two nodes."""

    source_id: str
    target_id: str

    def __hash__(self):
        """Make the relation hashable based on its id."""
        return hash(self.id)

    def __eq__(self, other):
        """Define equality based on id."""
        if not isinstance(other, Relation):
            return NotImplemented
        return self.id == other.id


@dataclass(kw_only=True)
class BaseNode:
    label: str
    properties: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __hash__(self):
        """Make the relation hashable based on its id."""
        return hash(self.id)

    def __eq__(self, other):
        """Define equality based on id."""
        if not isinstance(other, Relation):
            return NotImplemented
        return self.id == other.id


@dataclass(kw_only=True)
class Node(BaseNode):
    """Simple node class with label and properties."""

    name: str
    full_name: str
