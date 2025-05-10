# Enhanced Codebase Analyzer

This repository contains an enhanced version of the Comprehensive Codebase Analyzer, with additional features for advanced code analysis.

## Enhanced Features

In addition to the standard codebase analyzer features, this enhanced version includes:

### 1. Call Chain Analysis
- Analyze call chains between functions
- Identify the longest call chains
- Find the most called functions
- Detect complex call patterns
- Generate call chain statistics

### 2. Dead Code Detection with Filtering
- Detect dead code in the codebase
- Filter out specific patterns from analysis
- Identify unused functions, classes, and methods
- Calculate dead code percentage
- Generate detailed reports

### 3. Path Finding in Call Graphs
- Find paths between functions in the call graph
- Discover multiple paths between functions
- Analyze path lengths
- Identify the shortest path
- Visualize paths in the call graph

### 4. Dead Symbol Detection
- Detect dead symbols in the codebase
- Identify unused functions, classes, variables, and imports
- Generate comprehensive statistics
- Provide recommendations for code cleanup

### 5. Symbol Import Analysis
- Analyze symbol imports in the codebase
- Detect import patterns
- Find circular imports
- Identify unused imports
- Generate import statistics
- Provide import optimization recommendations

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

## Implementation

The implementation is modular and extensible, with each feature implemented in a separate file:
- `call_chain_analysis.py`: Call chain analysis
- `dead_code_detection.py`: Dead code detection
- `path_finding.py`: Path finding in call graphs
- `dead_symbol_detection.py`: Dead symbol detection
- `symbol_import_analysis.py`: Symbol import analysis

The `enhanced_analyzer.py` file provides functions to integrate these features with the `CodebaseAnalyzer` class, and the `codebase_analyzer_patch.py` file applies the enhancements to the existing codebase analyzer.

## Requirements

- Python 3.8+
- Codegen SDK
- NetworkX
- Matplotlib
- Rich

