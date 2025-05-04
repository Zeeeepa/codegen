from codegen.sdk.core.class_definition import Class
from codegen.sdk.core.codebase import Codebase
from codegen.sdk.core.external_module import ExternalModule
from codegen.sdk.core.file import SourceFile
from codegen.sdk.core.function import Function
from codegen.sdk.core.import_resolution import Import
from codegen.sdk.core.symbol import Symbol
from codegen.sdk.enums import EdgeType, SymbolType


def get_codebase_summary(codebase: Codebase) -> str:
    node_summary = f"""Contains {len(codebase.ctx.get_nodes())} nodes
- {len(list(codebase.files))} files
- {len(list(codebase.imports))} imports
- {len(list(codebase.external_modules))} external_modules
- {len(list(codebase.symbols))} symbols
\t- {len(list(codebase.classes))} classes
\t- {len(list(codebase.functions))} functions
\t- {len(list(codebase.global_vars))} global_vars
\t- {len(list(codebase.interfaces))} interfaces
"""
    edge_summary = f"""Contains {len(codebase.ctx.edges)} edges
- {len([x for x in codebase.ctx.edges if x[2].type == EdgeType.SYMBOL_USAGE])} symbol -> used symbol
- {len([x for x in codebase.ctx.edges if x[2].type == EdgeType.IMPORT_SYMBOL_RESOLUTION])} \
import -> used symbol
"""

    return f"{node_summary}\n{edge_summary}"


def get_file_summary(file: SourceFile) -> str:
    return f"""==== [ `{file.name}` (SourceFile) Dependency Summary ] ====
- {len(file.imports)} imports
- {len(file.symbols)} symbol references
\t- {len(file.classes)} classes
\t- {len(file.functions)} functions
\t- {len(file.global_vars)} global variables
\t- {len(file.interfaces)} interfaces

==== [ `{file.name}` Usage Summary ] ====
- {len(file.imports)} importers
"""


def get_class_summary(cls: Class) -> str:
    return f"""==== [ `{cls.name}` (Class) Dependency Summary ] ====
- parent classes: {cls.parent_class_names}
- {len(cls.methods)} methods
- {len(cls.attributes)} attributes
- {len(cls.decorators)} decorators
- {len(cls.dependencies)} dependencies

{get_symbol_summary(cls)}
    """


def get_function_summary(func: Function) -> str:
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
    usages = symbol.symbol_usages
    imported_symbols = [x.imported_symbol for x in usages if isinstance(x, Import)]

    # Create variables for the long expressions to avoid line length issues
    func_usages = len([x for x in usages if isinstance(x, Symbol) and x.symbol_type == SymbolType.Function])
    class_usages = len([x for x in usages if isinstance(x, Symbol) and x.symbol_type == SymbolType.Class])
    var_usages = len([x for x in usages if isinstance(x, Symbol) and x.symbol_type == SymbolType.GlobalVar])
    interface_usages = len([x for x in usages if isinstance(x, Symbol) and x.symbol_type == SymbolType.Interface])
    
    imported_func = len([x for x in imported_symbols if isinstance(x, Symbol) and 
                         x.symbol_type == SymbolType.Function])
    imported_class = len([x for x in imported_symbols if isinstance(x, Symbol) and 
                          x.symbol_type == SymbolType.Class])
    imported_var = len([x for x in imported_symbols if isinstance(x, Symbol) and 
                        x.symbol_type == SymbolType.GlobalVar])
    imported_interface = len([x for x in imported_symbols if isinstance(x, Symbol) and 
                              x.symbol_type == SymbolType.Interface])
    imported_modules = len([x for x in imported_symbols if isinstance(x, ExternalModule)])
    imported_files = len([x for x in imported_symbols if isinstance(x, SourceFile)])

    return f"""==== [ `{symbol.name}` ({type(symbol).__name__}) Usage Summary ] ====
- {len(usages)} usages
\t- {func_usages} functions
\t- {class_usages} classes
\t- {var_usages} global variables
\t- {interface_usages} interfaces
\t- {len(imported_symbols)} imports
\t\t- {imported_func} functions
\t\t- {imported_class} classes
\t\t- {imported_var} global variables
\t\t- {imported_interface} interfaces
\t\t- {imported_modules} external modules
\t\t- {imported_files} files
    """
