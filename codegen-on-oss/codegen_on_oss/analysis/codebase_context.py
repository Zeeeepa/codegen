"""
Codebase context module for code analysis.

This module provides classes and functions for managing codebase context,
including symbol resolution, import tracking, and dependency analysis.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from codegen import Codebase
from codegen.sdk.core.class_definition import Class
from codegen.sdk.core.function import Function
from codegen.sdk.core.import_resolution import Import
from codegen.sdk.core.symbol import Symbol


@dataclass
class CodebaseContext:
    """
    Manages context for a codebase.

    This class provides methods for resolving symbols, tracking imports,
    and analyzing dependencies within a codebase.
    """

    projects: List[Any]
    config: Optional[Any] = None
    _symbol_cache: Dict[str, Symbol] = None
    _import_cache: Dict[str, Import] = None
    _dependency_graph: Dict[str, Set[str]] = None

    def __post_init__(self):
        """Initialize caches and graphs after instance creation."""
        self._symbol_cache = {}
        self._import_cache = {}
        self._dependency_graph = {}
        self._build_caches()

    def _build_caches(self):
        """Build caches for symbols and imports."""
        for project in self.projects:
            if hasattr(project, "codebase") and project.codebase:
                self._cache_symbols(project.codebase)
                self._cache_imports(project.codebase)
                self._build_dependency_graph(project.codebase)

    def _cache_symbols(self, codebase: Codebase):
        """
        Cache symbols from a codebase.

        Args:
            codebase: The codebase to cache symbols from
        """
        for symbol in codebase.symbols:
            if hasattr(symbol, "name") and symbol.name:
                self._symbol_cache[symbol.name] = symbol

    def _cache_imports(self, codebase: Codebase):
        """
        Cache imports from a codebase.

        Args:
            codebase: The codebase to cache imports from
        """
        for file in codebase.files:
            if hasattr(file, "imports"):
                for imp in file.imports:
                    if hasattr(imp, "source") and imp.source:
                        self._import_cache[imp.source] = imp

    def _build_dependency_graph(self, codebase: Codebase):
        """
        Build a dependency graph for a codebase.

        Args:
            codebase: The codebase to build a dependency graph for
        """
        for symbol in codebase.symbols:
            if hasattr(symbol, "name") and symbol.name:
                self._dependency_graph[symbol.name] = set()
                if hasattr(symbol, "dependencies"):
                    for dep in symbol.dependencies:
                        if hasattr(dep, "name") and dep.name:
                            self._dependency_graph[symbol.name].add(dep.name)

    def get_symbol(self, name: str) -> Optional[Symbol]:
        """
        Get a symbol by name.

        Args:
            name: The name of the symbol to get

        Returns:
            The symbol if found, None otherwise
        """
        return self._symbol_cache.get(name)

    def get_import(self, source: str) -> Optional[Import]:
        """
        Get an import by source.

        Args:
            source: The source of the import to get

        Returns:
            The import if found, None otherwise
        """
        return self._import_cache.get(source)

    def get_dependencies(self, symbol_name: str) -> Set[str]:
        """
        Get dependencies for a symbol.

        Args:
            symbol_name: The name of the symbol to get dependencies for

        Returns:
            A set of dependency symbol names
        """
        return self._dependency_graph.get(symbol_name, set())

    def get_dependents(self, symbol_name: str) -> Set[str]:
        """
        Get symbols that depend on a symbol.

        Args:
            symbol_name: The name of the symbol to get dependents for

        Returns:
            A set of dependent symbol names
        """
        dependents = set()
        for name, deps in self._dependency_graph.items():
            if symbol_name in deps:
                dependents.add(name)
        return dependents

    def get_function(self, name: str) -> Optional[Function]:
        """
        Get a function by name.

        Args:
            name: The name of the function to get

        Returns:
            The function if found, None otherwise
        """
        symbol = self.get_symbol(name)
        if symbol and isinstance(symbol, Function):
            return symbol
        return None

    def get_class(self, name: str) -> Optional[Class]:
        """
        Get a class by name.

        Args:
            name: The name of the class to get

        Returns:
            The class if found, None otherwise
        """
        symbol = self.get_symbol(name)
        if symbol and isinstance(symbol, Class):
            return symbol
        return None

    def get_symbols_by_type(self, symbol_type: str) -> List[Symbol]:
        """
        Get symbols by type.

        Args:
            symbol_type: The type of symbols to get

        Returns:
            A list of symbols of the specified type
        """
        return [
            symbol
            for symbol in self._symbol_cache.values()
            if hasattr(symbol, "type") and symbol.type == symbol_type
        ]

    def get_symbols_by_file(self, file_path: str) -> List[Symbol]:
        """
        Get symbols defined in a file.

        Args:
            file_path: The path to the file

        Returns:
            A list of symbols defined in the file
        """
        return [
            symbol
            for symbol in self._symbol_cache.values()
            if hasattr(symbol, "filepath") and symbol.filepath == file_path
        ]

    def get_imports_by_file(self, file_path: str) -> List[Import]:
        """
        Get imports in a file.

        Args:
            file_path: The path to the file

        Returns:
            A list of imports in the file
        """
        return [
            imp
            for imp in self._import_cache.values()
            if hasattr(imp, "filepath") and imp.filepath == file_path
        ]

    def find_symbol_usages(self, symbol_name: str) -> List[Symbol]:
        """
        Find usages of a symbol.

        Args:
            symbol_name: The name of the symbol to find usages of

        Returns:
            A list of symbols that use the specified symbol
        """
        dependents = self.get_dependents(symbol_name)
        return [
            self.get_symbol(name) for name in dependents if name in self._symbol_cache
        ]

    def find_import_usages(self, import_source: str) -> List[Symbol]:
        """
        Find usages of an import.

        Args:
            import_source: The source of the import to find usages of

        Returns:
            A list of symbols that use the specified import
        """
        usages = []
        for symbol in self._symbol_cache.values():
            if hasattr(symbol, "imports"):
                for imp in symbol.imports:
                    if (
                        hasattr(imp, "source")
                        and imp.source == import_source
                    ):
                        usages.append(symbol)
        return usages

    def find_related_symbols(
        self, symbol_name: str, max_depth: int = 2
    ) -> Tuple[Set[Symbol], Set[Symbol]]:
        """
        Find symbols related to a symbol.

        Args:
            symbol_name: The name of the symbol to find related symbols for
            max_depth: The maximum depth to search for related symbols

        Returns:
            A tuple of (dependencies, dependents) sets of symbols
        """
        dependencies = set()
        dependents = set()

        # Find dependencies
        def find_dependencies(name: str, depth: int):
            if depth > max_depth:
                return
            deps = self.get_dependencies(name)
            for dep_name in deps:
                dep = self.get_symbol(dep_name)
                if dep:
                    dependencies.add(dep)
                    find_dependencies(dep_name, depth + 1)

        # Find dependents
        def find_dependents(name: str, depth: int):
            if depth > max_depth:
                return
            deps = self.get_dependents(name)
            for dep_name in deps:
                dep = self.get_symbol(dep_name)
                if dep:
                    dependents.add(dep)
                    find_dependents(dep_name, depth + 1)

        find_dependencies(symbol_name, 1)
        find_dependents(symbol_name, 1)

        return dependencies, dependents

    def get_import_graph(self) -> Dict[str, Set[str]]:
        """
        Get the import graph for the codebase.

        Returns:
            A dictionary mapping file paths to sets of imported file paths
        """
        import_graph = {}
        for file in self.get_all_files():
            if hasattr(file, "filepath") and file.filepath:
                import_graph[file.filepath] = set()
                if hasattr(file, "imports"):
                    for imp in file.imports:
                        if (
                            hasattr(imp, "resolved_filepath")
                            and imp.resolved_filepath
                        ):
                            import_graph[file.filepath].add(imp.resolved_filepath)
        return import_graph

    def get_all_files(self) -> List[Any]:
        """
        Get all files in the codebase.

        Returns:
            A list of all files in the codebase
        """
        files = []
        for project in self.projects:
            if hasattr(project, "codebase") and project.codebase:
                files.extend(project.codebase.files)
        return files

    def get_all_symbols(self) -> List[Symbol]:
        """
        Get all symbols in the codebase.

        Returns:
            A list of all symbols in the codebase
        """
        return list(self._symbol_cache.values())

    def get_all_imports(self) -> List[Import]:
        """
        Get all imports in the codebase.

        Returns:
            A list of all imports in the codebase
        """
        return list(self._import_cache.values())

    def get_symbol_dependencies(self, symbol_name: str) -> List[Symbol]:
        """
        Get dependencies for a symbol.

        Args:
            symbol_name: The name of the symbol to get dependencies for

        Returns:
            A list of dependency symbols
        """
        deps = self.get_dependencies(symbol_name)
        return [
            self.get_symbol(name) for name in deps if name in self._symbol_cache
        ]

    def get_symbol_dependents(self, symbol_name: str) -> List[Symbol]:
        """
        Get symbols that depend on a symbol.

        Args:
            symbol_name: The name of the symbol to get dependents for

        Returns:
            A list of dependent symbols
        """
        deps = self.get_dependents(symbol_name)
        return [
            self.get_symbol(name) for name in deps if name in self._symbol_cache
        ]

