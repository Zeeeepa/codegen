# Graph-Sitter with Serena LSP Integration

This repository contains the graph-sitter project with comprehensive Serena LSP integration for advanced error analysis and code intelligence.

## Structure

```
src/graph_sitter/
├── core/
│   ├── __init__.py
│   ├── codebase.py              # Core Codebase class
│   └── errors.py                # Main error analysis module (imports all serena features)
├── codebase/
│   ├── __init__.py
│   └── codebase_analysis.py     # Codebase analysis functions
├── extensions/
│   ├── __init__.py
│   └── lsp/
│       ├── __init__.py
│       ├── serena_bridge.py     # Enhanced Serena LSP bridge (merged with transaction manager)
│       └── serena_analysis.py   # Comprehensive analysis module
└── shared/
    ├── __init__.py
    └── logging/
        ├── __init__.py
        └── get_logger.py        # Logging utilities
```

## Key Features

### Core Error Analysis (`src/graph_sitter/core/errors.py`)
- Imports all Serena analysis features
- Integrates with graph-sitter's codebase analysis
- Provides unified access to all error analysis capabilities

### Serena LSP Bridge (`src/graph_sitter/extensions/lsp/serena_bridge.py`)
- Enhanced bridge between Serena's solidlsp implementation and graph-sitter
- Merged transaction manager functionality for real-time diagnostic updates
- Comprehensive error detection with runtime support
- Advanced LSP capabilities and context analysis

### Comprehensive Analysis (`src/graph_sitter/extensions/lsp/serena_analysis.py`)
- GitHub repository analyzer with Serena LSP integration
- Real-time error monitoring and context-aware reporting
- Performance metrics and caching
- Async repository cloning and analysis

## Usage

```python
# Import all serena analysis features
from graph_sitter.core.errors import *

# Use the comprehensive analysis
from graph_sitter.extensions.lsp import analyze_github_repository

# Analyze a repository
result = await analyze_github_repository(
    "https://github.com/user/repo",
    branch="main",
    severity_filter=["error", "warning"]
)
```

## Dependencies

The modules are designed to gracefully handle missing Serena dependencies:

- `solidlsp` - Serena's LSP implementation
- `serena` - Serena analysis tools
- Standard Python libraries for async operations and analysis

## Integration Points

1. **Transaction Manager Integration**: Merged into `serena_bridge.py` for real-time diagnostic updates
2. **Bridge Classes**: All bridge-defined classes are imported into `serena_analysis.py`
3. **Core Error Module**: `errors.py` imports all serena analysis features and graph-sitter functions
4. **Unified Exports**: All modules properly export their functionality through `__all__`

## Development

The structure follows Python packaging best practices with proper `__init__.py` files and clear module separation. All imports are designed to be resilient to missing dependencies while providing full functionality when Serena components are available.
