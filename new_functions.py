    def visualize_blast_radius(self, symbol_name: str) -> Dict[str, Any]:
        """Create a visualization of the blast radius for a given symbol.
        
        The blast radius shows how changes to one function might affect other parts 
        of the codebase by tracing usage relationships.
        
        Args:
            symbol_name: Name of the symbol to analyze
            
        Returns:
            Dict containing the visualization data
        """
        if not self.codebase:
            msg = "Codebase not initialized. Please initialize the codebase first."
            raise ValueError(msg)
            
        # Create a directed graph for the blast radius
        G = nx.DiGraph()
        
        # Find the target symbol
        symbol = None
        for func in self.codebase.functions:
            if func.name == symbol_name:
                symbol = func
                break
                
        if not symbol:
            return {"error": f"Symbol '{symbol_name}' not found in codebase"}
            
        # Add the root node
        G.add_node(symbol, name=symbol_name, color="#9cdcfe")  # Light blue for root node
        
        # Define HTTP methods for detection
        HTTP_METHODS = ["get", "put", "patch", "post", "head", "delete"]
        
        # Define color palette
        COLOR_PALETTE = {
            "PyFunction": "#a277ff",        # Soft purple
            "PyClass": "#ffca85",           # Warm peach/orange
            "HTTP_METHOD": "#ff6e6e",       # Red for HTTP methods
            "ExternalModule": "#f694ff"     # Bright magenta/pink
        }
        
        # Helper function to check if a symbol is an HTTP method
        def is_http_method(sym):
            if hasattr(sym, "is_method") and sym.is_method and hasattr(sym, "name"):
                return sym.name.lower() in HTTP_METHODS
            return False
            
        # Helper function to generate edge metadata
        def generate_edge_meta(usage):
            return {
                "name": usage.match.source if hasattr(usage, "match") and hasattr(usage.match, "source") else "usage",
                "file_path": usage.match.filepath if hasattr(usage, "match") and hasattr(usage.match, "filepath") else "",
                "symbol_name": usage.match.__class__.__name__ if hasattr(usage, "match") else ""
            }
            
        # Recursive function to build the blast radius visualization
        def build_blast_radius(sym, depth=0, max_depth=5):
            if depth >= max_depth:
                return
                
            if hasattr(sym, "usages"):
                for usage in sym.usages:
                    if hasattr(usage, "usage_symbol"):
                        usage_symbol = usage.usage_symbol
                        
                        # Determine node color based on type
                        if is_http_method(usage_symbol):
                            color = COLOR_PALETTE.get("HTTP_METHOD")
                        else:
                            color = COLOR_PALETTE.get(usage_symbol.__class__.__name__, "#f694ff")
                            
                        # Add node and edge to graph
                        G.add_node(usage_symbol, color=color)
                        G.add_edge(sym, usage_symbol, **generate_edge_meta(usage))
                        
                        # Recursively process usage symbol
                        build_blast_radius(usage_symbol, depth + 1, max_depth)
        
        # Build the blast radius visualization
        build_blast_radius(symbol)
        
        # Convert the graph to a serializable format
        nodes = []
        for node in G.nodes():
            node_data = G.nodes[node]
            nodes.append({
                "id": str(id(node)),
                "name": node.name if hasattr(node, "name") else str(node),
                "color": node_data.get("color", "#cccccc"),
                "type": node.__class__.__name__ if hasattr(node, "__class__") else "Unknown"
            })
            
        edges = []
        for source, target in G.edges():
            edge_data = G.edges[source, target]
            edges.append({
                "source": str(id(source)),
                "target": str(id(target)),
                "name": edge_data.get("name", ""),
                "file_path": edge_data.get("file_path", "")
            })
            
        return {
            "nodes": nodes,
            "edges": edges,
            "root_node": str(id(symbol)),
            "symbol_name": symbol_name
        }
        
    def detect_http_methods(self) -> List[str]:
        """Detect HTTP endpoint methods in the codebase.
        
        Returns:
            List of HTTP endpoint methods found in the codebase
        """
        if not self.codebase:
            msg = "Codebase not initialized. Please initialize the codebase first."
            raise ValueError(msg)
            
        http_methods = []
        HTTP_METHOD_NAMES = ["get", "put", "patch", "post", "head", "delete", "options"]
        
        for func in self.codebase.functions:
            if hasattr(func, "is_method") and func.is_method and hasattr(func, "name"):
                if func.name.lower() in HTTP_METHOD_NAMES:
                    # Check for common API/endpoint patterns
                    is_endpoint = False
                    
                    # Check if parent class has View, Controller, API, Endpoint, etc. in name
                    if hasattr(func, "parent_class") and hasattr(func.parent_class, "name"):
                        parent_name = func.parent_class.name.lower()
                        if any(pattern in parent_name for pattern in ["view", "controller", "api", "endpoint", "resource", "handler"]):
                            is_endpoint = True
                    
                    # Check for common decorators
                    if hasattr(func, "decorators"):
                        for decorator in func.decorators:
                            decorator_name = str(decorator).lower()
                            if any(pattern in decorator_name for pattern in ["route", "api", "endpoint", "http", "get", "post", "put", "delete"]):
                                is_endpoint = True
                                break
                    
                    if is_endpoint:
                        parent_class_name = func.parent_class.name if hasattr(func, "parent_class") and hasattr(func.parent_class, "name") else "Unknown"
                        http_methods.append({
                            "name": func.name,
                            "parent_class": parent_class_name,
                            "file_path": func.file.file_path if hasattr(func, "file") and hasattr(func.file, "file_path") else "Unknown",
                            "method_type": func.name.upper()
                        })
        
        return http_methods
        
    def visualize_usage_relationships(self, symbol_name: str) -> Dict[str, Any]:
        """Create a visualization of usage relationships for a given symbol.
        
        This shows how a symbol is used throughout the codebase and the relationships
        between different usages.
        
        Args:
            symbol_name: Name of the symbol to analyze
            
        Returns:
            Dict containing the visualization data
        """
        if not self.codebase:
            msg = "Codebase not initialized. Please initialize the codebase first."
            raise ValueError(msg)
            
        # Create a directed graph for the usage relationships
        G = nx.DiGraph()
        
        # Find the target symbol
        symbol = None
        for func in self.codebase.functions:
            if func.name == symbol_name:
                symbol = func
                break
                
        if not symbol:
            for cls in self.codebase.classes:
                if cls.name == symbol_name:
                    symbol = cls
                    break
                    
        if not symbol:
            return {"error": f"Symbol '{symbol_name}' not found in codebase"}
            
        # Add the root node
        G.add_node(symbol, name=symbol_name, color="#9cdcfe")  # Light blue for root node
        
        # Define color palette
        COLOR_PALETTE = {
            "PyFunction": "#a277ff",        # Soft purple
            "PyClass": "#ffca85",           # Warm peach/orange
            "PyVariable": "#61afef",        # Blue
            "ExternalModule": "#f694ff"     # Bright magenta/pink
        }
        
        # Helper function to generate edge metadata
        def generate_edge_meta(usage_type, location=""):
            return {
                "usage_type": usage_type,
                "location": location
            }
            
        # Process direct usages
        if hasattr(symbol, "usages"):
            for usage in symbol.usages:
                if hasattr(usage, "usage_symbol"):
                    usage_symbol = usage.usage_symbol
                    
                    # Add node with appropriate styling
                    G.add_node(
                        usage_symbol, 
                        name=usage_symbol.name if hasattr(usage_symbol, "name") else str(usage_symbol),
                        color=COLOR_PALETTE.get(usage_symbol.__class__.__name__, "#cccccc")
                    )
                    
                    # Add edge with usage information
                    G.add_edge(
                        symbol, 
                        usage_symbol, 
                        **generate_edge_meta(
                            "direct_usage",
                            usage.match.filepath if hasattr(usage, "match") and hasattr(usage.match, "filepath") else ""
                        )
                    )
        
        # Process imports of the symbol
        if hasattr(symbol, "imports"):
            for imp in symbol.imports:
                if hasattr(imp, "resolved_symbol") and imp.resolved_symbol:
                    # Add node with appropriate styling
                    G.add_node(
                        imp.resolved_symbol,
                        name=imp.resolved_symbol.name if hasattr(imp.resolved_symbol, "name") else str(imp.resolved_symbol),
                        color=COLOR_PALETTE.get(imp.resolved_symbol.__class__.__name__, "#cccccc")
                    )
                    
                    # Add edge with import information
                    G.add_edge(
                        symbol,
                        imp.resolved_symbol,
                        **generate_edge_meta("import", imp.file.file_path if hasattr(imp, "file") and hasattr(imp.file, "file_path") else "")
                    )
        
        # Convert the graph to a serializable format
        nodes = []
        for node in G.nodes():
            node_data = G.nodes[node]
            nodes.append({
                "id": str(id(node)),
                "name": node_data.get("name", str(node)),
                "color": node_data.get("color", "#cccccc"),
                "type": node.__class__.__name__ if hasattr(node, "__class__") else "Unknown"
            })
            
        edges = []
        for source, target in G.edges():
            edge_data = G.edges[source, target]
            edges.append({
                "source": str(id(source)),
                "target": str(id(target)),
                "usage_type": edge_data.get("usage_type", "unknown"),
                "location": edge_data.get("location", "")
            })
            
        return {
            "nodes": nodes,
            "edges": edges,
            "root_node": str(id(symbol)),
            "symbol_name": symbol_name
        }
        
    def track_symbol_usages(self, symbol_name: str) -> Dict[str, Any]:
        """Track all usages of a symbol across the codebase.
        
        This provides detailed information about where and how a symbol is used.
        
        Args:
            symbol_name: Name of the symbol to track
            
        Returns:
            Dict containing usage information
        """
        if not self.codebase:
            msg = "Codebase not initialized. Please initialize the codebase first."
            raise ValueError(msg)
            
        # Find the target symbol
        symbol = None
        for func in self.codebase.functions:
            if func.name == symbol_name:
                symbol = func
                break
                
        if not symbol:
            for cls in self.codebase.classes:
                if cls.name == symbol_name:
                    symbol = cls
                    break
                    
        if not symbol:
            return {"error": f"Symbol '{symbol_name}' not found in codebase"}
            
        # Collect usage information
        usages = []
        
        if hasattr(symbol, "usages"):
            for usage in symbol.usages:
                usage_info = {
                    "type": "reference",
                    "location": {
                        "file": usage.match.filepath if hasattr(usage, "match") and hasattr(usage.match, "filepath") else "Unknown",
                        "line": usage.match.start_point[0] if hasattr(usage, "match") and hasattr(usage.match, "start_point") else 0,
                        "column": usage.match.start_point[1] if hasattr(usage, "match") and hasattr(usage.match, "start_point") else 0
                    },
                    "context": usage.match.source if hasattr(usage, "match") and hasattr(usage.match, "source") else "",
                    "using_symbol": {
                        "name": usage.usage_symbol.name if hasattr(usage, "usage_symbol") and hasattr(usage.usage_symbol, "name") else "Unknown",
                        "type": usage.usage_symbol.__class__.__name__ if hasattr(usage, "usage_symbol") and hasattr(usage.usage_symbol, "__class__") else "Unknown"
                    }
                }
                usages.append(usage_info)
        
        # Collect import information
        imports = []
        
        for file in self.codebase.files:
            for imp in file.imports:
                if hasattr(imp, "resolved_symbol") and imp.resolved_symbol == symbol:
                    import_info = {
                        "type": "import",
                        "location": {
                            "file": file.file_path,
                            "line": imp.start_point[0] if hasattr(imp, "start_point") else 0,
                            "column": imp.start_point[1] if hasattr(imp, "start_point") else 0
                        },
                        "import_statement": imp.source if hasattr(imp, "source") else "Unknown"
                    }
                    imports.append(import_info)
        
        # Collect inheritance information if it's a class
        inheritance = []
        
        if hasattr(symbol, "__class__") and symbol.__class__.__name__ == "PyClass":
            for cls in self.codebase.classes:
                if hasattr(cls, "bases") and symbol in cls.bases:
                    inheritance_info = {
                        "type": "inheritance",
                        "subclass": cls.name,
                        "location": {
                            "file": cls.file.file_path if hasattr(cls, "file") and hasattr(cls.file, "file_path") else "Unknown",
                            "line": cls.start_point[0] if hasattr(cls, "start_point") else 0,
                            "column": cls.start_point[1] if hasattr(cls, "start_point") else 0
                        }
                    }
                    inheritance.append(inheritance_info)
        
        # Collect function call information if it's a function
        calls = []
        
        if hasattr(symbol, "__class__") and symbol.__class__.__name__ == "PyFunction":
            for func in self.codebase.functions:
                if hasattr(func, "function_calls"):
                    for call in func.function_calls:
                        if hasattr(call, "function_definition") and call.function_definition == symbol:
                            call_info = {
                                "type": "call",
                                "caller": func.name,
                                "location": {
                                    "file": func.file.file_path if hasattr(func, "file") and hasattr(func.file, "file_path") else "Unknown",
                                    "line": call.start_point[0] if hasattr(call, "start_point") else 0,
                                    "column": call.start_point[1] if hasattr(call, "start_point") else 0
                                },
                                "call_statement": call.source if hasattr(call, "source") else "Unknown"
                            }
                            calls.append(call_info)
        
        return {
            "symbol": {
                "name": symbol_name,
                "type": symbol.__class__.__name__ if hasattr(symbol, "__class__") else "Unknown",
                "file": symbol.file.file_path if hasattr(symbol, "file") and hasattr(symbol.file, "file_path") else "Unknown"
            },
            "usage_count": len(usages),
            "import_count": len(imports),
            "inheritance_count": len(inheritance),
            "call_count": len(calls),
            "usages": usages,
            "imports": imports,
            "inheritance": inheritance,
            "calls": calls
        }

