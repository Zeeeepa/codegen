"""Symbol resolution utilities for the SDK."""

from typing import Optional, Union, Any

from codegen.sdk.core.codebase import Codebase
from codegen.sdk.core.symbol import Symbol
from codegen.sdk.core.function import Function
from codegen.sdk.core.class_definition import Class
from codegen.sdk.core.variable import Variable

def resolve_symbol(
    codebase: Codebase,
    symbol_name: str,
    filepath: Optional[str] = None
) -> Optional[Union[Symbol, Function, Class, Variable, Any]]:
    """
    Resolve a symbol by name in the codebase.
    
    Args:
        codebase: The codebase to search in
        symbol_name: The name of the symbol to resolve
        filepath: Optional filepath to help resolve the symbol
        
    Returns:
        The resolved symbol or None if not found
    """
    # Try to find the symbol directly in the codebase
    try:
        # If filepath is provided, try to find the symbol in that file first
        if filepath:
            file = codebase.get_file(filepath)
            for symbol in file.symbols():
                if symbol.name == symbol_name:
                    return symbol
                
            # Check if the symbol is a member of a class in the file
            for cls in file.classes():
                for method in cls.methods:
                    if method.name == symbol_name:
                        return method
                for prop in cls.properties:
                    if prop.name == symbol_name:
                        return prop
        
        # Search for the symbol across the entire codebase
        # First try exact matches
        for file in codebase.files():
            for symbol in file.symbols():
                if symbol.name == symbol_name:
                    return symbol
                
            # Check class members
            for cls in file.classes():
                if cls.name == symbol_name:
                    return cls
                for method in cls.methods:
                    if method.name == symbol_name:
                        return method
                for prop in cls.properties:
                    if prop.name == symbol_name:
                        return prop
                    
        # If no exact match, try to handle qualified names (e.g., "module.Class.method")
        parts = symbol_name.split('.')
        if len(parts) > 1:
            # Try to find the parent symbol first
            parent_name = '.'.join(parts[:-1])
            parent = resolve_symbol(codebase, parent_name)
            if parent and isinstance(parent, Class):
                # Look for the child symbol in the parent class
                child_name = parts[-1]
                for method in parent.methods:
                    if method.name == child_name:
                        return method
                for prop in parent.properties:
                    if prop.name == child_name:
                        return prop
    
    except Exception as e:
        # If any error occurs during resolution, return None
        print(f"Error resolving symbol '{symbol_name}': {str(e)}")
        return None
    
    return None
