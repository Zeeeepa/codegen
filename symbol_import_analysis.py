    def get_symbol_import_analysis(self) -> Dict[str, Any]:
        """
        Analyze symbol imports in the codebase.
        
        This function analyzes how symbols are imported and used throughout the codebase,
        identifying patterns, potential issues, and optimization opportunities.
        
        Returns:
            Dict containing symbol import analysis results
        """
        import_analysis = {
            "import_patterns": {},
            "most_imported_modules": [],
            "unused_imports": [],
            "duplicate_imports": [],
            "circular_imports": [],
            "import_chains": [],
            "import_statistics": {
                "total_imports": 0,
                "unique_modules": 0,
                "external_imports": 0,
                "internal_imports": 0,
                "relative_imports": 0,
                "absolute_imports": 0
            }
        }
        
        try:
            # Get all imports from files
            all_imports = []
            file_imports = {}  # Map files to their imports
            
            for file in self.codebase.files:
                if hasattr(file, "imports"):
                    file_imports[file.file_path] = file.imports
                    all_imports.extend(file.imports)
            
            # Count total imports
            import_analysis["import_statistics"]["total_imports"] = len(all_imports)
            
            # Count unique modules
            unique_modules = set()
            for imp in all_imports:
                if hasattr(imp, "module"):
                    unique_modules.add(imp.module)
            
            import_analysis["import_statistics"]["unique_modules"] = len(unique_modules)
            
            # Analyze import patterns
            import_patterns = {}
            external_count = 0
            internal_count = 0
            relative_count = 0
            absolute_count = 0
            
            for imp in all_imports:
                if not hasattr(imp, "module"):
                    continue
                
                module = imp.module
                
                # Count in patterns
                if module in import_patterns:
                    import_patterns[module] += 1
                else:
                    import_patterns[module] = 1
                
                # Check if external or internal
                is_external = True
                for file_path in file_imports.keys():
                    if module.replace(".", "/") in file_path:
                        is_external = False
                        break
                
                if is_external:
                    external_count += 1
                else:
                    internal_count += 1
                
                # Check if relative or absolute
                if module.startswith("."):
                    relative_count += 1
                else:
                    absolute_count += 1
            
            import_analysis["import_statistics"]["external_imports"] = external_count
            import_analysis["import_statistics"]["internal_imports"] = internal_count
            import_analysis["import_statistics"]["relative_imports"] = relative_count
            import_analysis["import_statistics"]["absolute_imports"] = absolute_count
            
            # Get most imported modules
            sorted_patterns = sorted(import_patterns.items(), key=lambda x: x[1], reverse=True)
            import_analysis["import_patterns"] = import_patterns
            import_analysis["most_imported_modules"] = [
                {"module": module, "count": count}
                for module, count in sorted_patterns[:10]  # Top 10
            ]
            
            # Find unused imports
            used_imports = set()
            for file in self.codebase.files:
                if not hasattr(file, "imports"):
                    continue
                
                for imp in file.imports:
                    if not hasattr(imp, "name") or not hasattr(imp, "module"):
                        continue
                    
                    # Check if the import is used in the file
                    is_used = False
                    
                    # Check in functions
                    for func in self.codebase.functions:
                        if not hasattr(func, "file") or func.file.file_path != file.file_path:
                            continue
                        
                        for node in func.ast_node.walk():
                            # Check for attribute access (e.g., module.attribute)
                            if hasattr(node, "value") and hasattr(node.value, "id") and node.value.id == imp.name:
                                is_used = True
                                break
                            
                            # Check for direct usage of imported name
                            if hasattr(node, "id") and node.id == imp.name:
                                is_used = True
                                break
                    
                    if not is_used:
                        used_imports.add(imp.id)
                        import_analysis["unused_imports"].append({
                            "name": imp.name,
                            "module": imp.module,
                            "file": file.file_path,
                            "line": imp.line_number if hasattr(imp, "line_number") else 0
                        })
            
            # Find duplicate imports
            for file_path, imports in file_imports.items():
                import_map = {}
                
                for imp in imports:
                    if not hasattr(imp, "name") or not hasattr(imp, "module"):
                        continue
                    
                    key = f"{imp.module}.{imp.name}"
                    
                    if key in import_map:
                        import_analysis["duplicate_imports"].append({
                            "name": imp.name,
                            "module": imp.module,
                            "file": file_path,
                            "line1": import_map[key],
                            "line2": imp.line_number if hasattr(imp, "line_number") else 0
                        })
                    else:
                        import_map[key] = imp.line_number if hasattr(imp, "line_number") else 0
            
            # Detect circular imports
            import_graph = nx.DiGraph()
            
            for file_path, imports in file_imports.items():
                import_graph.add_node(file_path)
                
                for imp in imports:
                    if not hasattr(imp, "module"):
                        continue
                    
                    # Try to resolve the module to a file path
                    target_file = None
                    for other_file in file_imports.keys():
                        if other_file.endswith(imp.module.replace(".", "/") + ".py"):
                            target_file = other_file
                            break
                    
                    if target_file and target_file != file_path:
                        import_graph.add_edge(file_path, target_file)
            
            # Find cycles in the import graph
            try:
                cycles = list(nx.simple_cycles(import_graph))
                for cycle in cycles:
                    import_analysis["circular_imports"].append({
                        "files": cycle,
                        "length": len(cycle)
                    })
            except:
                # Simple cycles might not be available for all graph types
                pass
            
            # Find import chains (long chains of imports)
            all_paths = []
            for source in import_graph.nodes():
                for target in import_graph.nodes():
                    if source != target:
                        try:
                            paths = list(nx.all_simple_paths(import_graph, source, target, cutoff=5))
                            all_paths.extend(paths)
                        except:
                            continue
            
            # Get the longest import chains
            long_chains = sorted(all_paths, key=len, reverse=True)[:5]  # Top 5 longest chains
            import_analysis["import_chains"] = [
                {
                    "path": path,
                    "length": len(path)
                }
                for path in long_chains
            ]
            
            return import_analysis
        except Exception as e:
            logger.error(f"Error in symbol import analysis: {e}")
            return {"error": str(e)}
