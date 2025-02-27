from typing import TYPE_CHECKING, TypeVar

from tree_sitter import Node as TSNode

from codegen.sdk.core.interfaces.editable import Editable
from codegen.sdk.core.interfaces.has_attribute import HasAttribute
from codegen.sdk.core.node_id_factory import NodeId
from codegen.sdk.core.symbol_groups.dict import Dict, Pair
from codegen.sdk.extensions.autocommit import reader
from codegen.shared.decorators.docs import apidoc

if TYPE_CHECKING:
    from codegen.sdk.codebase.codebase_context import CodebaseContext
    from codegen.sdk.core.expressions.expression import Expression

TExpression = TypeVar("TExpression", bound="Expression")
Parent = TypeVar("Parent", bound="Editable")


class PyPair(Pair):
    """A key, value pair belonging to a Python dictionary."""

    def __init__(self, ts_node: TSNode, file_node_id: NodeId, ctx: "CodebaseContext", parent: Parent) -> None:
        super().__init__(ts_node, file_node_id, ctx, parent)


class PyDict(Dict, HasAttribute):
    """Represents a Python dictionary literal in the source code.

    Attributes:
        unpack: An optional unpacking element, if present.
    """

    def __init__(self, ts_node: TSNode, file_node_id: NodeId, ctx: "CodebaseContext", parent: Parent, delimiter: str = ",", pair_type: type[Pair] = PyPair) -> None:
        super().__init__(ts_node, file_node_id, ctx, parent, delimiter=delimiter, pair_type=pair_type)

    @property
    @reader
    def spread_elements(self) -> list[str]:
        """Returns a list of spread elements in this dictionary.

        For dictionaries with unpacking operators like `{ 'a': 1, **b, 'c': 2 }`, this returns
        the spread elements (e.g., `['**b']`).

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

    @apidoc
    def merge(self, other: "PyDict") -> "PyDict":
        """Merges this dictionary with another dictionary.

        Creates a new PyDict object that contains all key-value pairs from both dictionaries.
        If a key exists in both dictionaries, the value from the other dictionary takes precedence.
        Spread elements from both dictionaries are included in the result.

        Args:
            other (PyDict): The dictionary to merge with this one.

        Returns:
            PyDict: A new PyDict object containing the merged key-value pairs.
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
                    merged_items.append(f"'{key}': {value.source}")
                else:
                    merged_items.append(f"'{key}': {value}")
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
                    merged_items.append(f"'{key}': {value.source}")
                else:
                    merged_items.append(f"'{key}': {value}")
                keys_added.add(key)
            except Exception:
                # Handle shorthand properties
                merged_items.append(key)
                keys_added.add(key)

        # Create a new dictionary with the merged items
        merged_source = "{" + ", ".join(merged_items) + "}"

        # Parse the merged source into a new PyDict object
        import tempfile

        from codegen.sdk.codebase.factory.get_session import get_codebase_session
        from codegen.shared.enums.programming_language import ProgrammingLanguage

        # Create a temporary directory for the codebase session
        with tempfile.TemporaryDirectory() as tmpdir:
            with get_codebase_session(tmpdir=tmpdir, files={"temp.py": f"temp = {merged_source}"}, programming_language=ProgrammingLanguage.PYTHON) as codebase:
                file = codebase.get_file("temp.py")
                temp = file.get_symbol("temp")
                return temp.value
