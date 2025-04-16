"""
MCP Data Models
This module defines the core data models used in the MCP server implementation.
These models represent code elements like symbols, functions, classes, etc.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union

@dataclass
class Location:
    """Represents a location in a file."""
    file_path: str
    start_line: int
    start_column: int
    end_line: int
    end_column: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "file_path": self.file_path,
            "start_line": self.start_line,
            "start_column": self.start_column,
            "end_line": self.end_line,
            "end_column": self.end_column
        }

@dataclass
class Symbol:
    """Base class for all symbols in the codebase."""
    name: str
    location: Optional[Location] = None
    symbol_type: str = "symbol"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "location": self.location.to_dict() if self.location else None,
            "symbol_type": self.symbol_type
        }

@dataclass
class Parameter:
    """Represents a function parameter."""
    name: str
    type_annotation: Optional[str] = None
    default_value: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "type_annotation": self.type_annotation,
            "default_value": self.default_value
        }

@dataclass
class Function(Symbol):
    """Represents a function in the codebase."""
    parameters: List[Parameter] = field(default_factory=list)
    return_type: Optional[str] = None
    is_async: bool = False
    decorators: List[str] = field(default_factory=list)
    docstring: Optional[str] = None
    symbol_type: str = "function"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = super().to_dict()
        result.update({
            "parameters": [p.to_dict() for p in self.parameters],
            "return_type": self.return_type,
            "is_async": self.is_async,
            "decorators": self.decorators,
            "docstring": self.docstring
        })
        return result

@dataclass
class Class(Symbol):
    """Represents a class in the codebase."""
    methods: List[Function] = field(default_factory=list)
    attributes: List[Dict[str, Any]] = field(default_factory=list)
    parent_class_names: List[str] = field(default_factory=list)
    is_abstract: bool = False
    decorators: List[str] = field(default_factory=list)
    symbol_type: str = "class"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = super().to_dict()
        result.update({
            "methods": [m.to_dict() for m in self.methods],
            "attributes": self.attributes,
            "parent_class_names": self.parent_class_names,
            "is_abstract": self.is_abstract,
            "decorators": self.decorators
        })
        return result

@dataclass
class Import(Symbol):
    """Represents an import statement in the codebase."""
    source: str
    alias: Optional[str] = None
    symbol_type: str = "import"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = super().to_dict()
        result.update({
            "source": self.source,
            "alias": self.alias
        })
        return result

@dataclass
class File:
    """Represents a file in the codebase."""
    path: str
    name: str
    symbols: List[Symbol] = field(default_factory=list)
    functions: List[Function] = field(default_factory=list)
    classes: List[Class] = field(default_factory=list)
    imports: List[Import] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    interfaces: List[Dict[str, Any]] = field(default_factory=list)
    types: List[Dict[str, Any]] = field(default_factory=list)
    global_vars: List[Dict[str, Any]] = field(default_factory=list)
    line_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "path": self.path,
            "name": self.name,
            "symbols": [s.to_dict() for s in self.symbols],
            "functions": [f.to_dict() for f in self.functions],
            "classes": [c.to_dict() for c in self.classes],
            "imports": [i.to_dict() for i in self.imports],
            "exports": self.exports,
            "interfaces": self.interfaces,
            "types": self.types,
            "global_vars": self.global_vars,
            "line_count": self.line_count
        }

@dataclass
class SemanticEditTool:
    """Tool for making semantic edits to a file."""
    file: File
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "file": self.file.to_dict()
        }

@dataclass
class ReplacementEditTool:
    """Tool for applying regex-based replacements."""
    pattern: str
    replacement: str
    files: List[File] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "pattern": self.pattern,
            "replacement": self.replacement,
            "files": [f.to_dict() for f in self.files]
        }

@dataclass
class CallGraph:
    """Represents a call graph between functions."""
    nodes: List[Function] = field(default_factory=list)
    edges: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": self.edges
        }

@dataclass
class Codebase:
    """Represents the entire codebase."""
    path: str
    files: List[File] = field(default_factory=list)
    _symbols_cache: Dict[str, Symbol] = field(default_factory=dict)
    _functions_cache: Dict[str, Function] = field(default_factory=dict)
    _classes_cache: Dict[str, Class] = field(default_factory=dict)
    _imports_cache: Dict[str, Import] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "path": self.path,
            "files": [f.to_dict() for f in self.files]
        }
