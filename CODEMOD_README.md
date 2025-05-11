# Codegen Analyzer Refactoring Tools

This directory contains tools for refactoring the Codegen analyzers codebase by separating functions and classes into different modules based on their functionality.

## Available Scripts

### 1. Simple Analyzer Refactoring Script (`simple_analyzer_refactor.py`)

This script analyzes Python files in the analyzers directory and separates functions into different modules based on their names and functionality. It doesn't require any external dependencies beyond the Python standard library.

#### Usage:

```bash
python simple_analyzer_refactor.py [--dry-run] [--output-dir OUTPUT_DIR]
```

Options:
- `--dry-run`: Only analyze and print what would be done, without making changes
- `--output-dir`: Directory to output the refactored modules (default: ./refactored_analyzers)

#### How it works:

1. The script analyzes all Python files in the analyzers directory
2. It extracts functions and classes using Python's AST (Abstract Syntax Tree) module
3. Functions and classes are categorized based on their names and content
4. New module files are created for each category
5. An `__init__.py` file is created to re-export all public symbols

### 2. Advanced Analyzer Refactoring Script (`codemod_analyzer_refactor.py`)

This script provides a more sophisticated analysis of the codebase, including dependency analysis and visualization. It requires additional dependencies like NetworkX and matplotlib.

#### Dependencies:

```bash
pip install networkx matplotlib python-louvain
```

#### Usage:

```bash
python codemod_analyzer_refactor.py [--dry-run] [--output-dir OUTPUT_DIR]
```

Options:
- `--dry-run`: Only analyze and print what would be done, without making changes
- `--output-dir`: Directory to output the refactored modules (default: ./refactored_analyzers)

#### How it works:

1. The script analyzes all Python files in the analyzers directory
2. It extracts functions, classes, and their dependencies using Python's AST module
3. A dependency graph is built to represent relationships between functions and classes
4. Community detection algorithms are used to identify related functions and classes
5. New module files are created based on these communities
6. A visualization of the dependency graph is generated
7. An `__init__.py` file is created to re-export all public symbols

## Example Output

After running either script, you'll get a new directory structure like:

```
refactored_analyzers/
├── __init__.py
├── analyzer.py
├── dependency.py
├── quality.py
├── issue.py
├── error.py
├── visualization.py
├── context.py
└── ...
```

Each module contains related functions and classes, and the `__init__.py` file re-exports all public symbols so that the refactored code can be used as a drop-in replacement for the original code.

## Best Practices

1. Always run with `--dry-run` first to see what changes would be made
2. Review the generated modules to ensure they make sense
3. Run tests after refactoring to ensure functionality is preserved
4. Consider manually adjusting the generated modules if needed

## Customization

You can customize the categorization logic by modifying the `categorize_function` and `categorize_class` methods in the `FunctionExtractor` class of the simple script, or by adjusting the module identification logic in the advanced script.

