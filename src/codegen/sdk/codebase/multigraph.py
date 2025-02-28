from collections import defaultdict
from dataclasses import dataclass, field
from typing import Generic, TypeVar

from codegen.sdk import TYPE_CHECKING
from codegen.sdk.core.detached_symbols.function_call import FunctionCall

if TYPE_CHECKING:
    from codegen.sdk.core.function import Function
