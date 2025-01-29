from typing import TYPE_CHECKING, Generic, TypeVar

from tree_sitter import Node as TSNode

from codegen.sdk.codebase.codebase_graph import CodebaseGraph
from codegen.sdk.core.expressions import Expression, Name
from codegen.sdk.core.expressions.chained_attribute import ChainedAttribute
from codegen.sdk.core.node_id_factory import NodeId
from codegen.shared.decorators.docs import py_apidoc

if TYPE_CHECKING:
    from codegen.sdk.core.interfaces.editable import Editable

Parent = TypeVar("Parent", bound="Editable")


@py_apidoc
class PyChainedAttribute(ChainedAttribute[Expression, Name, Parent], Generic[Parent]):
    """Abstract representation of a python chained attribute.
    This includes methods of python classes and module functions.
    """

    def __init__(self, ts_node: TSNode, file_node_id: NodeId, G: CodebaseGraph, parent: Parent) -> None:
        super().__init__(ts_node, file_node_id, G, parent=parent, object=ts_node.child_by_field_name("object"), attribute=ts_node.child_by_field_name("attribute"))
