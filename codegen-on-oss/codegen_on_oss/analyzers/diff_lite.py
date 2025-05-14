from enum import Enum, auto
from os import PathLike
from pathlib import Path
from typing import NamedTuple, Self, Optional

from git import Diff
from watchfiles import Change


class ChangeType(str, Enum):
    """
    Enumeration of change types for tracking file modifications.

    Attributes:
        Modified: File content has been modified
        Removed: File has been deleted
        Renamed: File has been renamed
        Added: New file has been added
    """

    ADDED = "added"
    DELETED = "deleted"
    MODIFIED = "modified"
    RENAMED = "renamed"
    UNKNOWN = "unknown"

    @staticmethod
    def from_git_change_type(change_type: str) -> "ChangeType":
        """
        Convert git change type to ChangeType.

        Args:
            change_type: The git change type string

        Returns:
            Corresponding ChangeType enum value
        """
        if change_type == "A":
            return ChangeType.ADDED
        elif change_type == "D":
            return ChangeType.DELETED
        elif change_type == "M":
            return ChangeType.MODIFIED
        elif change_type == "R":
            return ChangeType.RENAMED
        else:
            return ChangeType.UNKNOWN
            
    @staticmethod
    def from_watch_change_type(change: Change) -> "ChangeType":
        """
        Convert watchfiles Change enum to ChangeType.
        
        Args:
            change: The watchfiles Change enum value
            
        Returns:
            Corresponding ChangeType enum value
        """
        if change == Change.added:
            return ChangeType.ADDED
        elif change == Change.deleted:
            return ChangeType.DELETED
        elif change == Change.modified:
            return ChangeType.MODIFIED
        else:
            return ChangeType.UNKNOWN


class DiffLite(NamedTuple):
    """
    Simple diff implementation for tracking file changes during code analysis.

    This lightweight diff implementation provides support for tracking file changes,
    including modifications, removals, renames, and additions.

    Attributes:
        change_type: Type of change (added, deleted, modified, renamed)
        path: Path to the file
        rename_from: Original path for renamed files (None for non-renamed files)
        rename_to: New path for renamed files (None for non-renamed files)
        old_content: Previous content of the file (None if not available)
        new_content: New content of the file (None if not available)
    """

    change_type: ChangeType
    path: Path
    rename_from: Optional[Path] = None
    rename_to: Optional[Path] = None
    old_content: bytes = b""
    new_content: bytes = b""

    @classmethod
    def from_watch_change(cls, change: Change, path: PathLike) -> Self:
        """
        Create a DiffLite instance from a watchfiles Change.

        Args:
            change: The watchfiles Change enum value
            path: Path to the file

        Returns:
            DiffLite instance representing the change
        """
        return cls(
            change_type=ChangeType.from_watch_change_type(change),
            path=Path(path),
        )

    @classmethod
    def from_git_diff(cls, git_diff: Diff) -> Self:
        """
        Create a DiffLite instance from a git Diff object.

        Args:
            git_diff: Git Diff object

        Returns:
            DiffLite instance representing the git diff
        """
        old = b""
        new = b""

        if git_diff.a_blob:
            old = git_diff.a_blob.data_stream.read()

        if git_diff.b_blob:
            new = git_diff.b_blob.data_stream.read()

        # Ensure path is never None
        path = Path(git_diff.a_path) if git_diff.a_path else Path("")

        return cls(
            change_type=ChangeType.from_git_change_type(git_diff.change_type or ""),
            path=path,
            rename_from=Path(git_diff.rename_from) if git_diff.rename_from else None,
            rename_to=Path(git_diff.rename_to) if git_diff.rename_to else None,
            old_content=old,
            new_content=new,
        )

    @classmethod
    def from_reverse_diff(cls, diff_lite: "DiffLite") -> Self:
        """
        Create a DiffLite instance that represents the reverse of another DiffLite.

        This is useful for undoing changes or representing the opposite operation.

        Args:
            diff_lite: Original DiffLite instance

        Returns:
            DiffLite instance representing the reverse change
        """
        if diff_lite.change_type == ChangeType.ADDED:
            change_type = ChangeType.DELETED
        elif diff_lite.change_type == ChangeType.DELETED:
            change_type = ChangeType.ADDED
        else:
            change_type = diff_lite.change_type

        if diff_lite.change_type == ChangeType.RENAMED:
            return cls(
                change_type=change_type,
                path=diff_lite.path,
                rename_from=diff_lite.rename_to,
                rename_to=diff_lite.rename_from,
            )

        return cls(change_type=change_type, path=diff_lite.path)
