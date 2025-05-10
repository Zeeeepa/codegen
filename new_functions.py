    def analyze_type_coverage(self) -> Dict[str, Any]:
        """Analyze type coverage across parameters, return types, and class attributes.
        
        Returns:
            Dict containing comprehensive type coverage analysis with percentages.
        """
        # Initialize counters for parameters
        total_parameters = 0
        typed_parameters = 0
        
        # Initialize counters for return types
        total_functions = 0
        typed_returns = 0
        
        # Initialize counters for class attributes
        total_attributes = 0
        typed_attributes = 0
        
        # Count parameter and return type coverage
        for function in self.codebase.functions:
            # Count parameters
            total_parameters += len(function.parameters)
            typed_parameters += sum(1 for param in function.parameters if hasattr(param, "is_typed") and param.is_typed)
            
            # Count return types
            total_functions += 1
            if hasattr(function, "return_type") and function.return_type and hasattr(function.return_type, "is_typed") and function.return_type.is_typed:
                typed_returns += 1
        
        # Count class attribute coverage
        for cls in self.codebase.classes:
            for attr in cls.attributes:
                total_attributes += 1
                if hasattr(attr, "is_typed") and attr.is_typed:
                    typed_attributes += 1
        
        # Calculate percentages
        param_percentage = (typed_parameters / total_parameters * 100) if total_parameters > 0 else 0
        return_percentage = (typed_returns / total_functions * 100) if total_functions > 0 else 0
        attr_percentage = (typed_attributes / total_attributes * 100) if total_attributes > 0 else 0
        
        # Prepare results
        results = {
            "parameters": {
                "percentage": param_percentage,
                "typed_count": typed_parameters,
                "total_count": total_parameters
            },
            "return_types": {
                "percentage": return_percentage,
                "typed_count": typed_returns,
                "total_count": total_functions
            },
            "class_attributes": {
                "percentage": attr_percentage,
                "typed_count": typed_attributes,
                "total_count": total_attributes
            },
            "overall_percentage": (param_percentage + return_percentage + attr_percentage) / 3 if (total_parameters > 0 and total_functions > 0 and total_attributes > 0) else 0
        }
        
        return results
    
    def find_functions_without_return_statements(self) -> List[Dict[str, str]]:
        """Find functions that don't have any return statements.
        
        Returns:
            List of dictionaries containing function name and file path.
        """
        functions_without_return = []
        
        for function in self.codebase.functions:
            # Skip if it's a constructor, abstract method, or interface method
            if function.name in ["__init__", "constructor"] or hasattr(function, "is_abstract") and function.is_abstract:
                continue
                
            # Check if the function has no return statements
            if not hasattr(function, "return_statements") or len(function.return_statements) == 0:
                file_path = function.file.file_path if hasattr(function, "file") else "Unknown"
                functions_without_return.append({
                    "name": function.name,
                    "file": file_path,
                    "line": function.start_position.line if hasattr(function, "start_position") else 0
                })
        
        return functions_without_return
    
    def integrate_with_type_checkers(self, checker: str = "mypy") -> Dict[str, Any]:
        """Interface with type checkers like mypy and tsc for precise type inference.
        
        Args:
            checker: The type checker to use ('mypy' or 'tsc')
            
        Returns:
            Dict containing the type checker results and analysis.
        """
        results = {
            "checker": checker,
            "success": False,
            "errors": [],
            "type_issues": [],
            "summary": {}
        }
        
        try:
            if checker.lower() == "mypy":
                # Check if mypy is installed
                try:
                    subprocess.run(["mypy", "--version"], capture_output=True, check=True)
                except (subprocess.SubprocessError, FileNotFoundError):
                    results["errors"].append("mypy is not installed or not in PATH")
                    return results
                
                # Run mypy on the codebase
                repo_path = self.codebase.ctx.repo_path
                cmd = ["mypy", "--show-column-numbers", "--show-error-codes", "--no-error-summary", repo_path]
                process = subprocess.run(cmd, capture_output=True, text=True)
                
                # Parse mypy output
                if process.returncode != 0:
                    error_lines = process.stdout.strip().split("\n")
                    type_issues = []
                    
                    for line in error_lines:
                        if line and ":" in line:
                            parts = line.split(":", 3)
                            if len(parts) >= 4:
                                file_path, line_num, col_num, error_msg = parts
                                type_issues.append({
                                    "file": file_path,
                                    "line": int(line_num),
                                    "column": int(col_num) if col_num.strip().isdigit() else 0,
                                    "message": error_msg.strip(),
                                    "error_code": error_msg.split("[")[-1].split("]")[0] if "[" in error_msg and "]" in error_msg else ""
                                })
                    
                    results["type_issues"] = type_issues
                    
                    # Generate summary
                    error_types = {}
                    for issue in type_issues:
                        error_code = issue.get("error_code", "unknown")
                        if error_code in error_types:
                            error_types[error_code] += 1
                        else:
                            error_types[error_code] = 1
                    
                    results["summary"] = {
                        "total_issues": len(type_issues),
                        "error_types": error_types
                    }
                
                results["success"] = True
                
            elif checker.lower() == "tsc":
                # Check if tsc is installed
                try:
                    subprocess.run(["tsc", "--version"], capture_output=True, check=True)
                except (subprocess.SubprocessError, FileNotFoundError):
                    results["errors"].append("TypeScript compiler (tsc) is not installed or not in PATH")
                    return results
                
                # Run tsc on the codebase
                repo_path = self.codebase.ctx.repo_path
                cmd = ["tsc", "--noEmit", "--pretty", "false", "--project", repo_path]
                process = subprocess.run(cmd, capture_output=True, text=True)
                
                # Parse tsc output
                if process.returncode != 0:
                    error_lines = process.stdout.strip().split("\n")
                    type_issues = []
                    
                    for line in error_lines:
                        if line and ":" in line and "error TS" in line:
                            # Parse TypeScript error format: file(line,col): error TSxxxx: message
                            match = re.match(r"(.+)\((\d+),(\d+)\): error (TS\d+): (.+)", line)
                            if match:
                                file_path, line_num, col_num, error_code, error_msg = match.groups()
                                type_issues.append({
                                    "file": file_path,
                                    "line": int(line_num),
                                    "column": int(col_num),
                                    "message": error_msg.strip(),
                                    "error_code": error_code
                                })
                    
                    results["type_issues"] = type_issues
                    
                    # Generate summary
                    error_types = {}
                    for issue in type_issues:
                        error_code = issue.get("error_code", "unknown")
                        if error_code in error_types:
                            error_types[error_code] += 1
                        else:
                            error_types[error_code] = 1
                    
                    results["summary"] = {
                        "total_issues": len(type_issues),
                        "error_types": error_types
                    }
                
                results["success"] = True
            else:
                results["errors"].append(f"Unsupported type checker: {checker}. Supported checkers are 'mypy' and 'tsc'.")
        
        except Exception as e:
            results["errors"].append(str(e))
        
        return results
