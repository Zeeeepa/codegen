from collections import defaultdict
from dataclasses import dataclass, field

from graph_sitter import TYPE_CHECKING
from graph_sitter.core.detached_symbols.function_call import FunctionCall

if TYPE_CHECKING:
    from graph_sitter.core.function import Function


@dataclass
class MultiGraph[TFunction: Function]:
    """Mapping of API endpoints to their definitions and usages across languages."""

    api_definitions: dict[str, TFunction] = field(default_factory=dict)
    usages: defaultdict[str, list[FunctionCall]] = field(default_factory=lambda: defaultdict(list))
