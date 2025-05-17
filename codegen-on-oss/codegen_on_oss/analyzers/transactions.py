#!/usr/bin/env python3
"""
Transactions Module for Analyzers

This module defines transaction classes for code modifications during analysis.
It provides a structured way to represent and execute code changes.
"""

from collections.abc import Callable
from difflib import unified_diff
from enum import IntEnum
from functools import cached_property
from pathlib import Path
from typing import Any, Protocol, runtime_checkable


# Define change types for diffs
class ChangeType(IntEnum):
    """Types of changes that can be made to files."""

    Modified = 1
    Removed = 2
    Renamed = 3
    Added = 4


# Simple diff class for tracking changes
class DiffLite:
    """Simple diff for tracking code changes."""

    def __init__(
        self,
        change_type: ChangeType,
        path: Path,
        rename_from: Path | None = None,
        rename_to: Path | None = None,
        old_content: bytes | None = None,
    ):
        self.change_type = change_type
        self.path = path
        self.rename_from = rename_from
        self.rename_to = rename_to
        self.old_content = old_content


class TransactionPriority(IntEnum):
    """Priority levels for different types of transactions."""

    Remove = 0  # Remove always has highest priority
    Edit = 1  # Edit comes next
    Insert = 2  # Insert is always the last of the edit operations
    # File operations happen last, since they will mess up all other transactions
    FileAdd = 10
    FileRename = 11
    FileRemove = 12


@runtime_checkable
class ContentFunc(Protocol):
    """A function executed to generate a content block dynamically."""

    def __call__(self) -> str: ...


class Transaction:
    """Base class for all transactions.

    A transaction represents an atomic modification to a file in the codebase.
    """

    start_byte: int
    end_byte: int
    file_path: Path
    priority: int | tuple
    transaction_order: TransactionPriority
    transaction_counter: int = 0

    def __init__(
        self,
        start_byte: int,
        end_byte: int,
        file_path: Path,
        priority: int | tuple = 0,
        new_content: str | Callable[[], str] | None = None,
    ) -> None:
        self.start_byte = start_byte
        assert self.start_byte >= 0
        self.end_byte = end_byte
        self.file_path = file_path
        self.priority = priority
        self._new_content = new_content
        self.transaction_id = Transaction.transaction_counter

        Transaction.transaction_counter += 1

    def __repr__(self) -> str:
        return f"<Transaction at bytes [{self.start_byte}:{self.end_byte}] on {self.file_path}>"

    def __hash__(self):
        return hash((
            self.start_byte,
            self.end_byte,
            self.file_path,
            self.priority,
            self.new_content,
        ))

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False

        # Check for everything EXCEPT transaction_id
        return (
            self.start_byte == other.start_byte
            and self.end_byte == other.end_byte
            and self.file_path == other.file_path
            and self.priority == other.priority
            and self._new_content == other._new_content
        )

    @property
    def length(self):
        """Length of the transaction in bytes."""
        return self.end_byte - self.start_byte

    def execute(self):
        """Execute the transaction to modify the file."""
        msg = "Transaction.execute() must be implemented by subclasses"
        raise NotImplementedError(msg)

    def get_diff(self) -> DiffLite:
        """Gets the diff produced by this transaction."""
        msg = "Transaction.get_diff() must be implemented by subclasses"
        raise NotImplementedError(msg)

    def diff_str(self):
        """Human-readable string representation of the change."""
        msg = "Transaction.diff_str() must be implemented by subclasses"
        raise NotImplementedError(msg)

    def _to_sort_key(transaction: "Transaction"):
        """Key function for sorting transactions."""
        # Sort by:
        # 1. Descending start_byte
        # 2. Ascending transaction type
        # 3. Ascending priority
        # 4. Descending time of transaction
        priority = (
            (transaction.priority,)
            if isinstance(transaction.priority, int)
            else transaction.priority
        )

        return (
            -transaction.start_byte,
            transaction.transaction_order.value,
            priority,
            -transaction.transaction_id,
        )

    @cached_property
    def new_content(self) -> str | None:
        """Get the new content, evaluating the content function if necessary."""
        return (
            self._new_content()
            if isinstance(self._new_content, ContentFunc)
            else self._new_content
        )

    @staticmethod
    def create_new_file(filepath: str | Path, content: str) -> "FileAddTransaction":
        """Create a transaction to add a new file."""
        return FileAddTransaction(Path(filepath))

    @staticmethod
    def delete_file(filepath: str | Path) -> "FileRemoveTransaction":
        """Create a transaction to delete a file."""
        # In a real implementation, this would need a File object
        # For now, we'll create a placeholder implementation
        from pathlib import Path

        class FilePlaceholder:
            def __init__(self, path):
                self.path = Path(path)

        return FileRemoveTransaction(FilePlaceholder(filepath))


