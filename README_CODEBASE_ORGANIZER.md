# Codebase Organizer

This repository contains scripts to help you organize your codebase structure, specifically designed for the analyzers module shown in the screenshot.

## Overview

The scripts help you:

1. **Create a proper directory structure** - Organize files into logical directories
1. **Move related functions to appropriate files** - Split functions between files based on their purpose
1. **Eliminate code duplication** - Identify and consolidate duplicate functions
1. **Ensure proper imports and dependencies** - Automatically update imports when moving code

## Available Scripts

### 1. `organize_analyzers.py`

A general-purpose script that analyzes your codebase and organizes it based on function naming patterns and content.

```bash
# Run in dry-run mode (no changes applied)
python organize_analyzers.py /path/to/analyzers/directory

# Execute changes
python organize_analyzers.py /path/to/analyzers/directory --execute
```

### 2. `organize_with_codegen_sdk.py`

Uses the Codegen SDK to organize your codebase, which provides more powerful capabilities for moving symbols between files while maintaining code correctness.

```bash
# Run in dry-run mode (no changes applied)
python organize_with_codegen_sdk.py /path/to/analyzers/directory

# Execute changes
python organize_with_codegen_sdk.py /path/to/analyzers/directory --execute
```

### 3. `organize_specific_codebase.py`

Specifically designed for the exact structure shown in your screenshot, with 5 folders and 21 .py files in the root.

```bash
# Run in dry-run mode (no changes applied)
python organize_specific_codebase.py /path/to/analyzers/directory

# Execute changes
python organize_specific_codebase.py /path/to/analyzers/directory --execute
```

## How It Works

### Directory Structure

The scripts will create the following directory structure:

```
analyzers/
├── context/
│   ├── __init__.py
│   ├── context.py
│   └── context_manager.py
├── models/
│   ├── __init__.py
│   ├── model.py
│   └── model_manager.py
├── resolution/
│   ├── __init__.py
│   ├── resolver.py
│   └── resolution_manager.py
├── snapshot/
│   ├── __init__.py
│   ├── snapshot.py
│   └── snapshot_manager.py
├── visualization/
│   ├── __init__.py
│   ├── visualizer.py
│   └── visualization_manager.py
├── analyzer.py
├── analyzer_manager.py
├── api.py
├── base_analyzer.py
├── code_quality.py
├── code_quality_analyzer.py
├── codebase_analyzer.py
├── dependencies.py
├── dependency_analyzer.py
├── error_analyzer.py
├── issue_analyzer.py
├── issue_types.py
├── issues.py
└── unified_analyzer.py
```

### Function Categorization

Functions are categorized based on their names and content:

- **Context-related functions** → `context/` directory
- **Model-related functions** → `models/` directory
- **Resolution-related functions** → `resolution/` directory
- **Snapshot-related functions** → `snapshot/` directory
- **Visualization-related functions** → `visualization/` directory
- **API-related functions** → `api.py`
- **Base analyzer functions** → `base_analyzer.py`
- **Code quality functions** → `code_quality.py` and `code_quality_analyzer.py`
- **Dependency functions** → `dependency_analyzer.py` and `dependencies.py`
- **Error analysis functions** → `error_analyzer.py`
- **Issue-related functions** → `issue_analyzer.py`, `issue_types.py`, and `issues.py`

## Best Practices

1. **Run in dry-run mode first** to see what changes would be made
1. **Back up your code** before executing changes
1. **Review the changes** after execution to ensure everything is correct
1. **Run tests** to verify that the reorganized code still works as expected

## Using the Codegen SDK

The `organize_with_codegen_sdk.py` script uses the Codegen SDK, which provides powerful capabilities for code organization:

- **Symbol Movement** - Move functions, classes, and other symbols between files
- **Automatic Import Updates** - Updates all imports across the codebase
- **Dependency Handling** - Ensures that moved code continues to function correctly

To use this script, you need to have the Codegen SDK installed:

```bash
pip install codegen-sdk
```

## Example Usage

Let's say you have a messy codebase with functions scattered across files. Here's how you would use these scripts:

1. First, run in dry-run mode to see what changes would be made:

```bash
python organize_specific_codebase.py ./analyzers
```

2. If the proposed changes look good, execute them:

```bash
python organize_specific_codebase.py ./analyzers --execute
```

3. For more advanced reorganization using the Codegen SDK:

```bash
python organize_with_codegen_sdk.py ./analyzers --execute
```

## Customization

You can customize the organization logic by modifying the scripts:

- Edit the `file_mapping` dictionary to change where files are placed
- Edit the `function_mapping` dictionary to change where functions are placed
- Add new patterns to match additional function naming conventions

## Troubleshooting

If you encounter issues:

- Check that you have the necessary permissions to modify files
- Ensure that the Codegen SDK is installed (for `organize_with_codegen_sdk.py`)
- Try running with the `--execute` flag to see detailed error messages
- Check for syntax errors in your Python files that might prevent parsing

