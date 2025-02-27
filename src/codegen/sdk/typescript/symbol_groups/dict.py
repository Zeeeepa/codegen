import logging
from typing import TYPE_CHECKING, Self, TypeVar, override

from tree_sitter import Node as TSNode

from codegen.sdk.core.autocommit import writer
from codegen.sdk.core.expressions import Expression
from codegen.sdk.core.expressions.string import String
from codegen.sdk.core.interfaces.editable import Editable
from codegen.sdk.core.interfaces.has_attribute import HasAttribute
from codegen.sdk.core.node_id_factory import NodeId
from codegen.sdk.core.symbol_groups.dict import Dict, Pair
from codegen.sdk.extensions.autocommit import reader
from codegen.shared.decorators.docs import apidoc, noapidoc, ts_apidoc

if TYPE_CHECKING:
    from codegen.sdk.codebase.codebase_context import CodebaseContext

Parent = TypeVar("Parent", bound="Editable")
TExpression = TypeVar("TExpression", bound=Expression)

logger = logging.getLogger(__name__)


@ts_apidoc
class TSPair(Pair):
    """A TypeScript pair node that represents key-value pairs in object literals.

    A specialized class extending `Pair` for handling TypeScript key-value pairs,
    particularly in object literals. It provides functionality for handling both
    regular key-value pairs and shorthand property identifiers, with support for
    reducing boolean conditions.

    Attributes:
        shorthand (bool): Indicates whether this pair uses shorthand property syntax.
    """

    shorthand: bool

    def __init__(self, ts_node: TSNode, file_node_id: NodeId, ctx: "CodebaseContext", parent: Parent) -> None:
        super().__init__(ts_node, file_node_id, ctx, parent)
        self.shorthand = ts_node.type == "shorthand_property_identifier"

    def _get_key_value(self) -> tuple[Expression[Self] | None, Expression[Self] | None]:
        from codegen.sdk.typescript.function import TSFunction

        key, value = None, None

        if self.ts_node.type == "pair":
            key = self.child_by_field_name("key")
            value = self.child_by_field_name("value")
            if TSFunction.is_valid_node(value.ts_node):
                value = self._parse_expression(value.ts_node)
        elif self.ts_node.type == "shorthand_property_identifier":
            key = value = self._parse_expression(self.ts_node)
        elif TSFunction.is_valid_node(self.ts_node):
            value = self._parse_expression(self.ts_node)
            key = value.get_name()
        else:
            return super()._get_key_value()
        return key, value

    @writer
    def reduce_condition(self, bool_condition: bool, node: Editable | None = None) -> None:
        """Reduces an editable to the following condition"""
        if self.shorthand and node == self.value:
            # Object shorthand
            self.parent[self.key.source] = self.ctx.node_classes.bool_conversion[bool_condition]
        else:
            super().reduce_condition(bool_condition, node)


