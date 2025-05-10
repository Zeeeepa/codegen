# Codebase Analyzer

A comprehensive codebase analyzer using the Codegen SDK.

## Features

- **Call Chain Analysis**: Analyze call chains between functions, identifying the longest chains, most called functions, and complex call patterns.
- **Dead Code Detection**: Detect dead code in the codebase with filtering options, identifying functions, classes, and methods that are defined but never used.
- **Path Finding in Call Graphs**: Find paths between functions in the call graph, with options to limit the search depth.
- **Dead Symbol Detection**: Detect dead symbols (functions, classes, variables) in the codebase.
- **Symbol Import Analysis**: Analyze symbol imports in the codebase, identifying patterns, potential issues, and optimization opportunities.

## Usage

```bash
# Analyze call chains
python codebase_analyzer.py --repo-url https://github.com/username/repo --call-chain

# Detect dead code with filtering
python codebase_analyzer.py --repo-url https://github.com/username/repo --dead-code --exclude-patterns "test_*" ".*_test"

# Find paths between functions
python codebase_analyzer.py --repo-url https://github.com/username/repo --path-finding --source-function main --target-function process_data

# Detect dead symbols
python codebase_analyzer.py --repo-url https://github.com/username/repo --dead-symbols

# Analyze symbol imports
python codebase_analyzer.py --repo-url https://github.com/username/repo --import-analysis
```

## Integration

The codebase analyzer is integrated with the Codegen SDK modules:
- `codegen.sdk.core.codebase`
- `codegen.sdk.codebase.codebase_analysis`
- `codegen.sdk.codebase.codebase_context`

## Implementation

The implementation is modular and extensible, with each feature implemented in a separate file:
- `call_chain_analysis.py`: Call chain analysis
- `dead_code_detection.py`: Dead code detection
- `path_finding.py`: Path finding in call graphs
- `dead_symbol_detection.py`: Dead symbol detection
- `symbol_import_analysis.py`: Symbol import analysis

The `integration.py` file provides functions to integrate these features with the `CodebaseAnalyzer` class.

