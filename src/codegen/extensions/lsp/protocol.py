import os
from pathlib import Path
from typing import TYPE_CHECKING

from lsprotocol.types import INITIALIZE, InitializeParams, InitializeResult
from pygls.protocol import LanguageServerProtocol, lsp_method

from codegen.configs.models.codebase import CodebaseConfig
from codegen.extensions.lsp.io import LSPIO
from codegen.extensions.lsp.progress import LSPProgress
from codegen.extensions.lsp.utils import get_path
from codegen.sdk.core.codebase import Codebase

if TYPE_CHECKING:
    from codegen.extensions.lsp.server import CodegenLanguageServer


class CodegenLanguageServerProtocol(LanguageServerProtocol):
    _server: "CodegenLanguageServer"

    def _init_codebase(self, params: InitializeParams) -> None:
        progress = LSPProgress(self._server, params.work_done_token)
        if params.root_path:
            root = Path(params.root_path)
        elif params.root_uri:
            root = get_path(params.root_uri)
        else:
            root = os.getcwd()
        config = CodebaseConfig().model_copy(update={"full_range_index": True})
        io = LSPIO(self.workspace)
        self._server.codebase = Codebase(repo_path=str(root), config=config, io=io, progress=progress)
        self._server.progress_manager = progress
        self._server.io = io
        progress.finish_initialization()

    @lsp_method(INITIALIZE)
    def lsp_initialize(self, params: InitializeParams):
        # Call parent's generator and consume it to initialize workspace
        gen = super().lsp_initialize(params)
        # The generator yields (handler, args, kwargs) tuples
        # We need to consume the generator to let it initialize the workspace
        try:
            handler, args, kwargs = next(gen)
            # Call the handler if it exists
            if handler is not None:
                if kwargs:
                    handler(*args, **kwargs)
                else:
                    handler(*args)
        except StopIteration as e:
            # Generator finished, get the return value
            ret = e.value
        
        # Now workspace is initialized, we can init codebase
        self._init_codebase(params)
        return ret
