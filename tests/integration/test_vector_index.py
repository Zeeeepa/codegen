from pathlib import Path

import numpy as np
import pytest

from codegen.extensions.vector_index import VectorIndex
from codegen.sdk.codebase.factory.get_session import get_codebase_session


def test_vector_index_lifecycle(tmpdir) -> None:
    # language=python
    content1 = """
def hello():
    print("Hello, world!")

def goodbye():
    print("Goodbye, world!")
"""

    # language=python
    content2 = """
def greet(name: str):
    print(f"Hi {name}!")
"""

    with get_codebase_session(tmpdir=tmpdir, files={"greetings.py": content1, "hello.py": content2}) as codebase:
        # Test construction and initial indexing
        index = VectorIndex(codebase)
        index.create()

        # Verify initial state
        assert index.E is not None
        assert index.file_paths is not None
        assert len(index.file_paths) == 2  # Both files should be indexed
        assert index.commit_hash is not None

        # Test similarity search
        results = index.similarity_search("greeting someone", k=2)
        assert len(results) == 2
        # The greet function should be most relevant to greeting
        assert any("hello.py" in filepath for filepath, _ in results)

        # Test saving
        save_dir = Path(tmpdir) / ".codegen"
        index.save()
        assert save_dir.exists()
        saved_files = list(save_dir.glob("vector_index_*.pkl"))
        assert len(saved_files) == 1

        # Test loading
        new_index = VectorIndex(codebase)
        new_index.load(saved_files[0])
        assert np.array_equal(index.E, new_index.E)
        assert np.array_equal(index.file_paths, new_index.file_paths)
        assert index.commit_hash == new_index.commit_hash

        # Test updating after file changes
        # Add a new function to greetings.py
        greetings_file = codebase.get_file("greetings.py")
        new_content = greetings_file.content + "\n\ndef welcome():\n    print('Welcome!')\n"
        greetings_file.edit(new_content)

        # Update the index
        index.update()

        # Verify the update
        assert len(index.file_paths) >= 2  # Should have at least the original files

        # Search for the new content
        results = index.similarity_search("welcome message", k=2)
        assert len(results) == 2
        # The updated greetings.py should be relevant now
        assert any("greetings.py" in filepath for filepath, _ in results)

        # Test that the commit hash was updated
        # TODO - requires saving
        # assert index.commit_hash != new_index.commit_hash


def test_vector_index_empty_file(tmpdir) -> None:
    """Test that the vector index handles empty files gracefully."""
    with get_codebase_session(tmpdir=tmpdir, files={"empty.py": ""}) as codebase:
        index = VectorIndex(codebase)
        index.create()
        assert len(index.file_paths) == 0  # Empty file should be skipped


def test_vector_index_large_file(tmpdir) -> None:
    """Test that the vector index handles files larger than the token limit."""
    # Create a large file by repeating a simple function many times
    large_content = "def f():\n    print('test')\n\n" * 10000

    with get_codebase_session(tmpdir=tmpdir, files={"large.py": large_content}) as codebase:
        index = VectorIndex(codebase)
        index.create()

        # Should have multiple chunks for the large file
        assert len([fp for fp in index.file_paths if "large.py" in fp]) > 1

        # Test searching in large file
        results = index.similarity_search("function that prints test", k=1)
        assert len(results) == 1
        assert "large.py" in results[0][0]


def test_vector_index_invalid_operations(tmpdir) -> None:
    """Test that the vector index properly handles invalid operations."""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": "print('test')"}) as codebase:
        index = VectorIndex(codebase)

        # Test searching before creating index
        with pytest.raises(ValueError, match="No embeddings available"):
            index.similarity_search("test")

        # Test saving before creating index
        with pytest.raises(ValueError, match="No embeddings to save"):
            index.save()

        # Test updating before creating index
        with pytest.raises(ValueError, match="No index to update"):
            index.update()

        # Test loading from non-existent path
        with pytest.raises(FileNotFoundError):
            index.load("nonexistent.pkl")
