from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, Union
from codegen.sdk.core.autocommit.constants import AutoCommitSymbol
from codegen.sdk.core.node_id_factory import NodeId
from pathlib import Path

if TYPE_CHECKING:
    from codegen.sdk.core.file import File


@dataclass
class AutoCommitNode:
    """The pending update for a node.

    Attributes:
        symbol: The symbol being updated. Kept to ensure correctness
        generation: Version of the symbol
        new_id: New id to fetch (if applicable)
        new_file: File symbol was moved to (if applicable)
    """

    symbol: AutoCommitSymbol
    generation: int
    new_id: NodeId | None = None
    new_file: Optional["File"] = None

@dataclass
class PendingFiles:
    """Current files autocommit is operating on.

    For example, if we read a symbol and find another symbol out of date in the same file, we would
    not want to update it.
    """

    files: set[Path] | None
    all: bool = False

    def __bool__(self) -> bool:
        return bool(self.files) or self.all
