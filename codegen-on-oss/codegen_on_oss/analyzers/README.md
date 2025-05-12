# Analyzers Package

This package provides tools for analyzing and modifying code during analysis.

## Transaction Manager

The `transaction_manager.py` module provides a transaction manager for handling code modifications during analysis. It's responsible for queuing, sorting, and committing transactions in a controlled manner.

### Key Features

- **Transaction Queuing**: Queue up code modifications to be applied later
- **Transaction Sorting**: Sort transactions by priority and position
- **Conflict Resolution**: Detect and resolve conflicts between transactions
- **Transaction Limits**: Set limits on the number of transactions and execution time
- **Bulk Commits**: Commit multiple transactions at once
- **Undo Support**: Revert transactions if needed

### Usage Example

```python
from codegen_on_oss.analyzers.transaction_manager import TransactionManager
from codegen_on_oss.analyzers.transactions import EditTransaction

# Create a transaction manager
manager = TransactionManager()

# Set limits
manager.set_max_transactions(100)  # Limit to 100 transactions
manager.reset_stopwatch(5)  # Limit to 5 seconds

# Create a transaction
transaction = EditTransaction(start_byte=10, end_byte=20, file=file_obj, new_content="new code")

# Add the transaction to the queue
manager.add_transaction(transaction)

# Commit all transactions
files_to_commit = manager.to_commit()
diffs = manager.commit(files_to_commit)

# Or apply a single transaction immediately
manager.apply(transaction)

# Or apply all transactions at once
diffs = manager.apply_all()

# Revert all transactions
manager.revert_all()
```

### Transaction Types

The following transaction types are supported:

- **EditTransaction**: Replace content in a file
- **InsertTransaction**: Insert content at a specific position
- **RemoveTransaction**: Remove content from a file
- **FileAddTransaction**: Add a new file
- **FileRenameTransaction**: Rename a file
- **FileRemoveTransaction**: Remove a file

### Error Handling

The transaction manager can raise the following exceptions:

- **MaxTransactionsExceeded**: Raised when the number of transactions exceeds the limit
- **MaxPreviewTimeExceeded**: Raised when the execution time exceeds the limit
- **TransactionError**: Raised when there's a conflict between transactions

### Integration with Analyzers

The transaction manager is designed to be used with the analyzers package to provide a consistent way to modify code during analysis. It can be integrated with other components of the analyzers package to provide a complete code analysis and modification solution.

