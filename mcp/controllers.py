"""
MCP Controllers
This module defines the controller classes that implement the business logic
for the MCP operations. Each controller handles a specific set of operations
related to a particular aspect of the codebase (symbols, functions, classes, etc.).
"""
from typing import Dict, List, Optional, Any, Union, Callable
from .models import Codebase, File, Symbol, Function, Class, Import, Parameter, Location
class SymbolController:
    """Controller for symbol-related operations."""
    def __init__(self, codebase: Codebase):
        """Initialize with a codebase reference."""
        self.codebase = codebase
    def get_symbol(self, name: str, optional: bool = False) -> Optional[Symbol]:
        """Get a symbol by name."""
        # Implementation would use the actual codebase API
        if name in self.codebase._symbols_cache:
            return self.codebase._symbols_cache[name]
        
        # If not found and not optional, raise error
        if not optional:
            raise ValueError(f"Symbol '{name}' not found in codebase")
        
        return None
    def get_symbols(self, name: str) -> List[Symbol]:
        """Get all symbols matching a name pattern."""
        # Implementation would use the actual codebase API
        return [s for s_name, s in self.codebase._symbols_cache.items() if name in s_name]
    def has_symbol(self, symbol_name: str) -> bool:
        """Check if a symbol exists in the codebase."""
        return symbol_name in self.codebase._symbols_cache
    def symbols(self) -> List[Symbol]:
        """Get all symbols in the codebase."""
        return list(self.codebase._symbols_cache.values())
    def functions(self) -> List[Function]:
        """Get all functions in the codebase."""
        return list(self.codebase._functions_cache.values())
    def classes(self) -> List[Class]:
        """Get all classes in the codebase."""
        return list(self.codebase._classes_cache.values())
    def imports(self) -> List[Import]:
        """Get all imports in the codebase."""
        return list(self.codebase._imports_cache.values())
    def exports(self) -> List[str]:
        """Get all exports in the codebase."""
        # Implementation would use the actual codebase API
        exports = []
        for file in self.codebase.files:
            exports.extend(file.exports)
        return exports
    def interfaces(self) -> List[Dict[str, Any]]:
        """Get all interfaces in the codebase."""
        # Implementation would use the actual codebase API
        interfaces = []
        for file in self.codebase.files:
            interfaces.extend(file.interfaces)
        return interfaces
    def types(self) -> List[Dict[str, Any]]:
        """Get all types in the codebase."""
        # Implementation would use the actual codebase API
        types = []
        for file in self.codebase.files:
            types.extend(file.types)
        return types
    def global_vars(self) -> List[Dict[str, Any]]:
        """Get all global variables in the codebase."""
        # Implementation would use the actual codebase API
        global_vars = []
        for file in self.codebase.files:
            global_vars.extend(file.global_vars)
        return global_vars
class FileSymbolController:
    """Controller for file-level symbol operations."""
    def __init__(self, file: File):
        """Initialize with a file reference."""
        self.file = file
    def get_symbol(self, name: str) -> Optional[Symbol]:
        """Get a symbol from the file by name."""
        for symbol in self.file.symbols:
            if symbol.name == name:
                return symbol
        return None
    @property
    def symbols(self) -> List[Symbol]:
        """Get all symbols in the file."""
        return self.file.symbols
    @property
    def functions(self) -> List[Function]:
        """Get all functions in the file."""
        return self.file.functions
    @property
    def classes(self) -> List[Class]:
        """Get all classes in the file."""
        return self.file.classes
    @property
    def imports(self) -> List[Import]:
        """Get all imports in the file."""
        return self.file.imports
    @property
    def exports(self) -> List[str]:
        """Get all exports in the file."""
        return self.file.exports
    @property
    def interfaces(self) -> List[Dict[str, Any]]:
        """Get all interfaces in the file."""
        return self.file.interfaces
    @property
    def types(self) -> List[Dict[str, Any]]:
        """Get all types in the file."""
        return self.file.types
    @property
    def global_vars(self) -> List[Dict[str, Any]]:
        """Get all global variables in the file."""
        return self.file.global_vars
