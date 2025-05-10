"""
Symbol Import Analysis Module

This module provides functions for analyzing symbol imports in a codebase.
"""

import logging
from typing import Any, Dict, List, Optional
import networkx as nx

logger = logging.getLogger(__name__)

def get_symbol_import_analysis(codebase) -> Dict[str, Any]:
    """
    Analyze symbol imports in the codebase.
    
    This function analyzes how symbols are imported and used across the codebase,
    identifying patterns, potential issues, and optimization opportunities.
    
    Args:
        codebase: The codebase object to analyze
        
    Returns:
        Dict containing symbol import analysis results
    """
    import_analysis = {
        "import_patterns": [],
        "circular_imports": [],
        "unused_imports": [],
        "duplicate_imports": [],
        "import_statistics": {
            "total_imports": 0,
            "external_imports": 0,
            "internal_imports": 0,
            "relative_imports": 0,
            "star_imports": 0,
            "most_imported_modules": []
        },
        "import_recommendations": []
    }
    
    try:
        # Get all imports from the codebase
        all_imports = []
        import_counts = {}  # Count occurrences of each imported module
        
        for file in codebase.files:
            if hasattr(file, "imports"):
                all_imports.extend(file.imports)
                
                # Count imports by module
                for imp in file.imports:
                    if hasattr(imp, "module"):
                        module = imp.module
                        if module in import_counts:
                            import_counts[module] += 1
                        else:
                            import_counts[module] = 1
        
        # Calculate import statistics
        import_analysis["import_statistics"]["total_imports"] = len(all_imports)
        
        # Count different types of imports
        for imp in all_imports:
            # Check if it's an external or internal import
            if hasattr(imp, "module"):
                module = imp.module
                
                # External imports typically don't have a file path in the codebase
                is_external = True
                for file in codebase.files:
                    if hasattr(file, "module_name") and file.module_name == module:
                        is_external = False
                        break
                
                if is_external:
                    import_analysis["import_statistics"]["external_imports"] += 1
                else:
                    import_analysis["import_statistics"]["internal_imports"] += 1
                
                # Check for relative imports
                if module.startswith("."):
                    import_analysis["import_statistics"]["relative_imports"] += 1
                
                # Check for star imports
                if hasattr(imp, "is_star_import") and imp.is_star_import:
                    import_analysis["import_statistics"]["star_imports"] += 1
        
        # Get most imported modules
        most_imported = sorted(import_counts.items(), key=lambda x: x[1], reverse=True)[:10]  # Top 10
        import_analysis["import_statistics"]["most_imported_modules"] = [
            {"module": module, "count": count}
            for module, count in most_imported
        ]
        
        # Detect circular imports
        import_graph = nx.DiGraph()
        
        # Add nodes and edges for imports
        for file in codebase.files:
            if hasattr(file, "module_name") and file.module_name:
                import_graph.add_node(file.module_name)
                
                if hasattr(file, "imports"):
                    for imp in file.imports:
                        if hasattr(imp, "module") and imp.module:
                            # Skip external modules
                            is_internal = False
                            for other_file in codebase.files:
                                if hasattr(other_file, "module_name") and other_file.module_name == imp.module:
                                    is_internal = True
                                    break
                            
                            if is_internal:
                                import_graph.add_node(imp.module)
                                import_graph.add_edge(file.module_name, imp.module)
        
        # Find cycles in the import graph
        try:
            cycles = list(nx.simple_cycles(import_graph))
            import_analysis["circular_imports"] = [
                {
                    "modules": cycle,
                    "length": len(cycle)
                }
                for cycle in cycles
            ]
        except:
            # Simple cycles might not be available for all graph types
            import_analysis["circular_imports"] = []
        
        # Detect unused imports
        used_imports = set()
        
        # Check all function bodies for import usage
        for func in codebase.functions:
            for node in func.ast_node.walk():
                if hasattr(node, "value") and hasattr(node.value, "id"):
                    # This might be a reference to an imported symbol
                    symbol_name = node.value.id
                    
                    for imp in all_imports:
                        if hasattr(imp, "name") and imp.name == symbol_name:
                            used_imports.add(imp.id)
        
        # Find unused imports
        for imp in all_imports:
            if hasattr(imp, "id") and imp.id not in used_imports:
                # Skip imports that might be used for side effects
                if not (hasattr(imp, "is_side_effect_import") and imp.is_side_effect_import):
                    import_analysis["unused_imports"].append({
                        "name": imp.name if hasattr(imp, "name") else "Unknown",
                        "module": imp.module if hasattr(imp, "module") else "Unknown",
                        "file": imp.file.file_path if hasattr(imp, "file") else "Unknown",
                        "line": imp.line_number if hasattr(imp, "line_number") else 0
                    })
        
        # Detect duplicate imports
        import_map = {}  # Maps (file_path, module, name) to import objects
        
        for imp in all_imports:
            if hasattr(imp, "file") and hasattr(imp, "module") and hasattr(imp, "name"):
                key = (imp.file.file_path, imp.module, imp.name)
                
                if key in import_map:
                    # This is a duplicate import
                    import_analysis["duplicate_imports"].append({
                        "name": imp.name,
                        "module": imp.module,
                        "file": imp.file.file_path,
                        "lines": [
                            import_map[key].line_number if hasattr(import_map[key], "line_number") else 0,
                            imp.line_number if hasattr(imp, "line_number") else 0
                        ]
                    })
                else:
                    import_map[key] = imp
        
        # Identify import patterns
        import_patterns = {}
        
        for file in codebase.files:
            if hasattr(file, "imports"):
                # Group imports by module
                modules = {}
                
                for imp in file.imports:
                    if hasattr(imp, "module"):
                        module = imp.module
                        
                        if module in modules:
                            modules[module].append(imp)
                        else:
                            modules[module] = [imp]
                
                # Check for patterns
                for module, imports in modules.items():
                    if len(imports) > 3:
                        # This might be a candidate for a star import or a more concise import
                        import_patterns[module] = len(imports)
        
        # Convert patterns to list
        import_analysis["import_patterns"] = [
            {
                "module": module,
                "symbol_count": count,
                "recommendation": "Consider using 'from {} import *' or grouping imports" if count > 5 else "Consider grouping imports"
            }
            for module, count in sorted(import_patterns.items(), key=lambda x: x[1], reverse=True)
        ]
        
        # Generate recommendations
        recommendations = []
        
        # Recommend fixing circular imports
        if import_analysis["circular_imports"]:
            recommendations.append({
                "type": "circular_imports",
                "message": f"Fix {len(import_analysis['circular_imports'])} circular import cycles to improve code maintainability and reduce import time"
            })
        
        # Recommend removing unused imports
        if import_analysis["unused_imports"]:
            recommendations.append({
                "type": "unused_imports",
                "message": f"Remove {len(import_analysis['unused_imports'])} unused imports to improve code clarity and potentially reduce import time"
            })
        
        # Recommend fixing duplicate imports
        if import_analysis["duplicate_imports"]:
            recommendations.append({
                "type": "duplicate_imports",
                "message": f"Fix {len(import_analysis['duplicate_imports'])} duplicate imports to improve code clarity"
            })
        
        # Recommend optimizing import patterns
        if import_analysis["import_patterns"]:
            recommendations.append({
                "type": "import_patterns",
                "message": f"Optimize import patterns for {len(import_analysis['import_patterns'])} modules to make imports more concise"
            })
        
        import_analysis["import_recommendations"] = recommendations
        
        return import_analysis
    except Exception as e:
        logger.error(f"Error in symbol import analysis: {e}")
        return {"error": str(e)}

