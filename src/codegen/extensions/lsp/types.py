from dataclasses import dataclass
from pathlib import Path

from lsprotocol import types
from lsprotocol.types import CreateFile, DeleteFile, RenameFile, TextEdit
from pygls.workspace import TextDocument


@dataclass
class File:
    doc: TextDocument | None
    path: Path
    change: TextEdit | None = None
    other_change: CreateFile | RenameFile | DeleteFile | None = None
    version: int = 0

    @property
    def deleted(self) -> bool:
        return self.other_change is not None and self.other_change.kind == "delete"

    @property
    def created(self) -> bool:
        return self.other_change is not None and self.other_change.kind == "create"

    @property
    def identifier(self) -> types.OptionalVersionedTextDocumentIdentifier:
        return types.OptionalVersionedTextDocumentIdentifier(uri=self.path.as_uri(), version=self.version)
