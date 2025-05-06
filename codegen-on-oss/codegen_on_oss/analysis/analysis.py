"""
Unified Analysis Module for Codegen-on-OSS

This module serves as a central hub for all code analysis functionality, integrating
various specialized analysis components into a cohesive system.
"""

import difflib
import math
import os
import re
import subprocess
from datetime import UTC, datetime, timedelta
from typing import Any, Dict, List, Optional

import requests
import uvicorn
from graph_sitter.core.codebase import Codebase
from graph_sitter.core.class_definition import Class
from graph_sitter.core.expressions.binary_expression import BinaryExpression
from graph_sitter.core.expressions.comparison_expression import ComparisonExpression
from graph_sitter.core.expressions.unary_expression import UnaryExpression
from graph_sitter.core.external_module import ExternalModule
from graph_sitter.core.file import SourceFile
from graph_sitter.core.function import Function
from graph_sitter.core.statements.for_loop_statement import ForLoopStatement
from graph_sitter.core.statements.if_block_statement import IfBlockStatement
from graph_sitter.core.statements.try_catch_statement import TryCatchStatement
from graph_sitter.core.statements.while_statement import WhileStatement
from graph_sitter.core.symbol import Symbol

# ... rest of the imports ...
