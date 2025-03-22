"""Code smell detection and refactoring module for Codegen.

This module provides tools to automatically detect and refactor common code smells
in Python and TypeScript codebases.
"""

from codegen.sdk.extensions.code_smells.detector import CodeSmellDetector
from codegen.sdk.extensions.code_smells.refactorer import CodeSmellRefactorer
from codegen.sdk.extensions.code_smells.smells import (
    CodeSmell,
    DuplicateCode,
    LongFunction,
    LongParameterList,
    DeadCode,
    ComplexConditional,
    DataClump,
)

__all__ = [
    "CodeSmellDetector",
    "CodeSmellRefactorer",
    "CodeSmell",
    "DuplicateCode",
    "LongFunction",
    "LongParameterList",
    "DeadCode",
    "ComplexConditional",
    "DataClump",
]