class SymbolOperationsController:
    """Controller for operations on individual symbols."""
    def __init__(self, codebase: Codebase):
        """Initialize with a codebase reference."""
        self.codebase = codebase
    def get_name(self, symbol: Symbol) -> str:
        """Get the name of a symbol."""
        return symbol.name
    def get_usages(self, symbol: Symbol, usage_type: Optional[str] = None) -> List[Location]:
        """Get all usages of a symbol."""
        # Implementation would use the actual codebase API
        # For now, return an empty list
        return []
    def move_to_file(self, symbol: Symbol, target_file: File, 
                    include_dependencies: bool = True, 
                    strategy: str = 'update_all_imports') -> Dict[str, Any]:
        """Move a symbol to another file."""
        # Implementation would use the actual codebase API
        return {
            "success": True,
            "symbol": symbol.name,
            "source_file": symbol.location.file_path if symbol.location else None,
            "target_file": target_file.path,
            "updated_imports": []
        }
    def rename(self, symbol: Symbol, new_name: str, priority: int = 0) -> Dict[str, Any]:
        """Rename a symbol."""
        # Implementation would use the actual codebase API
        old_name = symbol.name
        symbol.name = new_name
        return {
            "success": True,
            "old_name": old_name,
            "new_name": new_name,
            "updated_references": []
        }
    def remove(self, symbol: Symbol) -> Dict[str, Any]:
        """Remove a symbol from the codebase."""
        # Implementation would use the actual codebase API
        return {
            "success": True,
            "removed_symbol": symbol.name,
            "file": symbol.location.file_path if symbol.location else None
        }
class FunctionController:
    """Controller for function-related operations."""
    def __init__(self, codebase: Codebase):
        """Initialize with a codebase reference."""
        self.codebase = codebase
        self.symbol_controller = SymbolController(codebase)
    def get_return_type(self, function: Function) -> Optional[str]:
        """Get the return type of a function."""
        return function.return_type
    def get_parameters(self, function: Function) -> List[Parameter]:
        """Get the parameters of a function."""
        return function.parameters
    def is_async(self, function: Function) -> bool:
        """Check if a function is asynchronous."""
        return function.is_async
    def get_decorators(self, function: Function) -> List[str]:
        """Get the decorators of a function."""
        return function.decorators
    def get_function_calls(self, function: Function) -> List[Dict[str, Any]]:
        """Get all function calls made within the function."""
        # Implementation would use the actual codebase API
        return []
    def set_return_type(self, function: Function, return_type: str) -> Dict[str, Any]:
        """Set the return type of a function."""
        old_type = function.return_type
        function.return_type = return_type
        return {
            "success": True,
            "function": function.name,
            "old_type": old_type,
            "new_type": return_type
        }
    def add_parameter(self, function: Function, name: str, param_type: Optional[str] = None) -> Dict[str, Any]:
        """Add a parameter to a function."""
        param = Parameter(name=name, type_annotation=param_type)
        function.parameters.append(param)
        return {
            "success": True,
            "function": function.name,
            "parameter": param.to_dict()
        }
    def remove_parameter(self, function: Function, name: str) -> Dict[str, Any]:
        """Remove a parameter from a function."""
        for i, param in enumerate(function.parameters):
            if param.name == name:
                removed = function.parameters.pop(i)
                return {
                    "success": True,
                    "function": function.name,
                    "removed_parameter": removed.to_dict()
                }
        
        return {
            "success": False,
            "error": f"Parameter '{name}' not found in function '{function.name}'"
        }
    def add_decorator(self, function: Function, decorator: str) -> Dict[str, Any]:
        """Add a decorator to a function."""
        function.decorators.append(decorator)
        return {
            "success": True,
            "function": function.name,
            "decorator": decorator
        }
    def set_docstring(self, function: Function, docstring: str) -> Dict[str, Any]:
        """Set the docstring of a function."""
        function.docstring = docstring
        return {
            "success": True,
            "function": function.name
        }
    def generate_docstring(self, function: Function) -> Dict[str, Any]:
        """Generate a docstring for a function."""
        # Implementation would use the actual codebase API
        # For now, generate a simple docstring
        params_doc = "\n".join([f"    {p.name}: {p.type_annotation or 'Any'}" for p in function.parameters])
        return_doc = f"    {function.return_type or 'None'}"
        
        docstring = f"""Function {function.name}.
        
Parameters:
{params_doc}
Returns:
{return_doc}
"""
        function.docstring = docstring
        return {
            "success": True,
            "function": function.name,
            "docstring": docstring
        }
    def rename_local_variable(self, function: Function, old_var_name: str, 
                             new_var_name: str, fuzzy_match: bool = False) -> Dict[str, Any]:
        """Rename a local variable in a function."""
        # Implementation would use the actual codebase API
        return {
            "success": True,
            "function": function.name,
            "old_name": old_var_name,
            "new_name": new_var_name,
            "occurrences_replaced": 0
        }
    def call_sites(self, function: Function) -> List[Location]:
        """Get all call sites of a function."""
        # Implementation would use the actual codebase API
        return []
    def dependencies(self, function: Function) -> List[str]:
        """Get all dependencies of a function."""
        # Implementation would use the actual codebase API
        return []
