#!/usr/bin/env python3
"""
Code Parser Module for Analyzers

This module provides specialized parsing functionality for code analysis,
including abstract syntax tree (AST) generation and traversal for multiple
programming languages. It serves as a foundation for various code analyzers
in the system.
"""

import os
import sys
import logging
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional, Union, TypeVar, Generic, cast

try:
    from codegen.sdk.core.codebase import Codebase
    from codegen.sdk.core.node import Node
    from codegen.shared.enums.programming_language import ProgrammingLanguage
    
    # Import from our own modules
    from codegen_on_oss.analyzers.issue_types import Issue, IssueSeverity, AnalysisType, IssueCategory
except ImportError:
    print("Codegen SDK or required modules not found.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Type variable for generic parser implementations
T = TypeVar('T')

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
        children: Optional[List['ASTNode']] = None,
        parent: Optional['ASTNode'] = None,
        start_position: Optional[Tuple[int, int]] = None,
        end_position: Optional[Tuple[int, int]] = None,
        metadata: Optional[Dict[str, Any]] = None
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
    
    def add_child(self, child: 'ASTNode') -> None:
        """
        Add a child node to this node.
        
        Args:
            child: Child node to add
        """
        self.children.append(child)
        child.parent = self
    
    def find_nodes_by_type(self, node_type: str) -> List['ASTNode']:
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
            "children": [child.to_dict() for child in self.children]
        }
    
    def __repr__(self) -> str:
        """String representation of the node."""
        return f"ASTNode({self.node_type}, value={self.value}, children={len(self.children)})"

