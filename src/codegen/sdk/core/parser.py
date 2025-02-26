from __future__ import annotations

from typing import TYPE_CHECKING, Generic, Protocol, TypeVar

from codegen.sdk.core.types import Parent

if TYPE_CHECKING:
    from tree_sitter import Node as TSNode

    from codegen.sdk.codebase.codebase_context import CodebaseContext
    from codegen.sdk.core.interfaces.editable import Editable
    from codegen.sdk.core.node_id_factory import NodeId


Parent = TypeVar("Parent", bound="Editable")


class CanParse(Protocol, Generic[Parent]):
    def __init__(self, node: TSNode, file_node_id: NodeId, ctx: CodebaseContext, parent: Parent) -> None: ...
