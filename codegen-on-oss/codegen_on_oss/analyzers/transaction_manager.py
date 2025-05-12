#!/usr/bin/env python3
"""
Transaction Manager Module for Analyzers

This module provides a transaction manager for handling code modifications during analysis.
It's responsible for queuing, sorting, and committing transactions in a controlled manner.
"""

import math
import time
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Dict, List, Set, Optional, Union, Any

from codegen_on_oss.analyzers.transactions import (
    EditTransaction,
    FileAddTransaction,
    FileRemoveTransaction,
    FileRenameTransaction,
    RemoveTransaction,
    Transaction,
    TransactionPriority,
    DiffLite,
    ChangeType,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class MaxTransactionsExceeded(Exception):
    """Raised when the number of transactions exceeds the max_transactions limit."""
    def __init__(self, message: str, threshold: Optional[int] = None):
        super().__init__(message)
        self.threshold = threshold

class MaxPreviewTimeExceeded(Exception):
    """Raised when more than the allotted time has passed for previewing transactions."""
    def __init__(self, message: str, threshold: Optional[int] = None):
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
        self.queued_transactions: Dict[Path, List[Transaction]] = dict()
        self.pending_undos: Set[Callable[[], None]] = set()
        self._commiting: bool = False
        self.max_transactions: Optional[int] = None  # None = no limit
        self.stopwatch_start: Optional[float] = None
        self.stopwatch_max_seconds: Optional[int] = None  # None = no limit
        self.session: Dict[str, Any] = {}  # Session data for tracking state

    def sort_transactions(self) -> None:
        """Sort transactions by priority and position."""
        for file_path, file_transactions in self.queued_transactions.items():
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

    def _format_transactions(self, transactions: List[Transaction]) -> str:
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
        return sum([len(transactions) for transactions in self.queued_transactions.values()])

    def set_max_transactions(self, max_transactions: Optional[int] = None) -> None:
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

    def reset_stopwatch(self, max_seconds: Optional[int] = None) -> None:
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

    def add_transaction(self, transaction: Transaction, dedupe: bool = True, solve_conflicts: bool = True) -> bool:
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
        if new_transaction := self._resolve_conflicts(transaction, file_queue, solve_conflicts=solve_conflicts):
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
            logger.info(f"Max transactions reached: {self.max_transactions}. Stopping analysis.")
            msg = f"Max transactions reached: {self.max_transactions}"
            raise MaxTransactionsExceeded(msg, threshold=self.max_transactions)

    def check_max_preview_time(self) -> None:
        """Check if the maximum preview time has been exceeded."""
        if self.is_time_exceeded():
            logger.info(f"Max preview time exceeded: {self.stopwatch_max_seconds}. Stopping analysis.")
            msg = f"Max preview time exceeded: {self.stopwatch_max_seconds}"
            raise MaxPreviewTimeExceeded(msg, threshold=self.stopwatch_max_seconds)

    ####################################################################################################################
    # Commit
    ####################################################################################################################

    def to_commit(self, files: Optional[Set[Path]] = None) -> Set[Path]:
        """Get paths of files to commit.
        
        Args:
            files: Optional set of files to filter by
            
        Returns:
            Set of file paths to commit
        """
        if files is None:
            return set(self.queued_transactions.keys())
        return files.intersection(self.queued_transactions)

    def commit(self, files: Set[Path]) -> List[DiffLite]:
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
            diffs: List[DiffLite] = []
            if not self.queued_transactions or len(self.queued_transactions) == 0:
                return diffs

            self.sort_transactions()

            # Log information about the commit
            if len(files) > 3:
                num_transactions = sum([len(self.queued_transactions[file_path]) for file_path in files])
                logger.info(f"Committing {num_transactions} transactions for {len(files)} files")
            else:
                for file in files:
                    logger.info(f"Committing {len(self.queued_transactions[file])} transactions for {file}")
            
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

    def apply_all(self) -> List[DiffLite]:
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

    def _resolve_conflicts(self, transaction: Transaction, file_queue: List[Transaction], solve_conflicts: bool = True) -> Optional[Transaction]:
        """Resolve conflicts between the new transaction and existing transactions.
        
        Args:
            transaction: The new transaction
            file_queue: List of existing transactions for the file
            solve_conflicts: Whether to attempt to resolve conflicts
            
        Returns:
            The transaction to add, or None if it should be discarded
        """
        def break_down(to_break: EditTransaction) -> bool:
            """Break down an edit transaction into smaller transactions."""
            if new_transactions := to_break.break_down():
                try:
                    insert_idx = file_queue.index(to_break)
                    file_queue.pop(insert_idx)
                except ValueError:
                    insert_idx = len(file_queue)
                for new_transaction in new_transactions:
                    if broken_down := self._resolve_conflicts(new_transaction, file_queue, solve_conflicts=solve_conflicts):
                        file_queue.insert(insert_idx, broken_down)
                return True
            return False

        try:
            conflicts = self._get_conflicts(transaction)
            if solve_conflicts and conflicts:
                # Check if the current transaction completely overlaps with any existing transaction
                if (completely_overlapping := self._get_overlapping_conflicts(transaction)) is not None:
                    # If it does, check the overlapping transaction's type
                    # If the overlapping transaction is a remove, remove the current transaction
                    if isinstance(completely_overlapping, RemoveTransaction):
                        return None
                    # If the overlapping transaction is an edit, raise an error
                    elif isinstance(completely_overlapping, EditTransaction):
                        if break_down(completely_overlapping):
                            return transaction

                        raise TransactionError()
                else:
                    # If current transaction is deleted, remove all conflicting transactions
                    if isinstance(transaction, RemoveTransaction):
                        for t in conflicts:
                            file_queue.remove(t)
                    # If current transaction is edit, raise an error
                    elif isinstance(transaction, EditTransaction):
                        if break_down(transaction):
                            return None
                        raise TransactionError()

            # Add to priority queue and rebuild the queue
            return transaction
        except TransactionError as e:
            logger.exception(e)
            msg = (
                f"Potential conflict detected in file {transaction.file_path}!\\n"
                "Attempted to perform code modification:\\n"
                "\\n"
                f"{self._format_transactions([transaction])}\\n"
                "\\n"
                "That potentially conflicts with the following other modifications:\\n"
                "\\n"
                f"{self._format_transactions(conflicts)}\\n"
                "\\n"
                "Aborting!\\n"
                "\\n"
                f"[Conflict Detected] Potential Modification Conflict in File {transaction.file_path}!"
            )
            raise TransactionError(msg)

    def get_transactions_at_range(self, file_path: Path, start_byte: int, end_byte: int, 
                                 transaction_order: Optional[TransactionPriority] = None, *, 
                                 combined: bool = False) -> List[Transaction]:
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
        matching_transactions: List[Transaction] = []
        if file_path not in self.queued_transactions:
            return matching_transactions

        for t in self.queued_transactions[file_path]:
            if t.start_byte == start_byte:
                if t.end_byte == end_byte:
                    if transaction_order is None or t.transaction_order == transaction_order:
                        matching_transactions.append(t)
                elif combined and t.start_byte != t.end_byte:
                    if other := self.get_transactions_at_range(t.file_path, t.end_byte, end_byte, transaction_order, combined=combined):
                        return [t, *other]

        return matching_transactions

    def get_transaction_containing_range(self, file_path: Path, start_byte: int, end_byte: int, 
                                        transaction_order: Optional[TransactionPriority] = None) -> Optional[Transaction]:
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
            if t.start_byte <= start_byte and t.end_byte >= end_byte:
                if transaction_order is None or t.transaction_order == transaction_order:
                    smallest_difference = min(smallest_difference, abs(t.start_byte - start_byte) + abs(t.end_byte - end_byte))
                    if smallest_difference == 0:
                        return t
                    best_fit_transaction = t
        return best_fit_transaction

    def _get_conflicts(self, transaction: Transaction) -> List[Transaction]:
        """Returns all transactions that overlap with the given transaction.
        
        Args:
            transaction: The transaction to check for conflicts
            
        Returns:
            List of conflicting transactions
        """
        overlapping_transactions: List[Transaction] = []
        if transaction.file_path not in self.queued_transactions:
            return overlapping_transactions

        for t in self.queued_transactions[transaction.file_path]:
            # Skip if it's the same transaction
            if t == transaction:
                continue

            # Check if the transactions overlap
            if (
                (t.start_byte <= transaction.start_byte < t.end_byte)
                or (t.start_byte < transaction.end_byte <= t.end_byte)
                or (transaction.start_byte <= t.start_byte < transaction.end_byte)
                or (transaction.start_byte < t.end_byte <= transaction.end_byte)
            ):
                overlapping_transactions.append(t)

        return overlapping_transactions

    def _get_overlapping_conflicts(self, transaction: Transaction) -> Optional[Transaction]:
        """Returns the transaction that completely overlaps with the given transaction.
        
        Args:
            transaction: The transaction to check for overlaps
            
        Returns:
            The overlapping transaction, or None if not found
        """
        if transaction.file_path not in self.queued_transactions:
            return None

        for t in self.queued_transactions[transaction.file_path]:
            if transaction.start_byte >= t.start_byte and transaction.end_byte <= t.end_byte:
                return t
        return None
