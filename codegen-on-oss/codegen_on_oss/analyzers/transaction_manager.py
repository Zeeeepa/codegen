#!/usr/bin/env python3
"""
Transaction Manager Module for Analyzers

This module provides a transaction manager for handling code modifications during analysis.
It's responsible for queuing, sorting, and committing transactions in a controlled manner.
"""

import logging
import math
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from codegen_on_oss.analyzers.transactions import (
    ChangeType,
    DiffLite,
    EditTransaction,
    FileAddTransaction,
    FileRemoveTransaction,
    FileRenameTransaction,
    RemoveTransaction,
    Transaction,
    TransactionPriority,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class MaxTransactionsExceeded(Exception):
    """Raised when the number of transactions exceeds the max_transactions limit."""

    def __init__(self, message: str, threshold: int | None = None):
        super().__init__(message)
        self.threshold = threshold


class MaxPreviewTimeExceeded(Exception):
    """Raised when more than the allotted time has passed for previewing transactions."""

    def __init__(self, message: str, threshold: int | None = None):
        super().__init__(message)
        self.threshold = threshold


class TransactionError(Exception):
    """Exception raised for transaction-related errors."""

    pass


class TransactionManager:
    """Responsible for handling `Transaction` objects - basically an atomic modification of a codebase.

    This is used to queue up transactions and then commit them in bulk.
    """

    def __init__(self) -> None:
        """Initialize the transaction manager."""
        self.queued_transactions: dict[Path, list[Transaction]] = {}
        self.pending_undos: set[Callable[[], None]] = set()
        self._commiting: bool = False
        self.max_transactions: int | None = None  # None = no limit
        self.stopwatch_start: float | None = None
        self.stopwatch_max_seconds: int | None = None  # None = no limit
        self.session: dict[str, Any] = {}  # Session data for tracking state

    def sort_transactions(self) -> None:
        """Sort transactions by priority and position."""
        for _file_path, file_transactions in self.queued_transactions.items():
            file_transactions.sort(key=Transaction._to_sort_key)

    def clear_transactions(self) -> None:
        """Clear all transactions and reset limits.

        Should be called between analysis runs to remove any potential extraneous transactions.
        """
        if len(self.queued_transactions) > 0:
            logger.warning("Not all transactions have been committed")
            self.queued_transactions.clear()
        for undo in self.pending_undos:
            undo()
        self.pending_undos.clear()
        self.set_max_transactions(None)
        self.reset_stopwatch()

    def _format_transactions(self, transactions: list[Transaction]) -> str:
        """Format transactions for display."""
        return "\\n".join([
            ">" * 100 + f"\\n[ID: {t.transaction_id}]: {t.diff_str()}" + "<" * 100
            for t in transactions
        ])

    def get_transactions_str(self) -> str:
        """Returns a human-readable string representation of the transactions."""
        return "\\n\\n\\n".join([
            f"{file_path}:\\n{self._format_transactions(transactions)}"
            for file_path, transactions in self.queued_transactions.items()
        ])

    ####################################################################################################################
    # Transaction Limits
    ####################################################################################################################

    def get_num_transactions(self) -> int:
        """Returns total number of transactions created to date."""
        return sum([
            len(transactions) for transactions in self.queued_transactions.values()
        ])

    def set_max_transactions(self, max_transactions: int | None = None) -> None:
        """Set the maximum number of transactions allowed."""
        self.max_transactions = max_transactions

    def max_transactions_exceeded(self) -> bool:
        """Util method to check if the max transactions limit has been exceeded."""
        if self.max_transactions is None:
            return False
        return self.get_num_transactions() >= self.max_transactions

    ####################################################################################################################
    # Stopwatch
    ####################################################################################################################

    def reset_stopwatch(self, max_seconds: int | None = None) -> None:
        """Reset the stopwatch with an optional time limit."""
        self.stopwatch_start = time.time()
        self.stopwatch_max_seconds = max_seconds

    def is_time_exceeded(self) -> bool:
        """Check if the stopwatch time limit has been exceeded."""
        if self.stopwatch_max_seconds is None or self.stopwatch_start is None:
            return False
        else:
            num_seconds = time.time() - self.stopwatch_start
            return num_seconds > self.stopwatch_max_seconds

    ####################################################################################################################
    # Transaction Creation
    ####################################################################################################################

    def add_file_add_transaction(self, filepath: Path) -> None:
        """Add a transaction to create a new file."""
        t = FileAddTransaction(filepath)
        self.add_transaction(t)

    def add_file_rename_transaction(self, file: Any, new_filepath: str) -> None:
        """Add a transaction to rename a file."""
        t = FileRenameTransaction(file, new_filepath)
        self.add_transaction(t)

    def add_file_remove_transaction(self, file: Any) -> None:
        """Add a transaction to remove a file."""
        t = FileRemoveTransaction(file)
        self.add_transaction(t)

    def add_transaction(
        self,
        transaction: Transaction,
        dedupe: bool = True,
        solve_conflicts: bool = True,
    ) -> bool:
        """Add a transaction to the queue.

        Args:
            transaction: The transaction to add
            dedupe: Whether to check for duplicate transactions
            solve_conflicts: Whether to resolve conflicts with existing transactions

        Returns:
            True if the transaction was added, False otherwise
        """
        # Get the list of transactions for the file
        file_path = transaction.file_path
        if file_path not in self.queued_transactions:
            self.queued_transactions[file_path] = []
        file_queue = self.queued_transactions[file_path]

        # Dedupe transactions
        if dedupe and transaction in file_queue:
            logger.debug(f"Transaction already exists in queue: {transaction}")
            return False

        # Solve conflicts
        if new_transaction := self._resolve_conflicts(
            transaction, file_queue, solve_conflicts=solve_conflicts
        ):
            file_queue.append(new_transaction)

        self.check_limits()
        return True

    def add(self, transaction: Transaction) -> bool:
        """Alias for add_transaction."""
        return self.add_transaction(transaction)

    def check_limits(self) -> None:
        """Check if any limits have been exceeded."""
        self.check_max_transactions()
        self.check_max_preview_time()

    def check_max_transactions(self) -> None:
        """Check if the maximum number of transactions has been exceeded."""
        if self.max_transactions_exceeded():
            logger.info(
                f"Max transactions reached: {self.max_transactions}. Stopping analysis."
            )
            msg = f"Max transactions reached: {self.max_transactions}"
            raise MaxTransactionsExceeded(msg, threshold=self.max_transactions)

    def check_max_preview_time(self) -> None:
        """Check if the maximum preview time has been exceeded."""
        if self.is_time_exceeded():
            logger.info(
                f"Max preview time exceeded: {self.stopwatch_max_seconds}. Stopping analysis."
            )
            msg = f"Max preview time exceeded: {self.stopwatch_max_seconds}"
            raise MaxPreviewTimeExceeded(msg, threshold=self.stopwatch_max_seconds)

    ####################################################################################################################
    # Commit
    ####################################################################################################################

    def to_commit(self, files: set[Path] | None = None) -> set[Path]:
        """Get paths of files to commit.

        Args:
            files: Optional set of files to filter by

        Returns:
            Set of file paths to commit
        """
        if files is None:
            return set(self.queued_transactions.keys())
        return files.intersection(self.queued_transactions)

    def commit(self, files: set[Path]) -> list[DiffLite]:
        """Execute transactions in bulk for each file, in reverse order of start_byte.

        Args:
            files: Set of file paths to commit

        Returns:
            List of diffs that were committed
        """
        if self._commiting:
            logger.warning("Skipping commit, already committing")
            return []

        self._commiting = True
        try:
            diffs: list[DiffLite] = []
            if not self.queued_transactions or len(self.queued_transactions) == 0:
                return diffs

            self.sort_transactions()

            # Log information about the commit
            if len(files) > 3:
                num_transactions = sum([
                    len(self.queued_transactions[file_path]) for file_path in files
                ])
                logger.info(
                    f"Committing {num_transactions} transactions for {len(files)} files"
                )
            else:
                for file in files:
                    logger.info(
                        f"Committing {len(self.queued_transactions[file])} transactions for {file}"
                    )

            # Execute transactions for each file
            for file_path in files:
                file_transactions = self.queued_transactions.pop(file_path, [])
                modified = False
                for transaction in file_transactions:
                    # Add diff IF the file is a source file
                    diff = transaction.get_diff()
                    if diff.change_type == ChangeType.Modified:
                        if not modified:
                            modified = True
                            diffs.append(diff)
                    else:
                        diffs.append(diff)
                    transaction.execute()

            return diffs
        finally:
            self._commiting = False

    def apply(self, transaction: Transaction) -> None:
        """Apply a single transaction immediately.

        Args:
            transaction: The transaction to apply
        """
        self.add_transaction(transaction)
        self.commit({transaction.file_path})

    def apply_all(self) -> list[DiffLite]:
        """Apply all queued transactions.

        Returns:
            List of diffs that were committed
        """
        files = self.to_commit()
        return self.commit(files)

    def revert_all(self) -> None:
        """Revert all pending transactions."""
        self.queued_transactions.clear()
        for undo in self.pending_undos:
            undo()
        self.pending_undos.clear()

    ####################################################################################################################
    # Conflict Resolution
    ####################################################################################################################

    def _resolve_conflicts(
        self,
        transaction: Transaction,
        file_queue: list[Transaction],
        solve_conflicts: bool = True,
    ) -> Transaction | None:
        """Resolve conflicts between the new transaction and existing transactions.

        Args:
            transaction: The new transaction
            file_queue: List of existing transactions for the file
            solve_conflicts: Whether to attempt to resolve conflicts

        Returns:
            The transaction to add, or None if it should be discarded
        """
        # Extract the conflict resolution logic to reduce complexity
        try:
            conflicts = self._get_conflicts(transaction)
            if solve_conflicts and conflicts:
                return self._handle_conflicts(transaction, file_queue, conflicts)
            else:
                # Add to priority queue and rebuild the queue
                return transaction
        except TransactionError:
            logger.exception("Transaction conflict detected")
            self._log_conflict_error(transaction, self._get_conflicts(transaction))
            raise

    def _handle_conflicts(
        self,
        transaction: Transaction,
        file_queue: list[Transaction],
        conflicts: list[Transaction],
    ) -> Transaction | None:
        """Handle conflicts between transactions.

        Args:
            transaction: The new transaction
            file_queue: List of existing transactions for the file
            conflicts: List of conflicting transactions

        Returns:
            The transaction to add, or None if it should be discarded
        """
        # Check if the current transaction completely overlaps with any existing transaction
        completely_overlapping = self._get_overlapping_conflicts(transaction)
        if completely_overlapping is not None:
            # If it does, check the overlapping transaction's type
            # If the overlapping transaction is a remove, remove the current transaction
            if isinstance(completely_overlapping, RemoveTransaction):
                return None
            # If the overlapping transaction is an edit, try to break it down
            elif isinstance(completely_overlapping, EditTransaction):
                if self._break_down_transaction(completely_overlapping, file_queue):
                    return transaction

                raise TransactionError()
        else:
            # If current transaction is deleted, remove all conflicting transactions
            if isinstance(transaction, RemoveTransaction):
                for t in conflicts:
                    file_queue.remove(t)
            # If current transaction is edit, try to break it down
            elif isinstance(transaction, EditTransaction):
                if self._break_down_transaction(transaction, file_queue):
                    return None
                raise TransactionError()

        return transaction

    def _break_down_transaction(
        self, to_break: EditTransaction, file_queue: list[Transaction]
    ) -> bool:
        """Break down an edit transaction into smaller transactions.

        Args:
            to_break: The transaction to break down
            file_queue: List of existing transactions for the file

        Returns:
            True if the transaction was broken down, False otherwise
        """
        new_transactions = to_break.break_down()
        if not new_transactions:
            return False

        try:
            insert_idx = file_queue.index(to_break)
            file_queue.pop(insert_idx)
        except ValueError:
            insert_idx = len(file_queue)

        for new_transaction in new_transactions:
            broken_down = self._resolve_conflicts(
                new_transaction, file_queue, solve_conflicts=True
            )
            if broken_down:
                file_queue.insert(insert_idx, broken_down)

        return True

    def _log_conflict_error(
        self, transaction: Transaction, conflicts: list[Transaction]
    ) -> None:
        """Log a conflict error.

        Args:
            transaction: The transaction that caused the conflict
            conflicts: List of conflicting transactions
        """
        msg = (
            f"Potential conflict detected in file {transaction.file_path}!\n"
            "Attempted to perform code modification:\n"
            "\n"
            f"{self._format_transactions([transaction])}\n"
            "\n"
            "That potentially conflicts with the following other modifications:\n"
            "\n"
            f"{self._format_transactions(conflicts)}\n"
            "\n"
            "Aborting!\n"
            "\n"
            f"[Conflict Detected] Potential Modification Conflict in File {transaction.file_path}!"
        )
        raise TransactionError(msg)

    def get_transactions_at_range(
        self,
        file_path: Path,
        start_byte: int,
        end_byte: int,
        transaction_order: TransactionPriority | None = None,
        *,
        combined: bool = False,
    ) -> list[Transaction]:
        """Returns list of queued transactions that matches the given filtering criteria.

        Args:
            file_path: Path to the file
            start_byte: Start byte position
            end_byte: End byte position
            transaction_order: Optional filter by transaction order
            combined: Return a list of transactions which collectively apply to the given range

        Returns:
            List of matching transactions
        """
        matching_transactions: list[Transaction] = []
        if file_path not in self.queued_transactions:
            return matching_transactions

        for t in self.queued_transactions[file_path]:
            if t.start_byte == start_byte:
                if t.end_byte == end_byte and (
                    transaction_order is None
                    or t.transaction_order == transaction_order
                ):
                    matching_transactions.append(t)
                elif combined and t.start_byte != t.end_byte:
                    other = self.get_transactions_at_range(
                        t.file_path,
                        t.end_byte,
                        end_byte,
                        transaction_order,
                        combined=combined,
                    )
                    if other:
                        return [t, *other]

        return matching_transactions

    def get_transaction_containing_range(
        self,
        file_path: Path,
        start_byte: int,
        end_byte: int,
        transaction_order: TransactionPriority | None = None,
    ) -> Transaction | None:
        """Returns the nearest transaction that includes the range specified given the filtering criteria.

        Args:
            file_path: Path to the file
            start_byte: Start byte position
            end_byte: End byte position
            transaction_order: Optional filter by transaction order

        Returns:
            The transaction containing the range, or None if not found
        """
        if file_path not in self.queued_transactions:
            return None

        smallest_difference = math.inf
        best_fit_transaction = None
        for t in self.queued_transactions[file_path]:
            if (
                t.start_byte <= start_byte
                and t.end_byte >= end_byte
                and (
                    transaction_order is None
                    or t.transaction_order == transaction_order
                )
            ):
                smallest_difference = min(
                    smallest_difference,
                    abs(t.start_byte - start_byte) + abs(t.end_byte - end_byte),
                )
                if smallest_difference == 0:
                    return t
                best_fit_transaction = t
        return best_fit_transaction

    def _get_conflicts(self, transaction: Transaction) -> list[Transaction]:
        """Returns all transactions that overlap with the given transaction.

        Args:
            transaction: The transaction to check for conflicts

        Returns:
            List of conflicting transactions
        """
        conflicts: list[Transaction] = []
        if transaction.file_path not in self.queued_transactions:
            return conflicts

        for t in self.queued_transactions[transaction.file_path]:
            # Skip if the transaction is the same
            if t == transaction:
                continue

            # Check if the transaction overlaps with the given transaction
            if (
                (t.start_byte <= transaction.start_byte < t.end_byte)
                or (t.start_byte < transaction.end_byte <= t.end_byte)
                or (transaction.start_byte <= t.start_byte < transaction.end_byte)
                or (transaction.start_byte < t.end_byte <= transaction.end_byte)
            ):
                conflicts.append(t)

        return conflicts

    def _get_overlapping_conflicts(
        self, transaction: Transaction
    ) -> Transaction | None:
        """Returns the transaction that completely overlaps with the given transaction.

        Args:
            transaction: The transaction to check for overlaps

        Returns:
            The overlapping transaction, or None if not found
        """
        if transaction.file_path not in self.queued_transactions:
            return None

        for t in self.queued_transactions[transaction.file_path]:
            if (
                transaction.start_byte >= t.start_byte
                and transaction.end_byte <= t.end_byte
            ):
                return t
        return None
