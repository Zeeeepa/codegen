import logging
from typing import TYPE_CHECKING, Any

from lsprotocol.types import Position, Range

from codegen.extensions.lsp.codemods.base import CodeAction

if TYPE_CHECKING:
    from codegen.extensions.lsp.server import CodegenLanguageServer

logger = logging.getLogger(__name__)


def process_args(args: Any) -> tuple[str, Range]:
    uri = args[0]
    range = args[1]
    range = Range(start=Position(line=range["start"]["line"], character=range["start"]["character"]), end=Position(line=range["end"]["line"], character=range["end"]["character"]))
    return uri, range


def execute_action(server: "CodegenLanguageServer", action: CodeAction, args: Any) -> None:
    uri, range = process_args(args)
    node = server.get_node_under_cursor(uri, range.start, range.end)
    if node is None:
        logger.warning(f"No node found for range {range}")
        return
    action.execute(server, node, *args[2:])
    server.codebase.commit()
