"""
Unified Analysis Module for Codegen-on-OSS

This module serves as a central hub for all code analysis functionality, integrating
various specialized analysis components into a cohesive system for comprehensive
code analysis, error detection, and validation.
"""

import json
import os
import subprocess
import tempfile
from datetime import UTC, datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple, TypeVar, Union
from urllib.parse import urlparse

import networkx as nx
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from codegen import Codebase
from codegen.sdk.core.class_definition import Class
from codegen.sdk.core.external_module import ExternalModule
from codegen.sdk.core.file import SourceFile
from codegen.sdk.core.function import Function
from codegen.sdk.core.import_resolution import Import
from codegen.sdk.core.symbol import Symbol
from codegen.sdk.enums import EdgeType, SymbolType

# Import from other analysis modules
from codegen_on_oss.analysis.codebase_context import CodebaseContext
from codegen_on_oss.analysis.codebase_analysis import (
    get_codebase_summary,
    get_file_summary,
    get_class_summary,
    get_function_summary,
    get_symbol_summary
)
from codegen_on_oss.analysis.error_detection import (
    CodeAnalysisError,
    ErrorCategory,
    ErrorSeverity,
    CodeError
)
from codegen_on_oss.analysis.function_call_analysis import (
    FunctionCallAnalysis,
    FunctionCallGraph,
    ParameterUsageAnalysis
)
from codegen_on_oss.analysis.type_validation import (
    TypeValidation,
    TypeValidationError,
    TypeAnnotationValidator,
    TypeCompatibilityChecker,
    TypeInference
)
from codegen_on_oss.analysis.analysis_import import (
    create_graph_from_codebase,
    find_import_cycles,
    find_problematic_import_loops
)

# Create FastAPI app
app = FastAPI(
    title="Code Analysis API",
    description="API for comprehensive code analysis, error detection, and validation",
    version="1.0.0"
)


