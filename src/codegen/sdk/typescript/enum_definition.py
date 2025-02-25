from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self, TypeVar, override

from codegen.sdk.core.autocommit import commiter, reader, writer
from codegen.sdk.core.dataclasses.usage import UsageKind
from codegen.sdk.core.import_resolution import Import
from codegen.sdk.core.interfaces.has_attribute import HasAttribute
from codegen.sdk.core.symbol import Symbol
from codegen.sdk.enums import SymbolType
from codegen.sdk.typescript.interfaces.has_block import TSHasBlock
from codegen.sdk.typescript.statements.attribute import TSAttribute
from codegen.sdk.typescript.symbol import TSSymbol
from codegen.shared.decorators.docs import noapidoc, ts_apidoc

if TYPE_CHECKING:
    from tree_sitter import Node as TSNode

    from codegen.sdk.codebase.codebase_context import CodebaseContext
    from codegen.sdk.core.detached_symbols.code_block import CodeBlock
    from codegen.sdk.core.expressions import Expression
    from codegen.sdk.core.interfaces.has_name import HasName
    from codegen.sdk.core.interfaces.importable import Importable
    from codegen.sdk.core.node_id_factory import NodeId
    from codegen.sdk.core.statements.statement import Statement
    from codegen.sdk.typescript.detached_symbols.code_block import TSCodeBlock

Parent = TypeVar("Parent", bound="TSHasBlock")


@ts_apidoc
class TSEnum(TSHasBlock, TSSymbol, HasAttribute[TSAttribute]):
    """Representation of an Enum in TypeScript.

    Attributes:
        symbol_type: The type of symbol, set to SymbolType.Enum.
        body: The expression representing the body of the enum.
        code_block: The code block associated with the enum.
    """

    symbol_type = SymbolType.Enum
    body: Expression[Self]
    code_block: TSCodeBlock

    def __init__(
        self,
        ts_node: TSNode,
        file_id: NodeId,
        ctx: CodebaseContext,
        parent: Statement[CodeBlock[TSHasBlock, Any]],
    ) -> None:
        name_node = ts_node.child_by_field_name("name")
        super().__init__(ts_node, file_id, ctx, parent, name_node=name_node)
        body_expr = self._parse_expression(ts_node.child_by_field_name("body"))
        if body_expr is not None:
            # Type checking will be handled at runtime
            self.body = body_expr  # type: ignore

    @property
    @reader
    def attributes(self) -> list[TSAttribute]:
        """Property that retrieves the attributes of a TypeScript enum.

        Returns the list of attributes defined within the enum's code block.

        Returns:
            list[TSAttribute]: List of TSAttribute objects representing the enum's attributes.
        """
        # Cast the attributes to the expected type
        return self.code_block.attributes  # type: ignore

    @reader
    def get_attribute(self, name: str) -> TSAttribute | None:
        """Returns an attribute from the TypeScript enum by its name.

        Args:
            name (str): The name of the attribute to retrieve.

        Returns:
            TSAttribute | None: The attribute with the given name if it exists, None otherwise.
        """
        return next((x for x in self.attributes if x.name == name), None)

    @noapidoc
    @commiter
    def _compute_dependencies(self, usage_type: UsageKind = UsageKind.BODY, dest: HasName | None = None) -> None:
        dest = dest or self.self_dest
        self.body._compute_dependencies(usage_type, dest)

    @property
    @noapidoc
    def descendant_symbols(self) -> list[Importable[Any]]:  # type: ignore[override]
        # Return the descendant symbols from both the parent class and the body
        return super().descendant_symbols + self.body.descendant_symbols

    @noapidoc
    @reader
    @override
    def resolve_attribute(self, name: str) -> TSAttribute | None:
        return self.get_attribute(name)

    @staticmethod
    @noapidoc
    def _get_name_node(ts_node: TSNode) -> TSNode | None:
        if ts_node.type == "enum_declaration":
            return ts_node.child_by_field_name("name")
        return None

    @writer
    def add_attribute_from_source(self, source: str) -> None:
        """Adds an attribute to a TypeScript enum from raw source code.

        This method intelligently places the new attribute in the enum body, maintaining proper formatting.

        Args:
            source (str): The source code of the attribute to be added.

        Returns:
            None
        """
        # Ensure the source ends with a comma for proper TypeScript syntax
        source_to_add = source.strip()
        if not source_to_add.endswith(","):
            source_to_add = source_to_add + ","

        # Get the current content of the enum
        enum_content = self.source

        # Find the closing brace position
        closing_brace_index = enum_content.rfind("}")
        if closing_brace_index == -1:
            return  # Invalid enum format

        # Determine the indentation level
        indent = "    "  # Default indentation

        # Check if the last non-whitespace character before the closing brace is a comma
        last_content = enum_content[:closing_brace_index].rstrip()
        if last_content and last_content[-1] != ",":
            # Add a comma after the last attribute
            insert_point = len(last_content)
            new_content = last_content + "," + f"\n{indent}{source_to_add}\n" + enum_content[closing_brace_index:]
        else:
            # Create the new content with the attribute added before the closing brace
            new_content = last_content + f"\n{indent}{source_to_add}\n" + enum_content[closing_brace_index:]

        # Replace the entire enum content
        self.edit(new_content, fix_indentation=False)

    @writer
    def add_attribute(self, attribute: TSAttribute, include_dependencies: bool = False) -> None:
        """Adds an attribute to a TypeScript enum from another enum or class.

        This method adds an attribute to an enum, optionally including its dependencies.
        If dependencies are included, it will add any necessary imports to the enum's file.

        Args:
            attribute (TSAttribute): The attribute to add to the enum.
            include_dependencies (bool, optional): Whether to include the attribute's dependencies.
                If True, adds any necessary imports to the enum's file. Defaults to False.

        Returns:
            None
        """
        self.add_attribute_from_source(attribute.source)

        if include_dependencies:
            deps = attribute.dependencies
            file = self.file
            for d in deps:
                if isinstance(d, Import) and d.imported_symbol is not None:
                    # Type checking will be handled at runtime
                    file.add_symbol_import(d.imported_symbol)  # type: ignore
                elif isinstance(d, Symbol):
                    file.add_symbol_import(d)