class BaseParser(ABC, Generic[T]):
    """
    Abstract base class for all code parsers.
    
    This class defines the common interface for parsing code and
    generating abstract syntax trees for different programming languages.
    """
    
    def __init__(
        self,
        language: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the parser.
        
        Args:
            language: Programming language to parse
            config: Additional configuration options
        """
        self.language = language
        self.config = config or {}
        self.errors: List[ParseError] = []
    
    @abstractmethod
    def parse_file(self, file_path: Union[str, Path]) -> T:
        """
        Parse a file and generate an AST.
        
        Args:
            file_path: Path to the file to parse
            
        Returns:
            Generated AST
            
        Raises:
            ParseError: If parsing fails
        """
        pass
    
    @abstractmethod
    def parse_code(self, code: str, file_path: Optional[Union[str, Path]] = None) -> T:
        """
        Parse a string of code and generate an AST.
        
        Args:
            code: Code string to parse
            file_path: Optional path for context
            
        Returns:
            Generated AST
            
        Raises:
            ParseError: If parsing fails
        """
        pass
    
    @abstractmethod
    def get_symbols(self, ast: T) -> List[Dict[str, Any]]:
        """
        Extract symbols (functions, classes, variables) from an AST.
        
        Args:
            ast: AST to extract symbols from
            
        Returns:
            List of symbols with metadata
        """
        pass
    
    @abstractmethod
    def get_dependencies(self, ast: T) -> List[Dict[str, Any]]:
        """
        Extract dependencies (imports, requires) from an AST.
        
        Args:
            ast: AST to extract dependencies from
            
        Returns:
            List of dependencies with metadata
        """
        pass
    
    def get_errors(self) -> List[ParseError]:
        """
        Get any errors that occurred during parsing.
        
        Returns:
            List of parse errors
        """
        return self.errors

class CodegenParser(BaseParser[ASTNode]):
    """
    Parser implementation using Codegen SDK for AST generation.
    
    This parser leverages the Codegen SDK to parse code and generate
    abstract syntax trees for analysis.
    """
    
    def __init__(
        self,
        language: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        codebase: Optional[Codebase] = None
    ):
        """
        Initialize the Codegen parser.
        
        Args:
            language: Programming language to parse
            config: Additional configuration options
            codebase: Optional Codebase instance to use
        """
        super().__init__(language, config)
        self.codebase = codebase
        
        # Map Codegen node types to our ASTNode types
        self.node_type_mapping = {
            "function": "function",
            "class": "class",
            "method": "method",
            "variable": "variable",
            "import": "import",
            "module": "module",
            # Add more mappings as needed
        }
    
    def parse_file(self, file_path: Union[str, Path]) -> ASTNode:
        """
        Parse a file using Codegen SDK and convert to our ASTNode format.
        
        Args:
            file_path: Path to the file to parse
            
        Returns:
            ASTNode representing the file
            
        Raises:
            ParseError: If parsing fails
        """
        try:
            # Ensure file_path is a Path object
            if isinstance(file_path, str):
                file_path = Path(file_path)
            
            # Read the file content
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            # Parse the code
            return self.parse_code(code, file_path)
            
        except Exception as e:
            error = ParseError(f"Error parsing file {file_path}: {str(e)}")
            self.errors.append(error)
            raise error
    
    def parse_code(self, code: str, file_path: Optional[Union[str, Path]] = None) -> ASTNode:
        """
        Parse a string of code using Codegen SDK and convert to our ASTNode format.
        
        Args:
            code: Code string to parse
            file_path: Optional path for context
            
        Returns:
            ASTNode representing the code
            
        Raises:
            ParseError: If parsing fails
        """
        try:
            # If we don't have a codebase, we can't parse the code
            if not self.codebase:
                raise ParseError("No codebase provided for parsing")
            
            # Use Codegen SDK to parse the code
            # This is a simplified approach - in a real implementation,
            # you would use the appropriate Codegen SDK methods
            
            # Create a root node for the file
            root_node = ASTNode(
                node_type="file",
                value=str(file_path) if file_path else None,
                start_position=(1, 1),
                end_position=None,  # Will be set later
                metadata={"language": self.language}
            )
            
            # In a real implementation, you would:
            # 1. Use Codegen SDK to parse the code into its AST
            # 2. Traverse the Codegen AST and convert to our ASTNode format
            # 3. Build the tree structure
            
            # For now, we'll create a simplified structure based on basic parsing
            self._build_simplified_ast(root_node, code)
            
            return root_node
            
        except Exception as e:
            error = ParseError(f"Error parsing code: {str(e)}")
            self.errors.append(error)
            raise error
    
    def _build_simplified_ast(self, root_node: ASTNode, code: str) -> None:
        """
        Build a simplified AST from code.
        
        This is a placeholder implementation that creates a basic structure
        based on simple parsing rules. In a real implementation, you would
        use the Codegen SDK's parsing capabilities.
        
        Args:
            root_node: Root node to build from
            code: Code string to parse
        """
        lines = code.split('\n')
        line_count = len(lines)
        
        # Set the end position of the root node
        root_node.end_position = (line_count, len(lines[-1]) if lines else 0)
        
        # Simple parsing for Python-like code
        # This is just a demonstration - real parsing would be more sophisticated
        current_class = None
        current_function = None
        
        for i, line in enumerate(lines):
            line_num = i + 1
            stripped = line.strip()
            
            # Class definition
            if stripped.startswith('class ') and ':' in stripped:
                class_name = stripped[6:stripped.find(':')].strip()
                if '(' in class_name:
                    class_name = class_name[:class_name.find('(')].strip()
                
                class_node = ASTNode(
                    node_type="class",
                    value=class_name,
                    start_position=(line_num, line.find('class') + 1),
                    end_position=None,  # Will be set when the class ends
                    metadata={"indentation": len(line) - len(stripped)}
                )
                
                root_node.add_child(class_node)
                current_class = class_node
            
            # Function/method definition
            elif stripped.startswith('def ') and ':' in stripped:
                func_name = stripped[4:stripped.find('(')].strip()
                
                func_node = ASTNode(
                    node_type="function" if not current_class else "method",
                    value=func_name,
                    start_position=(line_num, line.find('def') + 1),
                    end_position=None,  # Will be set when the function ends
                    metadata={
                        "indentation": len(line) - len(stripped),
                        "class": current_class.value if current_class else None
                    }
                )
                
                if current_class and (len(line) - len(stripped)) > current_class.metadata["indentation"]:
                    current_class.add_child(func_node)
                else:
                    root_node.add_child(func_node)
                
                current_function = func_node
            
            # Import statement
            elif stripped.startswith('import ') or stripped.startswith('from '):
                import_node = ASTNode(
                    node_type="import",
                    value=stripped,
                    start_position=(line_num, 1),
                    end_position=(line_num, len(line)),
                    metadata={}
                )
                
                root_node.add_child(import_node)
            
            # Variable assignment
            elif '=' in stripped and not stripped.startswith('#'):
                var_name = stripped[:stripped.find('=')].strip()
                
                var_node = ASTNode(
                    node_type="variable",
                    value=var_name,
                    start_position=(line_num, 1),
                    end_position=(line_num, len(line)),
                    metadata={}
                )
                
                if current_function and (len(line) - len(stripped)) > current_function.metadata["indentation"]:
                    current_function.add_child(var_node)
                elif current_class and (len(line) - len(stripped)) > current_class.metadata["indentation"]:
                    current_class.add_child(var_node)
                else:
                    root_node.add_child(var_node)
    
    def get_symbols(self, ast: ASTNode) -> List[Dict[str, Any]]:
        """
        Extract symbols from an AST.
        
        Args:
            ast: AST to extract symbols from
            
        Returns:
            List of symbols with metadata
        """
        symbols = []
        
        # Find all class nodes
        class_nodes = ast.find_nodes_by_type("class")
        for node in class_nodes:
            symbols.append({
                "type": "class",
                "name": node.value,
                "start_line": node.start_position[0] if node.start_position else None,
                "end_line": node.end_position[0] if node.end_position else None,
                "methods": [
                    child.value for child in node.children 
                    if child.node_type == "method"
                ]
            })
        
        # Find all function nodes (excluding methods)
        function_nodes = [
            node for node in ast.find_nodes_by_type("function")
            if node.parent and node.parent.node_type != "class"
        ]
        
        for node in function_nodes:
            symbols.append({
                "type": "function",
                "name": node.value,
                "start_line": node.start_position[0] if node.start_position else None,
                "end_line": node.end_position[0] if node.end_position else None,
                "class": node.metadata.get("class")
            })
        
        # Find global variables
        var_nodes = [
            node for node in ast.find_nodes_by_type("variable")
            if node.parent and node.parent.node_type == "file"
        ]
        
        for node in var_nodes:
            symbols.append({
                "type": "variable",
                "name": node.value,
                "start_line": node.start_position[0] if node.start_position else None,
                "line": node.start_position[0] if node.start_position else None
            })
        
        return symbols
    
    def get_dependencies(self, ast: ASTNode) -> List[Dict[str, Any]]:
        """
        Extract dependencies from an AST.
        
        Args:
            ast: AST to extract dependencies from
            
        Returns:
            List of dependencies with metadata
        """
        dependencies = []
        
        # Find all import nodes
        import_nodes = ast.find_nodes_by_type("import")
        
        for node in import_nodes:
            # Parse the import statement
            import_value = node.value
            
            if import_value.startswith('import '):
                # Handle 'import x' or 'import x as y'
                imported = import_value[7:].strip()
                if ' as ' in imported:
                    module, alias = imported.split(' as ', 1)
                    dependencies.append({
                        "type": "import",
                        "module": module.strip(),
                        "alias": alias.strip(),
                        "line": node.start_position[0] if node.start_position else None
                    })
                else:
                    dependencies.append({
                        "type": "import",
                        "module": imported,
                        "line": node.start_position[0] if node.start_position else None
                    })
            
            elif import_value.startswith('from '):
                # Handle 'from x import y'
                parts = import_value.split(' import ')
                if len(parts) == 2:
                    module = parts[0][5:].strip()  # Remove 'from '
                    imports = parts[1].strip()
                    
                    for imp in imports.split(','):
                        imp = imp.strip()
                        if ' as ' in imp:
                            name, alias = imp.split(' as ', 1)
                            dependencies.append({
                                "type": "from_import",
                                "module": module,
                                "name": name.strip(),
                                "alias": alias.strip(),
                                "line": node.start_position[0] if node.start_position else None
                            })
                        else:
                            dependencies.append({
                                "type": "from_import",
                                "module": module,
                                "name": imp,
                                "line": node.start_position[0] if node.start_position else None
                            })
        
        return dependencies

class PythonParser(CodegenParser):
    """
    Specialized parser for Python code.
    
    This parser extends the CodegenParser with Python-specific parsing
    capabilities and AST traversal.
    """
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        codebase: Optional[Codebase] = None
    ):
        """
        Initialize the Python parser.
        
        Args:
            config: Additional configuration options
            codebase: Optional Codebase instance to use
        """
        super().__init__("python", config, codebase)
    
    def parse_code(self, code: str, file_path: Optional[Union[str, Path]] = None) -> ASTNode:
        """
        Parse Python code with enhanced Python-specific parsing.
        
        Args:
            code: Python code string to parse
            file_path: Optional path for context
            
        Returns:
            ASTNode representing the code
            
        Raises:
            ParseError: If parsing fails
        """
        try:
            # First use the base implementation
            ast = super().parse_code(code, file_path)
            
            # Enhance with Python-specific parsing
            # In a real implementation, you would use Python's ast module
            # or another Python-specific parser
            
            # For demonstration purposes, we'll just return the base AST
            return ast
            
        except Exception as e:
            error = ParseError(f"Error parsing Python code: {str(e)}")
            self.errors.append(error)
            raise error

class JavaScriptParser(CodegenParser):
    """
    Specialized parser for JavaScript code.
    
    This parser extends the CodegenParser with JavaScript-specific parsing
    capabilities and AST traversal.
    """
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        codebase: Optional[Codebase] = None
    ):
        """
        Initialize the JavaScript parser.
        
        Args:
            config: Additional configuration options
            codebase: Optional Codebase instance to use
        """
        super().__init__("javascript", config, codebase)
    
    def parse_code(self, code: str, file_path: Optional[Union[str, Path]] = None) -> ASTNode:
        """
        Parse JavaScript code with enhanced JavaScript-specific parsing.
        
        Args:
            code: JavaScript code string to parse
            file_path: Optional path for context
            
        Returns:
            ASTNode representing the code
            
        Raises:
            ParseError: If parsing fails
        """
        try:
            # First use the base implementation
            ast = super().parse_code(code, file_path)
            
            # Enhance with JavaScript-specific parsing
            # In a real implementation, you would use a JavaScript parser
            # like esprima, acorn, or babel-parser
            
            # For demonstration purposes, we'll just return the base AST
            return ast
            
        except Exception as e:
            error = ParseError(f"Error parsing JavaScript code: {str(e)}")
            self.errors.append(error)
            raise error

class TypeScriptParser(JavaScriptParser):
    """
    Specialized parser for TypeScript code.
    
    This parser extends the JavaScriptParser with TypeScript-specific parsing
    capabilities and AST traversal.
    """
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        codebase: Optional[Codebase] = None
    ):
        """
        Initialize the TypeScript parser.
        
        Args:
            config: Additional configuration options
            codebase: Optional Codebase instance to use
        """
        # Initialize with JavaScript as the base language
        super().__init__(config, codebase)
        # Override the language
        self.language = "typescript"
    
    def parse_code(self, code: str, file_path: Optional[Union[str, Path]] = None) -> ASTNode:
        """
        Parse TypeScript code with enhanced TypeScript-specific parsing.
        
        Args:
            code: TypeScript code string to parse
            file_path: Optional path for context
            
        Returns:
            ASTNode representing the code
            
        Raises:
            ParseError: If parsing fails
        """
        try:
            # First use the JavaScript implementation
            ast = super().parse_code(code, file_path)
            
            # Enhance with TypeScript-specific parsing
            # In a real implementation, you would use the TypeScript compiler API
            # or another TypeScript-specific parser
            
            # For demonstration purposes, we'll just return the base AST
            return ast
            
        except Exception as e:
            error = ParseError(f"Error parsing TypeScript code: {str(e)}")
            self.errors.append(error)
            raise error

def create_parser(
    language: str,
    config: Optional[Dict[str, Any]] = None,
    codebase: Optional[Codebase] = None
) -> BaseParser:
    """
    Factory function to create a parser for the specified language.
    
    Args:
        language: Programming language to parse
        config: Additional configuration options
        codebase: Optional Codebase instance to use
        
    Returns:
        Appropriate parser instance for the language
        
    Raises:
        ValueError: If the language is not supported
    """
    language = language.lower()
    
    if language == "python":
        return PythonParser(config, codebase)
    elif language == "javascript":
        return JavaScriptParser(config, codebase)
    elif language == "typescript":
        return TypeScriptParser(config, codebase)
    else:
        # Default to generic parser
        return CodegenParser(language, config, codebase)

def parse_file(
    file_path: Union[str, Path],
    language: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    codebase: Optional[Codebase] = None
) -> ASTNode:
    """
    Convenience function to parse a file.
    
    Args:
        file_path: Path to the file to parse
        language: Programming language of the file (auto-detected if None)
        config: Additional configuration options
        codebase: Optional Codebase instance to use
        
    Returns:
        ASTNode representing the file
        
    Raises:
        ParseError: If parsing fails
    """
    # Ensure file_path is a Path object
    if isinstance(file_path, str):
        file_path = Path(file_path)
    
    # Auto-detect language from file extension if not provided
    if language is None:
        ext = file_path.suffix.lower()
        if ext == '.py':
            language = 'python'
        elif ext == '.js':
            language = 'javascript'
        elif ext == '.ts':
            language = 'typescript'
        else:
            language = 'generic'
    
    # Create parser and parse file
    parser = create_parser(language, config, codebase)
    return parser.parse_file(file_path)

def parse_code(
    code: str,
    language: str,
    file_path: Optional[Union[str, Path]] = None,
    config: Optional[Dict[str, Any]] = None,
    codebase: Optional[Codebase] = None
) -> ASTNode:
    """
    Convenience function to parse a string of code.
    
    Args:
        code: Code string to parse
        language: Programming language of the code
        file_path: Optional path for context
        config: Additional configuration options
        codebase: Optional Codebase instance to use
        
    Returns:
        ASTNode representing the code
        
    Raises:
        ParseError: If parsing fails
    """
    # Create parser and parse code
    parser = create_parser(language, config, codebase)
    return parser.parse_code(code, file_path)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Code Parser for Analyzers")
    parser.add_argument("file", help="File to parse")
    parser.add_argument("--language", choices=["python", "javascript", "typescript"],
                        help="Programming language (auto-detected if not provided)")
    parser.add_argument("--output", help="Output file for AST (prints to stdout if not provided)")
    
    args = parser.parse_args()
    
    try:
        ast = parse_file(args.file, args.language)
        
        if args.output:
            import json
            with open(args.output, 'w') as f:
                json.dump(ast.to_dict(), f, indent=2)
        else:
            print(f"Successfully parsed {args.file}")
            print(f"Found {len(ast.children)} top-level nodes")
            
            # Print symbols
            parser = create_parser(args.language or "generic")
            symbols = parser.get_symbols(ast)
            print(f"\nSymbols found ({len(symbols)}):")
            for symbol in symbols:
                print(f"  {symbol['type']}: {symbol['name']}")
            
            # Print dependencies
            dependencies = parser.get_dependencies(ast)
            print(f"\nDependencies found ({len(dependencies)}):")
            for dep in dependencies:
                if dep["type"] == "import":
                    print(f"  import {dep['module']}")
                elif dep["type"] == "from_import":
                    print(f"  from {dep['module']} import {dep['name']}")
    
    except ParseError as e:
        print(f"Error: {e}")
        sys.exit(1)

