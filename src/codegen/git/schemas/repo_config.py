import logging
import os.path
from pathlib import Path

from pydantic import BaseModel

from codegen.git.schemas.enums import RepoVisibility
from codegen.shared.enums.programming_language import ProgrammingLanguage

logger = logging.getLogger(__name__)


class RepoConfig(BaseModel):
    """All the information about the repo needed to build a codebase"""

    name: str
    full_name: str | None = None
    visibility: RepoVisibility | None = None

    # Codebase fields
    base_dir: str = "/tmp"  # parent directory of the git repo
    language: ProgrammingLanguage = ProgrammingLanguage.PYTHON
    respect_gitignore: bool = True
    base_path: str | None = None  # root directory of the codebase within the repo
    subdirectories: list[str] | None = None

    @classmethod
    def from_repo_path(cls, repo_path: str) -> "RepoConfig":
        name = os.path.basename(repo_path)
        base_dir = os.path.dirname(repo_path)
        return cls(name=name, base_dir=base_dir)

    @property
    def repo_path(self) -> Path:
        return Path(f"{self.base_dir}/{self.name}")

    @property
    def organization_name(self) -> str | None:
        if self.full_name is not None:
            return self.full_name.split("/")[0]

        return None
