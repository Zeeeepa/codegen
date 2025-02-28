from __future__ import annotations

from codegen.sdk.core.dataclasses.types import UsageType
from codegen.sdk.core.dataclasses.types import UsageKind
from codegen.sdk.core.dataclasses.types import Usage
from dataclasses import dataclass
from enum import IntEnum, IntFlag, auto, unique
from typing import TYPE_CHECKING

from dataclasses_json import dataclass_json

from codegen.shared.decorators.docs import apidoc

if TYPE_CHECKING:
    from codegen.sdk.core.detached_symbols.function_call import FunctionCall
    from codegen.sdk.core.export import Export
    from codegen.sdk.core.expressions import Name
    from codegen.sdk.core.expressions.chained_attribute import ChainedAttribute
    from codegen.sdk.core.file import SourceFile
    from codegen.sdk.core.import_resolution import Import
    from codegen.sdk.core.symbol import Symbol
