#!/usr/bin/env python3
"""
Tests for the Transaction Manager module in the analyzers package.
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from codegen_on_oss.analyzers.transaction_manager import (
    MaxPreviewTimeExceeded,
    MaxTransactionsExceeded,
    TransactionManager,
)
from codegen_on_oss.analyzers.transactions import (
    ChangeType,
    DiffLite,
    EditTransaction,
    FileAddTransaction,
    FileRemoveTransaction,
    FileRenameTransaction,
    InsertTransaction,
    RemoveTransaction,
    TransactionPriority,
)


class TestTransactionManager(unittest.TestCase):
    """Test cases for the TransactionManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = TransactionManager()

        # Create a temporary file for testing
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_file_path = Path(os.path.join(self.temp_dir.name, "test_file.txt"))
        with open(self.test_file_path, "w") as f:
            f.write("This is a test file content.")

        # Create a mock file object
        self.mock_file = MagicMock()
        self.mock_file.path = self.test_file_path
        self.mock_file.content = "This is a test file content."
        self.mock_file.content_bytes = b"This is a test file content."
        self.mock_file.write_bytes = MagicMock()

    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_init(self):
        """Test initialization of TransactionManager."""
        self.assertEqual(self.manager.queued_transactions, {})
        self.assertEqual(self.manager.pending_undos, set())
        self.assertFalse(self.manager._commiting)
        self.assertIsNone(self.manager.max_transactions)
        self.assertIsNone(self.manager.stopwatch_max_seconds)

    def test_add_transaction(self):
        """Test adding a transaction to the manager."""
        transaction = EditTransaction(0, 5, self.mock_file, "New")
        result = self.manager.add_transaction(transaction)

        self.assertTrue(result)
        self.assertIn(self.test_file_path, self.manager.queued_transactions)
        self.assertEqual(len(self.manager.queued_transactions[self.test_file_path]), 1)
        self.assertEqual(
            self.manager.queued_transactions[self.test_file_path][0], transaction
        )

    def test_add_duplicate_transaction(self):
        """Test adding a duplicate transaction."""
        transaction = EditTransaction(0, 5, self.mock_file, "New")
        self.manager.add_transaction(transaction)
        result = self.manager.add_transaction(transaction)

        self.assertFalse(result)
        self.assertEqual(len(self.manager.queued_transactions[self.test_file_path]), 1)

    def test_sort_transactions(self):
        """Test sorting transactions."""
        # Add transactions in reverse order
        t1 = EditTransaction(10, 15, self.mock_file, "Edit1")
        t2 = InsertTransaction(5, self.mock_file, "Insert")
        t3 = RemoveTransaction(0, 5, self.mock_file)

        self.manager.add_transaction(t1)
        self.manager.add_transaction(t2)
        self.manager.add_transaction(t3)

        self.manager.sort_transactions()

        # Check that they're sorted by start_byte (descending) and transaction_order
        sorted_transactions = self.manager.queued_transactions[self.test_file_path]
        self.assertEqual(sorted_transactions[0], t1)  # EditTransaction at byte 10
        self.assertEqual(sorted_transactions[1], t2)  # InsertTransaction at byte 5
        self.assertEqual(sorted_transactions[2], t3)  # RemoveTransaction at byte 0

    def test_clear_transactions(self):
        """Test clearing transactions."""
        transaction = EditTransaction(0, 5, self.mock_file, "New")
        self.manager.add_transaction(transaction)

        # Add a mock undo function
        mock_undo = MagicMock()
        self.manager.pending_undos.add(mock_undo)

        self.manager.clear_transactions()

        self.assertEqual(self.manager.queued_transactions, {})
        self.assertEqual(self.manager.pending_undos, set())
        mock_undo.assert_called_once()

    def test_get_num_transactions(self):
        """Test getting the number of transactions."""
        self.assertEqual(self.manager.get_num_transactions(), 0)

        t1 = EditTransaction(0, 5, self.mock_file, "Edit1")
        t2 = InsertTransaction(5, self.mock_file, "Insert")

        self.manager.add_transaction(t1)
        self.manager.add_transaction(t2)

        self.assertEqual(self.manager.get_num_transactions(), 2)

    def test_set_max_transactions(self):
        """Test setting the maximum number of transactions."""
        self.assertIsNone(self.manager.max_transactions)

        self.manager.set_max_transactions(10)
        self.assertEqual(self.manager.max_transactions, 10)

        self.manager.set_max_transactions(None)
        self.assertIsNone(self.manager.max_transactions)

    def test_max_transactions_exceeded(self):
        """Test checking if max transactions is exceeded."""
        self.assertFalse(self.manager.max_transactions_exceeded())

        self.manager.set_max_transactions(2)
        self.assertFalse(self.manager.max_transactions_exceeded())

        t1 = EditTransaction(0, 5, self.mock_file, "Edit1")
        t2 = InsertTransaction(5, self.mock_file, "Insert")

        self.manager.add_transaction(t1)
        self.manager.add_transaction(t2)

        self.assertTrue(self.manager.max_transactions_exceeded())

    @patch("time.time")
    def test_reset_stopwatch(self, mock_time):
        """Test resetting the stopwatch."""
        mock_time.return_value = 100

        self.manager.reset_stopwatch(5)

        self.assertEqual(self.manager.stopwatch_start, 100)
        self.assertEqual(self.manager.stopwatch_max_seconds, 5)

    @patch("time.time")
    def test_is_time_exceeded(self, mock_time):
        """Test checking if time is exceeded."""
        # Set up stopwatch
        mock_time.return_value = 100
        self.manager.reset_stopwatch(5)

        # Time not exceeded
        mock_time.return_value = 104
        self.assertFalse(self.manager.is_time_exceeded())

        # Time exceeded
        mock_time.return_value = 106
        self.assertTrue(self.manager.is_time_exceeded())

        # No time limit
        self.manager.reset_stopwatch(None)
        mock_time.return_value = 200
        self.assertFalse(self.manager.is_time_exceeded())

    def test_add_file_transactions(self):
        """Test adding file-related transactions."""
        # Test add file transaction
        self.manager.add_file_add_transaction(self.test_file_path)
        self.assertIn(self.test_file_path, self.manager.queued_transactions)
        self.assertEqual(len(self.manager.queued_transactions[self.test_file_path]), 1)
        self.assertIsInstance(
            self.manager.queued_transactions[self.test_file_path][0], FileAddTransaction
        )

        # Clear transactions
        self.manager.clear_transactions()

        # Test rename file transaction
        self.manager.add_file_rename_transaction(self.mock_file, "new_name.txt")
        self.assertIn(self.test_file_path, self.manager.queued_transactions)
        self.assertEqual(len(self.manager.queued_transactions[self.test_file_path]), 1)
        self.assertIsInstance(
            self.manager.queued_transactions[self.test_file_path][0],
            FileRenameTransaction,
        )

        # Clear transactions
        self.manager.clear_transactions()

        # Test remove file transaction
        self.manager.add_file_remove_transaction(self.mock_file)
        self.assertIn(self.test_file_path, self.manager.queued_transactions)
        self.assertEqual(len(self.manager.queued_transactions[self.test_file_path]), 1)
        self.assertIsInstance(
            self.manager.queued_transactions[self.test_file_path][0],
            FileRemoveTransaction,
        )

    def test_check_limits(self):
        """Test checking transaction limits."""
        # Test max transactions
        self.manager.set_max_transactions(1)
        t1 = EditTransaction(0, 5, self.mock_file, "Edit1")
        self.manager.add_transaction(t1)

        with self.assertRaises(MaxTransactionsExceeded):
            t2 = InsertTransaction(5, self.mock_file, "Insert")
            self.manager.add_transaction(t2)

        # Reset limits
        self.manager.clear_transactions()
        self.manager.set_max_transactions(None)

        # Test max preview time
        with patch("time.time") as mock_time:
            mock_time.return_value = 100
            self.manager.reset_stopwatch(5)

            # Add a transaction (time not exceeded)
            mock_time.return_value = 104
            t1 = EditTransaction(0, 5, self.mock_file, "Edit1")
            self.manager.add_transaction(t1)

            # Add another transaction (time exceeded)
            mock_time.return_value = 106
            t2 = InsertTransaction(5, self.mock_file, "Insert")

            with self.assertRaises(MaxPreviewTimeExceeded):
                self.manager.add_transaction(t2)

    def test_to_commit(self):
        """Test getting files to commit."""
        # Add transactions for two files
        t1 = EditTransaction(0, 5, self.mock_file, "Edit1")
        self.manager.add_transaction(t1)

        # Create another mock file
        mock_file2 = MagicMock()
        mock_file2.path = Path(os.path.join(self.temp_dir.name, "test_file2.txt"))
        mock_file2.content = "Another test file."
        mock_file2.content_bytes = b"Another test file."

        t2 = EditTransaction(0, 5, mock_file2, "Edit2")
        self.manager.add_transaction(t2)

        # Get all files to commit
        files_to_commit = self.manager.to_commit()
        self.assertEqual(len(files_to_commit), 2)
        self.assertIn(self.test_file_path, files_to_commit)
        self.assertIn(mock_file2.path, files_to_commit)

        # Get specific files to commit
        specific_files = {self.test_file_path}
        files_to_commit = self.manager.to_commit(specific_files)
        self.assertEqual(len(files_to_commit), 1)
        self.assertIn(self.test_file_path, files_to_commit)
        self.assertNotIn(mock_file2.path, files_to_commit)

    def test_commit(self):
        """Test committing transactions."""
        # Add a transaction
        t1 = EditTransaction(0, 5, self.mock_file, "New")
        self.manager.add_transaction(t1)

        # Commit the transaction
        diffs = self.manager.commit({self.test_file_path})

        # Check that the transaction was executed
        self.mock_file.write_bytes.assert_called_once()

        # Check that the transaction was removed from the queue
        self.assertNotIn(self.test_file_path, self.manager.queued_transactions)

        # Check that a diff was returned
        self.assertEqual(len(diffs), 1)
        self.assertIsInstance(diffs[0], DiffLite)
        self.assertEqual(diffs[0].change_type, ChangeType.Modified)
        self.assertEqual(diffs[0].path, self.test_file_path)

    def test_apply(self):
        """Test applying a single transaction."""
        t1 = EditTransaction(0, 5, self.mock_file, "New")
        self.manager.apply(t1)

        # Check that the transaction was executed
        self.mock_file.write_bytes.assert_called_once()

        # Check that the transaction was removed from the queue
        self.assertNotIn(self.test_file_path, self.manager.queued_transactions)

    def test_apply_all(self):
        """Test applying all transactions."""
        # Add transactions for two files
        t1 = EditTransaction(0, 5, self.mock_file, "Edit1")
        self.manager.add_transaction(t1)

        # Create another mock file
        mock_file2 = MagicMock()
        mock_file2.path = Path(os.path.join(self.temp_dir.name, "test_file2.txt"))
        mock_file2.content = "Another test file."
        mock_file2.content_bytes = b"Another test file."

        t2 = EditTransaction(0, 5, mock_file2, "Edit2")
        self.manager.add_transaction(t2)

        # Apply all transactions
        diffs = self.manager.apply_all()

        # Check that both transactions were executed
        self.mock_file.write_bytes.assert_called_once()
        mock_file2.write_bytes.assert_called_once()

        # Check that both transactions were removed from the queue
        self.assertEqual(self.manager.queued_transactions, {})

        # Check that diffs were returned
        self.assertEqual(len(diffs), 2)

    def test_revert_all(self):
        """Test reverting all transactions."""
        # Add a transaction
        t1 = EditTransaction(0, 5, self.mock_file, "New")
        self.manager.add_transaction(t1)

        # Add a mock undo function
        mock_undo = MagicMock()
        self.manager.pending_undos.add(mock_undo)

        # Revert all transactions
        self.manager.revert_all()

        # Check that the transaction was removed from the queue
        self.assertEqual(self.manager.queued_transactions, {})

        # Check that the undo function was called
        mock_undo.assert_called_once()

    def test_get_transactions_at_range(self):
        """Test getting transactions at a specific range."""
        # Add transactions
        t1 = EditTransaction(0, 5, self.mock_file, "Edit1")
        t2 = EditTransaction(5, 10, self.mock_file, "Edit2")
        t3 = EditTransaction(10, 15, self.mock_file, "Edit3")

        self.manager.add_transaction(t1)
        self.manager.add_transaction(t2)
        self.manager.add_transaction(t3)

        # Get transactions at a specific range
        transactions = self.manager.get_transactions_at_range(self.test_file_path, 0, 5)
        self.assertEqual(len(transactions), 1)
        self.assertEqual(transactions[0], t1)

        # Get transactions with a specific transaction order
        transactions = self.manager.get_transactions_at_range(
            self.test_file_path, 0, 5, TransactionPriority.Edit
        )
        self.assertEqual(len(transactions), 1)
        self.assertEqual(transactions[0], t1)

        # Get transactions with a different transaction order (should return empty list)
        transactions = self.manager.get_transactions_at_range(
            self.test_file_path, 0, 5, TransactionPriority.Remove
        )
        self.assertEqual(len(transactions), 0)

    def test_get_transaction_containing_range(self):
        """Test getting a transaction containing a specific range."""
        # Add a transaction
        t1 = EditTransaction(0, 10, self.mock_file, "Edit1")
        self.manager.add_transaction(t1)

        # Get transaction containing a range
        transaction = self.manager.get_transaction_containing_range(
            self.test_file_path, 2, 8
        )
        self.assertEqual(transaction, t1)

        # Get transaction with a specific transaction order
        transaction = self.manager.get_transaction_containing_range(
            self.test_file_path, 2, 8, TransactionPriority.Edit
        )
        self.assertEqual(transaction, t1)

        # Get transaction with a different transaction order (should return None)
        transaction = self.manager.get_transaction_containing_range(
            self.test_file_path, 2, 8, TransactionPriority.Remove
        )
        self.assertIsNone(transaction)

    def test_get_conflicts(self):
        """Test getting conflicting transactions."""
        # Add a transaction
        t1 = EditTransaction(0, 10, self.mock_file, "Edit1")
        self.manager.add_transaction(t1)

        # Create a conflicting transaction
        t2 = EditTransaction(5, 15, self.mock_file, "Edit2")

        # Get conflicts
        conflicts = self.manager._get_conflicts(t2)
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0], t1)

        # Create a non-conflicting transaction
        t3 = EditTransaction(15, 20, self.mock_file, "Edit3")

        # Get conflicts (should be empty)
        conflicts = self.manager._get_conflicts(t3)
        self.assertEqual(len(conflicts), 0)

    def test_get_overlapping_conflicts(self):
        """Test getting completely overlapping transactions."""
        # Add a transaction
        t1 = EditTransaction(0, 20, self.mock_file, "Edit1")
        self.manager.add_transaction(t1)

        # Create a completely overlapped transaction
        t2 = EditTransaction(5, 15, self.mock_file, "Edit2")

        # Get overlapping conflict
        conflict = self.manager._get_overlapping_conflicts(t2)
        self.assertEqual(conflict, t1)

        # Create a partially overlapping transaction
        t3 = EditTransaction(15, 25, self.mock_file, "Edit3")

        # Get overlapping conflict (should be None)
        conflict = self.manager._get_overlapping_conflicts(t3)
        self.assertIsNone(conflict)

    def test_resolve_conflicts_with_remove(self):
        """Test resolving conflicts with a remove transaction."""
        # Add an edit transaction
        t1 = EditTransaction(0, 10, self.mock_file, "Edit1")
        self.manager.add_transaction(t1)

        # Create a conflicting remove transaction
        t2 = RemoveTransaction(0, 10, self.mock_file)

        # Resolve conflicts
        result = self.manager._resolve_conflicts(
            t2, self.manager.queued_transactions[self.test_file_path]
        )

        # Check that the remove transaction was returned
        self.assertEqual(result, t2)

        # Check that the edit transaction was removed from the queue
        self.assertEqual(len(self.manager.queued_transactions[self.test_file_path]), 0)

    def test_resolve_conflicts_with_edit(self):
        """Test resolving conflicts with an edit transaction."""
        # Add a remove transaction
        t1 = RemoveTransaction(0, 10, self.mock_file)
        self.manager.add_transaction(t1)

        # Create a conflicting edit transaction
        t2 = EditTransaction(0, 10, self.mock_file, "Edit1")

        # Resolve conflicts
        result = self.manager._resolve_conflicts(
            t2, self.manager.queued_transactions[self.test_file_path]
        )

        # Check that None was returned (edit transaction was discarded)
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
