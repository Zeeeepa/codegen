# Codegen Analyzers

This directory contains the code analysis modules for the Codegen project. These analyzers provide comprehensive static code analysis, quality checking, dependency analysis, and PR validation capabilities.

## Modules

### Core Analyzers

- **analyzer.py**: Modern analyzer architecture with plugin system
- **base_analyzer.py**: Base class for all code analyzers
- **codebase_analyzer.py**: Comprehensive codebase analysis
- **code_quality.py**: Code quality analysis
- **dependencies.py**: Dependency analysis
- **error_analyzer.py**: Error detection and analysis
- **parser.py**: Code parsing and AST generation for multiple languages
- **transaction_manager.py**: Transaction manager for handling code modifications

### Support Modules

- **api.py**: API interface for analyzers
- **analyzer_manager.py**: Manages analyzer plugins
- **codebase_context.py**: Provides context for codebase analysis
- **codebase_visualizer.py**: Visualization tools for codebases
- **issue_analyzer.py**: Issue detection and analysis
- **issue_types.py**: Definitions for issue types
- **issues.py**: Issue tracking system

## Parser Module

The `parser.py` module provides specialized parsing functionality for code analysis, including abstract syntax tree (AST) generation and traversal for multiple programming languages. It serves as a foundation for various code analyzers in the system.

### Key Features

- Abstract syntax tree (AST) generation and traversal
- Support for multiple programming languages (Python, JavaScript, TypeScript)
- Symbol extraction (functions, classes, variables)
- Dependency analysis (imports, requires)
- Error handling and reporting

### Usage Examples

#### Basic Parsing

```python
from codegen_on_oss.analyzers.parser import parse_file, parse_code

# Parse a file
ast = parse_file("path/to/file.py")

# Parse code directly
code = "def hello(): print('Hello, World!')"
ast = parse_code(code, "python")
```

#### Language-Specific Parsing

```python
from codegen_on_oss.analyzers.parser import PythonParser, JavaScriptParser, TypeScriptParser

# Python parsing
python_parser = PythonParser()
python_ast = python_parser.parse_file("script.py")

# JavaScript parsing
js_parser = JavaScriptParser()
js_ast = js_parser.parse_file("app.js")

# TypeScript parsing
ts_parser = TypeScriptParser()
ts_ast = ts_parser.parse_file("component.ts")
```

#### Symbol and Dependency Extraction

```python
from codegen_on_oss.analyzers.parser import parse_file, create_parser

# Parse a file
ast = parse_file("path/to/file.py")

# Create a parser for the language
parser = create_parser("python")

# Extract symbols (functions, classes, variables)
symbols = parser.get_symbols(ast)
for symbol in symbols:
    print(f"{symbol['type']}: {symbol['name']}")

# Extract dependencies (imports, requires)
dependencies = parser.get_dependencies(ast)
for dep in dependencies:
    if dep["type"] == "import":
        print(f"import {dep['module']}")
    elif dep["type"] == "from_import":
        print(f"from {dep['module']} import {dep['name']}")
```

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
