from codegen.sdk.codebase.flagging.types import Symbol
from codegen.sdk.codebase.flagging.types import Flags
from dataclasses import dataclass, field
from typing import TypeVar

from codegen.sdk.codebase.flagging.code_flag import CodeFlag
from codegen.sdk.codebase.flagging.enums import MessageType
from codegen.sdk.codebase.flagging.group import Group
from codegen.sdk.core.interfaces.editable import Editable
from codegen.shared.decorators.docs import noapidoc
