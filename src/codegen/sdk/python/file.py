from __future__ import annotations

from typing import TYPE_CHECKING

from codegen.sdk.core.autocommit import commiter, reader, writer
from codegen.sdk.core.file import SourceFile
from codegen.sdk.core.interface import Interface
from codegen.sdk.enums import ImportType, ProgrammingLanguage
from codegen.sdk.extensions.utils import cached_property, iter_all_descendants
from codegen.sdk.python import PyAssignment
from codegen.sdk.python.class_definition import PyClass
from codegen.sdk.python.detached_symbols.code_block import PyCodeBlock
from codegen.sdk.python.expressions.type import PyType
from codegen.sdk.python.function import PyFunction
from codegen.sdk.python.import_resolution import PyImport
from codegen.sdk.python.interfaces.has_block import PyHasBlock
from codegen.sdk.python.statements.attribute import PyAttribute
from codegen.sdk.python.statements.import_statement import PyImportStatement
from codegen.shared.decorators.docs import noapidoc, py_apidoc

if TYPE_CHECKING:
    from codegen.sdk.codebase.codebase_graph import CodebaseGraph
    from codegen.sdk.core.import_resolution import WildcardImport
    from codegen.sdk.python.symbol import PySymbol


@py_apidoc
class PyFile(SourceFile[PyImport, PyFunction, PyClass, PyAssignment, Interface[PyCodeBlock, PyAttribute, PyFunction, PyType], PyCodeBlock], PyHasBlock):
    """SourceFile representation for Python codebase"""

    programming_language = ProgrammingLanguage.PYTHON

    @staticmethod
    def get_extensions() -> list[str]:
        """Returns the file extensions associated with Python files.

        Gets the list of file extensions that are considered Python files.

        Returns:
            list[str]: A list containing '.py' as the only Python file extension.
        """
        return [".py"]

    def symbol_can_be_added(self, symbol: PySymbol) -> bool:
        """Checks if a Python symbol can be added to this Python source file.

        Verifies whether a given Python symbol is compatible with and can be added to this Python source file. Currently always returns True as Python files can contain any Python symbol type.

        Args:
            symbol (PySymbol): The Python symbol to check for compatibility with this file.

        Returns:
            bool: Always returns True as Python files can contain any Python symbol type.
        """
        return True

    @noapidoc
    @commiter
    def _parse_imports(self) -> None:
        for import_node in iter_all_descendants(self.ts_node, frozenset({"import_statement", "import_from_statement", "future_import_statement"})):
            PyImportStatement(import_node, self.node_id, self.G, self.code_block, 0)

    ####################################################################################################################
    # GETTERS
    ####################################################################################################################

    @noapidoc
    def get_import_module_name_for_file(self, filepath: str, G: CodebaseGraph) -> str:
        """Returns the module name that this file gets imported as

        For example, `my/package/name.py` => `my.package.name`
        """
        base_path = G.projects[0].base_path
        module = filepath.replace(".py", "")
        if module.endswith("__init__"):
            module = "/".join(module.split("/")[:-1])
        module = module.replace("/", ".")
        # TODO - FIX EDGE CASE WITH REPO BASE!!
        if base_path and module.startswith(base_path):
            module = module.replace(f"{base_path}.", "", 1)
        # TODO - FIX EDGE CASE WITH SRC BASE
        if module.startswith("src."):
            module = module.replace("src.", "", 1)
        return module

    @reader
    def get_import_string(self, alias: str | None = None, module: str | None = None, import_type: ImportType = ImportType.UNKNOWN, is_type_import: bool = False) -> str:
        """Generates an import string for a symbol.

        Constructs a Python import statement based on the provided parameters, handling different import types and module paths.

        Args:
            alias (str | None, optional): Alias to use for the imported symbol. Defaults to None.
            module (str | None, optional): Module path to import from. If None, uses module name from source. Defaults to None.
            import_type (ImportType, optional): Type of import statement to generate. Defaults to ImportType.UNKNOWN.
            is_type_import (bool, optional): Whether this is a type import. Currently unused. Defaults to False.

        Returns:
            str: A formatted import string in the form of 'from {module} import {symbol}' with optional alias or wildcard syntax.
        """
        symbol_name = self.name
        module = module if module is not None else self.import_module_name
        # Case: importing dir/file.py
        if f".{symbol_name}" in module:
            module = module.replace(f".{symbol_name}", "")
        # Case: importing file.py, symbol and module will be the same
        if symbol_name == module:
            module = "."

        if import_type == ImportType.WILDCARD:
            return f"from {module} import * as {symbol_name}"
        elif alias is not None and alias != self.name:
            return f"from {module} import {symbol_name} as {alias}"
        else:
            return f"from {module} import {symbol_name}"

    @reader
    def get_import_insert_index(self, import_string) -> int | None:
        """Determines the index position where a new import statement should be inserted in a Python file.

        The function determines the optimal position for inserting a new import statement, following Python's import ordering conventions.
        Future imports are placed at the top of the file, followed by all other imports.

        Args:
            import_string (str): The import statement to be inserted.

        Returns:
            int | None: The index where the import should be inserted. Returns 0 for future imports or if there are no existing imports after future imports.
            Returns None if there are no imports in the file.
        """
        if not self.imports:
            return None

        # Case: if the import is a future import, add to top of file
        if "__future__" in import_string:  # TODO: parse this into an import module and import name
            return 0

        # Case: file already had future imports, add import after the last one
        future_imp_idxs = [idx for idx, imp in enumerate(self.imports) if "__future__" in imp.source]
        if future_imp_idxs:
            return future_imp_idxs[-1] + 1

        # Case: default add import to top of file
        return 0

    ####################################################################################################################
    # MANIPULATIONS
    ####################################################################################################################

    @writer
    def add_import_from_import_string(self, import_string: str) -> None:
        """Adds an import statement to the file from a string representation.

        This method adds a new import statement to the file, handling placement based on existing imports.
        Future imports are placed at the top of the file, followed by regular imports.

        Args:
            import_string (str): The string representation of the import statement to add (e.g., 'from module import symbol').

        Returns:
            None: This function modifies the file in place.
        """
        if self.imports:
            import_insert_index = self.get_import_insert_index(import_string) or 0
            if import_insert_index < len(self.imports):
                self.imports[import_insert_index].insert_before(import_string, priority=1)
            else:
                # If import_insert_index is out of bounds, do insert after the last import
                self.imports[-1].insert_after(import_string, priority=1)
        else:
            self.insert_before(import_string, priority=1)

    @py_apidoc
    def remove_unused_imports(self) -> None:
        """Removes unused imports from the file.

        Handles different Python import styles:
        - Single imports (import x)
        - From imports (from y import z)
        - Multi-imports (from y import (a, b as c))
        - Wildcard imports (from x import *)
        - Type imports (from typing import List)
        - Future imports (from __future__ import annotations)

        Preserves:
        - Comments and whitespace where possible
        - Future imports even if unused
        - Type hints and annotations
        """
        # Track processed imports to avoid duplicates
        processed_imports = set()

        # Group imports by module for more efficient processing
        module_imports = {}

        # First pass - group imports by module
        for import_stmt in self.imports:
            if import_stmt in processed_imports:
                continue

            # Always preserve __future__ and star imports since we can't track their usage
            print(f"import_stmt: {import_stmt}", import_stmt.is_future_import, import_stmt.is_star_import)
            if import_stmt.is_future_import or import_stmt.is_star_import:
                continue

            module = import_stmt.module_name
            if module not in module_imports:
                module_imports[module] = []
                print(f"Adding {module} to module_imports")
            module_imports[module].append(import_stmt)

        print(f"module_imports: {module_imports}")
        # Second pass - process each module's imports
        for module, imports in module_imports.items():
            # Skip if any import from this module is used
            if any(imp.usages for imp in imports):
                # Remove individual unused imports if it's a from-style import
                if len(imports) > 1 and imports[0].is_from_import():
                    for imp in imports:
                        if not imp.usages and imp not in processed_imports:
                            processed_imports.add(imp)
                            imp.remove()
                continue

            # If no imports from module are used, remove them all
            for imp in imports:
                if imp not in processed_imports:
                    processed_imports.add(imp)
                    imp.remove()

        self.G.commit_transactions()

    @py_apidoc
    def remove_unused_exports(self) -> None:
        """Removes unused exports from the file.
        In Python this is equivalent to removing unused imports since Python doesn't have
        explicit export statements. Calls remove_unused_imports() internally.
        """
        self.remove_unused_imports()

    @cached_property
    @noapidoc
    @reader(cache=True)
    def valid_import_names(self) -> dict[str, PySymbol | PyImport | WildcardImport[PyImport]]:
        """Returns a dict mapping name => Symbol (or import) in this file that can be imported from
        another file.
        """
        if self.name == "__init__":
            ret = {}
            if self.directory:
                for file in self.directory:
                    if file.name == "__init__":
                        continue
                    ret[file.name] = file
            return ret
        return super().valid_import_names
