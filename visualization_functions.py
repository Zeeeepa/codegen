"""
Visualization functions for codebase_analyzer.py

This module contains the implementation of visualization functions mentioned in the
codebase-visualization.mdx documentation but not yet implemented in codebase_analyzer.py.
"""

from typing import Dict, Any
import networkx as nx

def visualize_component_tree(self, root_component: str) -> Dict[str, Any]:
    """Visualize the hierarchy of React components.
    
    This function creates a directed graph representing the hierarchy of React components,
    starting from a root component and traversing through its children.
    
    Args:
        root_component: The name of the root component to start visualization from
        
    Returns:
        A dictionary containing the component tree visualization data
    """
    result = {
        "nodes": [],
        "edges": [],
        "metadata": {
            "root_component": root_component,
            "component_count": 0,
            "max_depth": 0,
            "visualization_type": "component_tree"
        }
    }
    
    try:
        # Get the root component class
        root = None
        for cls in self.codebase.classes:
            if cls.name == root_component:
                root = cls
                break
                
        if not root:
            return {"error": f"Root component '{root_component}' not found"}
            
        # Create a directed graph
        graph = nx.DiGraph()
        
        # Track visited components to avoid cycles
        visited = set()
        
        # Track depth for metadata
        max_depth = 0
        
        def add_children(component, depth=0):
            nonlocal max_depth
            
            if depth > max_depth:
                max_depth = depth
                
            if component.name in visited:
                return
                
            visited.add(component.name)
            
            # Add the component as a node
            if component not in graph:
                graph.add_node(component)
                
            # Look for child components in the source code
            for usage in component.usages:
                # Check if the usage is within a React component
                if hasattr(usage, 'parent') and usage.parent and hasattr(usage.parent, 'bases'):
                    parent = usage.parent
                    if "Component" in parent.bases or "React.Component" in parent.bases:
                        if parent not in graph:
                            graph.add_node(parent)
                        graph.add_edge(component, parent)
                        add_children(parent, depth + 1)
        
        # Start building the tree from the root
        add_children(root)
        
        # Convert graph to result format
        for node in graph.nodes():
            result["nodes"].append({
                "id": node.name,
                "label": node.name,
                "file": node.file.file_path if hasattr(node, "file") else "Unknown"
            })
            
        for edge in graph.edges():
            result["edges"].append({
                "source": edge[0].name,
                "target": edge[1].name
            })
            
        # Update metadata
        result["metadata"]["component_count"] = len(graph.nodes())
        result["metadata"]["max_depth"] = max_depth
        
        return result
        
    except Exception as e:
        return {"error": str(e)}

def visualize_inheritance_hierarchy(self, base_class: str) -> Dict[str, Any]:
    """Visualize class inheritance hierarchies.
    
    This function creates a directed graph representing the inheritance hierarchy,
    starting from a base class and recursively adding all subclasses.
    
    Args:
        base_class: The name of the base class to start visualization from
        
    Returns:
        A dictionary containing the inheritance hierarchy visualization data
    """
    result = {
        "nodes": [],
        "edges": [],
        "metadata": {
            "base_class": base_class,
            "class_count": 0,
            "max_depth": 0,
            "visualization_type": "inheritance_hierarchy"
        }
    }
    
    try:
        # Get the base class
        base = None
        for cls in self.codebase.classes:
            if cls.name == base_class:
                base = cls
                break
                
        if not base:
            return {"error": f"Base class '{base_class}' not found"}
            
        # Create a directed graph
        graph = nx.DiGraph()
        
        # Track depth for metadata
        max_depth = 0
        
        def add_subclasses(cls, depth=0):
            nonlocal max_depth
            
            if depth > max_depth:
                max_depth = depth
            
            # Add the class as a node
            if cls not in graph:
                graph.add_node(cls)
            
            # Find all subclasses
            for subclass in self.codebase.classes:
                if hasattr(subclass, 'bases') and cls.name in subclass.bases:
                    if subclass not in graph:
                        graph.add_node(subclass)
                    graph.add_edge(cls, subclass)
                    add_subclasses(subclass, depth + 1)
        
        # Start building the hierarchy from the base class
        add_subclasses(base)
        
        # Convert graph to result format
        for node in graph.nodes():
            result["nodes"].append({
                "id": node.name,
                "label": node.name,
                "file": node.file.file_path if hasattr(node, "file") else "Unknown"
            })
            
        for edge in graph.edges():
            result["edges"].append({
                "source": edge[0].name,
                "target": edge[1].name
            })
            
        # Update metadata
        result["metadata"]["class_count"] = len(graph.nodes())
        result["metadata"]["max_depth"] = max_depth
        
        return result
        
    except Exception as e:
        return {"error": str(e)}

