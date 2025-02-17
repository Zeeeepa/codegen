import os

import pytest

from codegen.sdk.core.codebase import Codebase


def test_codebase_github_repo_path() -> None:
    """Test that trying to create a Codebase with a GitHub repo path raises an error."""
    with pytest.raises(ValueError, match="looks like a GitHub repository path"):
        Codebase(repo_path="fastapi/fastapi")


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
    assert str(codebase.repo_path) == str(path)
