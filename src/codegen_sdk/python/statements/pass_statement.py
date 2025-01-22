from __future__ import annotations

from typing import TYPE_CHECKING, override

from codegen_sdk.core.dataclasses.usage import UsageKind
from codegen_sdk.core.interfaces.has_name import HasName
from codegen_sdk.core.statements.statement import Statement, StatementType
from codegen_sdk.extensions.autocommit import commiter
from codegen_sdk.writer_decorators import noapidoc, py_apidoc

if TYPE_CHECKING:
    pass


@py_apidoc
class PyPassStatement(Statement["PyCodeBlock"]):
    """An abstract representation of a python pass statement."""

    statement_type = StatementType.PASS_STATEMENT

    @noapidoc
    @commiter
    @override
    def _compute_dependencies(self, usage_type: UsageKind, dest: HasName | None = None) -> None:
        pass
