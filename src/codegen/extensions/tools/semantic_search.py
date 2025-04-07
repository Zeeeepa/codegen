"""Semantic search over codebase files."""

from typing import ClassVar, Optional, List, Tuple

from pydantic import Field

from agentgen.extensions.index.code_index import CodeIndex
from agentgen.extensions.index.file_index import FileIndex
from codegen.sdk.core.codebase import Codebase
from codegen.sdk.core.file import File

# Import from our local utils module instead of codegen.sdk.extensions.utils
from agentgen.extensions.utils import get_file_metadata

from .observation import Observation


class SearchResult(Observation):
    """Information about a single search result."""

    filepath: str = Field(
        description="Path to the matching file",
    )
    score: float = Field(
        description="Similarity score of the match",
    )
    preview: str = Field(
        description="Preview of the file content",
    )
    language: Optional[str] = Field(
        default=None,
        description="Programming language of the file",
    )
    size: Optional[int] = Field(
        default=None,
        description="Size of the file in bytes",
    )

    str_template: ClassVar[str] = "{filepath} (score: {score})"


class SemanticSearchObservation(Observation):
    """Response from semantic search over codebase."""

    query: str = Field(
        description="The search query that was used",
    )
    results: list[SearchResult] = Field(
        description="List of search results",
    )
    index_type: str = Field(
        default="file",
        description="Type of index used for search (file or code)",
    )

    str_template: ClassVar[str] = "Found {result_count} results for '{query}'"

    def _get_details(self) -> dict[str, str | int]:
        """Get details for string representation."""
        return {
            "result_count": len(self.results),
            "query": self.query,
        }


def semantic_search(
    codebase: Codebase,
    query: str,
    k: int = 5,
    preview_length: int = 200,
    index_path: Optional[str] = None,
    index_type: str = "file",
    include_metadata: bool = True,
) -> SemanticSearchObservation:
    """Search the codebase using semantic similarity.

    This function provides semantic search over a codebase by using embeddings.
    It supports two types of indices:
    - "file": Searches for similar files (default)
    - "code": Searches for similar code snippets across files

    Args:
        codebase: The codebase to search
        query: The search query in natural language
        k: Number of results to return (default: 5)
        preview_length: Length of content preview in characters (default: 200)
        index_path: Optional path to a saved vector index
        index_type: Type of index to use ("file" or "code")
        include_metadata: Whether to include file metadata in results

    Returns:
        SemanticSearchObservation containing search results or error information.
    """
    try:
        # Initialize the appropriate vector index
        if index_type == "code":
            index = CodeIndex(codebase)
        else:
            index = FileIndex(codebase)

        # Try to load existing index
        try:
            if index_path:
                index.load(index_path)
            else:
                index.load()
        except FileNotFoundError:
            # Create new index if none exists
            index.create()
            if index_path:
                index.save(index_path)
            else:
                index.save()

        # Perform search
        results = index.similarity_search(query, k=k)

        # Format results with previews
        formatted_results = []
        for item, score in results:
            # Handle different result types based on index type
            if index_type == "code":
                # For code index, item is a tuple of (file, start_line, end_line)
                file, start_line, end_line = item
                filepath = file.filepath
                # Extract the relevant code snippet
                lines = file.content.splitlines()
                snippet = "\n".join(lines[start_line:end_line+1])
                preview = snippet[:preview_length].replace("\n", " ").strip()
                if len(snippet) > preview_length:
                    preview += "..."
            else:
                # For file index, item is a File object
                file = item
                filepath = file.filepath
                preview = file.content[:preview_length].replace("\n", " ").strip()
                if len(file.content) > preview_length:
                    preview += "..."

            # Get file metadata if requested
            language = None
            size = None
            if include_metadata:
                metadata = get_file_metadata(file)
                language = metadata.get("language")
                size = metadata.get("size")

            formatted_results.append(
                SearchResult(
                    status="success",
                    filepath=filepath,
                    score=float(score),
                    preview=preview,
                    language=language,
                    size=size,
                )
            )

        return SemanticSearchObservation(
            status="success",
            query=query,
            results=formatted_results,
            index_type=index_type,
        )

    except Exception as e:
        return SemanticSearchObservation(
            status="error",
            error=f"Failed to perform semantic search: {e!s}",
            query=query,
            results=[],
            index_type=index_type,
        )
