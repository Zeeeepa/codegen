# This file is auto-generated, do not modify manually. Edit this in src/codegen/gscli/generate/runner_imports.py.
def get_generated_imports():
    return """
# External imports
import os
import re
from pathlib import Path
import networkx as nx
import plotly

# GraphSitter imports (private)

from codegen.git.models.codemod_context import CodemodContext
from codegen.git.models.github_named_user_context import GithubNamedUserContext
from codegen.git.models.pr_options import PROptions
from codegen.git.models.pr_part_context import PRPartContext
from codegen.git.models.pull_request_context import PullRequestContext

from codegen.shared.exceptions.control_flow import StopCodemodException

# GraphSitter imports (public)
from codegen.sdk.codebase.flagging.enums import FlagKwargs
from codegen.sdk.codebase.flagging.enums import MessageType
from codegen.sdk.codebase.span import Span
from codegen.sdk.core.assignment import Assignment
from codegen.sdk.core.class_definition import Class
from codegen.sdk.core.codebase import Codebase
from codegen.sdk.core.codebase import CodebaseType
from codegen.sdk.core.codebase import PyCodebaseType
from codegen.sdk.core.codebase import TSCodebaseType
from codegen.sdk.core.codeowner import CodeOwner
from codegen.sdk.core.dataclasses.usage import Usage
from codegen.sdk.core.dataclasses.usage import UsageKind
from codegen.sdk.core.dataclasses.usage import UsageType
from codegen.sdk.core.detached_symbols.argument import Argument
from codegen.sdk.core.detached_symbols.code_block import CodeBlock
from codegen.sdk.core.detached_symbols.decorator import Decorator
from codegen.sdk.core.detached_symbols.function_call import FunctionCall
from codegen.sdk.core.detached_symbols.parameter import Parameter
from codegen.sdk.core.directory import Directory
from codegen.sdk.core.export import Export
from codegen.sdk.core.expressions.await_expression import AwaitExpression
from codegen.sdk.core.expressions.binary_expression import BinaryExpression
from codegen.sdk.core.expressions.boolean import Boolean
from codegen.sdk.core.expressions.chained_attribute import ChainedAttribute
from codegen.sdk.core.expressions.comparison_expression import ComparisonExpression
from codegen.sdk.core.expressions.expression import Expression
from codegen.sdk.core.expressions.generic_type import GenericType
from codegen.sdk.core.expressions.multi_expression import MultiExpression
from codegen.sdk.core.expressions.name import Name
from codegen.sdk.core.expressions.named_type import NamedType
from codegen.sdk.core.expressions.none_type import NoneType
from codegen.sdk.core.expressions.number import Number
from codegen.sdk.core.expressions.parenthesized_expression import ParenthesizedExpression
from codegen.sdk.core.expressions.placeholder_type import PlaceholderType
from codegen.sdk.core.expressions.string import String
from codegen.sdk.core.expressions.subscript_expression import SubscriptExpression
from codegen.sdk.core.expressions.ternary_expression import TernaryExpression
from codegen.sdk.core.expressions.tuple_type import TupleType
from codegen.sdk.core.expressions.type import Type
from codegen.sdk.core.expressions.unary_expression import UnaryExpression
from codegen.sdk.core.expressions.union_type import UnionType
from codegen.sdk.core.expressions.unpack import Unpack
from codegen.sdk.core.expressions.value import Value
from codegen.sdk.core.external_module import ExternalModule
from codegen.sdk.core.file import File
from codegen.sdk.core.file import SourceFile
from codegen.sdk.core.function import Function
from codegen.sdk.core.import_resolution import Import
from codegen.sdk.core.interface import Interface
from codegen.sdk.core.interfaces.callable import Callable
from codegen.sdk.core.interfaces.editable import Editable
from codegen.sdk.core.interfaces.exportable import Exportable
from codegen.sdk.core.interfaces.has_block import HasBlock
from codegen.sdk.core.interfaces.has_name import HasName
from codegen.sdk.core.interfaces.has_value import HasValue
from codegen.sdk.core.interfaces.importable import Importable
from codegen.sdk.core.interfaces.typeable import Typeable
from codegen.sdk.core.interfaces.unwrappable import Unwrappable
from codegen.sdk.core.interfaces.usable import Usable
from codegen.sdk.core.placeholder.placeholder import Placeholder
from codegen.sdk.core.placeholder.placeholder_stub import StubPlaceholder
from codegen.sdk.core.placeholder.placeholder_type import TypePlaceholder
from codegen.sdk.core.statements.assignment_statement import AssignmentStatement
from codegen.sdk.core.statements.attribute import Attribute
from codegen.sdk.core.statements.block_statement import BlockStatement
from codegen.sdk.core.statements.catch_statement import CatchStatement
from codegen.sdk.core.statements.comment import Comment
from codegen.sdk.core.statements.export_statement import ExportStatement
from codegen.sdk.core.statements.expression_statement import ExpressionStatement
from codegen.sdk.core.statements.for_loop_statement import ForLoopStatement
from codegen.sdk.core.statements.if_block_statement import IfBlockStatement
from codegen.sdk.core.statements.import_statement import ImportStatement
from codegen.sdk.core.statements.raise_statement import RaiseStatement
from codegen.sdk.core.statements.return_statement import ReturnStatement
from codegen.sdk.core.statements.statement import Statement
from codegen.sdk.core.statements.statement import StatementType
from codegen.sdk.core.statements.switch_case import SwitchCase
from codegen.sdk.core.statements.switch_statement import SwitchStatement
from codegen.sdk.core.statements.symbol_statement import SymbolStatement
from codegen.sdk.core.statements.try_catch_statement import TryCatchStatement
from codegen.sdk.core.statements.while_statement import WhileStatement
from codegen.sdk.core.symbol import Symbol
from codegen.sdk.core.symbol_group import SymbolGroup
from codegen.sdk.core.symbol_groups.comment_group import CommentGroup
from codegen.sdk.core.symbol_groups.dict import Dict
from codegen.sdk.core.symbol_groups.dict import Pair
from codegen.sdk.core.symbol_groups.expression_group import ExpressionGroup
from codegen.sdk.core.symbol_groups.list import List
from codegen.sdk.core.symbol_groups.multi_line_collection import MultiLineCollection
from codegen.sdk.core.symbol_groups.tuple import Tuple
from codegen.sdk.core.type_alias import TypeAlias
from codegen.sdk.enums import ImportType
from codegen.sdk.python.assignment import PyAssignment
from codegen.sdk.python.class_definition import PyClass
from codegen.sdk.python.detached_symbols.code_block import PyCodeBlock
from codegen.sdk.python.detached_symbols.decorator import PyDecorator
from codegen.sdk.python.detached_symbols.parameter import PyParameter
from codegen.sdk.python.expressions.chained_attribute import PyChainedAttribute
from codegen.sdk.python.expressions.conditional_expression import PyConditionalExpression
from codegen.sdk.python.expressions.generic_type import PyGenericType
from codegen.sdk.python.expressions.named_type import PyNamedType
from codegen.sdk.python.expressions.string import PyString
from codegen.sdk.python.expressions.union_type import PyUnionType
from codegen.sdk.python.file import PyFile
from codegen.sdk.python.function import PyFunction
from codegen.sdk.python.import_resolution import PyImport
from codegen.sdk.python.interfaces.has_block import PyHasBlock
from codegen.sdk.python.placeholder.placeholder_return_type import PyReturnTypePlaceholder
from codegen.sdk.python.statements.assignment_statement import PyAssignmentStatement
from codegen.sdk.python.statements.attribute import PyAttribute
from codegen.sdk.python.statements.block_statement import PyBlockStatement
from codegen.sdk.python.statements.break_statement import PyBreakStatement
from codegen.sdk.python.statements.catch_statement import PyCatchStatement
from codegen.sdk.python.statements.comment import PyComment
from codegen.sdk.python.statements.comment import PyCommentType
from codegen.sdk.python.statements.for_loop_statement import PyForLoopStatement
from codegen.sdk.python.statements.if_block_statement import PyIfBlockStatement
from codegen.sdk.python.statements.import_statement import PyImportStatement
from codegen.sdk.python.statements.match_case import PyMatchCase
from codegen.sdk.python.statements.match_statement import PyMatchStatement
from codegen.sdk.python.statements.pass_statement import PyPassStatement
from codegen.sdk.python.statements.try_catch_statement import PyTryCatchStatement
from codegen.sdk.python.statements.while_statement import PyWhileStatement
from codegen.sdk.python.statements.with_statement import WithStatement
from codegen.sdk.python.symbol import PySymbol
from codegen.sdk.python.symbol_groups.comment_group import PyCommentGroup
from codegen.sdk.python.symbol_groups.dict import PyDict
from codegen.sdk.typescript.assignment import TSAssignment
from codegen.sdk.typescript.class_definition import TSClass
from codegen.sdk.typescript.detached_symbols.code_block import TSCodeBlock
from codegen.sdk.typescript.detached_symbols.decorator import TSDecorator
from codegen.sdk.typescript.detached_symbols.jsx.element import JSXElement
from codegen.sdk.typescript.detached_symbols.jsx.expression import JSXExpression
from codegen.sdk.typescript.detached_symbols.jsx.prop import JSXProp
from codegen.sdk.typescript.detached_symbols.parameter import TSParameter
from codegen.sdk.typescript.enum_definition import TSEnum
from codegen.sdk.typescript.export import TSExport
from codegen.sdk.typescript.expressions.array_type import TSArrayType
from codegen.sdk.typescript.expressions.chained_attribute import TSChainedAttribute
from codegen.sdk.typescript.expressions.conditional_type import TSConditionalType
from codegen.sdk.typescript.expressions.expression_type import TSExpressionType
from codegen.sdk.typescript.expressions.function_type import TSFunctionType
from codegen.sdk.typescript.expressions.generic_type import TSGenericType
from codegen.sdk.typescript.expressions.lookup_type import TSLookupType
from codegen.sdk.typescript.expressions.named_type import TSNamedType
from codegen.sdk.typescript.expressions.object_type import TSObjectType
from codegen.sdk.typescript.expressions.query_type import TSQueryType
from codegen.sdk.typescript.expressions.readonly_type import TSReadonlyType
from codegen.sdk.typescript.expressions.string import TSString
from codegen.sdk.typescript.expressions.ternary_expression import TSTernaryExpression
from codegen.sdk.typescript.expressions.undefined_type import TSUndefinedType
from codegen.sdk.typescript.expressions.union_type import TSUnionType
from codegen.sdk.typescript.file import TSFile
from codegen.sdk.typescript.function import TSFunction
from codegen.sdk.typescript.import_resolution import TSImport
from codegen.sdk.typescript.interface import TSInterface
from codegen.sdk.typescript.interfaces.has_block import TSHasBlock
from codegen.sdk.typescript.namespace import TSNamespace
from codegen.sdk.typescript.placeholder.placeholder_return_type import TSReturnTypePlaceholder
from codegen.sdk.typescript.statements.assignment_statement import TSAssignmentStatement
from codegen.sdk.typescript.statements.attribute import TSAttribute
from codegen.sdk.typescript.statements.block_statement import TSBlockStatement
from codegen.sdk.typescript.statements.catch_statement import TSCatchStatement
from codegen.sdk.typescript.statements.comment import TSComment
from codegen.sdk.typescript.statements.comment import TSCommentType
from codegen.sdk.typescript.statements.for_loop_statement import TSForLoopStatement
from codegen.sdk.typescript.statements.if_block_statement import TSIfBlockStatement
from codegen.sdk.typescript.statements.import_statement import TSImportStatement
from codegen.sdk.typescript.statements.labeled_statement import TSLabeledStatement
from codegen.sdk.typescript.statements.switch_case import TSSwitchCase
from codegen.sdk.typescript.statements.switch_statement import TSSwitchStatement
from codegen.sdk.typescript.statements.try_catch_statement import TSTryCatchStatement
from codegen.sdk.typescript.statements.while_statement import TSWhileStatement
from codegen.sdk.typescript.symbol import TSSymbol
from codegen.sdk.typescript.symbol_groups.comment_group import TSCommentGroup
from codegen.sdk.typescript.symbol_groups.dict import TSDict
from codegen.sdk.typescript.symbol_groups.dict import TSPair
from codegen.sdk.typescript.symbol_groups.dict import merge
from codegen.sdk.typescript.ts_config import TSConfig
from codegen.sdk.typescript.type_alias import TSTypeAlias
"""
