"""
Analysis module for codegen-on-oss.

This module provides functionality for analyzing code.
"""

import json
import os
import re
import sys
import time
import traceback
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    TypeVar,
    Union,
    cast,
)

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from graph_sitter.core.codebase import Codebase
from graph_sitter.core.class_definition import Class
from graph_sitter.core.function import Function
from graph_sitter.core.file import SourceFile
from graph_sitter.enums import SymbolType, EdgeType
from graph_sitter.shared.enums.programming_language import ProgrammingLanguage
from graph_sitter.codebase.codebase_analysis import (
    get_class_summary,
    get_codebase_summary,
    get_file_summary,
    get_function_summary,
    get_symbol_summary,
)
from graph_sitter.codebase.codebase_context import CodebaseContext
from codegen_on_oss.analysis.commit_analysis import (
    CommitAnalysisResult,
    DiffAnalyzer,
)

# Import new analysis modules
from graph_sitter.code_generation.doc_utils.utils import document_function
from graph_sitter.code_generation.mdx_docs_generation import (
    create_class_doc, 
    render_mdx_page_for_class
)
from graph_sitter.codebase.module_dependencies import (
    visualize_module_dependencies,
)
from codegen_on_oss.analysis.swe_harness_agent import SWEHarnessAgent
from codegen_on_oss.snapshot.codebase_snapshot import CodebaseSnapshot, SnapshotManager

# Type variables
T = TypeVar("T")


class AnalysisResult(BaseModel):
    """Result of an analysis operation."""

    success: bool = True
    message: str = ""
    data: Dict[str, Any] = Field(default_factory=dict)


class CodeAnalyzer:
    """Analyzer for code."""

    def __init__(self, codebase: Codebase):
        """
        Initialize the code analyzer.
        
        Args:
            codebase: The codebase to analyze
        """
        self.codebase = codebase
        self.context = CodebaseContext(codebase)
    
    def analyze_file(self, file_path: str) -> AnalysisResult:
        """
        Analyze a file in the codebase.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            An AnalysisResult with the analysis results
        """
        try:
            file = self.codebase.get_file(file_path)
            if not file:
                return AnalysisResult(
                    success=False,
                    message=f"File not found: {file_path}",
                )
            
            summary = get_file_summary(file)
            return AnalysisResult(
                success=True,
                message=f"Successfully analyzed file: {file_path}",
                data={"summary": summary},
            )
        except Exception as e:
            return AnalysisResult(
                success=False,
                message=f"Error analyzing file: {str(e)}",
            )
    
    def analyze_function(self, function_name: str) -> AnalysisResult:
        """
        Analyze a function in the codebase.
        
        Args:
            function_name: Name of the function to analyze
            
        Returns:
            An AnalysisResult with the analysis results
        """
        try:
            functions = self.codebase.get_functions_by_name(function_name)
            if not functions:
                return AnalysisResult(
                    success=False,
                    message=f"Function not found: {function_name}",
                )
            
            results = []
            for function in functions:
                summary = get_function_summary(function)
                results.append(summary)
            
            return AnalysisResult(
                success=True,
                message=f"Successfully analyzed function: {function_name}",
                data={"summaries": results},
            )
        except Exception as e:
            return AnalysisResult(
                success=False,
                message=f"Error analyzing function: {str(e)}",
            )
    
    def analyze_class(self, class_name: str) -> AnalysisResult:
        """
        Analyze a class in the codebase.
        
        Args:
            class_name: Name of the class to analyze
            
        Returns:
            An AnalysisResult with the analysis results
        """
        try:
            classes = self.codebase.get_classes_by_name(class_name)
            if not classes:
                return AnalysisResult(
                    success=False,
                    message=f"Class not found: {class_name}",
                )
            
            results = []
            for cls in classes:
                summary = get_class_summary(cls)
                results.append(summary)
            
            return AnalysisResult(
                success=True,
                message=f"Successfully analyzed class: {class_name}",
                data={"summaries": results},
            )
        except Exception as e:
            return AnalysisResult(
                success=False,
                message=f"Error analyzing class: {str(e)}",
            )
    
    def analyze_codebase(self) -> AnalysisResult:
        """
        Analyze the entire codebase.
        
        Returns:
            An AnalysisResult with the analysis results
        """
        try:
            summary = get_codebase_summary(self.codebase)
            return AnalysisResult(
                success=True,
                message="Successfully analyzed codebase",
                data={"summary": summary},
            )
        except Exception as e:
            return AnalysisResult(
                success=False,
                message=f"Error analyzing codebase: {str(e)}",
            )


def analyze_code(codebase: Codebase, analysis_type: str, target: Optional[str] = None) -> AnalysisResult:
    """
    Analyze code based on the specified analysis type and target.
    
    Args:
        codebase: The codebase to analyze
        analysis_type: Type of analysis to perform (file, function, class, codebase)
        target: Target of the analysis (file path, function name, class name)
        
    Returns:
        An AnalysisResult with the analysis results
    """
    analyzer = CodeAnalyzer(codebase)
    
    if analysis_type == "file" and target:
        return analyzer.analyze_file(target)
    elif analysis_type == "function" and target:
        return analyzer.analyze_function(target)
    elif analysis_type == "class" and target:
        return analyzer.analyze_class(target)
    elif analysis_type == "codebase":
        return analyzer.analyze_codebase()
    else:
        return AnalysisResult(
            success=False,
            message=f"Invalid analysis type or missing target: {analysis_type}, {target}",
        )


def create_analysis_app() -> FastAPI:
    """
    Create a FastAPI app for code analysis.
    
    Returns:
        A FastAPI app
    """
    app = FastAPI(title="Code Analysis API")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    class AnalysisRequest(BaseModel):
        """Request for code analysis."""
        
        codebase_path: str
        analysis_type: str
        target: Optional[str] = None
    
    @app.post("/analyze")
    async def analyze(request: AnalysisRequest) -> AnalysisResult:
        """
        Analyze code based on the request.
        
        Args:
            request: The analysis request
            
        Returns:
            An AnalysisResult with the analysis results
        """
        try:
            codebase = Codebase.from_directory(request.codebase_path)
            return analyze_code(codebase, request.analysis_type, request.target)
        except Exception as e:
            return AnalysisResult(
                success=False,
                message=f"Error analyzing code: {str(e)}",
            )
    
    return app


# Main function for running the analysis server
def main():
    """Run the analysis server."""
    import uvicorn
    
    app = create_analysis_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()

