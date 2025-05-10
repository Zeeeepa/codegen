    def get_dead_code_detection_with_filtering(self, exclude_patterns: List[str] = None) -> Dict[str, Any]:
        """
        Detect dead code in the codebase with filtering options.
        
        This function identifies functions, classes, and methods that are defined but never used
        in the codebase, with the ability to exclude certain patterns from analysis.
        
        Args:
            exclude_patterns: List of regex patterns to exclude from dead code detection
            
        Returns:
            Dict containing dead code analysis results with filtering
        """
        if exclude_patterns is None:
            exclude_patterns = []
            
        # Compile exclude patterns
        compiled_patterns = [re.compile(pattern) for pattern in exclude_patterns]
        
        dead_code_analysis = {
            "dead_functions": [],
            "dead_classes": [],
            "dead_methods": [],
            "excluded_items": [],
            "total_dead_items": 0,
            "total_items": 0,
            "dead_code_percentage": 0.0
        }
        
        try:
            # Get all defined functions and classes
            all_functions = list(self.codebase.functions)
            all_classes = list(self.codebase.classes)
            
            # Get all function calls and class instantiations
            function_calls = set()
            class_instantiations = set()
            
            for func in all_functions:
                for call in func.function_calls:
                    if hasattr(call, "function_definition") and call.function_definition:
                        function_calls.add(call.function_definition.id)
                
                # Also check for class instantiations in the function
                for node in func.ast_node.walk():
                    if hasattr(node, "func") and hasattr(node.func, "id"):
                        # This is a potential class instantiation
                        class_name = node.func.id
                        for cls in all_classes:
                            if cls.name == class_name:
                                class_instantiations.add(cls.id)
            
            # Check for dead functions
            total_functions = len(all_functions)
            for func in all_functions:
                # Skip if function matches any exclude pattern
                should_exclude = False
                for pattern in compiled_patterns:
                    if pattern.search(func.name) or (hasattr(func, "file") and pattern.search(func.file.file_path)):
                        should_exclude = True
                        dead_code_analysis["excluded_items"].append({
                            "type": "function",
                            "name": func.name,
                            "file": func.file.file_path if hasattr(func, "file") else "Unknown",
                            "pattern": pattern.pattern
                        })
                        break
                
                if should_exclude:
                    continue
                
                # Check if function is used
                if func.id not in function_calls and not func.name.startswith("__"):
                    # Check if it's a special method or entry point
                    if not (func.name == "main" or func.name == "run" or func.name.startswith("test_")):
                        dead_code_analysis["dead_functions"].append({
                            "name": func.name,
                            "file": func.file.file_path if hasattr(func, "file") else "Unknown",
                            "line": func.line_number if hasattr(func, "line_number") else 0
                        })
            
            # Check for dead classes
            total_classes = len(all_classes)
            for cls in all_classes:
                # Skip if class matches any exclude pattern
                should_exclude = False
                for pattern in compiled_patterns:
                    if pattern.search(cls.name) or (hasattr(cls, "file") and pattern.search(cls.file.file_path)):
                        should_exclude = True
                        dead_code_analysis["excluded_items"].append({
                            "type": "class",
                            "name": cls.name,
                            "file": cls.file.file_path if hasattr(cls, "file") else "Unknown",
                            "pattern": pattern.pattern
                        })
                        break
                
                if should_exclude:
                    continue
                
                # Check if class is instantiated or inherited
                is_used = cls.id in class_instantiations
                
                # Also check if it's a parent class
                if not is_used:
                    for other_cls in all_classes:
                        if hasattr(other_cls, "bases") and cls.name in [base.name for base in other_cls.bases if hasattr(base, "name")]:
                            is_used = True
                            break
                
                if not is_used and not cls.name.startswith("__"):
                    dead_code_analysis["dead_classes"].append({
                        "name": cls.name,
                        "file": cls.file.file_path if hasattr(cls, "file") else "Unknown",
                        "line": cls.line_number if hasattr(cls, "line_number") else 0
                    })
            
            # Check for dead methods
            total_methods = 0
            for cls in all_classes:
                if hasattr(cls, "methods"):
                    methods = cls.methods
                    total_methods += len(methods)
                    
                    for method in methods:
                        # Skip if method matches any exclude pattern
                        should_exclude = False
                        for pattern in compiled_patterns:
                            if pattern.search(method.name):
                                should_exclude = True
                                dead_code_analysis["excluded_items"].append({
                                    "type": "method",
                                    "name": f"{cls.name}.{method.name}",
                                    "file": cls.file.file_path if hasattr(cls, "file") else "Unknown",
                                    "pattern": pattern.pattern
                                })
                                break
                        
                        if should_exclude:
                            continue
                        
                        # Check if method is called
                        is_used = method.id in function_calls
                        
                        # Special methods are considered used
                        if not is_used and not method.name.startswith("__"):
                            dead_code_analysis["dead_methods"].append({
                                "name": f"{cls.name}.{method.name}",
                                "file": cls.file.file_path if hasattr(cls, "file") else "Unknown",
                                "line": method.line_number if hasattr(method, "line_number") else 0
                            })
            
            # Calculate statistics
            total_dead_items = len(dead_code_analysis["dead_functions"]) + len(dead_code_analysis["dead_classes"]) + len(dead_code_analysis["dead_methods"])
            total_items = total_functions + total_classes + total_methods
            
            dead_code_analysis["total_dead_items"] = total_dead_items
            dead_code_analysis["total_items"] = total_items
            dead_code_analysis["dead_code_percentage"] = (total_dead_items / total_items * 100) if total_items > 0 else 0
            
            return dead_code_analysis
        except Exception as e:
            logger.error(f"Error in dead code detection: {e}")
            return {"error": str(e)}
