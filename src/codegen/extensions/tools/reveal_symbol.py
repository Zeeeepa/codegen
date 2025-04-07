"""Tool for revealing symbol definitions and usages."""

from typing import ClassVar, List, Optional, Dict, Any, Union

from langchain_core.messages import ToolMessage
from pydantic import Field

from codegen.sdk.core.codebase import Codebase
from codegen.sdk.core.symbol import Symbol
from codegen.sdk.core.function import Function
from codegen.sdk.core.class_definition import Class
from codegen.sdk.extensions.resolution import resolve_symbol

from .observation import Observation


class SymbolLocation:
    """Information about a symbol's location in code."""

    filepath: str
    start_line: int
    end_line: int
    start_column: Optional[int] = None
    end_column: Optional[int] = None

    def __init__(
        self,
        filepath: str,
        start_line: int,
        end_line: int,
        start_column: Optional[int] = None,
        end_column: Optional[int] = None,
    ):
        self.filepath = filepath
        self.start_line = start_line
        self.end_line = end_line
        self.start_column = start_column
        self.end_column = end_column

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "filepath": self.filepath,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "start_column": self.start_column,
            "end_column": self.end_column,
        }


class SymbolReference:
    """Information about a reference to a symbol."""

    filepath: str
    line: int
    column: Optional[int] = None
    context: Optional[str] = None

    def __init__(
        self,
        filepath: str,
        line: int,
        column: Optional[int] = None,
        context: Optional[str] = None,
    ):
        self.filepath = filepath
        self.line = line
        self.column = column
        self.context = context

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "filepath": self.filepath,
            "line": self.line,
            "column": self.column,
            "context": self.context,
        }


class RevealSymbolObservation(Observation):
    """Response from revealing a symbol."""

    symbol_name: str = Field(
        description="Name of the symbol",
    )
    symbol_type: str = Field(
        description="Type of the symbol (function, class, variable, etc.)",
    )
    definition: Optional[SymbolLocation] = Field(
        default=None,
        description="Location of the symbol definition",
    )
    references: List[SymbolReference] = Field(
        default_factory=list,
        description="List of references to the symbol",
    )
    source_code: Optional[str] = Field(
        default=None,
        description="Source code of the symbol definition",
    )
    docstring: Optional[str] = Field(
        default=None,
        description="Docstring of the symbol, if available",
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata about the symbol",
    )

    str_template: ClassVar[str] = "Symbol {symbol_name} ({symbol_type})"

    def render(self, tool_call_id: str) -> ToolMessage:
        """Render the symbol information."""
        if self.status == "error":
            return ToolMessage(
                content=f"[ERROR REVEALING SYMBOL]: {self.symbol_name}: {self.error}",
                status=self.status,
                tool_call_id=tool_call_id,
                name="reveal_symbol",
                additional_kwargs={
                    "error": self.error,
                },
            )

        # Build content with symbol information
        lines = [f"[SYMBOL]: {self.symbol_name} ({self.symbol_type})"]

        # Add definition location
        if self.definition:
            lines.append(
                f"\nDefined in {self.definition.filepath} (lines {self.definition.start_line}-{self.definition.end_line})"
            )

        # Add docstring if available
        if self.docstring:
            lines.append(f"\nDocumentation:\n{self.docstring}")

        # Add source code if available
        if self.source_code:
            lines.append(f"\nSource code:\n```\n{self.source_code}\n```")

        # Add references
        if self.references:
            lines.append(f"\nReferences ({len(self.references)}):")
            for i, ref in enumerate(self.references[:10], 1):  # Limit to 10 references
                context = f": {ref.context}" if ref.context else ""
                lines.append(f"{i}. {ref.filepath}:{ref.line}{context}")

            if len(self.references) > 10:
                lines.append(f"... and {len(self.references) - 10} more references")

        # Add metadata if available
        if self.metadata:
            lines.append("\nMetadata:")
            for key, value in self.metadata.items():
                if isinstance(value, (dict, list)):
                    continue  # Skip complex metadata
                lines.append(f"- {key}: {value}")

        return ToolMessage(
            content="\n".join(lines),
            status=self.status,
            tool_call_id=tool_call_id,
            name="reveal_symbol",
        )