def visualize_module_dependencies(self, start_file: str) -> Dict[str, Any]:
    """Visualize dependencies between modules.
    
    This function creates a directed graph representing the dependencies between modules,
    starting from a specific file and following all import relationships.
    
    Args:
        start_file: The path to the file to start visualization from
        
    Returns:
        A dictionary containing the module dependency visualization data
    """
    result = {
        "nodes": [],
        "edges": [],
        "metadata": {
            "start_file": start_file,
            "module_count": 0,
            "external_dependencies": 0,
            "internal_dependencies": 0,
            "visualization_type": "module_dependencies"
        }
    }
    
    try:
        # Get the starting file
        file_obj = None
        for file in self.codebase.files:
            if file.file_path == start_file or file.file_path.endswith(start_file):
                file_obj = file
                break
                
        if not file_obj:
            return {"error": f"Start file '{start_file}' not found"}
            
        # Create a directed graph
        graph = nx.DiGraph()
        
        # Track visited files to avoid cycles
        visited = set()
        
        # Count internal and external dependencies
        internal_deps = 0
        external_deps = 0
        
        def add_imports(file):
            nonlocal internal_deps, external_deps
            
            if file.file_path in visited:
                return
                
            visited.add(file.file_path)
            
            # Add the file as a node
            if file not in graph:
                graph.add_node(file)
            
            # Process all imports in the file
            if hasattr(file, 'imports'):
                for imp in file.imports:
                    # Check if the import resolves to a file in the codebase
                    if hasattr(imp, 'resolved_symbol') and imp.resolved_symbol and hasattr(imp.resolved_symbol, 'file'):
                        target_file = imp.resolved_symbol.file
                        
                        # Skip if it's the same file
                        if target_file.file_path == file.file_path:
                            continue
                            
                        if target_file not in graph:
                            graph.add_node(target_file)
                            
                        # Add the dependency edge
                        graph.add_edge(file, target_file)
                        
                        # Count as internal dependency
                        internal_deps += 1
                        
                        # Recursively process the imported file
                        add_imports(target_file)
                    else:
                        # This is an external dependency
                        external_deps += 1
        
        # Start building the dependency graph from the start file
        add_imports(file_obj)
        
        # Convert graph to result format
        for node in graph.nodes():
            result["nodes"].append({
                "id": node.file_path,
                "label": node.file_path.split("/")[-1],
                "file_path": node.file_path
            })
            
        for edge in graph.edges():
            result["edges"].append({
                "source": edge[0].file_path,
                "target": edge[1].file_path
            })
            
        # Update metadata
        result["metadata"]["module_count"] = len(graph.nodes())
        result["metadata"]["internal_dependencies"] = internal_deps
        result["metadata"]["external_dependencies"] = external_deps
        
        return result
        
    except Exception as e:
        return {"error": str(e)}

def analyze_function_modularity(self) -> Dict[str, Any]:
    """Analyze function groupings by modularity.
    
    This function creates an undirected graph representing the relationships between functions
    based on shared dependencies, then applies community detection to identify modules.
    
    Returns:
        A dictionary containing the function modularity analysis data
    """
    result = {
        "modules": [],
        "function_count": 0,
        "module_count": 0,
        "modularity_score": 0.0,
        "visualization_type": "function_modularity"
    }
    
    try:
        # Get all functions
        functions = list(self.codebase.functions)
        
        if not functions:
            return {"error": "No functions found in the codebase"}
            
        # Create an undirected graph
        graph = nx.Graph()
        
        # Add all functions as nodes
        for func in functions:
            graph.add_node(func)
        
        # Connect functions based on shared dependencies
        for i, func1 in enumerate(functions):
            func1_deps = set()
            
            # Collect dependencies of func1
            if hasattr(func1, 'dependencies'):
                func1_deps = set(func1.dependencies)
            elif hasattr(func1, 'call_sites'):
                func1_deps = {call.resolved_symbol for call in func1.call_sites if call.resolved_symbol}
            
            for j in range(i + 1, len(functions)):
                func2 = functions[j]
                func2_deps = set()
                
                # Collect dependencies of func2
                if hasattr(func2, 'dependencies'):
                    func2_deps = set(func2.dependencies)
                elif hasattr(func2, 'call_sites'):
                    func2_deps = {call.resolved_symbol for call in func2.call_sites if call.resolved_symbol}
                
                # Calculate shared dependencies
                shared_deps = len(func1_deps.intersection(func2_deps))
                
                # Add edge if there are shared dependencies
                if shared_deps > 0:
                    graph.add_edge(func1, func2, weight=shared_deps)
        
        # Apply community detection to identify modules
        # Using Louvain method for community detection
        try:
            from community import best_partition
            partition = best_partition(graph)
        except ImportError:
            # Fallback to connected components if community detection is not available
            partition = {}
            for i, component in enumerate(nx.connected_components(graph)):
                for node in component:
                    partition[node] = i
        
        # Calculate modularity score
        try:
            modularity = nx.algorithms.community.modularity(graph, 
                                                          [list(nodes) for nodes in nx.community.label_propagation.asyn_lpa_communities(graph)])
        except:
            modularity = 0.0
        
        # Group functions by module
        modules = {}
        for func, module_id in partition.items():
            if module_id not in modules:
                modules[module_id] = []
            modules[module_id].append({
                "name": func.name,
                "file": func.file.file_path if hasattr(func, "file") else "Unknown"
            })
        
        # Convert modules to result format
        for module_id, funcs in modules.items():
            result["modules"].append({
                "id": module_id,
                "functions": funcs,
                "size": len(funcs)
            })
        
        # Update metadata
        result["function_count"] = len(functions)
        result["module_count"] = len(modules)
        result["modularity_score"] = modularity
        
        return result
        
    except Exception as e:
        return {"error": str(e)}

