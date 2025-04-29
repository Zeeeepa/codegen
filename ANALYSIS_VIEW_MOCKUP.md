# Codegen SDK Analysis View Mockup

This document provides a mockup of how the analysis results would be presented when using the Codegen SDK for codebase analysis.

## Command Line Interface View

```
$ codegen analyze --repo=my-project --full

🔍 Analyzing repository: my-project
⏳ Building symbol tree...
⏳ Computing dependencies...
⏳ Analyzing code quality...
⏳ Generating visualizations...
✅ Analysis complete!

📊 ANALYSIS SUMMARY
==========================================

📁 FILE STATISTICS
------------------------------------------
Total Files: 324
  - Python: 187 (57.7%)
  - JavaScript: 98 (30.2%)
  - TypeScript: 39 (12.0%)
Total Lines of Code: 45,892
Average File Size: 141.6 lines
Largest File: src/core/processor.py (1,245 lines)

🧩 SYMBOL STATISTICS
------------------------------------------
Total Symbols: 2,456
  - Classes: 156 (6.4%)
  - Functions: 987 (40.2%)
  - Variables: 1,213 (49.4%)
  - Interfaces: 100 (4.1%)
Top-level Symbols: 1,245
Nested Symbols: 1,211

📦 IMPORT ANALYSIS
------------------------------------------
Total Imports: 1,876
External Dependencies: 23
Circular Imports Detected: 5
Unused Imports: 134 (7.1%)

⚙️ COMPLEXITY METRICS
------------------------------------------
Average Cyclomatic Complexity: 5.3
Max Cyclomatic Complexity: 32 (src/core/processor.py:process_data)
Average Maintainability Index: 68.4
Files Below Maintainability Threshold: 15

🔍 CODE QUALITY ISSUES
------------------------------------------
Unused Functions: 45
Unused Classes: 12
Duplicate Code Blocks: 28
Functions Exceeding Complexity Threshold: 23

🔝 TOP COMPLEX FUNCTIONS
------------------------------------------
1. process_data (src/core/processor.py) - CC: 32
2. validate_input (src/utils/validator.py) - CC: 28
3. transform_output (src/core/transformer.py) - CC: 25
4. parse_config (src/config/parser.py) - CC: 22
5. handle_request (src/api/handler.py) - CC: 21

📊 VISUALIZATION LINKS
------------------------------------------
Dependency Graph: http://localhost:8000/viz/dependency-graph
Call Graph: http://localhost:8000/viz/call-graph
Complexity Heatmap: http://localhost:8000/viz/complexity-heatmap

Full report saved to: ./codegen_analysis_report.html
```

## Web Interface View

### Dashboard Overview

