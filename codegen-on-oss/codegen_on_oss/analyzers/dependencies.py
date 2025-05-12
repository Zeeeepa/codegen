#!/usr/bin/env python3
"""
Dependency Analysis Module

This module provides comprehensive analysis of codebase dependencies, including
import relationships, circular dependencies, module coupling, and external
dependencies analysis.
"""

import logging
import sys
from dataclasses import dataclass, field
from typing import Any

import networkx as nx

try:
    from codegen.sdk.core.codebase import Codebase
    from codegen.sdk.core.file import SourceFile
    from codegen.sdk.core.function import Function
    from codegen.sdk.core.symbol import Symbol
    from codegen.sdk.enums import EdgeType, SymbolType

    from codegen_on_oss.analyzers.codebase_context import CodebaseContext

    # Import from our own modules
    from codegen_on_oss.analyzers.issues import (
        CodeLocation,
        Issue,
        IssueCategory,
        IssueCollection,
        IssueSeverity,
    )
    from codegen_on_oss.analyzers.models.analysis_result import (
        AnalysisResult,
        DependencyResult,
    )
except ImportError:
    print("Codegen SDK or required modules not found.")
    sys.exit(1)

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class ImportDependency:
    """Represents an import dependency between files or modules."""

    source: str
    target: str
    import_name: str | None = None
    is_external: bool = False
    is_relative: bool = False
    line_number: int | None = None


@dataclass
class ModuleDependency:
    """Represents a dependency between modules."""

    source_module: str
    target_module: str
    imports_count: int = 1
    is_circular: bool = False


@dataclass
class CircularDependency:
    """Represents a circular dependency in the codebase."""

    files: list[str]
    modules: list[str]
    length: int
    cycle_type: str = "import"  # Either "import" or "function_call"


@dataclass
class ModuleCoupling:
    """Represents coupling metrics for a module."""

    module: str
    file_count: int
    imported_modules: list[str]
    import_count: int
    coupling_ratio: float
    exported_symbols: list[str] = field(default_factory=list)


@dataclass
class ExternalDependency:
    """Represents an external dependency."""

    module_name: str
    usage_count: int
    importing_files: list[str] = field(default_factory=list)
    imported_symbols: list[str] = field(default_factory=list)


