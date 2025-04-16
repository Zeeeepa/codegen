"""
MCP Analysis Tools
This module defines controllers for analysis tools in the MCP server.
These tools provide functionality for code analysis and codebase analysis.
"""
from typing import Dict, List, Optional, Any, Union, Set
import re
import ast
import os
from pathlib import Path
from .models import Codebase, File, Symbol, Function, Class, Import, CallGraph

class CodeAnalysisController:
    """Controller for code analysis operations."""
    
    def __init__(self, codebase: Codebase):
        """Initialize with a codebase reference."""
        self.codebase = codebase
    
    def find_calls(self, func_name: str, arg_patterns: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Find function calls matching specific patterns.
        
        Args:
            func_name: Name of the function to find calls for
            arg_patterns: Optional list of patterns to match against function arguments
            
        Returns:
            List of dictionaries containing call information
        """
        results = []
        
        # Get the function if it exists in the codebase
        target_func = None
        for func in self.codebase._functions_cache.values():
            if func.name == func_name:
                target_func = func
                break
        
        if not target_func:
            return results
        
        # Iterate through all files to find calls
        for file in self.codebase.files:
            try:
                # Read the file content
                file_path = os.path.join(self.codebase.path, file.path)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse the file with ast
                tree = ast.parse(content)
                
                # Create a visitor to find function calls
                class CallVisitor(ast.NodeVisitor):
                    def __init__(self, target_name, arg_patterns):
                        self.target_name = target_name
                        self.arg_patterns = arg_patterns
                        self.calls = []
                    
                    def visit_Call(self, node):
                        # Check if this is a call to our target function
                        if isinstance(node.func, ast.Name) and node.func.id == self.target_name:
                            # Check if we need to match argument patterns
                            if self.arg_patterns:
                                args_match = True
                                for i, pattern in enumerate(self.arg_patterns):
                                    if i < len(node.args):
                                        # Convert the argument to a string representation
                                        arg_str = ast.unparse(node.args[i])
                                        if not re.search(pattern, arg_str):
                                            args_match = False
                                            break
                                    else:
                                        args_match = False
                                        break
                                
                                if not args_match:
                                    return
                            
                            # Get the line number and column offset
                            line_num = node.lineno
                            col_offset = node.col_offset
                            
                            # Get the line of code
                            lines = content.split('\n')
                            line = lines[line_num - 1] if line_num <= len(lines) else ""
                            
                            # Add the call to our results
                            self.calls.append({
                                'file': file.path,
                                'line': line_num,
                                'column': col_offset,
                                'code': line.strip(),
                                'args': [ast.unparse(arg) for arg in node.args]
                            })
                        
                        # Continue visiting child nodes
                        self.generic_visit(node)
                
                # Run the visitor
                visitor = CallVisitor(func_name, arg_patterns)
                visitor.visit(tree)
                
                # Add the calls to our results
                results.extend(visitor.calls)
                
            except Exception as e:
                # Skip files that can't be parsed
                continue
        
        return results
    
    def commit(self, message: str) -> Dict[str, Any]:
        """Commit changes made to the codebase.
        
        Args:
            message: Commit message
            
        Returns:
            Dictionary with commit information
        """
        import subprocess
        
        try:
            # Change to the codebase directory
            original_dir = os.getcwd()
            os.chdir(self.codebase.path)
            
            # Stage all changes
            subprocess.run(['git', 'add', '.'], check=True)
            
            # Commit the changes
            result = subprocess.run(
                ['git', 'commit', '-m', message],
                check=True,
                capture_output=True,
                text=True
            )
            
            # Get the commit hash
            commit_hash = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                check=True,
                capture_output=True,
                text=True
            ).stdout.strip()
            
            # Change back to the original directory
            os.chdir(original_dir)
            
            return {
                "success": True,
                "message": message,
                "commit_hash": commit_hash,
                "details": result.stdout
            }
        except subprocess.CalledProcessError as e:
            # Change back to the original directory
            if 'original_dir' in locals():
                os.chdir(original_dir)
            
            return {
                "success": False,
                "message": message,
                "error": str(e),
                "stderr": e.stderr if hasattr(e, 'stderr') else None
            }
        except Exception as e:
            # Change back to the original directory
            if 'original_dir' in locals():
                os.chdir(original_dir)
            
            return {
                "success": False,
                "message": message,
                "error": str(e)
            }
    
    def visualize(self, graph: CallGraph) -> Dict[str, Any]:
        """Visualize a graph structure.
        
        Args:
            graph: CallGraph object to visualize
            
        Returns:
            Dictionary with visualization information
        """
        try:
            import networkx as nx
            import matplotlib.pyplot as plt
            import tempfile
            
            # Create a NetworkX graph
            G = nx.DiGraph()
            
            # Add nodes
            for node in graph.nodes:
                G.add_node(node.name)
            
            # Add edges
            for edge in graph.edges:
                G.add_edge(edge["source"], edge["target"], weight=edge.get("weight", 1))
            
            # Create a temporary file for the visualization
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                temp_path = tmp.name
            
            # Create the visualization
            plt.figure(figsize=(12, 8))
            pos = nx.spring_layout(G)
            nx.draw(G, pos, with_labels=True, node_color='lightblue', 
                    node_size=1500, edge_color='gray', arrows=True)
            
            # Add edge weights
            edge_labels = {(u, v): d['weight'] for u, v, d in G.edges(data=True)}
            nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
            
            # Save the visualization
            plt.savefig(temp_path)
            plt.close()
            
            return {
                "success": True,
                "graph": graph.to_dict(),
                "visualization_type": "call_graph",
                "visualization_path": temp_path
            }
        except ImportError:
            # If visualization libraries are not available
            return {
                "success": False,
                "graph": graph.to_dict(),
                "visualization_type": "call_graph",
                "error": "Visualization libraries (networkx, matplotlib) not available"
            }
        except Exception as e:
            return {
                "success": False,
                "graph": graph.to_dict(),
                "visualization_type": "call_graph",
                "error": str(e)
            }
    
    def create_call_graph(self, start_func: Function, end_func: Optional[Function] = None, max_depth: int = 5) -> CallGraph:
        """Build a directed graph of function calls.
        
        Args:
            start_func: Starting function for the call graph
            end_func: Optional ending function to limit the graph
            max_depth: Maximum depth of the call graph
            
        Returns:
            CallGraph object representing the call relationships
        """
        # Create a call graph
        graph = CallGraph()
        
        # Add the start function as a node
        graph.nodes.append(start_func)
        
        # If end function is provided, add it as a node
        if end_func:
            graph.nodes.append(end_func)
        
        # Track visited functions to avoid cycles
        visited = set([start_func.name])
        
        # Helper function to recursively build the call graph
        def build_graph(func: Function, depth: int):
            if depth >= max_depth:
                return
            
            # Find all calls made by this function
            for file in self.codebase.files:
                try:
                    # Read the file content
                    file_path = os.path.join(self.codebase.path, file.path)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Find the function definition in the file
                    for file_func in file.functions:
                        if file_func.name == func.name and file_func.location:
                            # Extract the function code
                            lines = content.split('\n')
                            func_lines = lines[file_func.location.start_line - 1:file_func.location.end_line]
                            func_code = '\n'.join(func_lines)
                            
                            # Parse the function code to find calls
                            try:
                                tree = ast.parse(func_code)
                                
                                class CallVisitor(ast.NodeVisitor):
                                    def __init__(self):
                                        self.calls = []
                                    
                                    def visit_Call(self, node):
                                        if isinstance(node.func, ast.Name):
                                            self.calls.append(node.func.id)
                                        self.generic_visit(node)
                                
                                visitor = CallVisitor()
                                visitor.visit(tree)
                                
                                # Process each call
                                for call_name in visitor.calls:
                                    # Find the called function in the codebase
                                    called_func = None
                                    for f in self.codebase._functions_cache.values():
                                        if f.name == call_name:
                                            called_func = f
                                            break
                                    
                                    if called_func:
                                        # Add the called function as a node if not already present
                                        if called_func.name not in [n.name for n in graph.nodes]:
                                            graph.nodes.append(called_func)
                                        
                                        # Add an edge from the current function to the called function
                                        edge = {
                                            "source": func.name,
                                            "target": called_func.name,
                                            "weight": 1
                                        }
                                        
                                        # Check if the edge already exists
                                        if edge not in graph.edges:
                                            graph.edges.append(edge)
                                        
                                        # Recursively build the graph for the called function
                                        if called_func.name not in visited:
                                            visited.add(called_func.name)
                                            build_graph(called_func, depth + 1)
                                            
                                            # If we're looking for a path to end_func and found it, stop
                                            if end_func and called_func.name == end_func.name:
                                                return
                            except Exception:
                                # Skip functions that can't be parsed
                                continue
                except Exception:
                    # Skip files that can't be read
                    continue
        
        # Start building the graph from the start function
        build_graph(start_func, 0)
        
        return graph
    
    def find_dead_code(self) -> List[Function]:
        """Find unused functions in the codebase.
        
        Returns:
            List of unused Function objects
        """
        # Get all functions in the codebase
        all_functions = list(self.codebase._functions_cache.values())
        
        # Create a set of all function names
        all_function_names = {func.name for func in all_functions}
        
        # Create a set to track called functions
        called_functions = set()
        
        # Iterate through all files to find function calls
        for file in self.codebase.files:
            try:
                # Read the file content
                file_path = os.path.join(self.codebase.path, file.path)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse the file with ast
                tree = ast.parse(content)
                
                # Create a visitor to find function calls
                class CallVisitor(ast.NodeVisitor):
                    def visit_Call(self, node):
                        if isinstance(node.func, ast.Name):
                            called_functions.add(node.func.id)
                        self.generic_visit(node)
                
                # Run the visitor
                visitor = CallVisitor()
                visitor.visit(tree)
                
            except Exception:
                # Skip files that can't be parsed
                continue
        
        # Find functions that are never called
        dead_functions = []
        for func in all_functions:
            # Skip "main" functions and functions with special names (likely entry points)
            if func.name == "main" or func.name.startswith("__") and func.name.endswith("__"):
                continue
                
            if func.name not in called_functions:
                dead_functions.append(func)
        
        return dead_functions
    
    def get_max_call_chain(self, function: Function) -> List[Function]:
        """Find the longest call chain from a function.
        
        Args:
            function: Starting function for the call chain
            
        Returns:
            List of Function objects representing the longest call chain
        """
        # Create a call graph with a high max_depth
        graph = self.create_call_graph(function, max_depth=20)
        
        # Convert the graph to a NetworkX graph for path analysis
        try:
            import networkx as nx
            
            # Create a NetworkX graph
            G = nx.DiGraph()
            
            # Add nodes
            for node in graph.nodes:
                G.add_node(node.name)
            
            # Add edges
            for edge in graph.edges:
                G.add_edge(edge["source"], edge["target"])
            
            # Find all simple paths from the function
            all_paths = []
            for node in G.nodes():
                if node != function.name:
                    try:
                        paths = list(nx.all_simple_paths(G, function.name, node))
                        all_paths.extend(paths)
                    except nx.NetworkXNoPath:
                        continue
            
            # Find the longest path
            longest_path = max(all_paths, key=len, default=[function.name])
            
            # Convert the path of names back to Function objects
            result = []
            for name in longest_path:
                for func in self.codebase._functions_cache.values():
                    if func.name == name:
                        result.append(func)
                        break
            
            return result
        except ImportError:
            # If NetworkX is not available, use a simpler approach
            # Just return the function itself
            return [function]
        except Exception:
            # In case of any error, return just the function
            return [function]


class CodebaseAnalysisController:
    """Controller for codebase analysis operations."""
    
    def __init__(self, codebase: Codebase):
        """Initialize with a codebase reference."""
        self.codebase = codebase
    
    def get_codebase_summary(self) -> Dict[str, Any]:
        """Get a summary of the codebase.
        
        Returns:
            Dictionary with codebase statistics and information
        """
        # Count lines of code
        total_lines = 0
        for file in self.codebase.files:
            total_lines += file.line_count
        
        # Count by language/file extension
        extensions = {}
        for file in self.codebase.files:
            ext = os.path.splitext(file.path)[1]
            if ext:
                extensions[ext] = extensions.get(ext, 0) + 1
            else:
                extensions['no_extension'] = extensions.get('no_extension', 0) + 1
        
        # Get directory structure
        directories = set()
        for file in self.codebase.files:
            directory = os.path.dirname(file.path)
            if directory:
                directories.add(directory)
        
        return {
            "file_count": len(self.codebase.files),
            "function_count": len(self.codebase._functions_cache),
            "class_count": len(self.codebase._classes_cache),
            "import_count": len(self.codebase._imports_cache),
            "symbol_count": len(self.codebase._symbols_cache),
            "total_lines": total_lines,
            "extensions": extensions,
            "directory_count": len(directories),
            "path": self.codebase.path
        }
    
    def get_file_summary(self, file: File) -> Dict[str, Any]:
        """Get a summary of a file.
        
        Args:
            file: File object to summarize
            
        Returns:
            Dictionary with file statistics and information
        """
        # Get the file content
        try:
            file_path = os.path.join(self.codebase.path, file.path)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Count blank lines
            blank_lines = content.count('\n\n') + content.count('\r\n\r\n')
            
            # Count comment lines (simple approximation)
            comment_lines = 0
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('#') or line.startswith('//') or line.startswith('/*') or line.startswith('*'):
                    comment_lines += 1
            
            # Determine language based on extension
            ext = os.path.splitext(file.path)[1]
            language_map = {
                '.py': 'Python',
                '.js': 'JavaScript',
                '.ts': 'TypeScript',
                '.jsx': 'React JSX',
                '.tsx': 'React TSX',
                '.html': 'HTML',
                '.css': 'CSS',
                '.java': 'Java',
                '.c': 'C',
                '.cpp': 'C++',
                '.h': 'C/C++ Header',
                '.go': 'Go',
                '.rs': 'Rust',
                '.rb': 'Ruby',
                '.php': 'PHP',
                '.swift': 'Swift',
                '.kt': 'Kotlin',
                '.md': 'Markdown',
                '.json': 'JSON',
                '.yml': 'YAML',
                '.yaml': 'YAML',
                '.xml': 'XML',
                '.sh': 'Shell',
                '.bat': 'Batch',
                '.ps1': 'PowerShell'
            }
            language = language_map.get(ext, 'Unknown')
            
            return {
                "path": file.path,
                "name": file.name,
                "line_count": file.line_count,
                "blank_lines": blank_lines,
                "comment_lines": comment_lines,
                "code_lines": file.line_count - blank_lines - comment_lines,
                "function_count": len(file.functions),
                "class_count": len(file.classes),
                "import_count": len(file.imports),
                "symbol_count": len(file.symbols),
                "language": language,
                "size_bytes": len(content),
                "size_formatted": f"{len(content) / 1024:.2f} KB"
            }
        except Exception as e:
            # If there's an error reading the file, return basic information
            return {
                "path": file.path,
                "name": file.name,
                "line_count": file.line_count,
                "function_count": len(file.functions),
                "class_count": len(file.classes),
                "import_count": len(file.imports),
                "symbol_count": len(file.symbols),
                "error": str(e)
            }
    
    def get_class_summary(self, cls: Class) -> Dict[str, Any]:
        """Get a summary of a class.
        
        Args:
            cls: Class object to summarize
            
        Returns:
            Dictionary with class statistics and information
        """
        # Calculate complexity metrics
        method_count = len(cls.methods)
        
        # Calculate average method complexity (by parameters)
        total_params = sum(len(method.parameters) for method in cls.methods)
        avg_params = total_params / method_count if method_count > 0 else 0
        
        # Count public, protected, and private methods
        public_methods = 0
        protected_methods = 0
        private_methods = 0
        
        for method in cls.methods:
            if method.name.startswith('__') and method.name.endswith('__'):
                # Special methods like __init__
                public_methods += 1
            elif method.name.startswith('__'):
                # Private methods
                private_methods += 1
            elif method.name.startswith('_'):
                # Protected methods
                protected_methods += 1
            else:
                # Public methods
                public_methods += 1
        
        # Check for common design patterns
        is_singleton = any(method.name == 'get_instance' for method in cls.methods)
        is_factory = any(method.name.startswith('create_') or method.name.startswith('make_') for method in cls.methods)
        
        return {
            "name": cls.name,
            "method_count": method_count,
            "attribute_count": len(cls.attributes),
            "parent_classes": cls.parent_class_names,
            "is_abstract": cls.is_abstract,
            "public_methods": public_methods,
            "protected_methods": protected_methods,
            "private_methods": private_methods,
            "avg_params_per_method": avg_params,
            "has_docstring": any(method.docstring for method in cls.methods),
            "possible_patterns": {
                "singleton": is_singleton,
                "factory": is_factory
            }
        }
    
    def get_function_summary(self, function: Function) -> Dict[str, Any]:
        """Get a summary of a function.
        
        Args:
            function: Function object to summarize
            
        Returns:
            Dictionary with function statistics and information
        """
        # Find the function in a file to analyze its code
        function_code = None
        for file in self.codebase.files:
            for file_func in file.functions:
                if file_func.name == function.name and file_func.location:
                    try:
                        # Read the file content
                        file_path = os.path.join(self.codebase.path, file.path)
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Extract the function code
                        lines = content.split('\n')
                        func_lines = lines[file_func.location.start_line - 1:file_func.location.end_line]
                        function_code = '\n'.join(func_lines)
                        break
                    except Exception:
                        continue
            if function_code:
                break
        
        # Calculate cyclomatic complexity (simplified)
        complexity = 1  # Base complexity
        if function_code:
            # Count if statements
            complexity += function_code.count('if ') + function_code.count('elif ')
            # Count loops
            complexity += function_code.count('for ') + function_code.count('while ')
            # Count exception handlers
            complexity += function_code.count('except ')
            # Count logical operators
            complexity += function_code.count(' and ') + function_code.count(' or ')
        
        # Calculate parameter complexity
        param_complexity = 0
        for param in function.parameters:
            # Add 1 for each parameter
            param_complexity += 1
            # Add 0.5 for type annotations
            if param.type_annotation:
                param_complexity += 0.5
            # Add 0.5 for default values
            if param.default_value:
                param_complexity += 0.5
        
        # Determine function type
        function_type = "Regular"
        if function.is_async:
            function_type = "Async"
        elif any(d == '@staticmethod' for d in function.decorators):
            function_type = "Static Method"
        elif any(d == '@classmethod' for d in function.decorators):
            function_type = "Class Method"
        elif any(d == '@property' for d in function.decorators):
            function_type = "Property"
        
        return {
            "name": function.name,
            "parameter_count": len(function.parameters),
            "return_type": function.return_type,
            "is_async": function.is_async,
            "decorator_count": len(function.decorators),
            "decorators": function.decorators,
            "has_docstring": function.docstring is not None,
            "docstring_length": len(function.docstring) if function.docstring else 0,
            "cyclomatic_complexity": complexity,
            "parameter_complexity": param_complexity,
            "function_type": function_type
        }
