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
from typing import Any, Optional, TypeVar, Dict, List, Tuple, Union, Protocol, runtime_checkable, cast, Type, Callable

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
        value: str | None = None,
        children: list["ASTNode"] | None = None,
        parent: Optional["ASTNode"] = None,
        start_position: tuple[int, int] | None = None,
        end_position: tuple[int, int] | None = None,
        metadata: dict[str, Any] | None = None,
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

    def find_nodes_by_type(self, node_type: str) -> list["ASTNode"]:
        """
        Find all descendant nodes of a specific type.

        Args:
            node_type: Type of nodes to find

        Returns:
            List of matching nodes
        """
        result = []
        if self.node_type == node_type:
            result.append(self)

        for child in self.children:
            result.extend(child.find_nodes_by_type(node_type))

        return result

    def to_dict(self) -> dict[str, Any]:
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


class BaseParser:
    """
    Abstract base class for all parsers.
    
    This defines the interface that all parsers must implement.
    """
    
    def parse_file(self, file_path: str) -> ASTNode:
        """
        Parse a file and return an AST.
        
        Args:
            file_path: Path to the file to parse
            
        Returns:
            AST node representing the parsed file
            
        Raises:
            ParseError: If there is an error parsing the file
        """
        raise NotImplementedError("Subclasses must implement parse_file")
    
    def parse_code(self, code: str, filename: str = "<string>") -> ASTNode:
        """
        Parse code directly and return an AST.
        
        Args:
            code: Code to parse
            filename: Optional filename for error reporting
            
        Returns:
            AST node representing the parsed code
            
        Raises:
            ParseError: If there is an error parsing the code
        """
        raise NotImplementedError("Subclasses must implement parse_code")
    
    def get_symbols(self, ast: ASTNode) -> List[Dict[str, Any]]:
        """
        Extract symbols (functions, classes, variables) from an AST.
        
        Args:
            ast: AST to extract symbols from
            
        Returns:
            List of symbols with their metadata
        """
        raise NotImplementedError("Subclasses must implement get_symbols")
    
    def get_dependencies(self, ast: ASTNode) -> List[Dict[str, Any]]:
        """
        Extract dependencies (imports, requires) from an AST.
        
        Args:
            ast: AST to extract dependencies from
            
        Returns:
            List of dependencies with their metadata
        """
        raise NotImplementedError("Subclasses must implement get_dependencies")


class CodegenParser(BaseParser):
    """
    Parser implementation using Codegen SDK.
    
    This parser uses the Codegen SDK to parse code and generate ASTs.
    """
    
    def __init__(self) -> None:
        """Initialize the parser."""
        super().__init__()
        # Import Codegen SDK here to avoid circular imports
        try:
            from codegen.sdk.codebase import codebase_analysis
            self.codebase_analysis = codebase_analysis
        except ImportError:
            logger.error("Failed to import Codegen SDK. Make sure it's installed.")
            raise ImportError("Codegen SDK is required for CodegenParser")
    
    def parse_file(self, file_path: str) -> ASTNode:
        """
        Parse a file using Codegen SDK.
        
        Args:
            file_path: Path to the file to parse
            
        Returns:
            AST node representing the parsed file
        """
        try:
            # This is a placeholder for actual SDK implementation
            # In a real implementation, we would use the SDK to parse the file
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()
            return self.parse_code(code, file_path)
        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {e}")
            raise ParseError(f"Error parsing file {file_path}: {e}")
    
    def parse_code(self, code: str, filename: str = "<string>") -> ASTNode:
        """
        Parse code using Codegen SDK.
        
        Args:
            code: Code to parse
            filename: Optional filename for error reporting
            
        Returns:
            AST node representing the parsed code
        """
        try:
            # This is a placeholder for actual SDK implementation
            # In a real implementation, we would use the SDK to parse the code
            root = ASTNode("file", value=filename)
            # Add some basic structure based on simple parsing
            lines = code.split("\n")
            for i, line in enumerate(lines):
                line = line.strip()
                if line.startswith("def "):
                    # Simple function detection
                    func_name = line[4:].split("(")[0].strip()
                    func_node = ASTNode(
                        "function",
                        value=func_name,
                        start_position=(i, 0),
                        end_position=(i, len(line)),
                        metadata={"line": i}
                    )
                    root.add_child(func_node)
                elif line.startswith("class "):
                    # Simple class detection
                    class_name = line[6:].split("(")[0].split(":")[0].strip()
                    class_node = ASTNode(
                        "class",
                        value=class_name,
                        start_position=(i, 0),
                        end_position=(i, len(line)),
                        metadata={"line": i}
                    )
                    root.add_child(class_node)
                elif line.startswith("import ") or line.startswith("from "):
                    # Simple import detection
                    import_node = ASTNode(
                        "import",
                        value=line,
                        start_position=(i, 0),
                        end_position=(i, len(line)),
                        metadata={"line": i}
                    )
                    root.add_child(import_node)
            return root
        except Exception as e:
            logger.error(f"Error parsing code: {e}")
            raise ParseError(f"Error parsing code: {e}")
    
    def get_symbols(self, ast: ASTNode) -> List[Dict[str, Any]]:
        """
        Extract symbols from an AST.
        
        Args:
            ast: AST to extract symbols from
            
        Returns:
            List of symbols with their metadata
        """
        symbols = []
        
        # Find function nodes
        for func_node in ast.find_nodes_by_type("function"):
            symbols.append({
                "type": "function",
                "name": func_node.value or "",
                "line": func_node.metadata.get("line", 0),
                "start_position": func_node.start_position,
                "end_position": func_node.end_position
            })
        
        # Find class nodes
        for class_node in ast.find_nodes_by_type("class"):
            methods = []
            for method_node in class_node.find_nodes_by_type("function"):
                methods.append(method_node.value or "")
            
            symbols.append({
                "type": "class",
                "name": class_node.value or "",
                "methods": methods,
                "line": class_node.metadata.get("line", 0),
                "start_position": class_node.start_position,
                "end_position": class_node.end_position
            })
        
        return symbols
    
    def get_dependencies(self, ast: ASTNode) -> List[Dict[str, Any]]:
        """
        Extract dependencies from an AST.
        
        Args:
            ast: AST to extract dependencies from
            
        Returns:
            List of dependencies with their metadata
        """
        dependencies = []
        
        # Find import nodes
        for import_node in ast.find_nodes_by_type("import"):
            if import_node.value:
                if import_node.value.startswith("import "):
                    module = import_node.value[7:].strip()
                    dependencies.append({
                        "type": "import",
                        "module": module,
                        "line": import_node.metadata.get("line", 0)
                    })
                elif import_node.value.startswith("from "):
                    parts = import_node.value.split(" import ")
                    if len(parts) == 2:
                        module = parts[0][5:].strip()
                        names = [n.strip() for n in parts[1].split(",")]
                        for name in names:
                            dependencies.append({
                                "type": "from_import",
                                "module": module,
                                "name": name,
                                "line": import_node.metadata.get("line", 0)
                            })
        
        return dependencies