@apidoc
class TSDict(Dict, HasAttribute):
    """A typescript dict object. You can use standard operations to operate on this dict (IE len, del, set, get, etc)"""

    def __init__(self, ts_node: TSNode, file_node_id: NodeId, ctx: "CodebaseContext", parent: Parent, delimiter: str = ",", pair_type: type[Pair] = TSPair) -> None:
        super().__init__(ts_node, file_node_id, ctx, parent, delimiter=delimiter, pair_type=pair_type)

    @property
    @reader
    def spread_elements(self) -> list[str]:
        """Returns a list of spread elements in this dictionary.

        For dictionaries with spread operators like `{ a: 1, ...b, c: 2 }`, this returns
        the spread elements (e.g., `['...b']`).

        Returns:
            list[str]: A list of spread elements as strings.
        """
        result = []
        if self.unpack:
            # Extract the spread element from the unpack node
            spread_source = self.unpack.source
            # Remove the curly braces if they exist
            if spread_source.startswith("{") and spread_source.endswith("}"):
                spread_source = spread_source[1:-1].strip()
            result.append(spread_source)
        return result

    def __getitem__(self, __key: str) -> TExpression:
        for pair in self._underlying:
            pair_match = None

            if isinstance(pair, Pair):
                if isinstance(pair.key, String):
                    if pair.key.content == str(__key):
                        pair_match = pair
                elif pair.key is not None:
                    if pair.key.source == str(__key):
                        pair_match = pair

                if pair_match:
                    if pair_match.value is not None:
                        return pair_match.value
                    else:
                        return pair_match.key
        msg = f"Key {__key} not found in {list(self.keys())} {self._underlying!r}"
        raise KeyError(msg)

    def __setitem__(self, __key: str, __value: TExpression) -> None:
        new_value = __value.source if isinstance(__value, Editable) else str(__value)
        for pair in self._underlying:
            pair_match = None

            if isinstance(pair, Pair):
                if isinstance(pair.key, String):
                    if pair.key.content == str(__key):
                        pair_match = pair
                elif pair.key is not None:
                    if pair.key.source == str(__key):
                        pair_match = pair

                if pair_match:
                    # CASE: {a: b}
                    if not pair_match.shorthand:
                        if __key == new_value:
                            pair_match.edit(f"{__key}")
                        else:
                            pair.value.edit(f"{new_value}")
                    # CASE: {a}
                    else:
                        if __key == new_value:
                            pair_match.edit(f"{__key}")
                        else:
                            pair_match.edit(f"{__key}: {new_value}")
                    break
        # CASE: {}
        else:
            if not self.ctx.node_classes.int_dict_key:
                try:
                    int(__key)
                    __key = f"'{__key}'"
                except ValueError:
                    pass
            if __key == new_value:
                self._underlying.append(f"{__key}")
            else:
                self._underlying.append(f"{__key}: {new_value}")

    @apidoc
    def merge(self, other: "TSDict") -> "TSDict":
        """Merges this dictionary with another dictionary.

        Creates a new TSDict object that contains all key-value pairs from both dictionaries.
        If a key exists in both dictionaries, the value from the other dictionary takes precedence.
        Spread elements from both dictionaries are included in the result.

        Args:
            other (TSDict): The dictionary to merge with this one.

        Returns:
            TSDict: A new TSDict object containing the merged key-value pairs.
        """
        # Create a temporary object literal string with all key-value pairs
        merged_items = []
        keys_added = set()

        # Add spread elements from this dictionary
        if self.unpack:
            merged_items.append(self.unpack.source)

        # Add spread elements from the other dictionary (they take precedence)
        if other.unpack:
            merged_items.append(other.unpack.source)

        # Add all key-value pairs from the other dictionary first (they take precedence)
        for key in other:
            try:
                value = other[key]
                if isinstance(value, Editable):
                    merged_items.append(f"{key}: {value.source}")
                else:
                    merged_items.append(f"{key}: {value}")
                keys_added.add(key)
            except Exception:
                # Handle shorthand properties
                merged_items.append(key)
                keys_added.add(key)

        # Add all key-value pairs from this dictionary that aren't in the other dictionary
        for key in self:
            if key in keys_added:
                continue
            try:
                value = self[key]
                if isinstance(value, Editable):
                    merged_items.append(f"{key}: {value.source}")
                else:
                    merged_items.append(f"{key}: {value}")
                keys_added.add(key)
            except Exception:
                # Handle shorthand properties
                merged_items.append(key)
                keys_added.add(key)

        # Create a new dictionary with the merged items
        merged_source = "{" + ", ".join(merged_items) + "}"

        # Parse the merged source into a new TSDict object
        import tempfile

        from codegen.sdk.codebase.factory.get_session import get_codebase_session
        from codegen.shared.enums.programming_language import ProgrammingLanguage

        # Create a temporary directory for the codebase session
        with tempfile.TemporaryDirectory() as tmpdir:
            with get_codebase_session(tmpdir=tmpdir, files={"temp.ts": f"let temp = {merged_source}"}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
                file = codebase.get_file("temp.ts")
                temp = file.get_symbol("temp")
                return temp.value

    @reader
    @noapidoc
    @override
    def resolve_attribute(self, name: str) -> "Expression | None":
        return self.get(name, None)
