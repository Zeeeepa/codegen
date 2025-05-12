from enum import IntEnum, auto
from os import PathLike
from pathlib import Path
from typing import NamedTuple, Self

from git import Diff
from watchfiles import Change


class ChangeType(IntEnum):
    """
    Enumeration of change types for tracking file modifications.

    Attributes:
        Modified: File content has been modified
        Removed: File has been deleted
        Renamed: File has been renamed
        Added: New file has been added
    """

    Modified = auto()
    Removed = auto()
    Renamed = auto()
    Added = auto()

    @staticmethod
    def from_watch_change_type(change_type: Change) -> "ChangeType":
        """
        Convert watchfiles Change type to ChangeType.

        Args:
            change_type: The watchfiles Change enum value

        Returns:
            Corresponding ChangeType enum value
        """
        if change_type is Change.added:
            return ChangeType.Added
        elif change_type is Change.deleted:
            return ChangeType.Removed
        elif change_type is Change.modified:
            return ChangeType.Modified

        msg = f"Unsupported watch change type: {change_type}"
        raise ValueError(msg)

    @staticmethod
    def from_git_change_type(change_type: str | None) -> "ChangeType":
        """
        Convert git change type string to ChangeType.

        Args:
            change_type: Git change type string ('M', 'D', 'R', 'A')

        Returns:
            Corresponding ChangeType enum value

        Raises:
            ValueError: If the change type is not supported
        """
        if change_type == "M":
            return ChangeType.Modified
        if change_type == "D":
            return ChangeType.Removed
        if change_type == "R":
            return ChangeType.Renamed
        if change_type == "A":
            return ChangeType.Added

        msg = f"Invalid git change type: {change_type}"
        raise ValueError(msg)


class DiffLite(NamedTuple):
    """
    Simple diff implementation for tracking file changes during code analysis.

    This lightweight diff implementation provides support for tracking file changes,
    including modifications, removals, renames, and additions.

    Attributes:
        change_type: Type of change (Modified, Removed, Renamed, Added)
        path: Path to the file
        rename_from: Original path for renamed files (None for non-renamed files)
        rename_to: New path for renamed files (None for non-renamed files)
        old_content: Previous content of the file (None if not available)
    """

    change_type: ChangeType
    path: Path
    rename_from: Path | None = None
    rename_to: Path | None = None
    old_content: bytes | None = None

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
        old = None
        if git_diff.a_blob:
            old = git_diff.a_blob.data_stream.read()

        return cls(
            change_type=ChangeType.from_git_change_type(git_diff.change_type),
            path=Path(git_diff.a_path) if git_diff.a_path else None,
            rename_from=Path(git_diff.rename_from) if git_diff.rename_from else None,
            rename_to=Path(git_diff.rename_to) if git_diff.rename_to else None,
            old_content=old,
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
        if diff_lite.change_type == ChangeType.Added:
            change_type = ChangeType.Removed
        elif diff_lite.change_type == ChangeType.Removed:
            change_type = ChangeType.Added
        else:
            change_type = diff_lite.change_type

        if diff_lite.change_type == ChangeType.Renamed:
            return cls(
                change_type=change_type,
                path=diff_lite.path,
                rename_from=diff_lite.rename_to,
                rename_to=diff_lite.rename_from,
            )

        return cls(change_type=change_type, path=diff_lite.path)