class PythonParser(CodegenParser):
    """
    Parser for Python code.
    
    This parser specializes in parsing Python code and extracting Python-specific
    symbols and dependencies.
    """
    
    def parse_code(self, code: str, filename: str = "<string>") -> ASTNode:
        """
        Parse Python code.
        
        Args:
            code: Python code to parse
            filename: Optional filename for error reporting
            
        Returns:
            AST node representing the parsed code
        """
        try:
            # In a real implementation, we would use Python's ast module
            # or a more sophisticated parser
            return super().parse_code(code, filename)
        except Exception as e:
            logger.error(f"Error parsing Python code: {e}")
            raise ParseError(f"Error parsing Python code: {e}")


class JavaScriptParser(CodegenParser):
    """
    Parser for JavaScript code.
    
    This parser specializes in parsing JavaScript code and extracting JavaScript-specific
    symbols and dependencies.
    """
    
    def parse_code(self, code: str, filename: str = "<string>") -> ASTNode:
        """
        Parse JavaScript code.
        
        Args:
            code: JavaScript code to parse
            filename: Optional filename for error reporting
            
        Returns:
            AST node representing the parsed code
        """
        try:
            # In a real implementation, we would use a JavaScript parser
            # like esprima or acorn
            return super().parse_code(code, filename)
        except Exception as e:
            logger.error(f"Error parsing JavaScript code: {e}")
            raise ParseError(f"Error parsing JavaScript code: {e}")


class TypeScriptParser(CodegenParser):
    """
    Parser for TypeScript code.
    
    This parser specializes in parsing TypeScript code and extracting TypeScript-specific
    symbols and dependencies.
    """
    
    def parse_code(self, code: str, filename: str = "<string>") -> ASTNode:
        """
        Parse TypeScript code.
        
        Args:
            code: TypeScript code to parse
            filename: Optional filename for error reporting
            
        Returns:
            AST node representing the parsed code
        """
        try:
            # In a real implementation, we would use a TypeScript parser
            # like typescript-eslint or ts-morph
            return super().parse_code(code, filename)
        except Exception as e:
            logger.error(f"Error parsing TypeScript code: {e}")
            raise ParseError(f"Error parsing TypeScript code: {e}")


def create_parser(language: str) -> BaseParser:
    """
    Create a parser for the specified language.
    
    Args:
        language: Language to create a parser for (python, javascript, typescript)
        
    Returns:
        Parser for the specified language
        
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
        logger.warning(f"Unsupported language: {language}, using generic parser")
        return CodegenParser()


def parse_file(file_path: str) -> ASTNode:
    """
    Parse a file and return an AST.
    
    This is a convenience function that creates a parser based on the file extension
    and uses it to parse the file.
    
    Args:
        file_path: Path to the file to parse
        
    Returns:
        AST node representing the parsed file
        
    Raises:
        ParseError: If there is an error parsing the file
    """
    # Determine language from file extension
    if file_path.endswith(".py"):
        language = "python"
    elif file_path.endswith(".js"):
        language = "javascript"
    elif file_path.endswith(".ts"):
        language = "typescript"
    else:
        language = "generic"
    
    parser = create_parser(language)
    return parser.parse_file(file_path)


def parse_code(code: str, language: str, filename: str = "<string>") -> ASTNode:
    """
    Parse code directly and return an AST.
    
    This is a convenience function that creates a parser for the specified language
    and uses it to parse the code.
    
    Args:
        code: Code to parse
        language: Language of the code (python, javascript, typescript)
        filename: Optional filename for error reporting
        
    Returns:
        AST node representing the parsed code
        
    Raises:
        ParseError: If there is an error parsing the code
    """
    parser = create_parser(language)
    return parser.parse_code(code, filename)
