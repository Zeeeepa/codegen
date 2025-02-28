from __future__ import annotations

from codegen.sdk.core.types import Expression
from codegen.sdk.core.types import Parent
from codegen.sdk.core.types import Parser
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Generic, Protocol, Self, TypeVar

from rich.console import Console

from codegen.sdk.core.expressions.placeholder_type import PlaceholderType
from codegen.sdk.core.expressions.value import Value
from codegen.sdk.core.statements.symbol_statement import SymbolStatement
from codegen.sdk.utils import find_first_function_descendant, find_import_node

if TYPE_CHECKING:
    from tree_sitter import Node as TSNode

    from codegen.sdk.codebase.codebase_context import CodebaseContext
    from codegen.sdk.codebase.node_classes.node_classes import NodeClasses
    from codegen.sdk.core.expressions.type import Type
    from codegen.sdk.core.interfaces.editable import Editable
    from codegen.sdk.core.node_id_factory import NodeId
    from codegen.sdk.core.statements.statement import Statement
    from codegen.sdk.core.symbol import Symbol
    from codegen.sdk.python.detached_symbols.code_block import PyCodeBlock
    from codegen.sdk.typescript.detached_symbols.code_block import TSCodeBlock


Parent = TypeVar("Parent", bound="Editable")


class CanParse(Protocol, Generic[Parent]):
    def __init__(self, node: TSNode, file_node_id: NodeId, ctx: CodebaseContext, parent: Parent) -> None: ...