![Dashboard Overview](https://via.placeholder.com/800x500?text=Codegen+Analysis+Dashboard)

### File Statistics

```
Total Files: 324
  - Python: 187 (57.7%)
  - JavaScript: 98 (30.2%)
  - TypeScript: 39 (12.0%)
  
File Size Distribution:
  - < 100 lines: 156 files (48.1%)
  - 100-500 lines: 145 files (44.8%)
  - > 500 lines: 23 files (7.1%)
  
Directory Structure:
  - src/
    - core/ (45 files)
    - utils/ (32 files)
    - api/ (28 files)
    - models/ (35 files)
  - tests/ (78 files)
  - docs/ (15 files)
```

### Symbol Tree Visualization

```
my-project/
├── src/
│   ├── core/
│   │   ├── processor.py
│   │   │   ├── class Processor
│   │   │   │   ├── method __init__
│   │   │   │   ├── method process_data
│   │   │   │   └── method validate_input
│   │   │   └── function initialize_processor
│   │   └── transformer.py
│   │       ├── class Transformer
│   │       │   ├── method __init__
│   │       │   └── method transform_output
│   │       └── function apply_transformation
│   └── utils/
│       └── validator.py
│           ├── class Validator
│           │   ├── method __init__
│           │   └── method validate
│           └── function is_valid
└── tests/
    └── test_processor.py
        └── class TestProcessor
            ├── method setUp
            ├── method test_process_data
            └── method test_validate_input
```

### Dependency Graph

![Dependency Graph](https://via.placeholder.com/800x500?text=Dependency+Graph+Visualization)

### Call Graph

![Call Graph](https://via.placeholder.com/800x500?text=Call+Graph+Visualization)

### Complexity Heatmap

![Complexity Heatmap](https://via.placeholder.com/800x500?text=Complexity+Heatmap+Visualization)

### Function Detail View

```
Function: process_data
File: src/core/processor.py
Lines: 45-120
Cyclomatic Complexity: 32 (Very High)
Maintainability Index: 42 (Low)
Parameters: 5
Return Type: Dict[str, Any]
Call Sites: 15
Called Functions: 8

Issues:
- High complexity (32 > threshold of 15)
- Too many parameters (5 > threshold of 4)
- Low maintainability index (42 < threshold of 65)
- Contains nested loops (depth: 3)

Recommendations:
- Break down into smaller functions
- Reduce nesting depth
- Consider using a parameter object
- Add more comments (current comment ratio: 5%)
```

### Class Detail View

```
Class: Processor
File: src/core/processor.py
Lines: 10-250
Methods: 12
Attributes: 8
Inheritance: BaseProcessor -> Processor
Subclasses: AdvancedProcessor, StreamProcessor

Method Complexity:
- process_data: 32 (Very High)
- validate_input: 18 (High)
- transform_output: 15 (Moderate)
- initialize: 5 (Low)
- cleanup: 3 (Low)

Issues:
- Contains methods with high complexity
- Large class (240 lines > threshold of 200)
- High coupling (depends on 15 other classes)

Recommendations:
- Extract complex methods into separate classes
- Consider breaking into smaller, more focused classes
- Reduce dependencies on other classes
```

## API Response Format

```json
{
  "repository": "my-project",
  "analysis_date": "2025-04-29T18:57:13Z",
  "file_statistics": {
    "total_files": 324,
    "by_language": {
      "python": 187,
      "javascript": 98,
      "typescript": 39
    },
    "total_lines": 45892,
    "average_file_size": 141.6,
    "largest_file": {
      "path": "src/core/processor.py",
      "lines": 1245
    }
  },
  "symbol_statistics": {
    "total_symbols": 2456,
    "by_type": {
      "classes": 156,
      "functions": 987,
      "variables": 1213,
      "interfaces": 100
    },
    "top_level_symbols": 1245,
    "nested_symbols": 1211
  },
  "import_analysis": {
    "total_imports": 1876,
    "external_dependencies": 23,
    "circular_imports": 5,
    "unused_imports": 134
  },
  "complexity_metrics": {
    "average_cyclomatic_complexity": 5.3,
    "max_cyclomatic_complexity": {
      "value": 32,
      "function": "process_data",
      "file": "src/core/processor.py"
    },
    "average_maintainability_index": 68.4,
    "files_below_threshold": 15
  },
  "code_quality_issues": {
    "unused_functions": 45,
    "unused_classes": 12,
    "duplicate_code_blocks": 28,
    "high_complexity_functions": 23
  },
  "top_complex_functions": [
    {
      "name": "process_data",
      "file": "src/core/processor.py",
      "complexity": 32
    },
    {
      "name": "validate_input",
      "file": "src/utils/validator.py",
      "complexity": 28
    },
    {
      "name": "transform_output",
      "file": "src/core/transformer.py",
      "complexity": 25
    },
    {
      "name": "parse_config",
      "file": "src/config/parser.py",
      "complexity": 22
    },
    {
      "name": "handle_request",
      "file": "src/api/handler.py",
      "complexity": 21
    }
  ],
  "visualization_urls": {
    "dependency_graph": "http://localhost:8000/viz/dependency-graph",
    "call_graph": "http://localhost:8000/viz/call-graph",
    "complexity_heatmap": "http://localhost:8000/viz/complexity-heatmap"
  }
}
```

This mockup demonstrates how the Codegen SDK analysis results would be presented in different formats, including command line output, web interface, and API response. The analysis provides comprehensive insights into the codebase structure, quality metrics, and potential areas for improvement.
