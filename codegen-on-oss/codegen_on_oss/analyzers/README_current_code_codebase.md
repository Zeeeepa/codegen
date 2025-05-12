# Current Code Codebase Module

This module provides functionality for accessing and analyzing the current codebase. It offers tools to create codebase objects, import modules, and collect documented objects.

## Key Features

- **Reduced External Dependencies**: Minimized dependencies on external modules from the Codegen SDK
- **Enhanced Error Handling**: Proper exception handling and recovery mechanisms
- **Comprehensive Documentation**: Detailed docstrings and type annotations
- **Improved Logging**: Better logging and debugging capabilities
- **Language Detection**: Automatic detection of programming languages
- **Modular Design**: Clean, modular code structure for better maintainability

## Main Components

### Classes

- `CodebaseError`, `CodebaseInitError`, `ModuleImportError`, `DocumentationError`: Custom exceptions for better error handling
- `ProgrammingLanguage`: Enum for supported programming languages
- `RepoConfig`: Repository configuration
- `RepoOperator`: Repository operator for interacting with Git repositories
- `CodebaseConfig`: Configuration for codebase analysis
- `SecretsConfig`: Configuration for secrets and credentials
- `ProjectConfig`: Configuration for a project within a codebase
- `Codebase`: Main class for analyzing and interacting with code repositories
- `DocumentedObject`: Class representing a documented object in the codebase

### Functions

- `get_repo_path()`: Returns the base directory path of the repository being analyzed
- `get_base_path(repo_path)`: Determines the base path within the repository
- `detect_programming_language(repo_path, base_path)`: Detect the primary programming language of a repository
- `get_selected_codebase(...)`: Returns a Codebase instance for the selected repository
- `import_modules_from_path(...)`: Imports all Python modules from the given directory path
- `get_documented_objects(...)`: Get all objects decorated with API documentation decorators
- `get_codebase_with_docs(...)`: Convenience function to get both a codebase and its documented objects
- `set_log_level(level)`: Set the logging level for this module

## Usage Examples

### Basic Usage

```python
from codegen_on_oss.analyzers.current_code_codebase import get_selected_codebase

# Get a codebase for the current repository
codebase = get_selected_codebase()

# Access repository paths
for repo_path in codebase.repo_paths:
    print(f"Repository path: {repo_path}")

# Access base paths
for base_path in codebase.base_paths:
    print(f"Base path: {base_path}")
```

### Working with Documented Objects

```python
from codegen_on_oss.analyzers.current_code_codebase import get_documented_objects

# Get all documented objects
docs = get_documented_objects()

# Access different types of documented objects
for obj in docs["apidoc"]:
    print(f"API documented object: {obj.name} in module {obj.module}")

for obj in docs["py_apidoc"]:
    print(f"Python API documented object: {obj.name} in module {obj.module}")
```

### Getting Both Codebase and Documented Objects

```python
from codegen_on_oss.analyzers.current_code_codebase import get_codebase_with_docs

# Get both codebase and documented objects
codebase, docs = get_codebase_with_docs()

# Use codebase and docs as needed
print(f"Number of projects in codebase: {len(codebase.projects)}")
print(f"Number of API documented objects: {len(docs['apidoc'])}")
```

### Customizing Logging

```python
import logging
from codegen_on_oss.analyzers.current_code_codebase import set_log_level

# Set logging level to DEBUG for more detailed logs
set_log_level(logging.DEBUG)

# Set logging level back to INFO for normal operation
set_log_level(logging.INFO)
```

## Error Handling

The module provides comprehensive error handling with custom exceptions:

```python
from codegen_on_oss.analyzers.current_code_codebase import (
    get_selected_codebase, CodebaseError, CodebaseInitError
)

try:
    codebase = get_selected_codebase()
    # Use codebase...
except CodebaseInitError as e:
    print(f"Failed to initialize codebase: {e}")
except CodebaseError as e:
    print(f"General codebase error: {e}")
```

## Testing

The module includes comprehensive tests in `tests/test_current_code_codebase.py`. Run the tests using:

```bash
python -m unittest tests/test_current_code_codebase.py
```

