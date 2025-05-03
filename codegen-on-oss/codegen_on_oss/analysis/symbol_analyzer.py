"""
Symbol Analyzer for Codegen-on-OSS

This module provides a symbol analyzer that analyzes symbols in a codebase,
such as functions, classes, and variables.
"""

import logging
import os
import hashlib
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

class SymbolAnalyzer:
    """
    Symbol analyzer for analyzing symbols in a codebase.
    
    This class analyzes symbols in a codebase, such as functions, classes,
    and variables, and extracts metadata about them.
    """
    
    def __init__(self):
        """Initialize the symbol analyzer."""
        self.file_repo = FileRepository()
        self.symbol_repo = SymbolRepository()
    
    async def analyze(self, context: AnalysisContext) -> Dict[str, Any]:
        """
        Analyze symbols in a codebase.
        
        Args:
            context: The analysis context.
            
        Returns:
            Symbol analysis results.
        """
        logger.info(f"Analyzing symbols for repository: {context.repo_url}")
        
        codebase = context.codebase
        
        # Analyze symbols
        symbols = {
            "functions": [],
            "classes": [],
            "variables": []
        }
        
        # Analyze files
        for file_path in codebase.get_all_file_paths():
            try:
                source_file = codebase.get_source_file(file_path)
                
                # Skip non-source files
                if not source_file or not source_file.content:
                    continue
                
                # Analyze functions
                for function in source_file.get_functions():
                    function_data = await self._analyze_function(context, function)
                    symbols["functions"].append(function_data)
                    
                    # Add symbol to context
                    context.add_symbol(
                        name=function.name,
                        qualified_name=function.qualified_name,
                        type="function",
                        file_path=file_path,
                        line_start=function.start_line,
                        line_end=function.end_line,
                        content_hash=function_data["content_hash"]
                    )
                
                # Analyze classes
                for class_def in source_file.get_classes():
                    class_data = await self._analyze_class(context, class_def)
                    symbols["classes"].append(class_data)
                    
                    # Add symbol to context
                    context.add_symbol(
                        name=class_def.name,
                        qualified_name=class_def.qualified_name,
                        type="class",
                        file_path=file_path,
                        line_start=class_def.start_line,
                        line_end=class_def.end_line,
                        content_hash=class_data["content_hash"]
                    )
                
                # Analyze variables
                for variable in source_file.get_variables():
                    variable_data = await self._analyze_variable(context, variable)
                    symbols["variables"].append(variable_data)
                    
                    # Add symbol to context
                    context.add_symbol(
                        name=variable.name,
                        qualified_name=variable.qualified_name,
                        type="variable",
                        file_path=file_path,
                        line_start=variable.line,
                        line_end=variable.line,
                        content_hash=variable_data["content_hash"]
                    )
            except Exception as e:
                logger.warning(f"Error analyzing symbols in {file_path}: {e}")
                continue
        
        # Store symbols in database
        await self._store_symbols(context)
        
        # Add results to context
        symbol_counts = {
            "function_count": len(symbols["functions"]),
            "class_count": len(symbols["classes"]),
            "variable_count": len(symbols["variables"]),
            "total_count": len(symbols["functions"]) + len(symbols["classes"]) + len(symbols["variables"])
        }
        
        context.add_result("symbols", {
            "counts": symbol_counts,
            "symbols": symbols
        })
        
        return {
            "counts": symbol_counts,
            "symbols": symbols
        }
    
    async def _analyze_function(self, context: AnalysisContext, function: Function) -> Dict[str, Any]:
        """
        Analyze a function.
        
        Args:
            context: The analysis context.
            function: The function to analyze.
            
        Returns:
            Function metadata.
        """
        # Calculate content hash
        content_hash = hashlib.md5(function.content.encode()).hexdigest()
        
        # Extract function metadata
        return {
            "name": function.name,
            "qualified_name": function.qualified_name,
            "file_path": function.source_file.path,
            "line_start": function.start_line,
            "line_end": function.end_line,
            "parameters": function.parameters,
            "return_type": function.return_type,
            "docstring": function.docstring,
            "content_hash": content_hash
        }
    
    async def _analyze_class(self, context: AnalysisContext, class_def: Class) -> Dict[str, Any]:
        """
        Analyze a class.
        
        Args:
            context: The analysis context.
            class_def: The class to analyze.
            
        Returns:
            Class metadata.
        """
        # Calculate content hash
        content_hash = hashlib.md5(class_def.content.encode()).hexdigest()
        
        # Extract method names
        methods = [method.name for method in class_def.get_methods()]
        
        # Extract class metadata
        return {
            "name": class_def.name,
            "qualified_name": class_def.qualified_name,
            "file_path": class_def.source_file.path,
            "line_start": class_def.start_line,
            "line_end": class_def.end_line,
            "methods": methods,
            "docstring": class_def.docstring,
            "content_hash": content_hash
        }
    
    async def _analyze_variable(self, context: AnalysisContext, variable: Symbol) -> Dict[str, Any]:
        """
        Analyze a variable.
        
        Args:
            context: The analysis context.
            variable: The variable to analyze.
            
        Returns:
            Variable metadata.
        """
        # Calculate content hash
        content_hash = hashlib.md5(f"{variable.name}:{variable.line}".encode()).hexdigest()
        
        # Extract variable metadata
        return {
            "name": variable.name,
            "qualified_name": variable.qualified_name,
            "file_path": variable.source_file.path,
            "line": variable.line,
            "type": getattr(variable, "type", None),
            "content_hash": content_hash
        }
    
    async def _store_symbols(self, context: AnalysisContext):
        """
        Store symbols in the database.
        
        Args:
            context: The analysis context.
        """
        with get_db_session() as session:
            # Get files from database
            files = {}
            for file_data in context.files:
                file = self.file_repo.get_by_path(session, context.commit_id, file_data["path"])
                if file:
                    files[file_data["path"]] = file
            
            # Store symbols
            for symbol_data in context.symbols:
                file = files.get(symbol_data["file_path"])
                if file:
                    # Check if symbol already exists
                    existing_symbol = self.symbol_repo.get_by_qualified_name(
                        session, file.id, symbol_data["qualified_name"]
                    )
                    
                    if existing_symbol:
                        # Update existing symbol
                        self.symbol_repo.update(
                            session,
                            existing_symbol.id,
                            line_start=symbol_data.get("line_start"),
                            line_end=symbol_data.get("line_end"),
                            content_hash=symbol_data.get("content_hash")
                        )
                    else:
                        # Create new symbol
                        self.symbol_repo.create(
                            session,
                            file_id=file.id,
                            name=symbol_data["name"],
                            qualified_name=symbol_data["qualified_name"],
                            type=symbol_data["type"],
                            line_start=symbol_data.get("line_start"),
                            line_end=symbol_data.get("line_end"),
                            content_hash=symbol_data.get("content_hash")
                        )
            
            session.commit()

