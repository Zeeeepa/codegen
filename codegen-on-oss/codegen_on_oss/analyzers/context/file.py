#!/usr/bin/env python3
"""
File Context Module

This module provides a specialized context for file-level analysis,
including structure, imports, exports, and symbols within a file.
"""

import logging
import sys
from typing import Any

try:
    from codegen.sdk.core.class_definition import Class
    from codegen.sdk.core.file import SourceFile
    from codegen.sdk.core.function import Function
    from codegen.sdk.core.symbol import Symbol
    from codegen.sdk.enums import EdgeType, SymbolType
except ImportError:
    print("Codegen SDK not found. Please install it first.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class FileContext:
    """
    Context for file-level analysis.

    This class provides specialized analysis capabilities for a single file,
    including structure analysis, import/export analysis, and symbol analysis.
    """

    def __init__(self, file: SourceFile):
        """
        Initialize the FileContext.

        Args:
            file: The file to analyze
        """
        self.file = file
        self.path = file.file_path if hasattr(file, "file_path") else str(file)
        self.functions = list(file.functions) if hasattr(file, "functions") else []
        self.classes = list(file.classes) if hasattr(file, "classes") else []
        self.imports = list(file.imports) if hasattr(file, "imports") else []
        self.exports = list(file.exports) if hasattr(file, "exports") else []

        # Collect symbols
        self.symbols: list[Symbol] = []
        self.symbols.extend(self.functions)
        self.symbols.extend(self.classes)

        # Add symbols from file.symbols if available
        if hasattr(file, "symbols"):
            for symbol in file.symbols:
                if symbol not in self.symbols:
                    self.symbols.append(symbol)

    def get_symbol(self, name: str) -> Symbol | None:
        """
        Get a symbol by name.

        Args:
            name: Name of the symbol to get

        Returns:
            The symbol, or None if not found
        """
        for symbol in self.symbols:
            if hasattr(symbol, "name") and symbol.name == name:
                return symbol
        return None

    def get_function(self, name: str) -> Function | None:
        """
        Get a function by name.

        Args:
            name: Name of the function to get

        Returns:
            The function, or None if not found
        """
        for func in self.functions:
            if hasattr(func, "name") and func.name == name:
                return func
        return None

    def get_class(self, name: str) -> Class | None:
        """
        Get a class by name.

        Args:
            name: Name of the class to get

        Returns:
            The class, or None if not found
        """
        for cls in self.classes:
            if hasattr(cls, "name") and cls.name == name:
                return cls
        return None

    def get_import(self, name: str) -> Any | None:
        """
        Get an import by name.

        Args:
            name: Name of the import to get

        Returns:
            The import, or None if not found
        """
        for imp in self.imports:
            if hasattr(imp, "name") and imp.name == name:
                return imp
        return None

    def get_export(self, name: str) -> Any | None:
        """
        Get an export by name.

        Args:
            name: Name of the export to get

        Returns:
            The export, or None if not found
        """
        for exp in self.exports:
            if hasattr(exp, "name") and exp.name == name:
                return exp
        return None

    def get_symbols_by_type(self, symbol_type: SymbolType) -> list[Symbol]:
        """
        Get symbols by type.

        Args:
            symbol_type: Type of symbols to get

        Returns:
            List of symbols of the specified type
        """
        return [
            s
            for s in self.symbols
            if hasattr(s, "symbol_type") and s.symbol_type == symbol_type
        ]

    def get_imported_modules(self) -> list[str]:
        """
        Get imported module names.

        Returns:
            List of imported module names
        """
        modules = []
        for imp in self.imports:
            if hasattr(imp, "module_name"):
                modules.append(imp.module_name)
        return modules

    def get_exported_symbols(self) -> list[str]:
        """
        Get exported symbol names.

        Returns:
            List of exported symbol names
        """
        symbols = []
        for exp in self.exports:
            if hasattr(exp, "name"):
                symbols.append(exp.name)
        return symbols

    def analyze_complexity(self) -> dict[str, Any]:
        """
        Analyze code complexity in the file.

        Returns:
            Dictionary containing complexity metrics
        """
        result = {
            "functions": {},
            "average_complexity": 0,
            "max_complexity": 0,
            "total_complexity": 0,
        }

        total_complexity = 0
        max_complexity = 0
        function_count = 0

        for func in self.functions:
            # Calculate cyclomatic complexity
            complexity = self._calculate_cyclomatic_complexity(func)

            # Update metrics
            total_complexity += complexity
            max_complexity = max(max_complexity, complexity)
            function_count += 1

            # Add function metrics
            func_name = func.name if hasattr(func, "name") else str(func)
            result["functions"][func_name] = {
                "complexity": complexity,
                "line_count": len(func.source.split("\n"))
                if hasattr(func, "source")
                else 0,
            }

        # Update summary metrics
        result["average_complexity"] = (
            total_complexity / function_count if function_count > 0 else 0
        )
        result["max_complexity"] = max_complexity
        result["total_complexity"] = total_complexity

        return result

    def _calculate_cyclomatic_complexity(self, function) -> int:
        """
        Calculate cyclomatic complexity for a function.

        Args:
            function: Function to analyze

        Returns:
            Cyclomatic complexity score
        """
        complexity = 1  # Base complexity

        if not hasattr(function, "source"):
            return complexity

        source = function.source

        # Count branching statements
        complexity += source.count("if ")
        complexity += source.count("elif ")
        complexity += source.count("for ")
        complexity += source.count("while ")
        complexity += source.count("except:")
        complexity += source.count("except ")
        complexity += source.count(" and ")
        complexity += source.count(" or ")
        complexity += source.count("case ")

        return complexity

    def analyze_imports(self) -> dict[str, Any]:
        """
        Analyze imports in the file.

        Returns:
            Dictionary containing import analysis
        """
        result = {
            "total_imports": len(self.imports),
            "resolved_imports": 0,
            "unresolved_imports": 0,
            "external_imports": 0,
            "internal_imports": 0,
            "import_details": [],
        }

        for imp in self.imports:
            import_info = {
                "name": imp.name if hasattr(imp, "name") else str(imp),
                "module": imp.module_name if hasattr(imp, "module_name") else "unknown",
                "is_resolved": False,
                "is_external": False,
            }

            # Check if import is resolved
            if (hasattr(imp, "resolved_file") and imp.resolved_file) or (hasattr(imp, "resolved_symbol") and imp.resolved_symbol):
                import_info["is_resolved"] = True
                result["resolved_imports"] += 1
            else:
                result["unresolved_imports"] += 1

            # Check if import is external
            if hasattr(imp, "is_external"):
                import_info["is_external"] = imp.is_external
                if imp.is_external:
                    result["external_imports"] += 1
                else:
                    result["internal_imports"] += 1

            result["import_details"].append(import_info)

        return result

    def analyze_structure(self) -> dict[str, Any]:
        """
        Analyze file structure.

        Returns:
            Dictionary containing structure analysis
        """
        result = {
            "path": self.path,
            "line_count": 0,
            "function_count": len(self.functions),
            "class_count": len(self.classes),
            "import_count": len(self.imports),
            "export_count": len(self.exports),
        }

        # Count lines of code
        if hasattr(self.file, "content"):
            result["line_count"] = len(self.file.content.split("\n"))

        return result

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the file context to a dictionary.

        Returns:
            Dictionary representation of the file context
        """
        return {
            "path": self.path,
            "functions": [
                func.name if hasattr(func, "name") else str(func)
                for func in self.functions
            ],
            "classes": [
                cls.name if hasattr(cls, "name") else str(cls) for cls in self.classes
            ],
            "imports": [
                imp.name if hasattr(imp, "name") else str(imp) for imp in self.imports
            ],
            "exports": [
                exp.name if hasattr(exp, "name") else str(exp) for exp in self.exports
            ],
            "symbols": [
                sym.name if hasattr(sym, "name") else str(sym) for sym in self.symbols
            ],
        }
