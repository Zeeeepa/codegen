#!/usr/bin/env python3
"""
Codebase Context Retriever Module

This module provides utilities for retrieving and organizing context from a codebase
using the Codegen SDK. It focuses on extracting relevant information about code structure,
dependencies, and relationships to provide a comprehensive view of the codebase.
"""

import logging
import os
from typing import Any, Dict, List, Optional, Set, Tuple, Union

try:
    from codegen.sdk.core.codebase import Codebase
    from codegen.sdk.core.class_definition import Class
    from codegen.sdk.core.file import SourceFile
    from codegen.sdk.core.function import Function
    from codegen.sdk.core.import_resolution import Import
    from codegen.sdk.core.symbol import Symbol
    from codegen.sdk.enums import EdgeType, SymbolType
except ImportError:
    raise ImportError("Codegen SDK not found. Please install it first.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class CodebaseContext:
    """
    Class for retrieving and organizing context from a codebase.
    
    This class provides methods to extract relevant information about code structure,
    dependencies, and relationships to provide a comprehensive view of the codebase.
    """
    
    def __init__(self, codebase: Codebase):
        """
        Initialize the CodebaseContext.
        
        Args:
            codebase: The Codebase object to extract context from
        """
        self.codebase = codebase
        self.files = list(codebase.files)
        self.functions = list(codebase.functions)
        self.classes = list(codebase.classes)
        self.imports = list(codebase.imports)
        
        # Cache for expensive operations
        self._function_call_graph = None
        self._import_graph = None
        self._symbol_usage_map = None
    
    def get_codebase_summary(self) -> Dict[str, Any]:
        """
        Generate a comprehensive summary of the codebase.
        
        Returns:
            A dictionary containing summary information about the codebase
        """
        return {
            "files": len(self.files),
            "functions": len(self.functions),
            "classes": len(self.classes),
            "imports": len(self.imports),
            "file_extensions": self._get_file_extensions(),
            "top_level_directories": self._get_top_level_directories(),
        }
    
    def _get_file_extensions(self) -> Dict[str, int]:
        """Get a count of file extensions in the codebase."""
        extensions = {}
        for file in self.files:
            _, ext = os.path.splitext(file.file_path)
            if ext:
                if ext in extensions:
                    extensions[ext] += 1
                else:
                    extensions[ext] = 1
        return extensions
    
    def _get_top_level_directories(self) -> Dict[str, int]:
        """Get a count of files in top-level directories."""
        directories = {}
        for file in self.files:
            parts = file.file_path.split('/')
            if len(parts) > 1:
                top_dir = parts[0]
                if top_dir in directories:
                    directories[top_dir] += 1
                else:
                    directories[top_dir] = 1
        return directories
    
    def get_unused_functions(self) -> List[Function]:
        """
        Get a list of unused functions in the codebase.
        
        Returns:
            A list of Function objects that are never called
        """
        return [func for func in self.functions if not func.usages]
    
    def get_unused_imports(self) -> List[Import]:
        """
        Get a list of unused imports in the codebase.
        
        Returns:
            A list of Import objects that are never used
        """
        unused_imports = []
        for file in self.files:
            for import_stmt in file.imports:
                if not import_stmt.usages:
                    unused_imports.append(import_stmt)
        return unused_imports
    
    def get_functions_with_unused_parameters(self) -> List[Tuple[Function, List[str]]]:
        """
        Get a list of functions with unused parameters.
        
        Returns:
            A list of tuples containing (Function, list of unused parameter names)
        """
        result = []
        for func in self.functions:
            unused_params = []
            for param in func.parameters:
                # Check if parameter is used in function body
                if param.name not in [dep.name for dep in func.dependencies]:
                    unused_params.append(param.name)
            if unused_params:
                result.append((func, unused_params))
        return result
    
    def get_parameter_mismatches(self) -> List[Tuple[Function, List[str]]]:
        """
        Get a list of functions with parameter mismatches in call sites.
        
        Returns:
            A list of tuples containing (Function, list of missing parameter names)
        """
        result = []
        for func in self.functions:
            for call in func.call_sites:
                expected_params = set(p.name for p in func.parameters)
                actual_params = set(arg.parameter_name for arg in call.args if arg.parameter_name)
                missing = expected_params - actual_params
                if missing and not func.has_kwargs:
                    result.append((func, list(missing)))
        return result
    
    def get_function_call_graph(self) -> Dict[str, List[str]]:
        """
        Get a graph of function calls in the codebase.
        
        Returns:
            A dictionary mapping function names to lists of called function names
        """
        if self._function_call_graph is not None:
            return self._function_call_graph
        
        graph = {}
        for func in self.functions:
            graph[func.name] = []
            for call in func.function_calls:
                if hasattr(call, 'name'):
                    graph[func.name].append(call.name)
        
        self._function_call_graph = graph
        return graph
    
    def get_import_graph(self) -> Dict[str, List[str]]:
        """
        Get a graph of file imports in the codebase.
        
        Returns:
            A dictionary mapping file paths to lists of imported file paths
        """
        if self._import_graph is not None:
            return self._import_graph
        
        graph = {}
        for file in self.files:
            graph[file.file_path] = []
            for import_stmt in file.imports:
                if hasattr(import_stmt, 'resolved_file') and import_stmt.resolved_file:
                    graph[file.file_path].append(import_stmt.resolved_file.file_path)
        
        self._import_graph = graph
        return graph
    
    def get_circular_imports(self) -> List[Tuple[str, str]]:
        """
        Get a list of circular imports in the codebase.
        
        Returns:
            A list of tuples containing pairs of file paths with circular imports
        """
        import_graph = self.get_import_graph()
        circular_imports = []
        
        # Check for direct circular imports
        for file_path, imports in import_graph.items():
            for imported_file in imports:
                if imported_file in import_graph and file_path in import_graph[imported_file]:
                    circular_imports.append((file_path, imported_file))
        
        return circular_imports
    
    def get_symbol_usage_map(self) -> Dict[str, List[str]]:
        """
        Get a map of symbol usages in the codebase.
        
        Returns:
            A dictionary mapping symbol names to lists of file paths where they are used
        """
        if self._symbol_usage_map is not None:
            return self._symbol_usage_map
        
        usage_map = {}
        
        # Add functions
        for func in self.functions:
            usage_map[func.name] = []
            for usage in func.usages:
                if hasattr(usage, 'file') and usage.file:
                    usage_map[func.name].append(usage.file.file_path)
        
        # Add classes
        for cls in self.classes:
            usage_map[cls.name] = []
            for usage in cls.usages:
                if hasattr(usage, 'file') and usage.file:
                    usage_map[cls.name].append(usage.file.file_path)
        
        self._symbol_usage_map = usage_map
        return usage_map
    
    def get_recursive_functions(self) -> List[Function]:
        """
        Get a list of recursive functions in the codebase.
        
        Returns:
            A list of Function objects that call themselves
        """
        return [
            func for func in self.functions
            if any(call.name == func.name for call in func.function_calls)
        ]
    
    def get_complex_functions(self, threshold: int = 50) -> List[Tuple[Function, int]]:
        """
        Get a list of complex functions based on line count.
        
        Args:
            threshold: Line count threshold for considering a function complex
            
        Returns:
            A list of tuples containing (Function, line count)
        """
        complex_funcs = []
        for func in self.functions:
            if hasattr(func, 'source') and func.source:
                line_count = func.source.count('\n') + 1
                if line_count > threshold:
                    complex_funcs.append((func, line_count))
        return complex_funcs
    
    def get_file_context(self, file_path: str) -> Dict[str, Any]:
        """
        Get comprehensive context for a specific file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            A dictionary containing context information about the file
        """
        # Find the file
        file = next((f for f in self.files if f.file_path == file_path), None)
        if not file:
            return {"error": f"File not found: {file_path}"}
        
        # Get functions in the file
        functions = [f for f in self.functions if hasattr(f, 'file') and f.file.file_path == file_path]
        
        # Get classes in the file
        classes = [c for c in self.classes if hasattr(c, 'file') and c.file.file_path == file_path]
        
        # Get imports in the file
        imports = [i.source for i in file.imports] if hasattr(file, 'imports') else []
        
        # Get files that import this file
        imported_by = []
        for f in self.files:
            for imp in f.imports:
                if hasattr(imp, 'resolved_file') and imp.resolved_file and imp.resolved_file.file_path == file_path:
                    imported_by.append(f.file_path)
        
        return {
            "file_path": file_path,
            "functions": [f.name for f in functions],
            "classes": [c.name for c in classes],
            "imports": imports,
            "imported_by": imported_by,
        }
    
    def get_function_context(self, function_name: str) -> Dict[str, Any]:
        """
        Get comprehensive context for a specific function.
        
        Args:
            function_name: Name of the function
            
        Returns:
            A dictionary containing context information about the function
        """
        # Find the function
        func = next((f for f in self.functions if f.name == function_name), None)
        if not func:
            return {"error": f"Function not found: {function_name}"}
        
        # Get parameters
        parameters = [p.name for p in func.parameters] if hasattr(func, 'parameters') else []
        
        # Get function calls
        function_calls = [c.name for c in func.function_calls] if hasattr(func, 'function_calls') else []
        
        # Get call sites
        call_sites = []
        for f in self.functions:
            for call in f.function_calls:
                if hasattr(call, 'name') and call.name == function_name:
                    call_sites.append(f.name)
        
        return {
            "name": function_name,
            "file_path": func.file.file_path if hasattr(func, 'file') else None,
            "parameters": parameters,
            "function_calls": function_calls,
            "call_sites": call_sites,
            "is_recursive": function_name in function_calls,
        }
    
    def get_class_context(self, class_name: str) -> Dict[str, Any]:
        """
        Get comprehensive context for a specific class.
        
        Args:
            class_name: Name of the class
            
        Returns:
            A dictionary containing context information about the class
        """
        # Find the class
        cls = next((c for c in self.classes if c.name == class_name), None)
        if not cls:
            return {"error": f"Class not found: {class_name}"}
        
        # Get methods
        methods = [m.name for m in cls.methods] if hasattr(cls, 'methods') else []
        
        # Get attributes
        attributes = [a.name for a in cls.attributes] if hasattr(cls, 'attributes') else []
        
        # Get parent classes
        parent_classes = [p.name for p in cls.parent_classes] if hasattr(cls, 'parent_classes') else []
        
        # Get child classes
        child_classes = []
        for c in self.classes:
            if hasattr(c, 'parent_classes'):
                for parent in c.parent_classes:
                    if parent.name == class_name:
                        child_classes.append(c.name)
        
        return {
            "name": class_name,
            "file_path": cls.file.file_path if hasattr(cls, 'file') else None,
            "methods": methods,
            "attributes": attributes,
            "parent_classes": parent_classes,
            "child_classes": child_classes,
        }


def get_codebase_context(codebase: Codebase) -> CodebaseContext:
    """
    Get a CodebaseContext object for the given codebase.
    
    Args:
        codebase: The Codebase object to extract context from
        
    Returns:
        A CodebaseContext object
    """
    return CodebaseContext(codebase)


def analyze_codebase(repo_path: str) -> Dict[str, Any]:
    """
    Analyze a codebase and return a summary of its structure and issues.
    
    Args:
        repo_path: Path to the repository
        
    Returns:
        A dictionary containing analysis results
    """
    from codegen.configs.models.codebase import CodebaseConfig
    from codegen.configs.models.secrets import SecretsConfig
    from codegen.shared.enums.programming_language import ProgrammingLanguage
    
    # Initialize the codebase
    config = CodebaseConfig(
        debug=False,
        allow_external=True,
        py_resolve_syspath=True,
    )
    
    secrets = SecretsConfig()
    
    codebase = Codebase(
        repo_path=repo_path,
        config=config,
        secrets=secrets
    )
    
    # Get context
    context = get_codebase_context(codebase)
    
    # Get summary
    summary = context.get_codebase_summary()
    
    # Get issues
    issues = {
        "unused_functions": len(context.get_unused_functions()),
        "unused_imports": len(context.get_unused_imports()),
        "functions_with_unused_parameters": len(context.get_functions_with_unused_parameters()),
        "parameter_mismatches": len(context.get_parameter_mismatches()),
        "circular_imports": len(context.get_circular_imports()),
        "recursive_functions": len(context.get_recursive_functions()),
        "complex_functions": len(context.get_complex_functions()),
    }
    
    return {
        "summary": summary,
        "issues": issues,
    }


if __name__ == "__main__":
    import argparse
    import json
    import sys
    
    parser = argparse.ArgumentParser(description="Codebase Context Retriever")
    parser.add_argument("--repo-path", required=True, help="Path to the repository")
    parser.add_argument("--output-file", help="Path to the output file")
    
    args = parser.parse_args()
    
    try:
        results = analyze_codebase(args.repo_path)
        
        if args.output_file:
            with open(args.output_file, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"Results saved to {args.output_file}")
        else:
            print(json.dumps(results, indent=2))
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

