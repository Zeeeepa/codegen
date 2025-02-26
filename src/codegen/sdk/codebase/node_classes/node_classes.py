from __future__ import annotations

from codegen.sdk.codebase.node_classes.types import NodeClasses
from dataclasses import dataclass, field
from functools import cached_property
from typing import TYPE_CHECKING

from codegen.sdk.core.interfaces.resolvable import Resolvable

if TYPE_CHECKING:
    from codegen.sdk.core.class_definition import Class
    from codegen.sdk.core.detached_symbols.code_block import CodeBlock
    from codegen.sdk.core.detached_symbols.function_call import FunctionCall
    from codegen.sdk.core.detached_symbols.parameter import Parameter
    from codegen.sdk.core.expressions import Expression
    from codegen.sdk.core.expressions.type import Type
    from codegen.sdk.core.file import SourceFile
    from codegen.sdk.core.function import Function
    from codegen.sdk.core.import_resolution import Import
    from codegen.sdk.core.statements.comment import Comment
    from codegen.sdk.core.symbol import Symbol