class ClassController:
    """Controller for class-related operations."""
    def __init__(self, codebase: Codebase):
        """Initialize with a codebase reference."""
        self.codebase = codebase
        self.symbol_controller = SymbolController(codebase)
    def get_methods(self, cls: Class) -> List[Function]:
        """Get the methods of a class."""
        return cls.methods
    def get_properties(self, cls: Class) -> List[Dict[str, Any]]:
        """Get the properties of a class."""
        # Implementation would use the actual codebase API
        # For now, return an empty list
        return []
    def get_attributes(self, cls: Class) -> List[Dict[str, Any]]:
        """Get the attributes of a class."""
        return cls.attributes
    def is_abstract(self, cls: Class) -> bool:
        """Check if a class is abstract."""
        return cls.is_abstract
    def get_parent_class_names(self, cls: Class) -> List[str]:
        """Get the parent class names of a class."""
        return cls.parent_class_names
    def is_subclass_of(self, cls: Class, parent: str) -> bool:
        """Check if a class inherits from a specific parent."""
        return parent in cls.parent_class_names
    def add_method(self, cls: Class, method: Function) -> Dict[str, Any]:
        """Add a method to a class."""
        cls.methods.append(method)
        return {
            "success": True,
            "class": cls.name,
            "method": method.name
        }
    def remove_method(self, cls: Class, method: Union[Function, str]) -> Dict[str, Any]:
        """Remove a method from a class."""
        method_name = method.name if isinstance(method, Function) else method
        
        for i, m in enumerate(cls.methods):
            if m.name == method_name:
                removed = cls.methods.pop(i)
                return {
                    "success": True,
                    "class": cls.name,
                    "removed_method": removed.name
                }
        
        return {
            "success": False,
            "error": f"Method '{method_name}' not found in class '{cls.name}'"
        }
    def add_attribute(self, cls: Class, name: str, attr_type: Optional[str] = None, 
                     value: Optional[str] = None) -> Dict[str, Any]:
        """Add an attribute to a class."""
        attribute = {
            "name": name,
            "type": attr_type,
            "value": value
        }
        cls.attributes.append(attribute)
        return {
            "success": True,
            "class": cls.name,
            "attribute": attribute
        }
    def remove_attribute(self, cls: Class, name: str) -> Dict[str, Any]:
        """Remove an attribute from a class."""
        for i, attr in enumerate(cls.attributes):
            if attr["name"] == name:
                removed = cls.attributes.pop(i)
                return {
                    "success": True,
                    "class": cls.name,
                    "removed_attribute": removed
                }
        
        return {
            "success": False,
            "error": f"Attribute '{name}' not found in class '{cls.name}'"
        }
    def convert_to_protocol(self, cls: Class) -> Dict[str, Any]:
        """Convert a class to a protocol."""
        # Implementation would use the actual codebase API
        cls.is_abstract = True
        return {
            "success": True,
            "class": cls.name
        }
    def get_decorators(self, cls: Class) -> List[str]:
        """Get the decorators of a class."""
        return cls.decorators
class ImportController:
    """Controller for import-related operations."""
    def __init__(self, codebase: Codebase):
        """Initialize with a codebase reference."""
        self.codebase = codebase
        self.symbol_controller = SymbolController(codebase)
    def get_source(self, import_obj: Import) -> str:
        """Get the source of an import."""
        return import_obj.source
    def update_source(self, import_obj: Import, new_source: str) -> Dict[str, Any]:
        """Update the source of an import."""
        old_source = import_obj.source
        import_obj.source = new_source
        return {
            "success": True,
            "import": import_obj.name,
            "old_source": old_source,
            "new_source": new_source
        }
    def remove(self, import_obj: Import) -> Dict[str, Any]:
        """Remove an import."""
        # Implementation would use the actual codebase API
        return {
            "success": True,
            "removed_import": import_obj.name,
            "source": import_obj.source
        }
    def rename(self, import_obj: Import, new_name: str, priority: int = 0) -> Dict[str, Any]:
        """Rename an import."""
        old_name = import_obj.name
        import_obj.name = new_name
        return {
            "success": True,
            "old_name": old_name,
            "new_name": new_name
        }