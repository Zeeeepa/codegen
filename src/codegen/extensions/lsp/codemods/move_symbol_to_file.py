from typing import TYPE_CHECKING

from codegen.extensions.lsp.codemods.base import CodeAction
from codegen.sdk.core.interfaces.editable import Editable

if TYPE_CHECKING:
    from codegen.extensions.lsp.server import CodegenLanguageServer
