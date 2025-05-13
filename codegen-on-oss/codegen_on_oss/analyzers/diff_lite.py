"""Lightweight diff utilities for analyzing code changes."""

import logging
from enum import Enum
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Union

logger = logging.getLogger(__name__)


class ChangeType(str, Enum):
    """Enum representing the type of change in a diff."""

    ADDED = "added"
    DELETED = "deleted"
    MODIFIED = "modified"
    RENAMED = "renamed"
    UNKNOWN = "unknown"

    @classmethod
    def from_git_change_type(cls, git_change_type: str) -> "ChangeType":
        """Convert a git change type to a ChangeType enum.

        Args:
            git_change_type: The git change type string

        Returns:
            The corresponding ChangeType enum value
        """
        mapping = {
            "A": cls.ADDED,
            "D": cls.DELETED,
            "M": cls.MODIFIED,
            "R": cls.RENAMED,
        }
        return mapping.get(git_change_type, cls.UNKNOWN)


class DiffLite(NamedTuple):
    """Lightweight representation of a diff.

    This class provides a simplified view of a diff, containing only the essential
    information needed for analysis.

    Attributes:
        change_type: The type of change (added, deleted, modified, renamed)
        path: The path of the file
        rename_from: The original path if the file was renamed
        rename_to: The new path if the file was renamed
        old_content: The content of the file before the change
        new_content: The content of the file after the change
    """

    change_type: ChangeType
    path: Path
    rename_from: Optional[Path] = None
    rename_to: Optional[Path] = None
    old_content: Optional[bytes] = None
    new_content: Optional[bytes] = None

    @property
    def is_added(self) -> bool:
        """Check if the file was added.

        Returns:
            True if the file was added, False otherwise
        """
        return self.change_type == ChangeType.ADDED

    @property
    def is_deleted(self) -> bool:
        """Check if the file was deleted.

        Returns:
            True if the file was deleted, False otherwise
        """
        return self.change_type == ChangeType.DELETED

    @property
    def is_modified(self) -> bool:
        """Check if the file was modified.

        Returns:
            True if the file was modified, False otherwise
        """
        return self.change_type == ChangeType.MODIFIED

    @property
    def is_renamed(self) -> bool:
        """Check if the file was renamed.

        Returns:
            True if the file was renamed, False otherwise
        """
        return self.change_type == ChangeType.RENAMED

    @classmethod
    def from_git_diff(cls, git_diff) -> "DiffLite":
        """Create a DiffLite instance from a git diff.

        Args:
            git_diff: A git diff object

        Returns:
            A DiffLite instance representing the diff
        """
        # Get the content of the file before and after the change
        old = None
        new = None

        if git_diff.b_blob:
            new = git_diff.b_blob.data_stream.read()

        if git_diff.a_blob:
            old = git_diff.a_blob.data_stream.read()

        # Ensure path is never None
        path = Path(git_diff.a_path) if git_diff.a_path else Path("")

        return cls(
            change_type=ChangeType.from_git_change_type(git_diff.change_type),
            path=path,
            rename_from=Path(git_diff.rename_from) if git_diff.rename_from else None,
            rename_to=Path(git_diff.rename_to) if git_diff.rename_to else None,
            old_content=old,
            new_content=new,
        )

