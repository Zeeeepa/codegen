import os

import pytest

from codegen.sdk.core.codebase import Codebase


def test_codebase_github_repo_path() -> None:
    """Test that trying to create a Codebase with a GitHub repo path raises an error."""
    with pytest.raises(ValueError, match="looks like a GitHub repository path"):
        Codebase(repo_path="fastapi/fastapi")


def test_codebase_github_url_formats() -> None:
    """Test that trying to create a Codebase with various GitHub URL formats raises an error."""
    urls = [
        "https://github.com/fastapi/fastapi",
        "https://github.com/fastapi/fastapi.git",
        "http://github.com/fastapi/fastapi",
        "github.com/fastapi/fastapi",
        "<https://github.com/fastapi/fastapi>",
        "git@github.com:fastapi/fastapi.git",
    ]
    for url in urls:
        with pytest.raises(ValueError, match="is a GitHub URL"):
            Codebase(repo_path=url)


def test_codebase_github_url_with_path() -> None:
    """Test that trying to create a Codebase with a GitHub URL containing extra path components raises an error."""
    with pytest.raises(ValueError, match="is a GitHub URL"):
        Codebase(repo_path="https://github.com/fastapi/fastapi/tree/main")


def test_codebase_nonexistent_local_paths() -> None:
    """Test that trying to create a Codebase with nonexistent local paths raises appropriate errors."""
    # Absolute path
    with pytest.raises(ValueError, match="Local path .* does not exist"):
        Codebase(repo_path="/nonexistent/path")

    # Relative path
    with pytest.raises(ValueError, match="relative paths like"):
        Codebase(repo_path="path/to/file")

    # String variable
    test_string = "some/code/here"
    with pytest.raises(ValueError, match="relative paths like"):
        Codebase(repo_path=test_string)


def test_codebase_valid_path_with_slash(tmp_path) -> None:
    """Test that a valid path containing slashes works correctly."""
    # Initialize git repo at tmp_path
    import subprocess

    subprocess.run(["git", "init"], cwd=str(tmp_path), check=True)

    path = tmp_path / "some/nested/path"
    os.makedirs(path)
    # Create a Python file so language detection works
    with open(path / "test.py", "w") as f:
        f.write("# Test file")
    codebase: Codebase = Codebase(repo_path=str(path))
    # When initializing a Codebase from a path within a git repo, it uses the repo root
    assert str(codebase.repo_path) == str(tmp_path)
