"""
Dependency Analyzer for Codegen-on-OSS

This module provides a dependency analyzer that analyzes dependencies between
symbols in a codebase, such as function calls, class inheritance, and imports.
"""

import logging
import os
import re
from typing import Dict, List, Optional, Any, Union, Set, Tuple

from codegen import Codebase
from codegen.sdk.core.file import SourceFile
from codegen.sdk.core.function import Function
from codegen.sdk.core.class_definition import Class
from codegen.sdk.core.symbol import Symbol

from codegen_on_oss.database import (
    get_db_session, FileRepository, SymbolRepository
)
from codegen_on_oss.analysis.coordinator import AnalysisContext

logger = logging.getLogger(__name__)

class DependencyAnalyzer:
    """
    Dependency analyzer for analyzing dependencies between symbols.
    
    This class analyzes dependencies between symbols in a codebase,
    such as function calls, class inheritance, and imports.
    """
    
    def __init__(self):
        """Initialize the dependency analyzer."""
        self.file_repo = FileRepository()
        self.symbol_repo = SymbolRepository()
    
    async def analyze(self, context: AnalysisContext) -> Dict[str, Any]:
        """
        Analyze dependencies in a codebase.
        
        Args:
            context: The analysis context.
            
        Returns:
            Dependency analysis results.
        """
        logger.info(f"Analyzing dependencies for repository: {context.repo_url}")
        
        codebase = context.codebase
        
        # Get all symbols
        symbols = {}
        for file_path in codebase.get_all_file_paths():
            try:
                source_file = codebase.get_source_file(file_path)
                
                # Skip non-source files
                if not source_file or not source_file.content:
                    continue
                
                # Extract functions
                for function in source_file.get_functions():
                    symbol_id = f"{file_path}:{function.name}:{function.start_line}"
                    symbols[symbol_id] = {
                        "name": function.name,
                        "qualified_name": function.qualified_name,
                        "type": "function",
                        "file_path": file_path,
                        "content": function.content
                    }
                
                # Extract classes
                for class_def in source_file.get_classes():
                    symbol_id = f"{file_path}:{class_def.name}:{class_def.start_line}"
                    symbols[symbol_id] = {
                        "name": class_def.name,
                        "qualified_name": class_def.qualified_name,
                        "type": "class",
                        "file_path": file_path,
                        "content": class_def.content
                    }
            except Exception as e:
                logger.warning(f"Error extracting symbols from {file_path}: {e}")
                continue
        
        # Analyze dependencies
        dependencies = []
        for symbol_id, symbol_data in symbols.items():
            # Analyze imports
            if symbol_data["file_path"].endswith(".py"):
                imports = await self._analyze_python_imports(context, symbol_data["file_path"])
                for import_name in imports:
                    # Find target symbol
                    for target_id, target_data in symbols.items():
                        if target_data["name"] == import_name or target_data["qualified_name"].endswith(f".{import_name}"):
                            dependencies.append({
                                "source": symbol_id,
                                "target": target_id,
                                "type": "import"
                            })
                            
                            # Add dependency to context
                            context.add_dependency(symbol_id, target_id)
            
            # Analyze function calls
            if symbol_data["type"] == "function":
                calls = await self._analyze_function_calls(context, symbol_data["content"], symbol_data["file_path"])
                for call_name in calls:
                    # Find target symbol
                    for target_id, target_data in symbols.items():
                        if target_data["name"] == call_name:
                            dependencies.append({
                                "source": symbol_id,
                                "target": target_id,
                                "type": "call"
                            })
                            
                            # Add dependency to context
                            context.add_dependency(symbol_id, target_id)
            
            # Analyze class inheritance
            if symbol_data["type"] == "class":
                inheritance = await self._analyze_class_inheritance(context, symbol_data["content"], symbol_data["file_path"])
                for parent_name in inheritance:
                    # Find target symbol
                    for target_id, target_data in symbols.items():
                        if target_data["name"] == parent_name:
                            dependencies.append({
                                "source": symbol_id,
                                "target": target_id,
                                "type": "inheritance"
                            })
                            
                            # Add dependency to context
                            context.add_dependency(symbol_id, target_id)
        
        # Store dependencies in database
        await self._store_dependencies(context)
        
        # Add results to context
        dependency_results = {
            "dependencies": dependencies,
            "symbol_count": len(symbols),
            "dependency_count": len(dependencies)
        }
        
        context.add_result("dependencies", dependency_results)
        
        return dependency_results
    
    async def _analyze_python_imports(self, context: AnalysisContext, file_path: str) -> List[str]:
        """
        Analyze Python imports in a file.
        
        Args:
            context: The analysis context.
            file_path: The file path.
            
        Returns:
            A list of imported names.
        """
        codebase = context.codebase
        source_file = codebase.get_source_file(file_path)
        
        if not source_file or not source_file.content:
            return []
        
        content = source_file.content
        imports = []
        
        # Match import statements
        import_patterns = [
            r"import\s+([a-zA-Z0-9_.,\s]+)",  # import module
            r"from\s+([a-zA-Z0-9_.]+)\s+import\s+([a-zA-Z0-9_.,\s*]+)"  # from module import name
        ]
        
        for pattern in import_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                if len(match.groups()) == 1:
                    # import module
                    modules = match.group(1).split(',')
                    for module in modules:
                        module = module.strip()
                        if module:
                            imports.append(module.split('.')[-1])
                elif len(match.groups()) == 2:
                    # from module import name
                    names = match.group(2).split(',')
                    for name in names:
                        name = name.strip()
                        if name and name != '*':
                            imports.append(name)
        
        return imports
    
    async def _analyze_function_calls(self, context: AnalysisContext, content: str, file_path: str) -> List[str]:
        """
        Analyze function calls in a function.
        
        Args:
            context: The analysis context.
            content: The function content.
            file_path: The file path.
            
        Returns:
            A list of called function names.
        """
        calls = []
        
        # Match function calls based on file extension
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.py':
            # Python function calls
            pattern = r"([a-zA-Z0-9_]+)\s*\("
            matches = re.finditer(pattern, content)
            for match in matches:
                call_name = match.group(1)
                if call_name and call_name not in ['if', 'for', 'while', 'def', 'class']:
                    calls.append(call_name)
        
        elif ext in ['.js', '.jsx', '.ts', '.tsx']:
            # JavaScript/TypeScript function calls
            pattern = r"([a-zA-Z0-9_$.]+)\s*\("
            matches = re.finditer(pattern, content)
            for match in matches:
                call_name = match.group(1)
                if call_name and call_name not in ['if', 'for', 'while', 'function', 'class']:
                    calls.append(call_name.split('.')[-1])
        
        elif ext in ['.java', '.kt']:
            # Java/Kotlin function calls
            pattern = r"([a-zA-Z0-9_]+)\s*\("
            matches = re.finditer(pattern, content)
            for match in matches:
                call_name = match.group(1)
                if call_name and call_name not in ['if', 'for', 'while', 'switch']:
                    calls.append(call_name)
        
        return calls
    
    async def _analyze_class_inheritance(self, context: AnalysisContext, content: str, file_path: str) -> List[str]:
        """
        Analyze class inheritance in a class.
        
        Args:
            context: The analysis context.
            content: The class content.
            file_path: The file path.
            
        Returns:
            A list of parent class names.
        """
        inheritance = []
        
        # Match class inheritance based on file extension
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.py':
            # Python class inheritance
            pattern = r"class\s+[a-zA-Z0-9_]+\s*\(\s*([a-zA-Z0-9_.,\s]+)\s*\)"
            match = re.search(pattern, content)
            if match:
                parents = match.group(1).split(',')
                for parent in parents:
                    parent = parent.strip()
                    if parent:
                        inheritance.append(parent)
        
        elif ext in ['.java', '.kt']:
            # Java/Kotlin class inheritance
            pattern = r"class\s+[a-zA-Z0-9_]+\s+extends\s+([a-zA-Z0-9_]+)"
            match = re.search(pattern, content)
            if match:
                inheritance.append(match.group(1))
            
            # Java/Kotlin interface implementation
            pattern = r"class\s+[a-zA-Z0-9_]+(?:\s+extends\s+[a-zA-Z0-9_]+)?\s+implements\s+([a-zA-Z0-9_,\s]+)"
            match = re.search(pattern, content)
            if match:
                interfaces = match.group(1).split(',')
                for interface in interfaces:
                    interface = interface.strip()
                    if interface:
                        inheritance.append(interface)
        
        elif ext in ['.js', '.jsx', '.ts', '.tsx']:
            # JavaScript/TypeScript class inheritance
            pattern = r"class\s+[a-zA-Z0-9_]+\s+extends\s+([a-zA-Z0-9_]+)"
            match = re.search(pattern, content)
            if match:
                inheritance.append(match.group(1))
        
        return inheritance
    
    async def _store_dependencies(self, context: AnalysisContext):
        """
        Store dependencies in the database.
        
        Args:
            context: The analysis context.
        """
        with get_db_session() as session:
            # Get all symbols from database
            symbols = {}
            for symbol_data in context.symbols:
                file = self.file_repo.get_by_path(session, context.commit_id, symbol_data["file_path"])
                if file:
                    symbol = self.symbol_repo.get_by_qualified_name(session, file.id, symbol_data["qualified_name"])
                    if symbol:
                        symbols[f"{symbol_data['file_path']}:{symbol_data['name']}:{symbol_data.get('line_start', 0)}"] = symbol
            
            # Store dependencies
            for source_id, target_id in context.dependencies:
                source_symbol = symbols.get(source_id)
                target_symbol = symbols.get(target_id)
                
                if source_symbol and target_symbol:
                    self.symbol_repo.add_dependency(session, source_symbol.id, target_symbol.id)
            
            session.commit()

