#!/usr/bin/env python3
"""
Dependency Analyzer Module

This module provides analysis of codebase dependencies, including
import relationships, circular dependencies, and module coupling.
"""

import os
import sys
import logging
import networkx as nx
from typing import Dict, List, Set, Tuple, Any, Optional, Union

from codegen_on_oss.analyzers.base_analyzer import BaseCodeAnalyzer
from codegen_on_oss.analyzers.issue_types import Issue, IssueSeverity, AnalysisType, IssueCategory

# Configure logging
logger = logging.getLogger(__name__)

class DependencyAnalyzer(BaseCodeAnalyzer):
    """
    Analyzer for codebase dependencies.
    
    This analyzer detects issues related to dependencies, including
    import relationships, circular dependencies, and module coupling.
    """
    
    def analyze(self, analysis_type: AnalysisType = AnalysisType.DEPENDENCY) -> Dict[str, Any]:
        """
        Perform dependency analysis on the codebase.
        
        Args:
            analysis_type: Type of analysis to perform
            
        Returns:
            Dictionary containing analysis results
        """
        if not self.base_codebase:
            raise ValueError("Codebase not initialized")
            
        result = {
            "metadata": {
                "analysis_time": str(datetime.now()),
                "analysis_type": analysis_type,
                "repo_name": getattr(self.base_codebase.ctx, 'repo_name', None),
                "language": str(getattr(self.base_codebase.ctx, 'programming_language', None)),
            },
            "summary": {},
        }
        
        # Reset issues list
        self.issues = []
        
        # Perform appropriate analysis based on type
        if analysis_type == AnalysisType.DEPENDENCY:
            # Run all dependency checks
            result["import_dependencies"] = self._analyze_import_dependencies()
            result["circular_dependencies"] = self._find_circular_dependencies()
            result["module_coupling"] = self._analyze_module_coupling()
            result["external_dependencies"] = self._analyze_external_dependencies()
            
        # Add issues to the result
        result["issues"] = [issue.to_dict() for issue in self.issues]
        result["issue_counts"] = {
            "total": len(self.issues),
            "by_severity": {
                "critical": sum(1 for issue in self.issues if issue.severity == IssueSeverity.CRITICAL),
                "error": sum(1 for issue in self.issues if issue.severity == IssueSeverity.ERROR),
                "warning": sum(1 for issue in self.issues if issue.severity == IssueSeverity.WARNING),
                "info": sum(1 for issue in self.issues if issue.severity == IssueSeverity.INFO),
            },
            "by_category": {
                category.value: sum(1 for issue in self.issues if issue.category == category)
                for category in IssueCategory
                if any(issue.category == category for issue in self.issues)
            }
        }
        
        # Store results
        self.results = result
        
        return result
    
    def _analyze_import_dependencies(self) -> Dict[str, Any]:
        """
        Analyze import dependencies in the codebase.
        
        Returns:
            Dictionary containing import dependencies analysis results
        """
        import_deps = {
            "module_dependencies": [],
            "file_dependencies": [],
            "most_imported_modules": [],
            "most_importing_modules": [],
            "dependency_stats": {
                "total_imports": 0,
                "internal_imports": 0,
                "external_imports": 0,
                "relative_imports": 0
            }
        }
        
        # Create a directed graph for module dependencies
        G = nx.DiGraph()
        
        # Track import counts
        module_imports = {}  # modules importing others
        module_imported = {}  # modules being imported
        
        # Process all files to extract import information
        for file in self.base_codebase.files:
            # Skip if no imports
            if not hasattr(file, 'imports') or not file.imports:
                continue
            
            # Get file path
            file_path = file.filepath if hasattr(file, 'filepath') else str(file.path) if hasattr(file, 'path') else str(file)
            
            # Extract module name from file path
            file_parts = file_path.split('/')
            module_name = '/'.join(file_parts[:-1]) if len(file_parts) > 1 else file_parts[0]
            
            # Initialize import counts
            if module_name not in module_imports:
                module_imports[module_name] = 0
            
            # Process imports
            for imp in file.imports:
                import_deps["dependency_stats"]["total_imports"] += 1
                
                # Get imported module information
                imported_file = None
                imported_module = "unknown"
                is_external = False
                
                if hasattr(imp, 'resolved_file'):
                    imported_file = imp.resolved_file
                elif hasattr(imp, 'resolved_symbol') and hasattr(imp.resolved_symbol, 'file'):
                    imported_file = imp.resolved_symbol.file
                
                if imported_file:
                    # Get imported file path
                    imported_path = imported_file.filepath if hasattr(imported_file, 'filepath') else str(imported_file.path) if hasattr(imported_file, 'path') else str(imported_file)
                    
                    # Extract imported module name
                    imported_parts = imported_path.split('/')
                    imported_module = '/'.join(imported_parts[:-1]) if len(imported_parts) > 1 else imported_parts[0]
                    
                    # Check if external
                    is_external = hasattr(imported_file, 'is_external') and imported_file.is_external
                else:
                    # If we couldn't resolve the import, use the import name
                    imported_module = imp.name if hasattr(imp, 'name') else "unknown"
                    
                    # Assume external if we couldn't resolve
                    is_external = True
                
                # Update import type counts
                if is_external:
                    import_deps["dependency_stats"]["external_imports"] += 1
                else:
                    import_deps["dependency_stats"]["internal_imports"] += 1
                    
                    # Check if relative import
                    if hasattr(imp, 'is_relative') and imp.is_relative:
                        import_deps["dependency_stats"]["relative_imports"] += 1
                
                # Update module import counts
                module_imports[module_name] += 1
                
                if imported_module not in module_imported:
                    module_imported[imported_module] = 0
                module_imported[imported_module] += 1
                
                # Add to dependency graph
                if module_name != imported_module:  # Skip self-imports
                    G.add_edge(module_name, imported_module)
                    
                    # Add to file dependencies list
                    import_deps["file_dependencies"].append({
                        "source_file": file_path,
                        "target_file": imported_path if imported_file else "unknown",
                        "import_name": imp.name if hasattr(imp, 'name') else "unknown",
                        "is_external": is_external
                    })
        
        # Extract module dependencies from graph
        for source, target in G.edges():
            import_deps["module_dependencies"].append({
                "source_module": source,
                "target_module": target
            })
        
        # Find most imported modules
        most_imported = sorted(
            [(module, count) for module, count in module_imported.items()],
            key=lambda x: x[1],
            reverse=True
        )
        
        for module, count in most_imported[:10]:  # Top 10
            import_deps["most_imported_modules"].append({
                "module": module,
                "import_count": count
            })
        
        # Find modules that import the most
        most_importing = sorted(
            [(module, count) for module, count in module_imports.items()],
            key=lambda x: x[1],
            reverse=True
        )
        
        for module, count in most_importing[:10]:  # Top 10
            import_deps["most_importing_modules"].append({
                "module": module,
                "import_count": count
            })
        
        return import_deps
    
    def _find_circular_dependencies(self) -> Dict[str, Any]:
        """
        Find circular dependencies in the codebase.
        
        Returns:
            Dictionary containing circular dependencies analysis results
        """
        circular_deps = {
            "circular_imports": [],
            "circular_dependencies_count": 0,
            "affected_modules": set()
        }
        
        # Create dependency graph if not already available
        G = nx.DiGraph()
        
        # Process all files to build dependency graph
        for file in self.base_codebase.files:
            # Skip if no imports
            if not hasattr(file, 'imports') or not file.imports:
                continue
            
            # Get file path
            file_path = file.filepath if hasattr(file, 'filepath') else str(file.path) if hasattr(file, 'path') else str(file)
            
            # Process imports
            for imp in file.imports:
                # Get imported file
                imported_file = None
                
                if hasattr(imp, 'resolved_file'):
                    imported_file = imp.resolved_file
                elif hasattr(imp, 'resolved_symbol') and hasattr(imp.resolved_symbol, 'file'):
                    imported_file = imp.resolved_symbol.file
                
                if imported_file:
                    # Get imported file path
                    imported_path = imported_file.filepath if hasattr(imported_file, 'filepath') else str(imported_file.path) if hasattr(imported_file, 'path') else str(imported_file)
                    
                    # Add edge to graph
                    G.add_edge(file_path, imported_path)
        
        # Find cycles in the graph
        try:
            cycles = list(nx.simple_cycles(G))
            
            for cycle in cycles:
                circular_deps["circular_imports"].append({
                    "files": cycle,
                    "length": len(cycle)
                })
                
                # Add affected modules to set
                for file_path in cycle:
                    module_path = '/'.join(file_path.split('/')[:-1])
                    circular_deps["affected_modules"].add(module_path)
                
                # Add issue
                if len(cycle) >= 2:
                    self.add_issue(Issue(
                        file=cycle[0],
                        line=None,
                        message=f"Circular dependency detected between {len(cycle)} files",
                        severity=IssueSeverity.ERROR,
                        category=IssueCategory.DEPENDENCY_CYCLE,
                        suggestion="Break the circular dependency by refactoring the code"
                    ))
        
        except Exception as e:
            logger.error(f"Error finding circular dependencies: {e}")
        
        # Update cycle count
        circular_deps["circular_dependencies_count"] = len(circular_deps["circular_imports"])
        circular_deps["affected_modules"] = list(circular_deps["affected_modules"])
        
        return circular_deps
    
    def _analyze_module_coupling(self) -> Dict[str, Any]:
        """
        Analyze module coupling in the codebase.
        
        Returns:
            Dictionary containing module coupling analysis results
        """
        coupling = {
            "high_coupling_modules": [],
            "low_coupling_modules": [],
            "coupling_metrics": {},
            "average_coupling": 0.0
        }
        
        # Create module dependency graphs
        modules = {}  # Module name -> set of imported modules
        module_files = {}  # Module name -> list of files
        
        # Process all files to extract module information
        for file in self.base_codebase.files:
            # Get file path
            file_path = file.filepath if hasattr(file, 'filepath') else str(file.path) if hasattr(file, 'path') else str(file)
            
            # Extract module name from file path
            module_parts = file_path.split('/')
            module_name = '/'.join(module_parts[:-1]) if len(module_parts) > 1 else module_parts[0]
            
            # Initialize module structures
            if module_name not in modules:
                modules[module_name] = set()
                module_files[module_name] = []
            
            module_files[module_name].append(file_path)
            
            # Skip if no imports
            if not hasattr(file, 'imports') or not file.imports:
                continue
            
            # Process imports
            for imp in file.imports:
                # Get imported file
                imported_file = None
                
                if hasattr(imp, 'resolved_file'):
                    imported_file = imp.resolved_file
                elif hasattr(imp, 'resolved_symbol') and hasattr(imp.resolved_symbol, 'file'):
                    imported_file = imp.resolved_symbol.file
                
                if imported_file:
                    # Get imported file path
                    imported_path = imported_file.filepath if hasattr(imported_file, 'filepath') else str(imported_file.path) if hasattr(imported_file, 'path') else str(imported_file)
                    
                    # Extract imported module name
                    imported_parts = imported_path.split('/')
                    imported_module = '/'.join(imported_parts[:-1]) if len(imported_parts) > 1 else imported_parts[0]
                    
                    # Skip self-imports
                    if imported_module != module_name:
                        modules[module_name].add(imported_module)
        
        # Calculate coupling metrics for each module
        total_coupling = 0.0
        module_count = 0
        
        for module_name, imported_modules in modules.items():
            # Calculate metrics
            file_count = len(module_files[module_name])
            import_count = len(imported_modules)
            
            # Calculate coupling ratio (imports per file)
            coupling_ratio = import_count / file_count if file_count > 0 else 0
            
            # Add to metrics
            coupling["coupling_metrics"][module_name] = {
                "files": file_count,
                "imported_modules": list(imported_modules),
                "import_count": import_count,
                "coupling_ratio": coupling_ratio
            }
            
            # Track total for average
            total_coupling += coupling_ratio
            module_count += 1
            
            # Categorize coupling
            if coupling_ratio > 3:  # Threshold for "high coupling"
                coupling["high_coupling_modules"].append({
                    "module": module_name,
                    "coupling_ratio": coupling_ratio,
                    "import_count": import_count,
                    "file_count": file_count
                })
                
                # Add issue
                self.add_issue(Issue(
                    file=module_files[module_name][0] if module_files[module_name] else module_name,
                    line=None,
                    message=f"High module coupling: {coupling_ratio:.2f} imports per file",
                    severity=IssueSeverity.WARNING,
                    category=IssueCategory.DEPENDENCY_CYCLE,
                    suggestion="Consider refactoring to reduce coupling between modules"
                ))
            elif coupling_ratio < 0.5 and file_count > 1:  # Threshold for "low coupling"
                coupling["low_coupling_modules"].append({
                    "module": module_name,
                    "coupling_ratio": coupling_ratio,
                    "import_count": import_count,
                    "file_count": file_count
                })
        
        # Calculate average coupling
        coupling["average_coupling"] = total_coupling / module_count if module_count > 0 else 0.0
        
        # Sort coupling lists
        coupling["high_coupling_modules"].sort(key=lambda x: x["coupling_ratio"], reverse=True)
        coupling["low_coupling_modules"].sort(key=lambda x: x["coupling_ratio"])
        
        return coupling
    
    def _analyze_external_dependencies(self) -> Dict[str, Any]:
        """
        Analyze external dependencies in the codebase.
        
        Returns:
            Dictionary containing external dependencies analysis results
        """
        external_deps = {
            "external_modules": [],
            "external_module_usage": {},
            "most_used_external_modules": []
        }
        
        # Track external module usage
        external_usage = {}  # Module name -> usage count
        
        # Process all imports to find external dependencies
        for file in self.base_codebase.files:
            # Skip if no imports
            if not hasattr(file, 'imports') or not file.imports:
                continue
            
            # Process imports
            for imp in file.imports:
                # Check if external import
                is_external = False
                external_name = None
                
                if hasattr(imp, 'module_name'):
                    external_name = imp.module_name
                    
                    # Check if this is an external module
                    if hasattr(imp, 'is_external'):
                        is_external = imp.is_external
                    elif external_name and '.' not in external_name and '/' not in external_name:
                        # Simple heuristic: single-word module names without dots or slashes
                        # are likely external modules
                        is_external = True
                
                if is_external and external_name:
                    # Add to external modules list if not already there
                    if external_name not in external_usage:
                        external_usage[external_name] = 0
                        external_deps["external_modules"].append(external_name)
                    
                    external_usage[external_name] += 1
        
        # Add usage counts
        for module, count in external_usage.items():
            external_deps["external_module_usage"][module] = count
        
        # Find most used external modules
        most_used = sorted(
            [(module, count) for module, count in external_usage.items()],
            key=lambda x: x[1],
            reverse=True
        )
        
        for module, count in most_used[:10]:  # Top 10
            external_deps["most_used_external_modules"].append({
                "module": module,
                "usage_count": count
            })
        
        return external_deps