class CodeAnalyzer:
    """
    Central class for code analysis that integrates all analysis components.
    
    This class serves as the main entry point for all code analysis functionality,
    providing a unified interface to access various analysis capabilities including
    error detection, function call analysis, and type validation.
    """
    
    def __init__(self, codebase: Codebase):
        """
        Initialize the CodeAnalyzer with a codebase.
        
        Args:
            codebase: The Codebase object to analyze
        """
        self.codebase = codebase
        self._context = None
        self._initialized = False
        
        # Initialize analysis components
        self._error_analyzer = None
        self._function_call_analyzer = None
        self._type_validator = None
        
    def initialize(self):
        """
        Initialize the analyzer by setting up the context and other necessary components.
        This is called automatically when needed but can be called explicitly for eager initialization.
        """
        if self._initialized:
            return
            
        # Initialize context if not already done
        if self._context is None:
            self._context = self._create_context()
            
        self._initialized = True
    
    def _create_context(self) -> CodebaseContext:
        """
        Create a CodebaseContext instance for the current codebase.
        
        Returns:
            A new CodebaseContext instance
        """
        # If the codebase already has a context, use it
        if hasattr(self.codebase, "ctx") and self.codebase.ctx is not None:
            return self.codebase.ctx
            
        # Otherwise, create a new context from the codebase's configuration
        from codegen.sdk.codebase.config import ProjectConfig
        from codegen.configs.models.codebase import CodebaseConfig
        
        # Create a project config from the codebase
        project_config = ProjectConfig(
            repo_operator=self.codebase.repo_operator,
            programming_language=self.codebase.programming_language,
            base_path=self.codebase.base_path
        )
        
        # Create and return a new context
        return CodebaseContext([project_config], config=CodebaseConfig())
    
    @property
    def context(self) -> CodebaseContext:
        """
        Get the CodebaseContext for the current codebase.
        
        Returns:
            A CodebaseContext object for the codebase
        """
        if not self._initialized:
            self.initialize()
            
        return self._context
    
    @property
    def error_analyzer(self) -> CodeAnalysisError:
        """
        Get the CodeAnalysisError instance for error detection.
        
        Returns:
            A CodeAnalysisError instance
        """
        if self._error_analyzer is None:
            self._error_analyzer = CodeAnalysisError(self.codebase)
        return self._error_analyzer
    
    @property
    def function_call_analyzer(self) -> FunctionCallAnalysis:
        """
        Get the FunctionCallAnalysis instance for function call analysis.
        
        Returns:
            A FunctionCallAnalysis instance
        """
        if self._function_call_analyzer is None:
            self._function_call_analyzer = FunctionCallAnalysis(self.codebase)
        return self._function_call_analyzer
    
    @property
    def type_validator(self) -> TypeValidation:
        """
        Get the TypeValidation instance for type validation.
        
        Returns:
            A TypeValidation instance
        """
        if self._type_validator is None:
            self._type_validator = TypeValidation(self.codebase)
        return self._type_validator
    
    def get_codebase_summary(self) -> str:
        """
        Get a comprehensive summary of the codebase.
        
        Returns:
            A string containing summary information about the codebase
        """
        return get_codebase_summary(self.codebase)
    
    def get_file_summary(self, file_path: str) -> str:
        """
        Get a summary of a specific file.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            A string containing summary information about the file
        """
        file = self.codebase.get_file(file_path)
        if file is None:
            return f"File not found: {file_path}"
        return get_file_summary(file)
    
    def get_class_summary(self, class_name: str) -> str:
        """
        Get a summary of a specific class.
        
        Args:
            class_name: Name of the class to analyze
            
        Returns:
            A string containing summary information about the class
        """
        for cls in self.codebase.classes:
            if cls.name == class_name:
                return get_class_summary(cls)
        return f"Class not found: {class_name}"
    
    def get_function_summary(self, function_name: str) -> str:
        """
        Get a summary of a specific function.
        
        Args:
            function_name: Name of the function to analyze
            
        Returns:
            A string containing summary information about the function
        """
        for func in self.codebase.functions:
            if func.name == function_name:
                return get_function_summary(func)
        return f"Function not found: {function_name}"
    
    def get_symbol_summary(self, symbol_name: str) -> str:
        """
        Get a summary of a specific symbol.
        
        Args:
            symbol_name: Name of the symbol to analyze
            
        Returns:
            A string containing summary information about the symbol
        """
        for symbol in self.codebase.symbols:
            if symbol.name == symbol_name:
                return get_symbol_summary(symbol)
        return f"Symbol not found: {symbol_name}"
    
    def find_symbol_by_name(self, symbol_name: str) -> Optional[Symbol]:
        """
        Find a symbol by its name.
        
        Args:
            symbol_name: Name of the symbol to find
            
        Returns:
            The Symbol object if found, None otherwise
        """
        for symbol in self.codebase.symbols:
            if symbol.name == symbol_name:
                return symbol
        return None
    
    def find_file_by_path(self, file_path: str) -> Optional[SourceFile]:
        """
        Find a file by its path.
        
        Args:
            file_path: Path to the file to find
            
        Returns:
            The SourceFile object if found, None otherwise
        """
        return self.codebase.get_file(file_path)
    
    def find_class_by_name(self, class_name: str) -> Optional[Class]:
        """
        Find a class by its name.
        
        Args:
            class_name: Name of the class to find
            
        Returns:
            The Class object if found, None otherwise
        """
        for cls in self.codebase.classes:
            if cls.name == class_name:
                return cls
        return None
    
    def find_function_by_name(self, function_name: str) -> Optional[Function]:
        """
        Find a function by its name.
        
        Args:
            function_name: Name of the function to find
            
        Returns:
            The Function object if found, None otherwise
        """
        for func in self.codebase.functions:
            if func.name == function_name:
                return func
        return None
    
    def analyze_imports(self) -> Dict[str, Any]:
        """
        Analyze import relationships in the codebase.
        
        Returns:
            A dictionary containing import analysis results
        """
        graph = create_graph_from_codebase(self.codebase.repo_name)
        cycles = find_import_cycles(graph)
        problematic_loops = find_problematic_import_loops(graph, cycles)
        
        return {
            "import_cycles": cycles,
            "problematic_loops": problematic_loops
        }
    
    def analyze_errors(self, category: Optional[str] = None, severity: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze the codebase for errors.
        
        Args:
            category: Optional error category to filter by
            severity: Optional error severity to filter by
            
        Returns:
            A dictionary containing error analysis results
        """
        # Get all errors
        all_errors = self.error_analyzer.analyze()
        
        # Filter by category if specified
        if category:
            try:
                category_enum = ErrorCategory[category]
                all_errors = [error for error in all_errors if error.category == category_enum]
            except KeyError:
                pass
        
        # Filter by severity if specified
        if severity:
            try:
                severity_enum = ErrorSeverity[severity]
                all_errors = [error for error in all_errors if error.severity == severity_enum]
            except KeyError:
                pass
        
        # Convert errors to dictionaries
        error_dicts = [error.to_dict() for error in all_errors]
        
        # Get error summary
        error_summary = self.error_analyzer.get_error_summary()
        severity_summary = self.error_analyzer.get_severity_summary()
        
        return {
            "errors": error_dicts,
            "error_summary": error_summary,
            "severity_summary": severity_summary,
            "total_errors": len(all_errors)
        }
    
    def analyze_function_calls(self, function_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze function calls in the codebase.
        
        Args:
            function_name: Optional name of a specific function to analyze
            
        Returns:
            A dictionary containing function call analysis results
        """
        if function_name:
            # Analyze a specific function
            return self.function_call_analyzer.analyze_function_dependencies(function_name)
        else:
            # Analyze all functions
            return self.function_call_analyzer.analyze_all()
    
    def analyze_types(self, function_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze type annotations and compatibility in the codebase.
        
        Args:
            function_name: Optional name of a specific function to analyze
            
        Returns:
            A dictionary containing type analysis results
        """
        if function_name:
            # Find the function
            func = self.find_function_by_name(function_name)
            if not func:
                return {"error": f"Function {function_name} not found"}
            
            # Analyze the function
            annotation_errors = self.type_validator.annotation_validator.validate_function_annotations(func)
            compatibility_errors = self.type_validator.compatibility_checker.check_assignment_compatibility(func)
            compatibility_errors.extend(self.type_validator.compatibility_checker.check_return_compatibility(func))
            compatibility_errors.extend(self.type_validator.compatibility_checker.check_parameter_compatibility(func))
            inferred_types = self.type_validator.type_inference.infer_variable_types(func)
            
            return {
                "function_name": function_name,
                "annotation_errors": [error.to_dict() for error in annotation_errors],
                "compatibility_errors": [error.to_dict() for error in compatibility_errors],
                "inferred_types": inferred_types
            }
        else:
            # Analyze all types
            return self.type_validator.validate_all()
    
    def analyze_complexity(self) -> Dict[str, Any]:
        """
        Analyze code complexity metrics for the codebase.
        
        Returns:
            A dictionary containing complexity metrics
        """
        # Get complex functions from error analysis
        complex_function_errors = self.error_analyzer.analyze_by_category(ErrorCategory.COMPLEX_FUNCTION)
        complex_functions = [
            {
                "name": error.function_name,
                "file_path": error.file_path,
                "message": error.message
            }
            for error in complex_function_errors
        ]
        
        # Get call graph complexity from function call analysis
        call_graph = self.function_call_analyzer.call_graph
        most_complex = call_graph.get_most_complex_functions()
        most_called = call_graph.get_most_called_functions()
        
        return {
            "complex_functions": complex_functions,
            "most_complex_by_calls": most_complex,
            "most_called_functions": most_called,
            "circular_dependencies": call_graph.get_circular_dependencies()
        }
    
    def get_function_call_graph(self) -> FunctionCallGraph:
        """
        Get the function call graph for the codebase.
        
        Returns:
            A FunctionCallGraph instance
        """
        return self.function_call_analyzer.call_graph
    
    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze a specific file.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            A dictionary containing analysis results for the file
        """
        file = self.find_file_by_path(file_path)
        if not file:
            return {"error": f"File {file_path} not found"}
        
        # Get file summary
        summary = get_file_summary(file)
        
        # Get errors in the file
        errors = self.error_analyzer.analyze_file(file_path)
        error_dicts = [error.to_dict() for error in errors]
        
        # Get functions in the file
        functions = []
        for func in self.codebase.functions:
            if func.filepath == file_path:
                functions.append({
                    "name": func.name,
                    "parameters": [p.name for p in func.parameters] if hasattr(func, "parameters") else [],
                    "return_type": func.return_type if hasattr(func, "return_type") else None
                })
        
        # Get classes in the file
        classes = []
        for cls in self.codebase.classes:
            if cls.filepath == file_path:
                classes.append({
                    "name": cls.name,
                    "methods": [m.name for m in cls.methods] if hasattr(cls, "methods") else [],
                    "attributes": [a.name for a in cls.attributes] if hasattr(cls, "attributes") else []
                })
        
        # Get imports in the file
        imports = []
        if hasattr(file, "imports"):
            for imp in file.imports:
                if hasattr(imp, "source"):
                    imports.append(imp.source)
        
        return {
            "file_path": file_path,
            "summary": summary,
            "errors": error_dicts,
            "functions": functions,
            "classes": classes,
            "imports": imports
        }
    
    def analyze_function(self, function_name: str) -> Dict[str, Any]:
        """
        Analyze a specific function.
        
        Args:
            function_name: Name of the function to analyze
            
        Returns:
            A dictionary containing analysis results for the function
        """
        func = self.find_function_by_name(function_name)
        if not func:
            return {"error": f"Function {function_name} not found"}
        
        # Get function summary
        summary = get_function_summary(func)
        
        # Get errors in the function
        errors = self.error_analyzer.analyze_function(function_name)
        error_dicts = [error.to_dict() for error in errors]
        
        # Get function call analysis
        call_analysis = self.function_call_analyzer.analyze_function_dependencies(function_name)
        
        # Get parameter usage analysis
        param_analysis = self.function_call_analyzer.parameter_usage.analyze_parameter_usage(function_name)
        
        # Get type analysis
        type_analysis = self.analyze_types(function_name)
        
        return {
            "function_name": function_name,
            "file_path": func.filepath,
            "summary": summary,
            "errors": error_dicts,
            "call_analysis": call_analysis,
            "parameter_analysis": param_analysis,
            "type_analysis": type_analysis
        }
    
    def analyze_all(self) -> Dict[str, Any]:
        """
        Perform comprehensive analysis of the codebase.
        
        Returns:
            A dictionary containing all analysis results
        """
        return {
            "codebase_summary": self.get_codebase_summary(),
            "error_analysis": self.analyze_errors(),
            "function_call_analysis": self.analyze_function_calls(),
            "type_analysis": self.analyze_types(),
            "complexity_analysis": self.analyze_complexity(),
            "import_analysis": self.analyze_imports()
        }


# API Models
class AnalyzeRepoRequest(BaseModel):
    repo_url: str
    branch: Optional[str] = None


class AnalyzeFileRequest(BaseModel):
    repo_url: str
    file_path: str
    branch: Optional[str] = None


class AnalyzeFunctionRequest(BaseModel):
    repo_url: str
    function_name: str
    branch: Optional[str] = None


class AnalyzeErrorsRequest(BaseModel):
    repo_url: str
    category: Optional[str] = None
    severity: Optional[str] = None
    branch: Optional[str] = None


# Helper function to get codebase from repo URL
def get_codebase_from_url(repo_url: str, branch: Optional[str] = None) -> Codebase:
    """
    Get a Codebase object from a repository URL.
    
    Args:
        repo_url: URL of the repository to analyze
        branch: Optional branch to analyze
        
    Returns:
        A Codebase object
    """
    try:
        if branch:
            return Codebase.from_repo(repo_url, branch=branch)
        else:
            return Codebase.from_repo(repo_url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to load repository: {str(e)}")


# API Routes
@app.post("/analyze_repo")
async def analyze_repo(request: AnalyzeRepoRequest):
    """
    Analyze an entire repository.
    
    Args:
        request: AnalyzeRepoRequest object
        
    Returns:
        Analysis results for the repository
    """
    codebase = get_codebase_from_url(request.repo_url, request.branch)
    analyzer = CodeAnalyzer(codebase)
    return analyzer.analyze_all()


@app.post("/analyze_file")
async def analyze_file(request: AnalyzeFileRequest):
    """
    Analyze a specific file in a repository.
    
    Args:
        request: AnalyzeFileRequest object
        
    Returns:
        Analysis results for the file
    """
    codebase = get_codebase_from_url(request.repo_url, request.branch)
    analyzer = CodeAnalyzer(codebase)
    return analyzer.analyze_file(request.file_path)


@app.post("/analyze_function")
async def analyze_function(request: AnalyzeFunctionRequest):
    """
    Analyze a specific function in a repository.
    
    Args:
        request: AnalyzeFunctionRequest object
        
    Returns:
        Analysis results for the function
    """
    codebase = get_codebase_from_url(request.repo_url, request.branch)
    analyzer = CodeAnalyzer(codebase)
    return analyzer.analyze_function(request.function_name)


@app.post("/analyze_errors")
async def analyze_errors(request: AnalyzeErrorsRequest):
    """
    Analyze errors in a repository.
    
    Args:
        request: AnalyzeErrorsRequest object
        
    Returns:
        Error analysis results for the repository
    """
    codebase = get_codebase_from_url(request.repo_url, request.branch)
    analyzer = CodeAnalyzer(codebase)
    return analyzer.analyze_errors(request.category, request.severity)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

