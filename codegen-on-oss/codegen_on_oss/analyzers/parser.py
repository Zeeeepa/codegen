#!/usr/bin/env python3
"""
Code Parser Module for Analyzers

This module provides specialized parsing functionality for code analysis,
including abstract syntax tree (AST) generation and traversal for multiple
programming languages. It serves as a foundation for various code analyzers
in the system.
"""

import importlib.util
import logging
import sys
from enum import Enum
from typing import Any, Optional, TypeVar, Protocol, Dict, List, Tuple, Union, cast, Type
from abc import ABC, abstractmethod

# Check if required modules are available
if importlib.util.find_spec("codegen.sdk") is None:
    print("Codegen SDK not found.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Type variable for generic parser implementations
T = TypeVar("T")


class ParserType(Enum):
    """Enum defining the types of parsers available."""

    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GENERIC = "generic"


class ParseError(Exception):
    """Exception raised for errors during parsing."""

    pass


class ASTNode:
    """
    Base class representing a node in an Abstract Syntax Tree.

    This provides a common interface for working with AST nodes
    regardless of the underlying parser implementation.
    """

    def __init__(
        self,
        node_type: str,
        value: Optional[str] = None,
        children: Optional[List["ASTNode"]] = None,
        parent: Optional["ASTNode"] = None,
        start_position: Optional[Tuple[int, int]] = None,
        end_position: Optional[Tuple[int, int]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize an AST node.

        Args:
            node_type: Type of the node (e.g., 'function', 'class', 'variable')
            value: Optional value associated with the node
            children: List of child nodes
            parent: Parent node
            start_position: Tuple of (line, column) for the start position
            end_position: Tuple of (line, column) for the end position
            metadata: Additional metadata for the node
        """
        self.node_type = node_type
        self.value = value
        self.children = children or []
        self.parent = parent
        self.start_position = start_position
        self.end_position = end_position
        self.metadata = metadata or {}

    def add_child(self, child: "ASTNode") -> None:
        """
        Add a child node to this node.

        Args:
            child: Child node to add
        """
        self.children.append(child)
        child.parent = self

    def find_nodes_by_type(self, node_type: str) -> List["ASTNode"]:
        """
        Find all descendant nodes of a specific type.

        Args:
            node_type: Type of nodes to find

        Returns:
            List of matching nodes
        """
        result: List["ASTNode"] = []
        if self.node_type == node_type:
            result.append(self)

        for child in self.children:
            result.extend(child.find_nodes_by_type(node_type))

        return result

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the node to a dictionary representation.

        Returns:
            Dictionary representation of the node
        """
        return {
            "type": self.node_type,
            "value": self.value,
            "start_position": self.start_position,
            "end_position": self.end_position,
            "metadata": self.metadata,
            "children": [child.to_dict() for child in self.children],
        }

    def __repr__(self) -> str:
        """String representation of the node."""
        return f"ASTNode({self.node_type}, value={self.value}, children={len(self.children)})"


class BaseParser(ABC):
    """
    Abstract base class for all parsers.
    
    This defines the interface that all parser implementations must follow.
    """
    
    def parse_file(self, file_path: str) -> ASTNode:
        """
        Parse a file and return its AST.
        
        Args:
            file_path: Path to the file to parse
            
        Returns:
            AST representation of the file
            
        Raises:
            ParseError: If the file cannot be parsed
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return self.parse_code(content, file_path)
        except Exception as e:
            raise ParseError(f"Failed to parse file {file_path}: {str(e)}") from e
    
    @abstractmethod
    def parse_code(self, code: str, file_path: Optional[str] = None) -> ASTNode:
        """
        Parse code string and return its AST.
        
        Args:
            code: Code string to parse
            file_path: Optional path to the file (for error reporting)
            
        Returns:
            AST representation of the code
            
        Raises:
            ParseError: If the code cannot be parsed
        """
        pass
    
    @abstractmethod
    def get_symbols(self, ast: ASTNode) -> List[Dict[str, Any]]:
        """
        Extract symbols (functions, classes, variables) from an AST.
        
        Args:
            ast: AST to extract symbols from
            
        Returns:
            List of symbol information dictionaries
        """
        pass
    
    @abstractmethod
    def get_dependencies(self, ast: ASTNode) -> List[Dict[str, Any]]:
        """
        Extract dependencies (imports, requires) from an AST.
        
        Args:
            ast: AST to extract dependencies from
            
        Returns:
            List of dependency information dictionaries
        """
        pass


class CodegenParser(BaseParser):
    """
    Parser implementation using Codegen SDK.
    
    This parser leverages the Codegen SDK to parse code and build ASTs.
    """
    
    def __init__(self) -> None:
        """Initialize the CodegenParser."""
        super().__init__()
        # Import here to avoid circular imports
        try:
            from codegen.sdk.codebase import codebase_analysis
            self.codebase_analysis = codebase_analysis
        except ImportError:
            logger.warning("Codegen SDK codebase_analysis module not found, using placeholder implementation")
            self.codebase_analysis = None
    
    def parse_code(self, code: str, file_path: Optional[str] = None) -> ASTNode:
        """
        Parse code string using Codegen SDK.
        
        Args:
            code: Code string to parse
            file_path: Optional path to the file (for error reporting)
            
        Returns:
            AST representation of the code
        """
        try:
            # This is a placeholder for the actual implementation
            # In a real implementation, we would use the Codegen SDK to parse the code
            root = ASTNode("root", value=file_path or "<string>")
            # Add more nodes based on the actual parsing
            return root
        except Exception as e:
            file_info = f" in {file_path}" if file_path else ""
            raise ParseError(f"Failed to parse code{file_info}: {str(e)}") from e
    
    def get_symbols(self, ast: ASTNode) -> List[Dict[str, Any]]:
        """
        Extract symbols from an AST using Codegen SDK.
        
        Args:
            ast: AST to extract symbols from
            
        Returns:
            List of symbol information dictionaries
        """
        # Placeholder implementation
        return []
    
    def get_dependencies(self, ast: ASTNode) -> List[Dict[str, Any]]:
        """
        Extract dependencies from an AST using Codegen SDK.
        
        Args:
            ast: AST to extract dependencies from
            
        Returns:
            List of dependency information dictionaries
        """
        # Placeholder implementation
        return []


class PythonParser(CodegenParser):
    """Parser specialized for Python code."""
    
    def parse_code(self, code: str, file_path: Optional[str] = None) -> ASTNode:
        """
        Parse Python code.
        
        Args:
            code: Python code string to parse
            file_path: Optional path to the file (for error reporting)
            
        Returns:
            AST representation of the Python code
        """
        try:
            # Placeholder for Python-specific parsing
            root = ASTNode("python_module", value=file_path or "<string>")
            # Add more nodes based on the actual parsing
            return root
        except Exception as e:
            file_info = f" in {file_path}" if file_path else ""
            raise ParseError(f"Failed to parse Python code{file_info}: {str(e)}") from e
    
    def get_symbols(self, ast: ASTNode) -> List[Dict[str, Any]]:
        """
        Extract symbols from a Python AST.
        
        Args:
            ast: AST to extract symbols from
            
        Returns:
            List of symbol information dictionaries
        """
        # Placeholder implementation for Python symbols
        return []
    
    def get_dependencies(self, ast: ASTNode) -> List[Dict[str, Any]]:
        """
        Extract dependencies from a Python AST.
        
        Args:
            ast: AST to extract dependencies from
            
        Returns:
            List of dependency information dictionaries
        """
        # Placeholder implementation for Python dependencies
        return []


class JavaScriptParser(CodegenParser):
    """Parser specialized for JavaScript code."""
    
    def parse_code(self, code: str, file_path: Optional[str] = None) -> ASTNode:
        """
        Parse JavaScript code.
        
        Args:
            code: JavaScript code string to parse
            file_path: Optional path to the file (for error reporting)
            
        Returns:
            AST representation of the JavaScript code
        """
        try:
            # Placeholder for JavaScript-specific parsing
            root = ASTNode("javascript_module", value=file_path or "<string>")
            # Add more nodes based on the actual parsing
            return root
        except Exception as e:
            file_info = f" in {file_path}" if file_path else ""
            raise ParseError(f"Failed to parse JavaScript code{file_info}: {str(e)}") from e
    
    def get_symbols(self, ast: ASTNode) -> List[Dict[str, Any]]:
        """
        Extract symbols from a JavaScript AST.
        
        Args:
            ast: AST to extract symbols from
            
        Returns:
            List of symbol information dictionaries
        """
        # Placeholder implementation for JavaScript symbols
        return []
    
    def get_dependencies(self, ast: ASTNode) -> List[Dict[str, Any]]:
        """
        Extract dependencies from a JavaScript AST.
        
        Args:
            ast: AST to extract dependencies from
            
        Returns:
            List of dependency information dictionaries
        """
        # Placeholder implementation for JavaScript dependencies
        return []


class TypeScriptParser(JavaScriptParser):
    """Parser specialized for TypeScript code."""
    
    def parse_code(self, code: str, file_path: Optional[str] = None) -> ASTNode:
        """
        Parse TypeScript code.
        
        Args:
            code: TypeScript code string to parse
            file_path: Optional path to the file (for error reporting)
            
        Returns:
            AST representation of the TypeScript code
        """
        try:
            # Placeholder for TypeScript-specific parsing
            root = ASTNode("typescript_module", value=file_path or "<string>")
            # Add more nodes based on the actual parsing
            return root
        except Exception as e:
            file_info = f" in {file_path}" if file_path else ""
            raise ParseError(f"Failed to parse TypeScript code{file_info}: {str(e)}") from e
    
    def get_symbols(self, ast: ASTNode) -> List[Dict[str, Any]]:
        """
        Extract symbols from a TypeScript AST.
        
        Args:
            ast: AST to extract symbols from
            
        Returns:
            List of symbol information dictionaries
        """
        # Placeholder implementation for TypeScript symbols
        return []
    
    def get_dependencies(self, ast: ASTNode) -> List[Dict[str, Any]]:
        """
        Extract dependencies from a TypeScript AST.
        
        Args:
            ast: AST to extract dependencies from
            
        Returns:
            List of dependency information dictionaries
        """
        # Placeholder implementation for TypeScript dependencies
        return []


def create_parser(language: str) -> BaseParser:
    """
    Factory function to create a parser for a specific language.
    
    Args:
        language: Language to create a parser for (e.g., 'python', 'javascript')
        
    Returns:
        Parser instance for the specified language
        
    Raises:
        ValueError: If the language is not supported
    """
    language = language.lower()
    if language == "python":
        return PythonParser()
    elif language == "javascript":
        return JavaScriptParser()
    elif language == "typescript":
        return TypeScriptParser()
    else:
        # Default to a generic parser
        return CodegenParser()


def parse_file(file_path: str) -> ASTNode:
    """
    Convenience function to parse a file.
    
    Args:
        file_path: Path to the file to parse
        
    Returns:
        AST representation of the file
        
    Raises:
        ParseError: If the file cannot be parsed
    """
    # Determine the language based on the file extension
    parser: BaseParser
    if file_path.endswith(".py"):
        parser = PythonParser()
    elif file_path.endswith(".js"):
        parser = JavaScriptParser()
    elif file_path.endswith(".ts"):
        parser = TypeScriptParser()
    else:
        # Default to a generic parser
        parser = CodegenParser()
    
    return parser.parse_file(file_path)


def parse_code(code: str, language: str, file_path: Optional[str] = None) -> ASTNode:
    """
    Convenience function to parse code.
    
    Args:
        code: Code string to parse
        language: Language of the code (e.g., 'python', 'javascript')
        file_path: Optional path to the file (for error reporting)
        
    Returns:
        AST representation of the code
        
    Raises:
        ParseError: If the code cannot be parsed
    """
    parser = create_parser(language)
    return parser.parse_code(code, file_path)
