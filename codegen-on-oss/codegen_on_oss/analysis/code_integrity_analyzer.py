"""
Analysis module for code integrity.

This module provides tools for analyzing code integrity, including:
- Finding functions with issues
- Identifying classes with problems
- Detecting parameter usage errors
- Comparing error counts between branches
"""

import difflib
import logging
import re
from typing import Any, Dict, List, Optional

from codegen.sdk.core.class_definition import Class
from codegen.sdk.core.codebase import Codebase
from codegen.sdk.core.external_module import ExternalModule
from codegen.sdk.core.function import Function
from codegen.sdk.core.import_statement import Import
from codegen.sdk.core.source_file import SourceFile
from codegen.sdk.core.symbol import Symbol
from codegen.sdk.enums import EdgeType, SymbolType

logger = logging.getLogger(__name__)


def get_codebase_summary(codebase: Codebase) -> str:
    """
    Get a summary of the codebase.

    Args:
        codebase: The codebase to summarize

    Returns:
        A string summary of the codebase
    """
    node_summary = f"""Contains {len(codebase.ctx.get_nodes())} nodes
- {len(list(codebase.files))} files
- {len(list(codebase.imports))} imports
- {len(list(codebase.external_modules))} external_modules
- {len(list(codebase.symbols))} symbols
\t- {len(list(codebase.classes))} classes
\t- {len(list(codebase.functions))} functions
\t- {len(list(codebase.global_vars))} global vars
\t- {len(list(codebase.interfaces))} interfaces
"""
    edge_summary = f"""Contains {len(codebase.ctx.edges)} edges
- {len([x for x in codebase.ctx.edges if x[2].type == EdgeType.SYMBOL_USAGE])} symbol -> used symbol
- {
        len([x for x in codebase.ctx.edges if x[2].type == EdgeType.IMPORT_SYMBOL_RESOLUTION])
    } import -> used symbol
- {len([x for x in codebase.ctx.edges if x[2].type == EdgeType.EXPORT])} export -> exported symbol
    """

    return f"{node_summary}\n{edge_summary}"


def get_file_summary(file: SourceFile) -> str:
    """
    Get a summary of a file.

    Args:
        file: The file to summarize

    Returns:
        A string summary of the file
    """
    return f"""==== [ `{file.name}` (SourceFile) Dependency Summary ] ====
- {len(file.imports)} imports
- {len(file.symbols)} symbol references
\t- {len(file.classes)} classes
\t- {len(file.functions)} functions
\t- {len(file.global_vars)} global vars
\t- {len(file.interfaces)} interfaces

==== [ `{file.name}` Usage Summary ] ====
- {len(file.imports)} importers
"""


def get_class_summary(cls: Class) -> str:
    """
    Get a summary of a class.

    Args:
        cls: The class to summarize

    Returns:
        A string summary of the class
    """
    return f"""==== [ `{cls.name}` (Class) Dependency Summary ] ====
- parent classes: {cls.parent_class_names}
- {len(cls.methods)} methods
- {len(cls.attributes)} attributes
- {len(cls.decorators)} decorators
- {len(cls.dependencies)} dependencies

{get_symbol_summary(cls)}
    """


def get_function_summary(func: Function) -> str:
    """
    Get a summary of a function.

    Args:
        func: The function to summarize

    Returns:
        A string summary of the function
    """
    return f"""==== [ `{func.name}` (Function) Dependency Summary ] ====
- {len(func.return_statements)} return statements
- {len(func.parameters)} parameters
- {len(func.function_calls)} function calls
- {len(func.call_sites)} call sites
- {len(func.decorators)} decorators
- {len(func.dependencies)} dependencies

{get_symbol_summary(func)}
        """