class DependencyAnalyzer:
    """
    Analyzer for codebase dependencies.

    This analyzer provides comprehensive dependency analysis, including:
    1. Import dependencies analysis
    2. Circular dependencies detection
    3. Module coupling analysis
    4. External dependencies analysis
    5. Call graph analysis
    """

    def __init__(
        self,
        codebase: Codebase | None = None,
        context: CodebaseContext | None = None,
        issue_collection: IssueCollection | None = None,
    ):
        """
        Initialize the DependencyAnalyzer.

        Args:
            codebase: Codebase instance to analyze
            context: CodebaseContext for advanced graph analysis
            issue_collection: Collection to store detected issues
        """
        self.codebase = codebase
        self.context = context
        self.issues = issue_collection or IssueCollection()

        # Analysis results
        self.import_dependencies: list[ImportDependency] = []
        self.module_dependencies: list[ModuleDependency] = []
        self.circular_dependencies: list[CircularDependency] = []
        self.module_coupling: dict[str, ModuleCoupling] = {}
        self.external_dependencies: dict[str, ExternalDependency] = {}

        # Analysis graphs
        self.import_graph = nx.DiGraph()
        self.module_graph = nx.DiGraph()
        self.call_graph = nx.DiGraph()
        self.class_hierarchy_graph = nx.DiGraph()

        # Initialize context if needed
        if self.codebase and not self.context:
            try:
                self.context = CodebaseContext(codebase=self.codebase)
            except Exception as e:
                logger.exception(f"Error initializing context: {e}")

    def analyze(self) -> DependencyResult:
        """
        Perform comprehensive dependency analysis on the codebase.

        Returns:
            DependencyResult containing all dependency analysis results
        """
        # Reset results
        self.import_dependencies = []
        self.module_dependencies = []
        self.circular_dependencies = []
        self.module_coupling = {}
        self.external_dependencies = {}

        # Initialize graphs
        self.import_graph = nx.DiGraph()
        self.module_graph = nx.DiGraph()
        self.call_graph = nx.DiGraph()
        self.class_hierarchy_graph = nx.DiGraph()

        # Perform analysis
        self._analyze_import_dependencies()
        self._find_circular_dependencies()
        self._analyze_module_coupling()
        self._analyze_external_dependencies()
        self._analyze_call_graph()
        self._analyze_class_hierarchy()

        # Return structured results
        return self._create_result()

    def _create_result(self) -> DependencyResult:
        """Create a structured result object from the analysis results."""
        # Organize import dependencies
        import_deps = {
            "file_dependencies": [
                {
                    "source_file": dep.source,
                    "target_file": dep.target,
                    "import_name": dep.import_name,
                    "is_external": dep.is_external,
                    "is_relative": dep.is_relative,
                    "line_number": dep.line_number,
                }
                for dep in self.import_dependencies
            ],
            "module_dependencies": [
                {
                    "source_module": dep.source_module,
                    "target_module": dep.target_module,
                    "imports_count": dep.imports_count,
                    "is_circular": dep.is_circular,
                }
                for dep in self.module_dependencies
            ],
            "stats": {
                "total_imports": len(self.import_dependencies),
                "internal_imports": sum(
                    1 for dep in self.import_dependencies if not dep.is_external
                ),
                "external_imports": sum(
                    1 for dep in self.import_dependencies if dep.is_external
                ),
                "relative_imports": sum(
                    1 for dep in self.import_dependencies if dep.is_relative
                ),
            },
        }

        # Organize circular dependencies
        circular_deps = {
            "circular_imports": [
                {
                    "files": dep.files,
                    "modules": dep.modules,
                    "length": dep.length,
                    "cycle_type": dep.cycle_type,
                }
                for dep in self.circular_dependencies
            ],
            "circular_dependencies_count": len(self.circular_dependencies),
            "affected_modules": list(
                {
                    module
                    for dep in self.circular_dependencies
                    for module in dep.modules
                }
            ),
        }

        # Organize module coupling
        coupling = {
            "high_coupling_modules": [
                {
                    "module": module,
                    "coupling_ratio": data.coupling_ratio,
                    "import_count": data.import_count,
                    "file_count": data.file_count,
                    "imported_modules": data.imported_modules,
                }
                for module, data in self.module_coupling.items()
                if data.coupling_ratio > 3  # Threshold for high coupling
            ],
            "low_coupling_modules": [
                {
                    "module": module,
                    "coupling_ratio": data.coupling_ratio,
                    "import_count": data.import_count,
                    "file_count": data.file_count,
                    "imported_modules": data.imported_modules,
                }
                for module, data in self.module_coupling.items()
                if data.coupling_ratio < 0.5
                and data.file_count > 1  # Threshold for low coupling
            ],
            "average_coupling": (
                sum(data.coupling_ratio for data in self.module_coupling.values())
                / len(self.module_coupling)
                if self.module_coupling
                else 0
            ),
        }

        # Organize external dependencies
        external_deps = {
            "external_modules": list(self.external_dependencies.keys()),
            "most_used_external_modules": [
                {
                    "module": module,
                    "usage_count": data.usage_count,
                    "importing_files": data.importing_files[:10],  # Limit to 10 files
                }
                for module, data in sorted(
                    self.external_dependencies.items(),
                    key=lambda x: x[1].usage_count,
                    reverse=True,
                )[:10]  # Top 10 most used
            ],
            "total_external_modules": len(self.external_dependencies),
        }

        # Create result object
        return DependencyResult(
            import_dependencies=import_deps,
            circular_dependencies=circular_deps,
            module_coupling=coupling,
            external_dependencies=external_deps,
            call_graph=self._export_call_graph(),
            class_hierarchy=self._export_class_hierarchy(),
        )

    def _analyze_import_dependencies(self) -> None:
        """Analyze import dependencies in the codebase."""
        if not self.codebase:
            logger.error("Codebase not initialized")
            return

        # Process all files to extract import information
        for file in self.codebase.files:
            # Skip if no imports
            if not hasattr(file, "imports") or not file.imports:
                continue

            # Get file path
            file_path = str(
                file.file_path
                if hasattr(file, "file_path")
                else file.path
                if hasattr(file, "path")
                else file
            )

            # Extract module name from file path
            file_parts = file_path.split("/")
            module_name = (
                "/".join(file_parts[:-1]) if len(file_parts) > 1 else file_parts[0]
            )

            # Initialize module info in module graph
            if not self.module_graph.has_node(module_name):
                self.module_graph.add_node(module_name, files={file_path})
            else:
                self.module_graph.nodes[module_name]["files"].add(file_path)

            # Process imports
            for imp in file.imports:
                # Get import information
                import_name = imp.name if hasattr(imp, "name") else "unknown"
                line_number = imp.line if hasattr(imp, "line") else None
                is_relative = hasattr(imp, "is_relative") and imp.is_relative

                # Try to get imported file
                imported_file = None
                if hasattr(imp, "resolved_file"):
                    imported_file = imp.resolved_file
                elif hasattr(imp, "resolved_symbol") and hasattr(
                    imp.resolved_symbol, "file"
                ):
                    imported_file = imp.resolved_symbol.file

                # Get imported file path and module
                if imported_file:
                    # Get imported file path
                    imported_path = str(
                        imported_file.file_path
                        if hasattr(imported_file, "file_path")
                        else imported_file.path
                        if hasattr(imported_file, "path")
                        else imported_file
                    )

                    # Extract imported module name
                    imported_parts = imported_path.split("/")
                    imported_module = (
                        "/".join(imported_parts[:-1])
                        if len(imported_parts) > 1
                        else imported_parts[0]
                    )

                    # Check if external
                    is_external = (
                        hasattr(imported_file, "is_external")
                        and imported_file.is_external
                    )

                    # Add to import dependencies
                    self.import_dependencies.append(
                        ImportDependency(
                            source=file_path,
                            target=imported_path,
                            import_name=import_name,
                            is_external=is_external,
                            is_relative=is_relative,
                            line_number=line_number,
                        )
                    )

                    # Add to import graph
                    self.import_graph.add_edge(
                        file_path,
                        imported_path,
                        name=import_name,
                        external=is_external,
                        relative=is_relative,
                    )

                    # Add to module graph
                    if not is_external:
                        # Initialize imported module if needed
                        if not self.module_graph.has_node(imported_module):
                            self.module_graph.add_node(
                                imported_module, files={imported_path}
                            )
                        else:
                            self.module_graph.nodes[imported_module]["files"].add(
                                imported_path
                            )

                        # Add module dependency
                        if module_name != imported_module:  # Skip self-imports
                            if self.module_graph.has_edge(module_name, imported_module):
                                # Increment count for existing edge
                                self.module_graph[module_name][imported_module][
                                    "count"
                                ] += 1
                            else:
                                # Add new edge
                                self.module_graph.add_edge(
                                    module_name, imported_module, count=1
                                )
                else:
                    # Handle external import that couldn't be resolved
                    # Extract module name from import
                    if hasattr(imp, "module_name") and imp.module_name:
                        external_module = imp.module_name
                        is_external = True

                        # Add to import dependencies
                        self.import_dependencies.append(
                            ImportDependency(
                                source=file_path,
                                target=external_module,
                                import_name=import_name,
                                is_external=True,
                                is_relative=is_relative,
                                line_number=line_number,
                            )
                        )

                        # Track external dependency
                        self._track_external_dependency(
                            external_module, file_path, import_name
                        )

        # Extract module dependencies from module graph
        for source, target, data in self.module_graph.edges(data=True):
            self.module_dependencies.append(
                ModuleDependency(
                    source_module=source,
                    target_module=target,
                    imports_count=data.get("count", 1),
                )
            )

    def _find_circular_dependencies(self) -> None:
        """Find circular dependencies in the codebase."""
        # Find circular dependencies at the file level
        try:
            file_cycles = list(nx.simple_cycles(self.import_graph))

            for cycle in file_cycles:
                if len(cycle) < 2:
                    continue

                # Get the modules involved in the cycle
                modules = []
                for file_path in cycle:
                    parts = file_path.split("/")
                    module = "/".join(parts[:-1]) if len(parts) > 1 else parts[0]
                    modules.append(module)

                # Create circular dependency
                circular_dep = CircularDependency(
                    files=cycle, modules=modules, length=len(cycle), cycle_type="import"
                )

                self.circular_dependencies.append(circular_dep)

                # Create issue for this circular dependency
                self.issues.add(
                    Issue(
                        message=f"Circular import dependency detected between {len(cycle)} files",
                        severity=IssueSeverity.ERROR,
                        category=IssueCategory.DEPENDENCY_CYCLE,
                        location=CodeLocation(file=cycle[0], line=None),
                        suggestion="Refactor the code to break the circular dependency, potentially by extracting shared code into a separate module",
                    )
                )

                # Mark modules as circular in module dependencies
                for i in range(len(modules)):
                    source = modules[i]
                    target = modules[(i + 1) % len(modules)]

                    for dep in self.module_dependencies:
                        if dep.source_module == source and dep.target_module == target:
                            dep.is_circular = True

        except Exception as e:
            logger.exception(f"Error finding circular dependencies: {e}")

        # Find circular dependencies at the module level
        try:
            module_cycles = list(nx.simple_cycles(self.module_graph))

            for cycle in module_cycles:
                if len(cycle) < 2:
                    continue

                # Find files for these modules
                files = []
                for module in cycle:
                    if (
                        self.module_graph.has_node(module)
                        and "files" in self.module_graph.nodes[module]
                    ):
                        module_files = self.module_graph.nodes[module]["files"]
                        if module_files:
                            files.append(next(iter(module_files)))  # Take first file

                # Only add if we haven't already found this cycle at the file level
                if not any(
                    set(cycle) == set(dep.modules) for dep in self.circular_dependencies
                ):
                    circular_dep = CircularDependency(
                        files=files,
                        modules=cycle,
                        length=len(cycle),
                        cycle_type="import",
                    )

                    self.circular_dependencies.append(circular_dep)

                    # Create issue for this circular dependency
                    self.issues.add(
                        Issue(
                            message=f"Circular dependency detected between modules: {', '.join(cycle)}",
                            severity=IssueSeverity.ERROR,
                            category=IssueCategory.DEPENDENCY_CYCLE,
                            location=CodeLocation(
                                file=files[0] if files else cycle[0], line=None
                            ),
                            suggestion="Refactor the code to break the circular dependency",
                        )
                    )

        except Exception as e:
            logger.exception(f"Error finding circular module dependencies: {e}")

        # If we have context, also find circular function call dependencies
        if self.context and hasattr(self.context, "_graph"):
            try:
                # Try to find function call cycles
                function_nodes = [
                    node for node in self.context.nodes if isinstance(node, Function)
                ]

                # Build function call graph
                call_graph = nx.DiGraph()

                for func in function_nodes:
                    call_graph.add_node(func)

                    # Add call edges
                    for _, target, data in self.context.out_edges(func, data=True):
                        if (
                            isinstance(target, Function)
                            and data.get("type") == EdgeType.CALLS
                        ):
                            call_graph.add_edge(func, target)

                # Find cycles
                func_cycles = list(nx.simple_cycles(call_graph))

                for cycle in func_cycles:
                    if len(cycle) < 2:
                        continue

                    # Get files and function names
                    files = []
                    function_names = []

                    for func in cycle:
                        function_names.append(
                            func.name if hasattr(func, "name") else str(func)
                        )
                        if hasattr(func, "file") and hasattr(func.file, "file_path"):
                            files.append(str(func.file.file_path))

                    # Get modules
                    modules = []
                    for file_path in files:
                        parts = file_path.split("/")
                        module = "/".join(parts[:-1]) if len(parts) > 1 else parts[0]
                        modules.append(module)

                    # Create circular dependency
                    circular_dep = CircularDependency(
                        files=files,
                        modules=modules,
                        length=len(cycle),
                        cycle_type="function_call",
                    )

                    self.circular_dependencies.append(circular_dep)

                    # Create issue for this circular dependency
                    self.issues.add(
                        Issue(
                            message=f"Circular function call dependency detected: {' -> '.join(function_names)}",
                            severity=IssueSeverity.ERROR
                            if len(cycle) > 2
                            else IssueSeverity.WARNING,
                            category=IssueCategory.DEPENDENCY_CYCLE,
                            location=CodeLocation(
                                file=files[0] if files else "unknown", line=None
                            ),
                            suggestion="Refactor the code to eliminate the circular function calls",
                        )
                    )

            except Exception as e:
                logger.exception(f"Error finding circular function call dependencies: {e}")

    def _analyze_module_coupling(self) -> None:
        """Analyze module coupling in the codebase."""
        # Use module graph to calculate coupling metrics
        for module in self.module_graph.nodes():
            # Get files in this module
            files = self.module_graph.nodes[module].get("files", set())
            file_count = len(files)

            # Get imported modules
            imported_modules = []
            for _, target in self.module_graph.out_edges(module):
                imported_modules.append(target)

            # Calculate metrics
            import_count = len(imported_modules)
            coupling_ratio = import_count / file_count if file_count > 0 else 0

            # Find exported symbols if we have the context
            exported_symbols = []
            if self.context:
                for file_path in files:
                    file = self.context.get_file(file_path)
                    if file and hasattr(file, "exports"):
                        for export in file.exports:
                            if hasattr(export, "name"):
                                exported_symbols.append(export.name)

            # Create module coupling data
            self.module_coupling[module] = ModuleCoupling(
                module=module,
                file_count=file_count,
                imported_modules=imported_modules,
                import_count=import_count,
                coupling_ratio=coupling_ratio,
                exported_symbols=exported_symbols,
            )

            # Check for high coupling
            if coupling_ratio > 3 and file_count > 1:  # Threshold for high coupling
                self.issues.add(
                    Issue(
                        message=f"High module coupling: {module} has a coupling ratio of {coupling_ratio:.2f}",
                        severity=IssueSeverity.WARNING,
                        category=IssueCategory.DEPENDENCY_CYCLE,
                        location=CodeLocation(
                            file=next(iter(files)) if files else module, line=None
                        ),
                        suggestion="Consider refactoring to reduce the number of dependencies",
                    )
                )

    def _analyze_external_dependencies(self) -> None:
        """Analyze external dependencies in the codebase."""
        # Collect external dependencies from import dependencies
        for dep in self.import_dependencies:
            if dep.is_external:
                external_name = dep.target
                import_name = dep.import_name
                file_path = dep.source

                self._track_external_dependency(external_name, file_path, import_name)

    def _track_external_dependency(
        self, module_name: str, file_path: str, import_name: str | None = None
    ) -> None:
        """Track an external dependency."""
        if module_name not in self.external_dependencies:
            self.external_dependencies[module_name] = ExternalDependency(
                module_name=module_name,
                usage_count=1,
                importing_files=[file_path],
                imported_symbols=[import_name] if import_name else [],
            )
        else:
            # Update existing dependency
            self.external_dependencies[module_name].usage_count += 1

            if file_path not in self.external_dependencies[module_name].importing_files:
                self.external_dependencies[module_name].importing_files.append(
                    file_path
                )

            if (
                import_name
                and import_name
                not in self.external_dependencies[module_name].imported_symbols
            ):
                self.external_dependencies[module_name].imported_symbols.append(
                    import_name
                )

    def _analyze_call_graph(self) -> None:
        """Analyze function call relationships."""
        # Skip if we don't have context
        if not self.context:
            return

        # Find all functions
        functions = [node for node in self.context.nodes if isinstance(node, Function)]

        # Build call graph
        for func in functions:
            func_name = func.name if hasattr(func, "name") else str(func)
            func_path = (
                str(func.file.file_path)
                if hasattr(func, "file") and hasattr(func.file, "file_path")
                else "unknown"
            )

            # Add node to call graph
            if not self.call_graph.has_node(func_name):
                self.call_graph.add_node(func_name, path=func_path, function=func)

            # Process outgoing calls
            if hasattr(func, "calls"):
                for call in func.calls:
                    called_func = None

                    # Try to resolve the call
                    if hasattr(call, "resolved_symbol") and call.resolved_symbol:
                        called_func = call.resolved_symbol
                    elif hasattr(call, "name"):
                        # Try to find by name
                        for other_func in functions:
                            if (
                                hasattr(other_func, "name")
                                and other_func.name == call.name
                            ):
                                called_func = other_func
                                break

                    if called_func:
                        called_name = (
                            called_func.name
                            if hasattr(called_func, "name")
                            else str(called_func)
                        )
                        called_path = (
                            str(called_func.file.file_path)
                            if hasattr(called_func, "file")
                            and hasattr(called_func.file, "file_path")
                            else "unknown"
                        )

                        # Add target node if needed
                        if not self.call_graph.has_node(called_name):
                            self.call_graph.add_node(
                                called_name, path=called_path, function=called_func
                            )

                        # Add edge to call graph
                        self.call_graph.add_edge(
                            func_name,
                            called_name,
                            source_path=func_path,
                            target_path=called_path,
                        )

            # Check for recursive calls
            if self.call_graph.has_edge(func_name, func_name):
                self.issues.add(
                    Issue(
                        message=f"Recursive function: {func_name}",
                        severity=IssueSeverity.INFO,
                        category=IssueCategory.DEPENDENCY_CYCLE,
                        location=CodeLocation(
                            file=func_path,
                            line=func.line if hasattr(func, "line") else None,
                        ),
                        symbol=func_name,
                    )
                )

        # Analyze call chains
        self._analyze_deep_call_chains()

    def _analyze_deep_call_chains(self) -> None:
        """Analyze deep call chains in the call graph."""
        # Find entry points (functions not called by others)
        entry_points = [
            node
            for node in self.call_graph.nodes()
            if self.call_graph.in_degree(node) == 0
        ]

        # Find leaf functions (functions that don't call others)
        leaf_functions = [
            node
            for node in self.call_graph.nodes()
            if self.call_graph.out_degree(node) == 0
        ]

        # Look for long paths
        long_chains = []

        for entry in entry_points:
            for leaf in leaf_functions:
                try:
                    if nx.has_path(self.call_graph, entry, leaf):
                        path = nx.shortest_path(self.call_graph, entry, leaf)

                        if len(path) > 5:  # Threshold for "deep" call chains
                            long_chains.append({
                                "entry_point": entry,
                                "length": len(path),
                                "path": path,
                            })

                            # Create issue for very deep call chains
                            if len(path) > 8:  # Threshold for concerning depth
                                entry_path = self.call_graph.nodes[entry].get(
                                    "path", "unknown"
                                )

                                self.issues.add(
                                    Issue(
                                        message=f"Deep call chain starting from {entry} ({len(path)} levels deep)",
                                        severity=IssueSeverity.WARNING,
                                        category=IssueCategory.COMPLEXITY,
                                        location=CodeLocation(
                                            file=entry_path, line=None
                                        ),
                                        suggestion="Consider refactoring to reduce call depth",
                                    )
                                )
                except nx.NetworkXNoPath:
                    pass

        # Sort chains by length
        long_chains.sort(key=lambda x: x["length"], reverse=True)

        # Store top 10 longest chains
        self.long_call_chains = long_chains[:10]

    def _analyze_class_hierarchy(self) -> None:
        """Analyze class inheritance hierarchy."""
        # Skip if we don't have context
        if not self.context:
            return

        # Find all classes
        classes = [node for node in self.context.nodes if isinstance(node, Class)]

        # Build inheritance graph
        for cls in classes:
            cls_name = cls.name if hasattr(cls, "name") else str(cls)
            cls_path = (
                str(cls.file.file_path)
                if hasattr(cls, "file") and hasattr(cls.file, "file_path")
                else "unknown"
            )

            # Add node to class graph
            if not self.class_hierarchy_graph.has_node(cls_name):
                self.class_hierarchy_graph.add_node(
                    cls_name, path=cls_path, class_obj=cls
                )

            # Process superclasses
            if hasattr(cls, "superclasses"):
                for superclass in cls.superclasses:
                    super_name = (
                        superclass.name
                        if hasattr(superclass, "name")
                        else str(superclass)
                    )
                    super_path = (
                        str(superclass.file.file_path)
                        if hasattr(superclass, "file")
                        and hasattr(superclass.file, "file_path")
                        else "unknown"
                    )

                    # Add superclass node if needed
                    if not self.class_hierarchy_graph.has_node(super_name):
                        self.class_hierarchy_graph.add_node(
                            super_name, path=super_path, class_obj=superclass
                        )

                    # Add inheritance edge
                    self.class_hierarchy_graph.add_edge(cls_name, super_name)

        # Check for deep inheritance
        for cls_name in self.class_hierarchy_graph.nodes():
            # Calculate inheritance depth
            depth = 0
            current = cls_name

            while self.class_hierarchy_graph.out_degree(current) > 0:
                depth += 1
                successors = list(self.class_hierarchy_graph.successors(current))
                if not successors:
                    break
                current = successors[0]  # Follow first superclass

            # Check if depth exceeds threshold
            if depth > 3:  # Threshold for deep inheritance
                cls_path = self.class_hierarchy_graph.nodes[cls_name].get(
                    "path", "unknown"
                )

                self.issues.add(
                    Issue(
                        message=f"Deep inheritance: {cls_name} has an inheritance depth of {depth}",
                        severity=IssueSeverity.WARNING,
                        category=IssueCategory.DEPENDENCY_CYCLE,
                        location=CodeLocation(file=cls_path, line=None),
                        suggestion="Consider using composition instead of deep inheritance",
                    )
                )

    def _export_call_graph(self) -> dict[str, Any]:
        """Export the call graph for the analysis result."""
        nodes = []
        edges = []

        # Add nodes
        for node in self.call_graph.nodes():
            node_data = self.call_graph.nodes[node]
            nodes.append({"id": node, "path": node_data.get("path", "unknown")})

        # Add edges
        for source, target in self.call_graph.edges():
            edge_data = self.call_graph.get_edge_data(source, target)
            edges.append({
                "source": source,
                "target": target,
                "source_path": edge_data.get("source_path", "unknown"),
                "target_path": edge_data.get("target_path", "unknown"),
            })

        # Find entry points and leaf functions
        entry_points = [
            node
            for node in self.call_graph.nodes()
            if self.call_graph.in_degree(node) == 0
        ]

        leaf_functions = [
            node
            for node in self.call_graph.nodes()
            if self.call_graph.out_degree(node) == 0
        ]

        return {
            "nodes": nodes,
            "edges": edges,
            "entry_points": entry_points,
            "leaf_functions": leaf_functions,
            "deep_call_chains": self.long_call_chains
            if hasattr(self, "long_call_chains")
            else [],
        }

    def _export_class_hierarchy(self) -> dict[str, Any]:
        """Export the class hierarchy for the analysis result."""
        nodes = []
        edges = []

        # Add nodes
        for node in self.class_hierarchy_graph.nodes():
            node_data = self.class_hierarchy_graph.nodes[node]
            nodes.append({"id": node, "path": node_data.get("path", "unknown")})

        # Add edges
        for source, target in self.class_hierarchy_graph.edges():
            edges.append({"source": source, "target": target})

        # Find root classes (no superclasses) and leaf classes (no subclasses)
        root_classes = [
            node
            for node in self.class_hierarchy_graph.nodes()
            if self.class_hierarchy_graph.out_degree(node) == 0
        ]

        leaf_classes = [
            node
            for node in self.class_hierarchy_graph.nodes()
            if self.class_hierarchy_graph.in_degree(node) == 0
        ]

        return {
            "nodes": nodes,
            "edges": edges,
            "root_classes": root_classes,
            "leaf_classes": leaf_classes,
        }
