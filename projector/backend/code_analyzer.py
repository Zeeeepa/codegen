import re
import os
import logging
import json
from collections import defaultdict

class CodeAnalyzer:
    """Analyzer for code repositories and files."""
    
    def __init__(self):
        """Initialize the code analyzer."""
        self.logger = logging.getLogger(__name__)
    
    def analyze_code_structure(self, files_content):
        """Analyze the structure of code files."""
        structure = {
            "classes": [],
            "functions": [],
            "imports": [],
            "dependencies": [],
            "language_stats": defaultdict(int),
            "complexity_metrics": {
                "avg_function_length": 0,
                "avg_class_length": 0,
                "max_nesting_depth": 0
            }
        }
        
        # Track metrics for averaging
        total_function_length = 0
        function_count = 0
        total_class_length = 0
        class_count = 0
        max_nesting = 0
        
        for file_path, content in files_content.items():
            file_ext = os.path.splitext(file_path)[1]
            file_size = len(content)
            
            # Update language stats
            structure["language_stats"][file_ext] += file_size
            
            # Analyze based on file type
            if file_ext == '.py':
                self._analyze_python_file(content, structure)
                # Update metrics
                py_functions = [f for f in structure["functions"] if f.get("file_path") == file_path]
                for func in py_functions:
                    total_function_length += func.get("line_count", 0)
                    function_count += 1
                    max_nesting = max(max_nesting, func.get("max_nesting", 0))
                
                py_classes = [c for c in structure["classes"] if c.get("file_path") == file_path]
                for cls in py_classes:
                    total_class_length += cls.get("line_count", 0)
                    class_count += 1
                
            elif file_ext in ['.js', '.ts']:
                self._analyze_js_file(content, structure, file_path)
                # Update metrics similarly for JS files
                js_functions = [f for f in structure["functions"] if f.get("file_path") == file_path]
                for func in js_functions:
                    total_function_length += func.get("line_count", 0)
                    function_count += 1
                    max_nesting = max(max_nesting, func.get("max_nesting", 0))
            
            # Add more language analyzers as needed
        
        # Calculate averages
        if function_count > 0:
            structure["complexity_metrics"]["avg_function_length"] = total_function_length / function_count
        if class_count > 0:
            structure["complexity_metrics"]["avg_class_length"] = total_class_length / class_count
        structure["complexity_metrics"]["max_nesting_depth"] = max_nesting
        
        return structure
    
    def _analyze_python_file(self, content, structure, file_path=None):
        """Analyze a Python file."""
        # Extract classes
        class_matches = re.finditer(r'class\s+(\w+)(?:\(([^)]+)\))?:', content)
        for match in class_matches:
            class_name = match.group(1)
            parent_class = match.group(2) if match.group(2) else None
            class_start = match.start()
            
            # Find the end of the class (next class or EOF)
            next_class = re.search(r'class\s+\w+(?:\([^)]+\))?:', content[class_start + 1:])
            class_end = next_class.start() + class_start + 1 if next_class else len(content)
            
            # Calculate line count
            class_content = content[class_start:class_end]
            line_count = class_content.count('\n') + 1
            
            structure["classes"].append({
                "name": class_name,
                "parent": parent_class,
                "file_path": file_path,
                "location": class_start,
                "line_count": line_count
            })
        
        # Extract functions
        function_matches = re.finditer(r'def\s+(\w+)\s*\(([^)]*)\):', content)
        for match in function_matches:
            function_name = match.group(1)
            arguments = match.group(2)
            function_start = match.start()
            
            # Find the end of the function (next function/class or EOF)
            next_func_or_class = re.search(r'(def|class)\s+\w+', content[function_start + 1:])
            function_end = next_func_or_class.start() + function_start + 1 if next_func_or_class else len(content)
            
            # Calculate line count and max nesting
            function_content = content[function_start:function_end]
            line_count = function_content.count('\n') + 1
            max_nesting = self._calculate_max_nesting(function_content)
            
            structure["functions"].append({
                "name": function_name,
                "arguments": arguments,
                "file_path": file_path,
                "location": function_start,
                "line_count": line_count,
                "max_nesting": max_nesting
            })
        
        # Extract imports
        import_matches = re.finditer(r'import\s+(\w+)|from\s+(\w+(?:\.\w+)*)\s+import', content)
        for match in import_matches:
            module = match.group(1) if match.group(1) else match.group(2)
            if module not in structure["imports"]:
                structure["imports"].append(module)
                structure["dependencies"].append(module)
    
    def _analyze_js_file(self, content, structure, file_path=None):
        """Analyze a JavaScript/TypeScript file."""
        # Extract classes (ES6 class syntax)
        class_matches = re.finditer(r'class\s+(\w+)(?:\s+extends\s+(\w+))?\s*{', content)
        for match in class_matches:
            class_name = match.group(1)
            parent_class = match.group(2) if match.group(2) else None
            class_start = match.start()
            
            # Find the end of the class (matching closing brace)
            brace_count = 1
            class_end = class_start + match.group(0).index('{') + 1
            
            while brace_count > 0 and class_end < len(content):
                if content[class_end] == '{':
                    brace_count += 1
                elif content[class_end] == '}':
                    brace_count -= 1
                class_end += 1
            
            # Calculate line count
            class_content = content[class_start:class_end]
            line_count = class_content.count('\n') + 1
            
            structure["classes"].append({
                "name": class_name,
                "parent": parent_class,
                "file_path": file_path,
                "location": class_start,
                "line_count": line_count
            })
        
        # Extract functions (multiple patterns for JS functions)
        # Regular function declarations
        func_patterns = [
            r'function\s+(\w+)\s*\(([^)]*)\)',  # function name(args)
            r'const\s+(\w+)\s*=\s*function\s*\(([^)]*)\)',  # const name = function(args)
            r'const\s+(\w+)\s*=\s*\(([^)]*)\)\s*=>'  # const name = (args) =>
        ]
        
        for pattern in func_patterns:
            function_matches = re.finditer(pattern, content)
            for match in function_matches:
                function_name = match.group(1)
                arguments = match.group(2)
                function_start = match.start()
                
                # Find the end of the function (for simple cases)
                # In a more robust implementation, we'd need to handle nested functions and scoping
                func_body_start = content.find('{', function_start)
                if func_body_start < 0:  # Arrow function with implicit return
                    next_semicolon = content.find(';', function_start)
                    next_line = content.find('\n', function_start)
                    function_end = min(x for x in [next_semicolon, next_line] if x > 0)
                else:
                    # Find matching closing brace
                    brace_count = 1
                    function_end = func_body_start + 1
                    
                    while brace_count > 0 and function_end < len(content):
                        if content[function_end] == '{':
                            brace_count += 1
                        elif content[function_end] == '}':
                            brace_count -= 1
                        function_end += 1
                
                # Calculate line count and max nesting
                function_content = content[function_start:function_end]
                line_count = function_content.count('\n') + 1
                max_nesting = self._calculate_max_nesting(function_content)
                
                structure["functions"].append({
                    "name": function_name,
                    "arguments": arguments,
                    "file_path": file_path,
                    "location": function_start,
                    "line_count": line_count,
                    "max_nesting": max_nesting
                })
        
        # Extract imports (ES6 style)
        import_matches = re.finditer(r'import\s+.*?from\s+[\'"]([^\'"]+)[\'"]', content)
        for match in import_matches:
            module = match.group(1)
            if module not in structure["imports"]:
                structure["imports"].append(module)
                structure["dependencies"].append(module)
    
    def _calculate_max_nesting(self, content):
        """Calculate the maximum nesting depth in code."""
        lines = content.split('\n')
        max_depth = 0
        current_depth = 0
        
        for line in lines:
            stripped = line.strip()
            
            # Check for control structures that increase nesting
            if re.search(r'(if|for|while|def|class)\s+.*:$', stripped) or stripped.endswith('{'):
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            
            # Check for closing braces or blocks
            if stripped == '}' or stripped.startswith('return ') or stripped.startswith('break '):
                current_depth = max(0, current_depth - 1)
            
        return max_depth
    
    def suggest_improvements(self, code_structure):
        """Suggest improvements based on code structure analysis."""
        suggestions = []
        
        # Check for classes without parent classes (potential for inheritance)
        standalone_classes = [c for c in code_structure["classes"] if not c["parent"]]
        if len(standalone_classes) > 3:
            suggestions.append("Consider using inheritance for similar standalone classes")
        
        # Check for large functions
        large_functions = [f for f in code_structure["functions"] if f["line_count"] > 50]
        if large_functions:
            suggestions.append(f"Consider refactoring {len(large_functions)} large functions (>50 lines)")
        
        # Check for high nesting depth
        deep_nesting = [f for f in code_structure["functions"] if f.get("max_nesting", 0) > 4]
        if deep_nesting:
            suggestions.append(f"Reduce nesting depth in {len(deep_nesting)} functions (>4 levels deep)")
        
        # Check for common dependencies
        common_deps = set()
        for dep in code_structure["dependencies"]:
            if code_structure["dependencies"].count(dep) > 3:
                common_deps.add(dep)
        
        if common_deps:
            suggestions.append(f"Consider creating utility modules for commonly used dependencies: {', '.join(common_deps)}")
        
        return suggestions
    
    def generate_class_diagram(self, code_structure):
        """Generate a class diagram based on code structure."""
        mermaid_diagram = "classDiagram\n"
        
        # Add classes
        for cls in code_structure["classes"]:
            mermaid_diagram += f"    class {cls['name']}\n"
        
        # Add relationships
        for cls in code_structure["classes"]:
            if cls["parent"]:
                parent_classes = cls["parent"].split(',')
                for parent in parent_classes:
                    parent = parent.strip()
                    mermaid_diagram += f"    {parent} <|-- {cls['name']}\n"
        
        return mermaid_diagram
    
    def analyze_repository_statistics(self, files_content):
        """Generate statistics for the repository."""
        stats = {
            "total_files": len(files_content),
            "total_lines": sum(content.count('\n') + 1 for content in files_content.values()),
            "language_breakdown": {},
            "file_sizes": {},
            "complexity_score": 0
        }
        
        # Analyze language breakdown
        for file_path, content in files_content.items():
            ext = os.path.splitext(file_path)[1]
            if ext not in stats["language_breakdown"]:
                stats["language_breakdown"][ext] = 0
            stats["language_breakdown"][ext] += 1
            
            # File sizes
            size = len(content)
            size_category = "small" if size < 5000 else "medium" if size < 20000 else "large"
            if size_category not in stats["file_sizes"]:
                stats["file_sizes"][size_category] = 0
            stats["file_sizes"][size_category] += 1
        
        # Calculate a simple complexity score
        structure = self.analyze_code_structure(files_content)
        avg_function_length = structure["complexity_metrics"]["avg_function_length"]
        max_nesting = structure["complexity_metrics"]["max_nesting_depth"]
        
        # Simple complexity formula
        stats["complexity_score"] = (avg_function_length / 10) + (max_nesting * 5)
        
        return stats