def get_symbol_summary(symbol: Symbol) -> str:
    """
    Get a summary of a symbol.

    Args:
        symbol: The symbol to summarize

    Returns:
        A string summary of the symbol
    """
    usages = symbol.symbol_usages
    imported_symbols = [x.imported_symbol for x in usages if isinstance(x, Import)]

    return f"""==== [ `{symbol.name}` ({type(symbol).__name__}) Usage Summary ] ====
- {len(usages)} usages
\t- {
        len([x for x in usages if isinstance(x, Symbol) and x.symbol_type == SymbolType.Function])
    } functions
\t- {
        len([x for x in usages if isinstance(x, Symbol) and x.symbol_type == SymbolType.Class])
    } classes
\t- {
        len([x for x in usages if isinstance(x, Symbol) and x.symbol_type == SymbolType.GlobalVar])
    } global vars
\t- {
        len([x for x in usages if isinstance(x, Symbol) and x.symbol_type == SymbolType.Interface])
    } interfaces
\t- {len(imported_symbols)} imports
\t\t- {
        len(
            [
                x
                for x in imported_symbols
                if isinstance(x, Symbol) and x.symbol_type == SymbolType.Function
            ]
        )
    } functions
\t\t- {
        len(
            [
                x
                for x in imported_symbols
                if isinstance(x, Symbol) and x.symbol_type == SymbolType.Class
            ]
        )
    } classes
\t\t- {
        len(
            [
                x
                for x in imported_symbols
                if isinstance(x, Symbol) and x.symbol_type == SymbolType.GlobalVar
            ]
        )
    } global vars
\t\t- {
        len(
            [
                x
                for x in imported_symbols
                if isinstance(x, Symbol) and x.symbol_type == SymbolType.Interface
            ]
        )
    } interfaces
\t\t- {len([x for x in imported_symbols if isinstance(x, ExternalModule)])} external modules
\t\t- {len([x for x in imported_symbols if isinstance(x, SourceFile)])} files
    """