class RemoveTransaction(Transaction):
    """Transaction to remove content from a file."""

    transaction_order = TransactionPriority.Remove

    exec_func: Callable[[], None] | None = None

    def __init__(
        self,
        start_byte: int,
        end_byte: int,
        file: Any,
        priority: int = 0,
        exec_func: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(start_byte, end_byte, file.path, priority=priority)
        self.file = file
        self.exec_func = exec_func

    def _generate_new_content_bytes(self) -> bytes:
        """Generate the new content bytes after removal."""
        content_bytes = self.file.content_bytes
        new_content_bytes = (
            content_bytes[: self.start_byte] + content_bytes[self.end_byte :]
        )
        return new_content_bytes

    def execute(self) -> None:
        """Removes the content between start_byte and end_byte."""
        self.file.write_bytes(self._generate_new_content_bytes())
        if self.exec_func:
            self.exec_func()

    def get_diff(self) -> DiffLite:
        """Gets the diff produced by this transaction."""
        return DiffLite(
            ChangeType.Modified, self.file_path, old_content=self.file.content_bytes
        )

    def diff_str(self) -> str:
        """Human-readable string representation of the change."""
        diff = "".join(
            unified_diff(
                self.file.content.splitlines(True),
                self._generate_new_content_bytes().decode("utf-8").splitlines(True),
            )
        )
        return f"Remove {self.length} bytes at bytes ({self.start_byte}, {self.end_byte})\n{diff}"


class InsertTransaction(Transaction):
    """Transaction to insert content into a file."""

    transaction_order = TransactionPriority.Insert

    exec_func: Callable[[], None] | None = None

    def __init__(
        self,
        insert_byte: int,
        file: Any,
        new_content: str | Callable[[], str],
        *,
        priority: int | tuple = 0,
        exec_func: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(
            insert_byte,
            insert_byte,
            file.path,
            priority=priority,
            new_content=new_content,
        )
        self.insert_byte = insert_byte
        self.file = file
        self.exec_func = exec_func

    def _generate_new_content_bytes(self) -> bytes:
        """Generate the new content bytes after insertion."""
        if self.new_content is None:
            raise ValueError("Cannot generate content bytes: new_content is None")
        new_bytes = bytes(self.new_content, encoding="utf-8")
        content_bytes = self.file.content_bytes
        head = content_bytes[: self.insert_byte]
        tail = content_bytes[self.insert_byte :]
        new_content_bytes = head + new_bytes + tail
        return new_content_bytes

    def execute(self) -> None:
        """Inserts new_src at the specified byte_index."""
        self.file.write_bytes(self._generate_new_content_bytes())
        if self.exec_func:
            self.exec_func()

    def get_diff(self) -> DiffLite:
        """Gets the diff produced by this transaction."""
        return DiffLite(
            ChangeType.Modified, self.file_path, old_content=self.file.content_bytes
        )

    def diff_str(self) -> str:
        """Human-readable string representation of the change."""
        diff = "".join(
            unified_diff(
                self.file.content.splitlines(True),
                self._generate_new_content_bytes().decode("utf-8").splitlines(True),
            )
        )
        content_length = len(self.new_content) if self.new_content is not None else 0
        return f"Insert {content_length} bytes at bytes ({self.start_byte}, {self.end_byte})\n{diff}"


class EditTransaction(Transaction):
    """Transaction to edit content in a file."""

    transaction_order = TransactionPriority.Edit
    new_content: str

    def __init__(
        self,
        start_byte: int,
        end_byte: int,
        file: Any,
        new_content: str,
        priority: int = 0,
    ) -> None:
        super().__init__(
            start_byte, end_byte, file.path, priority=priority, new_content=new_content
        )
        self.file = file

    def _generate_new_content_bytes(self) -> bytes:
        """Generate the new content bytes after editing."""
        new_bytes = bytes(self.new_content, "utf-8")
        content_bytes = self.file.content_bytes
        new_content_bytes = (
            content_bytes[: self.start_byte]
            + new_bytes
            + content_bytes[self.end_byte :]
        )
        return new_content_bytes

    def execute(self) -> None:
        """Edits the entirety of this node's source to new_src."""
        self.file.write_bytes(self._generate_new_content_bytes())

    def get_diff(self) -> DiffLite:
        """Gets the diff produced by this transaction."""
        return DiffLite(
            ChangeType.Modified, self.file_path, old_content=self.file.content_bytes
        )

    def diff_str(self) -> str:
        """Human-readable string representation of the change."""
        diff = "".join(
            unified_diff(
                self.file.content.splitlines(True),
                self._generate_new_content_bytes().decode("utf-8").splitlines(True),
            )
        )
        return f"Edit {self.length} bytes at bytes ({self.start_byte}, {self.end_byte}), src: ({self.new_content[:50]})\n{diff}"

    def break_down(self) -> list[InsertTransaction] | None:
        """Break down an edit transaction into insert transactions."""
        old = self.file.content_bytes[self.start_byte : self.end_byte]
        new = bytes(self.new_content, "utf-8")
        if old and old in new:
            prefix, suffix = new.split(old, maxsplit=1)
            ret = []
            if suffix:
                ret.append(
                    InsertTransaction(
                        self.end_byte,
                        self.file,
                        suffix.decode("utf-8"),
                        priority=self.priority,
                    )
                )
            if prefix:
                ret.append(
                    InsertTransaction(
                        self.start_byte,
                        self.file,
                        prefix.decode("utf-8"),
                        priority=self.priority,
                    )
                )
            return ret
        return None


class FileAddTransaction(Transaction):
    """Transaction to add a new file."""

    transaction_order = TransactionPriority.FileAdd

    def __init__(
        self,
        file_path: Path,
        priority: int = 0,
    ) -> None:
        super().__init__(0, 0, file_path, priority=priority)

    def execute(self) -> None:
        """Adds a new file."""
        pass  # execute is a no-op as the file is immediately added

    def get_diff(self) -> DiffLite:
        """Gets the diff produced by this transaction."""
        return DiffLite(ChangeType.Added, self.file_path)

    def diff_str(self) -> str:
        """Human-readable string representation of the change."""
        return f"Add file at {self.file_path}"


class FileRenameTransaction(Transaction):
    """Transaction to rename a file."""

    transaction_order = TransactionPriority.FileRename

    def __init__(
        self,
        file: Any,
        new_file_path: str,
        priority: int = 0,
    ) -> None:
        super().__init__(0, 0, file.path, priority=priority, new_content=new_file_path)
        self.new_file_path = (
            file.ctx.to_absolute(new_file_path)
            if hasattr(file, "ctx")
            else Path(new_file_path)
        )
        self.file = file

    def execute(self) -> None:
        """Renames the file."""
        if hasattr(self.file, "ctx") and hasattr(self.file.ctx, "io"):
            self.file.ctx.io.save_files({self.file.path})
        self.file_path.rename(self.new_file_path)

    def get_diff(self) -> DiffLite:
        """Gets the diff produced by this transaction."""
        return DiffLite(
            ChangeType.Renamed,
            self.file_path,
            self.file_path,
            self.new_file_path,
            old_content=self.file.content_bytes
            if hasattr(self.file, "content_bytes")
            else None,
        )

    def diff_str(self) -> str:
        """Human-readable string representation of the change."""
        return f"Rename file from {self.file_path} to {self.new_file_path}"


class FileRemoveTransaction(Transaction):
    """Transaction to remove a file."""

    transaction_order = TransactionPriority.FileRemove

    def __init__(
        self,
        file: Any,
        priority: int = 0,
    ) -> None:
        super().__init__(0, 0, file.path, priority=priority)
        self.file = file

    def execute(self) -> None:
        """Removes the file."""
        if hasattr(self.file, "ctx") and hasattr(self.file.ctx, "io"):
            self.file.ctx.io.delete_file(self.file.path)
        else:
            # Fallback for when ctx.io is not available
            import os

            if os.path.exists(self.file_path):
                os.remove(self.file_path)

    def get_diff(self) -> DiffLite:
        """Gets the diff produced by this transaction."""
        return DiffLite(
            ChangeType.Removed,
            self.file_path,
            old_content=self.file.content_bytes
            if hasattr(self.file, "content_bytes")
            else None,
        )

    def diff_str(self) -> str:
        """Human-readable string representation of the change."""
        return f"Remove file at {self.file_path}"
