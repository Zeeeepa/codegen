"""
Dead Symbol Detection Module

This module provides functions for detecting dead symbols in a codebase.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

def get_dead_symbol_detection(codebase) -> Dict[str, Any]:
    """
    Detect dead symbols in the codebase.
    
    This function identifies symbols (functions, classes, variables) that are defined
    but never used in the codebase.
    
    Args:
        codebase: The codebase object to analyze
        
    Returns:
        Dict containing dead symbol analysis results
    """
    dead_symbol_analysis = {
        "dead_functions": [],
        "dead_classes": [],
        "dead_variables": [],
        "dead_imports": [],
        "total_dead_symbols": 0,
        "total_symbols": 0,
        "dead_symbol_percentage": 0.0
    }
    
    try:
        # Get all defined symbols
        all_functions = list(codebase.functions)
        all_classes = list(codebase.classes)
        all_variables = []
        all_imports = []
        
        # Extract variables and imports from files
        for file in codebase.files:
            if hasattr(file, "variables"):
                all_variables.extend(file.variables)
            
            if hasattr(file, "imports"):
                all_imports.extend(file.imports)
        
        # Get all symbol references
        function_refs = set()
        class_refs = set()
        variable_refs = set()
        import_refs = set()
        
        # Check function calls
        for func in all_functions:
            # Function calls
            for call in func.function_calls:
                if hasattr(call, "function_definition") and call.function_definition:
                    function_refs.add(call.function_definition.id)
            
            # Class instantiations and references
            for node in func.ast_node.walk():
                # Class instantiations
                if hasattr(node, "func") and hasattr(node.func, "id"):
                    class_name = node.func.id
                    for cls in all_classes:
                        if cls.name == class_name:
                            class_refs.add(cls.id)
                
                # Variable references
                if hasattr(node, "id") and isinstance(node.id, str):
                    var_name = node.id
                    for var in all_variables:
                        if hasattr(var, "name") and var.name == var_name:
                            variable_refs.add(var.id)
                
                # Import references
                if hasattr(node, "value") and hasattr(node.value, "id"):
                    import_name = node.value.id
                    for imp in all_imports:
                        if hasattr(imp, "name") and imp.name == import_name:
                            import_refs.add(imp.id)
        
        # Check for dead functions
        for func in all_functions:
            if func.id not in function_refs and not func.name.startswith("__"):
                # Check if it's a special method or entry point
                if not (func.name == "main" or func.name == "run" or func.name.startswith("test_")):
                    dead_symbol_analysis["dead_functions"].append({
                        "name": func.name,
                        "file": func.file.file_path if hasattr(func, "file") else "Unknown",
                        "line": func.line_number if hasattr(func, "line_number") else 0
                    })
        
        # Check for dead classes
        for cls in all_classes:
            is_used = cls.id in class_refs
            
            # Also check if it's a parent class
            if not is_used:
                for other_cls in all_classes:
                    if hasattr(other_cls, "bases") and cls.name in [base.name for base in other_cls.bases if hasattr(base, "name")]:
                        is_used = True
                        break
            
            if not is_used and not cls.name.startswith("__"):
                dead_symbol_analysis["dead_classes"].append({
                    "name": cls.name,
                    "file": cls.file.file_path if hasattr(cls, "file") else "Unknown",
                    "line": cls.line_number if hasattr(cls, "line_number") else 0
                })
        
        # Check for dead variables
        for var in all_variables:
            if hasattr(var, "id") and var.id not in variable_refs:
                # Skip special variables
                if not (hasattr(var, "name") and (var.name.startswith("__") or var.name in ["self", "cls"])):
                    dead_symbol_analysis["dead_variables"].append({
                        "name": var.name if hasattr(var, "name") else "Unknown",
                        "file": var.file.file_path if hasattr(var, "file") else "Unknown",
                        "line": var.line_number if hasattr(var, "line_number") else 0
                    })
        
        # Check for dead imports
        for imp in all_imports:
            if hasattr(imp, "id") and imp.id not in import_refs:
                dead_symbol_analysis["dead_imports"].append({
                    "name": imp.name if hasattr(imp, "name") else "Unknown",
                    "module": imp.module if hasattr(imp, "module") else "Unknown",
                    "file": imp.file.file_path if hasattr(imp, "file") else "Unknown",
                    "line": imp.line_number if hasattr(imp, "line_number") else 0
                })
        
        # Calculate statistics
        total_dead_symbols = (
            len(dead_symbol_analysis["dead_functions"]) +
            len(dead_symbol_analysis["dead_classes"]) +
            len(dead_symbol_analysis["dead_variables"]) +
            len(dead_symbol_analysis["dead_imports"])
        )
        
        total_symbols = len(all_functions) + len(all_classes) + len(all_variables) + len(all_imports)
        
        dead_symbol_analysis["total_dead_symbols"] = total_dead_symbols
        dead_symbol_analysis["total_symbols"] = total_symbols
        dead_symbol_analysis["dead_symbol_percentage"] = (total_dead_symbols / total_symbols * 100) if total_symbols > 0 else 0
        
        return dead_symbol_analysis
    except Exception as e:
        logger.error(f"Error in dead symbol detection: {e}")
        return {"error": str(e)}