class CodeIntegrityAnalyzer:
    """
    Analyzer for code integrity issues.

    This class provides methods for analyzing code integrity issues, including:
    - Finding all functions and classes
    - Identifying errors in functions and classes
    - Detecting improper parameter usage
    - Finding incorrect function callback points

    Attributes:
        codebase (Codebase): The codebase to analyze
        errors (List): List of errors found during analysis
        warnings (List): List of warnings found during analysis
        config (Dict): Configuration options for the analyzer
    """

    # Default thresholds for code quality metrics
    DEFAULT_CONFIG = {
        "max_function_parameters": 7,
        "max_function_returns": 5,
        "max_class_methods": 20,
        "max_class_attributes": 15,
        "max_function_complexity": 15,
        "max_line_length": 100,
        "require_docstrings": True,
        "require_type_hints": False,
        "ignore_patterns": [r"__pycache__", r"\.git", r"\.venv", r"\.env"],
        "severity_levels": {
            "missing_docstring": "warning",
            "empty_function": "error",
            "unused_parameter": "warning",
            "too_many_parameters": "warning",
            "too_many_returns": "warning",
            "empty_class": "error",
            "too_many_methods": "warning",
            "too_many_attributes": "warning",
            "missing_init": "warning",
            "wrong_parameter_type": "error",
            "wrong_callback_signature": "error",
            "high_complexity": "warning",
            "long_line": "warning",
            "missing_type_hints": "warning",
            "inconsistent_return_type": "error",
            "mutable_default_argument": "warning",
            "unused_import": "warning",
            "duplicate_code": "warning",
        },
    }

    def __init__(self, codebase: Codebase, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the analyzer.

        Args:
            codebase: The codebase to analyze
            config: Optional configuration options to override defaults
        """
        self.codebase = codebase
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []

        # Merge provided config with defaults
        self.config = self.DEFAULT_CONFIG.copy()
        if config:
            self.config.update(config)

    def analyze(self) -> Dict[str, Any]:
        """
        Analyze the codebase for integrity issues.

        Returns:
            A dictionary with analysis results
        """
        # Get all functions and classes
        functions = list(self.codebase.functions)
        classes = list(self.codebase.classes)
        files = list(self.codebase.files)

        # Analyze functions
        function_errors = self._analyze_functions(functions)

        # Analyze classes
        class_errors = self._analyze_classes(classes)

        # Analyze parameter usage
        parameter_errors = self._analyze_parameter_usage(functions)

        # Analyze callback points
        callback_errors = self._analyze_callback_points(functions)

        # Analyze imports
        import_errors = self._analyze_imports(files)

        # Analyze code complexity
        complexity_errors = self._analyze_complexity(functions)

        # Analyze type hints
        type_hint_errors = (
            self._analyze_type_hints(functions, classes)
            if self.config["require_type_hints"]
            else []
        )

        # Analyze code duplication
        duplication_errors = self._analyze_code_duplication(files)

        # Combine all errors
        all_errors = (
            function_errors
            + class_errors
            + parameter_errors
            + callback_errors
            + import_errors
            + complexity_errors
            + type_hint_errors
            + duplication_errors
        )

        # Filter errors by severity level if requested
        filtered_errors = all_errors

        # Create summary
        summary = {
            "total_functions": len(functions),
            "total_classes": len(classes),
            "total_files": len(files),
            "total_errors": len(filtered_errors),
            "function_errors": len(function_errors),
            "class_errors": len(class_errors),
            "parameter_errors": len(parameter_errors),
            "callback_errors": len(callback_errors),
            "import_errors": len(import_errors),
            "complexity_errors": len(complexity_errors),
            "type_hint_errors": len(type_hint_errors),
            "duplication_errors": len(duplication_errors),
            "errors": filtered_errors,
            "codebase_summary": get_codebase_summary(self.codebase),
        }

        return summary

    def _analyze_functions(self, functions: List[Function]) -> List[Dict[str, Any]]:
        """
        Analyze functions for errors.

        Args:
            functions: List of functions to analyze

        Returns:
            List of function errors
        """
        errors = []

        for func in functions:
            # Check for missing docstring
            if not func.docstring:
                errors.append(
                    {
                        "type": "function_error",
                        "error_type": "missing_docstring",
                        "name": func.name,
                        "filepath": func.filepath,
                        "line": func.line_range[0],
                        "message": f"Function '{func.name}' is missing a docstring",
                    }
                )

            # Check for empty function
            if not func.body:
                errors.append(
                    {
                        "type": "function_error",
                        "error_type": "empty_function",
                        "name": func.name,
                        "filepath": func.filepath,
                        "line": func.line_range[0],
                        "message": f"Function '{func.name}' has an empty body",
                    }
                )

            # Check for unused parameters
            used_params = set()
            for node in func.body:
                if hasattr(node, "name") and node.name in [p.name for p in func.parameters]:
                    used_params.add(node.name)

            for param in func.parameters:
                if param.name not in used_params and param.name != "self" and param.name != "cls":
                    errors.append(
                        {
                            "type": "function_error",
                            "error_type": "unused_parameter",
                            "name": func.name,
                            "filepath": func.filepath,
                            "line": func.line_range[0],
                            "message": (
                                f"Function '{func.name}' has unused parameter '{param.name}'"
                            ),
                        }
                    )

            # Check for too many parameters
            if len(func.parameters) > self.config["max_function_parameters"]:  # Arbitrary threshold
                errors.append(
                    {
                        "type": "function_error",
                        "error_type": "too_many_parameters",
                        "name": func.name,
                        "filepath": func.filepath,
                        "line": func.line_range[0],
                        "message": f"Function '{func.name}' has too many parameters "
                        f"({len(func.parameters)})",
                    }
                )

            # Check for too many return statements
            if (
                len(func.return_statements) > self.config["max_function_returns"]
            ):  # Arbitrary threshold
                errors.append(
                    {
                        "type": "function_error",
                        "error_type": "too_many_returns",
                        "name": func.name,
                        "filepath": func.filepath,
                        "line": func.line_range[0],
                        "message": f"Function '{func.name}' has too many return statements "
                        f"({len(func.return_statements)})",
                    }
                )

        return errors

    def _analyze_classes(self, classes: List[Class]) -> List[Dict[str, Any]]:
        """
        Analyze classes for errors.

        Args:
            classes: List of classes to analyze

        Returns:
            List of class errors
        """
        errors = []

        for cls in classes:
            # Check for missing docstring
            if not cls.docstring:
                errors.append(
                    {
                        "type": "class_error",
                        "error_type": "missing_docstring",
                        "name": cls.name,
                        "filepath": cls.filepath,
                        "line": cls.line_range[0],
                        "message": f"Class '{cls.name}' is missing a docstring",
                    }
                )

            # Check for empty class
            if not cls.methods and not cls.attributes:
                errors.append(
                    {
                        "type": "class_error",
                        "error_type": "empty_class",
                        "name": cls.name,
                        "filepath": cls.filepath,
                        "line": cls.line_range[0],
                        "message": f"Class '{cls.name}' has no methods or attributes",
                    }
                )

            # Check for too many methods
            if len(cls.methods) > self.config["max_class_methods"]:  # Arbitrary threshold
                errors.append(
                    {
                        "type": "class_error",
                        "error_type": "too_many_methods",
                        "name": cls.name,
                        "filepath": cls.filepath,
                        "line": cls.line_range[0],
                        "message": f"Class '{cls.name}' has too many methods ({len(cls.methods)})",
                    }
                )

            # Check for too many attributes
            if len(cls.attributes) > self.config["max_class_attributes"]:  # Arbitrary threshold
                errors.append(
                    {
                        "type": "class_error",
                        "error_type": "too_many_attributes",
                        "name": cls.name,
                        "filepath": cls.filepath,
                        "line": cls.line_range[0],
                        "message": (
                            f"Class '{cls.name}' has too many attributes ({len(cls.attributes)})"
                        ),
                    }
                )

            # Check for missing __init__ method
            if not any(method.name == "__init__" for method in cls.methods):
                errors.append(
                    {
                        "type": "class_error",
                        "error_type": "missing_init",
                        "name": cls.name,
                        "filepath": cls.filepath,
                        "line": cls.line_range[0],
                        "message": f"Class '{cls.name}' is missing an __init__ method",
                    }
                )

        return errors

    def _analyze_parameter_usage(self, functions: List[Function]) -> List[Dict[str, Any]]:
        """
        Analyze parameter usage for errors.

        Args:
            functions: List of functions to analyze

        Returns:
            List of parameter usage errors
        """
        errors = []

        for func in functions:
            # Check for parameters with wrong types
            for param in func.parameters:
                if param.annotation:
                    # Check if the parameter is used with the correct type
                    # This is a simplified check and would need more sophisticated
                    # analysis in a real implementation
                    for call in func.call_sites:
                        if hasattr(call, "args") and len(call.args) > 0:
                            for i, arg in enumerate(call.args):
                                if (
                                    i < len(func.parameters)
                                    and func.parameters[i].name == param.name
                                ):
                                    if hasattr(arg, "type") and arg.type != param.annotation:
                                        errors.append(
                                            {
                                                "type": "parameter_error",
                                                "error_type": "wrong_parameter_type",
                                                "name": func.name,
                                                "filepath": func.filepath,
                                                "line": call.line_range[0],
                                                "message": (
                                                    "Function "
                                                    f"'{func.name}' is called with wrong type "
                                                    f"for parameter '{param.name}'"
                                                ),
                                            }
                                        )

        return errors

    def _analyze_callback_points(self, functions: List[Function]) -> List[Dict[str, Any]]:
        """
        Analyze callback points for errors.

        Args:
            functions: List of functions to analyze

        Returns:
            List of callback point errors
        """
        errors = []

        for func in functions:
            # Check for functions passed as callbacks
            for call in func.function_calls:
                if hasattr(call, "args") and len(call.args) > 0:
                    for arg in call.args:
                        if hasattr(arg, "name") and arg.name in [f.name for f in functions]:
                            # This is a function being passed as a callback
                            callback_func = next((f for f in functions if f.name == arg.name), None)
                            if callback_func:
                                # Check if the callback function has the right signature
                                # This is a simplified check and would need more sophisticated
                                # analysis in a real implementation
                                if len(callback_func.parameters) == 0:
                                    errors.append(
                                        {
                                            "type": "callback_error",
                                            "error_type": "wrong_callback_signature",
                                            "name": func.name,
                                            "callback_name": callback_func.name,
                                            "filepath": func.filepath,
                                            "line": call.line_range[0],
                                            "message": (
                                                f"Function '{func.name}' passes "
                                                f'"{callback_func.name}" as a callback, '
                                                f"but it has no parameters"
                                            ),
                                        }
                                    )

        return errors

    def _analyze_imports(self, files: List[SourceFile]) -> List[Dict[str, Any]]:
        """
        Analyze imports for errors.

        Args:
            files: List of files to analyze

        Returns:
            List of import errors
        """
        errors = []

        for file in files:
            # Skip files that match ignore patterns
            if any(re.search(pattern, file.filepath) for pattern in self.config["ignore_patterns"]):
                continue

            # Check for unused imports
            used_imports = set()
            for symbol in file.symbols:
                for usage in symbol.symbol_usages:
                    if isinstance(usage, Import):
                        used_imports.add(usage)

            unused_imports = set(file.imports) - used_imports
            for unused_import in unused_imports:
                errors.append(
                    {
                        "type": "import_error",
                        "error_type": "unused_import",
                        "name": unused_import.name if hasattr(unused_import, "name") else "unknown",
                        "filepath": file.filepath,
                        "line": unused_import.line_range[0]
                        if hasattr(unused_import, "line_range")
                        else 0,
                        "message": f"Unused import in {file.name}",
                        "severity": self.config["severity_levels"]["unused_import"],
                    }
                )

        return errors

    def _analyze_complexity(self, functions: List[Function]) -> List[Dict[str, Any]]:
        """
        Analyze code complexity.

        Args:
            functions: List of functions to analyze

        Returns:
            List of complexity errors
        """
        errors = []

        for func in functions:
            # Skip functions that match ignore patterns
            if any(re.search(pattern, func.filepath) for pattern in self.config["ignore_patterns"]):
                continue

            # Calculate cyclomatic complexity (simplified)
            # In a real implementation, this would use a more sophisticated algorithm
            complexity = 1  # Base complexity

            # Count branches (if, for, while, etc.)
            if func.body:
                for node in func.body:
                    if hasattr(node, "type"):
                        if node.type in ["if", "for", "while", "try", "with"]:
                            complexity += 1

            # Check if complexity exceeds threshold
            if complexity > self.config["max_function_complexity"]:
                errors.append(
                    {
                        "type": "complexity_error",
                        "error_type": "high_complexity",
                        "name": func.name,
                        "filepath": func.filepath,
                        "line": func.line_range[0],
                        "message": f"Function '{func.name}' has high cyclomatic complexity "
                        f"({complexity})",
                        "complexity": complexity,
                        "severity": self.config["severity_levels"]["high_complexity"],
                    }
                )

            # Check for mutable default arguments
            for param in func.parameters:
                if hasattr(param, "default") and param.default:
                    if isinstance(param.default, (list, dict, set)):
                        errors.append(
                            {
                                "type": "complexity_error",
                                "error_type": "mutable_default_argument",
                                "name": func.name,
                                "filepath": func.filepath,
                                "line": func.line_range[0],
                                "message": f"Function '{func.name}' uses mutable default argument for parameter '{param.name}'",
                                "severity": self.config["severity_levels"][
                                    "mutable_default_argument"
                                ],
                            }
                        )

        return errors

    def _analyze_type_hints(
        self, functions: List[Function], classes: List[Class]
    ) -> List[Dict[str, Any]]:
        """
        Analyze type hints.

        Args:
            functions: List of functions to analyze
            classes: List of classes to analyze

        Returns:
            List of type hint errors
        """
        errors = []

        # Check functions for missing type hints
        for func in functions:
            # Skip functions that match ignore patterns
            if any(re.search(pattern, func.filepath) for pattern in self.config["ignore_patterns"]):
                continue

            # Check for missing parameter type hints
            for param in func.parameters:
                if param.name not in ["self", "cls"] and not param.annotation:
                    errors.append(
                        {
                            "type": "type_hint_error",
                            "error_type": "missing_type_hints",
                            "name": func.name,
                            "filepath": func.filepath,
                            "line": func.line_range[0],
                            "message": (
                                f"Function '{func.name}' is missing type hint "
                                f"for parameter '{param.name}'"
                            ),
                            "severity": self.config["severity_levels"]["missing_type_hints"],
                        }
                    )

            # Check for missing return type hint
            if not hasattr(func, "return_annotation") or not func.return_annotation:
                # Only flag if the function has return statements
                if func.return_statements:
                    errors.append(
                        {
                            "type": "type_hint_error",
                            "error_type": "missing_type_hints",
                            "name": func.name,
                            "filepath": func.filepath,
                            "line": func.line_range[0],
                            "message": f"Function '{func.name}' is missing return type hint",
                            "severity": self.config["severity_levels"]["missing_type_hints"],
                        }
                    )

            # Check for inconsistent return types
            return_types = set()
            for ret in func.return_statements:
                if hasattr(ret, "value") and hasattr(ret.value, "type"):
                    return_types.add(ret.value.type)

            if len(return_types) > 1:
                errors.append(
                    {
                        "type": "type_hint_error",
                        "error_type": "inconsistent_return_type",
                        "name": func.name,
                        "filepath": func.filepath,
                        "line": func.line_range[0],
                        "message": (
                            f"Function '{func.name}' has inconsistent return types: "
                            f"{', '.join(return_types)}"
                        ),
                        "severity": self.config["severity_levels"]["inconsistent_return_type"],
                    }
                )

        return errors

    def _analyze_code_duplication(self, files: List[SourceFile]) -> List[Dict[str, Any]]:
        """
        Analyze code for duplication.

        Args:
            files: List of files to analyze

        Returns:
            List of code duplication errors
        """
        errors = []

        # This is a simplified implementation
        # In a real implementation, this would use a more sophisticated algorithm
        # like suffix trees or rolling hashes

        # Extract code blocks (e.g., functions, methods) from files
        code_blocks = []
        for file in files:
            # Skip files that match ignore patterns
            if any(re.search(pattern, file.filepath) for pattern in self.config["ignore_patterns"]):
                continue

            # Add functions from this file
            for func in file.functions:
                if func.body:
                    code_blocks.append(
                        {
                            "name": func.name,
                            "filepath": file.filepath,
                            "line": func.line_range[0],
                            "code": "\n".join(func.body)
                            if isinstance(func.body, list)
                            else str(func.body),
                        }
                    )

        # Compare code blocks for similarity
        for i, block1 in enumerate(code_blocks):
            for j in range(i + 1, len(code_blocks)):
                block2 = code_blocks[j]

                # Skip comparing blocks from the same file with similar names
                # (e.g., overloaded methods or test functions)
                if block1["filepath"] == block2["filepath"] and (
                    block1["name"] in block2["name"] or block2["name"] in block1["name"]
                ):
                    continue

                # Calculate similarity ratio
                similarity = difflib.SequenceMatcher(None, block1["code"], block2["code"]).ratio()

                # Flag if similarity is above threshold (e.g., 0.8 or 80%)
                if similarity > 0.8:
                    errors.append(
                        {
                            "type": "duplication_error",
                            "error_type": "duplicate_code",
                            "name": f"{block1['name']} and {block2['name']}",
                            "filepath": block1["filepath"],
                            "line": block1["line"],
                            "message": f"Duplicate code detected: '{block1['name']}' "
                            f"in {block1['filepath']} "
                            f"and '{block2['name']}' in {block2['filepath']} "
                            f"(similarity: {similarity:.2f})",
                            "duplicate_filepath": block2["filepath"],
                            "duplicate_line": block2["line"],
                            "similarity": similarity,
                            "severity": self.config["severity_levels"]["duplicate_code"],
                        }
                    )

        return errors


def compare_branches(main_codebase: Codebase, branch_codebase: Codebase) -> Dict[str, Any]:
    """
    Compare two branches for code integrity issues.

    Args:
        main_codebase: The main branch codebase
        branch_codebase: The feature branch codebase

    Returns:
        A dictionary with comparison results
    """
    # Analyze both codebases
    main_analyzer = CodeIntegrityAnalyzer(main_codebase)
    branch_analyzer = CodeIntegrityAnalyzer(branch_codebase)

    main_results = main_analyzer.analyze()
    branch_results = branch_analyzer.analyze()

    # Compare error counts
    main_error_count = main_results["total_errors"]
    branch_error_count = branch_results["total_errors"]

    # Find new errors in branch
    main_error_keys = {f"{e['type']}:{e['name']}:{e['filepath']}" for e in main_results["errors"]}
    branch_error_keys = {
        f"{e['type']}:{e['name']}:{e['filepath']}" for e in branch_results["errors"]
    }

    new_error_keys = branch_error_keys - main_error_keys
    fixed_error_keys = main_error_keys - branch_error_keys

    new_errors = [
        e
        for e in branch_results["errors"]
        if f"{e['type']}:{e['name']}:{e['filepath']}" in new_error_keys
    ]
    fixed_errors = [
        e
        for e in main_results["errors"]
        if f"{e['type']}:{e['name']}:{e['filepath']}" in fixed_error_keys
    ]

    # Create comparison summary
    comparison = {
        "main_error_count": main_error_count,
        "branch_error_count": branch_error_count,
        "error_diff": branch_error_count - main_error_count,
        "new_errors": new_errors,
        "fixed_errors": fixed_errors,
        "main_summary": main_results["codebase_summary"],
        "branch_summary": branch_results["codebase_summary"],
    }

    return comparison


def analyze_pr(main_codebase: Codebase, pr_codebase: Codebase) -> Dict[str, Any]:
    """
    Analyze a pull request for code integrity issues.

    Args:
        main_codebase: The main branch codebase
        pr_codebase: The PR branch codebase

    Returns:
        A dictionary with analysis results
    """
    # Compare branches
    comparison = compare_branches(main_codebase, pr_codebase)

    # Get all functions and classes in the PR
    pr_functions = list(pr_codebase.functions)
    pr_classes = list(pr_codebase.classes)

    # Get all functions and classes in the main branch
    main_functions = list(main_codebase.functions)
    main_classes = list(main_codebase.classes)

    # Find new and modified functions and classes
    main_function_names = {f.name for f in main_functions}
    main_class_names = {c.name for c in main_classes}

    new_functions = [f for f in pr_functions if f.name not in main_function_names]
    new_classes = [c for c in pr_classes if c.name not in main_class_names]

    modified_functions = []
    for pr_func in pr_functions:
        if pr_func.name in main_function_names:
            main_func = next((f for f in main_functions if f.name == pr_func.name), None)
            if main_func and pr_func.body != main_func.body:
                modified_functions.append(pr_func)

    modified_classes = []
    for pr_class in pr_classes:
        if pr_class.name in main_class_names:
            main_class = next((c for c in main_classes if c.name == pr_class.name), None)
            if main_class and (
                pr_class.methods != main_class.methods
                or pr_class.attributes != main_class.attributes
            ):
                modified_classes.append(pr_class)

    # Analyze new and modified functions and classes
    analyzer = CodeIntegrityAnalyzer(pr_codebase)
    new_function_errors = analyzer._analyze_functions(new_functions)
    new_class_errors = analyzer._analyze_classes(new_classes)
    modified_function_errors = analyzer._analyze_functions(modified_functions)
    modified_class_errors = analyzer._analyze_classes(modified_classes)

    # Create PR analysis summary
    pr_analysis = {
        "comparison": comparison,
        "new_functions": len(new_functions),
        "new_classes": len(new_classes),
        "modified_functions": len(modified_functions),
        "modified_classes": len(modified_classes),
        "new_function_errors": new_function_errors,
        "new_class_errors": new_class_errors,
        "modified_function_errors": modified_function_errors,
        "modified_class_errors": modified_class_errors,
        "total_new_errors": len(new_function_errors)
        + len(new_class_errors)
        + len(modified_function_errors)
        + len(modified_class_errors),
    }

    return pr_analysis