def _get_symbol_metadata(symbol: Symbol) -> Dict[str, Any]:
    """Extract metadata from a symbol based on its type."""
    metadata = {}

    if isinstance(symbol, Function):
        metadata["return_type"] = getattr(symbol, "return_type", None)
        metadata["parameters"] = getattr(symbol, "parameters", [])
        metadata["is_async"] = getattr(symbol, "is_async", False)
        metadata["is_generator"] = getattr(symbol, "is_generator", False)
        metadata["is_method"] = getattr(symbol, "is_method", False)
        metadata["is_static"] = getattr(symbol, "is_static", False)
        metadata["is_class_method"] = getattr(symbol, "is_class_method", False)
        metadata["is_property"] = getattr(symbol, "is_property", False)

    elif isinstance(symbol, Class):
        metadata["base_classes"] = getattr(symbol, "base_classes", [])
        metadata["methods"] = [m.name for m in getattr(symbol, "methods", [])]
        metadata["properties"] = [p.name for p in getattr(symbol, "properties", [])]
        metadata["is_abstract"] = getattr(symbol, "is_abstract", False)

    # Check for Variable type by name instead of direct import
    elif type(symbol).__name__ == "Variable":
        metadata["type"] = getattr(symbol, "type", None)
        metadata["is_constant"] = getattr(symbol, "is_constant", False)

    return metadata


def _get_symbol_references(symbol: Symbol, max_refs: int = 50) -> List[SymbolReference]:
    """Get references to a symbol."""
    references = []

    try:
        # Try to get references using the symbol's references method
        refs = symbol.references()
        for ref in refs[:max_refs]:
            filepath = ref.filepath
            line = ref.line
            column = getattr(ref, "column", None)
            
            # Try to get context (the line of code where the reference appears)
            context = None
            try:
                file = symbol.codebase.get_file(filepath)
                lines = file.content.splitlines()
                if 0 <= line - 1 < len(lines):
                    context = lines[line - 1].strip()
            except:
                pass
                
            references.append(SymbolReference(filepath, line, column, context))
    except:
        # If references method fails, return empty list
        pass

    return references


def reveal_symbol(
    codebase: Codebase,
    symbol_name: str,
    filepath: Optional[str] = None,
    include_source: bool = True,
    include_references: bool = True,
    max_references: int = 50,
) -> RevealSymbolObservation:
    """Reveal information about a symbol in the codebase.

    This tool provides detailed information about a symbol, including its definition,
    source code, docstring, and references throughout the codebase.

    Args:
        codebase: The codebase to operate on
        symbol_name: Name of the symbol to reveal
        filepath: Optional filepath to help resolve the symbol
        include_source: Whether to include the source code of the symbol
        include_references: Whether to include references to the symbol
        max_references: Maximum number of references to include

    Returns:
        RevealSymbolObservation containing information about the symbol
    """
    try:
        # Try to resolve the symbol
        symbol = resolve_symbol(codebase, symbol_name, filepath)

        if not symbol:
            return RevealSymbolObservation(
                status="error",
                error=f"Symbol '{symbol_name}' not found in the codebase",
                symbol_name=symbol_name,
                symbol_type="unknown",
            )

        # Get symbol type
        symbol_type = type(symbol).__name__

        # Get definition location
        definition = None
        try:
            definition = SymbolLocation(
                filepath=symbol.filepath,
                start_line=symbol.start_line,
                end_line=symbol.end_line,
                start_column=getattr(symbol, "start_column", None),
                end_column=getattr(symbol, "end_column", None),
            )
        except:
            pass

        # Get source code if requested
        source_code = None
        if include_source:
            try:
                source_code = symbol.source
            except:
                try:
                    # Fallback to getting source from file
                    file = codebase.get_file(symbol.filepath)
                    lines = file.content.splitlines()
                    source_code = "\n".join(lines[symbol.start_line - 1 : symbol.end_line])
                except:
                    pass

        # Get docstring
        docstring = getattr(symbol, "docstring", None)

        # Get metadata
        metadata = _get_symbol_metadata(symbol)

        # Get references if requested
        references = []
        if include_references:
            references = _get_symbol_references(symbol, max_references)

        return RevealSymbolObservation(
            status="success",
            symbol_name=symbol_name,
            symbol_type=symbol_type,
            definition=definition,
            references=references,
            source_code=source_code,
            docstring=docstring,
            metadata=metadata,
        )

    except Exception as e:
        return RevealSymbolObservation(
            status="error",
            error=f"Error revealing symbol '{symbol_name}': {str(e)}",
            symbol_name=symbol_name,
            symbol_type="unknown",
        )
