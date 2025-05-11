# Analysis Categories and Metrics

This document provides a comprehensive overview of the analysis categories and metrics available in the Codebase Analysis Viewer.

## Overview

The Codebase Analysis Viewer organizes its analysis into several categories, each containing multiple metrics. These categories and metrics provide a comprehensive view of a codebase's structure, quality, and characteristics.

## Categories

The Codebase Analysis Viewer supports the following main categories:

1. **Codebase Structure**: Metrics related to the overall structure of the codebase
2. **Symbol Level**: Metrics related to individual symbols (functions, classes, etc.)
3. **Dependency Flow**: Metrics related to dependencies and call relationships
4. **Code Quality**: Metrics related to code quality and maintainability
5. **Visualization**: Visualizations of various aspects of the codebase
6. **Language Specific**: Metrics specific to particular programming languages
7. **Code Metrics**: General code metrics and statistics

## Codebase Structure Metrics

### File Count
- **Description**: The total number of files in the codebase
- **Interpretation**: A basic measure of codebase size
- **Example**: `{"file_count": 42}`

### Files by Language
- **Description**: The distribution of files by programming language
- **Interpretation**: Shows the language composition of the codebase
- **Example**: `{"files_by_language": {"python": 35, "markdown": 5, "yaml": 2}}`

### File Size Distribution
- **Description**: The distribution of file sizes in the codebase
- **Interpretation**: Helps identify unusually large files
- **Example**: 
  ```json
  {
    "file_size_distribution": {
      "small": 20,
      "medium": 15,
      "large": 5,
      "very_large": 2
    }
  }
  ```

### Directory Structure
- **Description**: The hierarchical structure of directories in the codebase
- **Interpretation**: Shows how the codebase is organized
- **Example**: 
  ```json
  {
    "directory_structure": {
      "src": {
        "core": {"file_count": 10},
        "utils": {"file_count": 5}
      },
      "tests": {"file_count": 15},
      "docs": {"file_count": 5}
    }
  }
  ```

### Symbol Count
- **Description**: The total number of symbols (functions, classes, etc.) in the codebase
- **Interpretation**: A measure of codebase complexity
- **Example**: `{"symbol_count": 156}`

### Symbol Type Distribution
- **Description**: The distribution of symbols by type
- **Interpretation**: Shows the composition of the codebase in terms of symbol types
- **Example**: `{"symbol_type_distribution": {"function": 87, "class": 23, "method": 46}}`

### Symbol Hierarchy
- **Description**: The hierarchical structure of symbols in the codebase
- **Interpretation**: Shows how symbols are organized and nested
- **Example**: 
  ```json
  {
    "symbol_hierarchy": {
      "module1": {
        "Class1": {
          "method1": {},
          "method2": {}
        },
        "function1": {}
      }
    }
  }
  ```

### Top Level vs Nested Symbols
- **Description**: The ratio of top-level symbols to nested symbols
- **Interpretation**: Indicates the degree of nesting in the codebase
- **Example**: `{"top_level_symbols": 50, "nested_symbols": 106, "ratio": 0.47}`

### Import Dependency Map
- **Description**: A map of import dependencies between modules
- **Interpretation**: Shows how modules depend on each other
- **Example**: 
  ```json
  {
    "import_dependency_map": {
      "module1": ["module2", "module3"],
      "module2": ["module3"],
      "module3": []
    }
  }
  ```

### External vs Internal Dependencies
- **Description**: The ratio of external dependencies to internal dependencies
- **Interpretation**: Indicates the degree of external dependency
- **Example**: `{"external_dependencies": 15, "internal_dependencies": 45, "ratio": 0.33}`

### Circular Imports
- **Description**: A list of circular import dependencies in the codebase
- **Interpretation**: Circular imports can indicate design issues
- **Example**: 
  ```json
  {
    "circular_imports": [
      ["module1", "module2", "module1"],
      ["module3", "module4", "module5", "module3"]
    ]
  }
  ```

### Unused Imports
- **Description**: A list of imports that are not used in the codebase
- **Interpretation**: Unused imports can indicate code cleanliness issues
- **Example**: 
  ```json
  {
    "unused_imports": [
      {"module": "module1", "import": "unused_function", "file": "src/file.py"}
    ]
  }
  ```

### Module Coupling Metrics
- **Description**: Metrics related to the coupling between modules
- **Interpretation**: High coupling can indicate design issues
- **Example**: 
  ```json
  {
    "module_coupling_metrics": {
      "avg_coupling": 3.2,
      "max_coupling": 8,
      "highly_coupled_modules": [
        {"module": "module1", "coupling": 8}
      ]
    }
  }
  ```

### Module Cohesion Analysis
- **Description**: Analysis of the cohesion within modules
- **Interpretation**: Low cohesion can indicate design issues
- **Example**: 
  ```json
  {
    "module_cohesion_analysis": {
      "avg_cohesion": 0.7,
      "min_cohesion": 0.3,
      "low_cohesion_modules": [
        {"module": "module1", "cohesion": 0.3}
      ]
    }
  }
  ```

### Package Structure
- **Description**: The structure of packages in the codebase
- **Interpretation**: Shows how the codebase is organized at the package level
- **Example**: 
  ```json
  {
    "package_structure": {
      "package1": {
        "subpackage1": {"module_count": 5},
        "subpackage2": {"module_count": 3}
      },
      "package2": {"module_count": 7}
    }
  }
  ```

### Module Dependency Graph
- **Description**: A graph of dependencies between modules
- **Interpretation**: Shows how modules depend on each other
- **Example**: 
  ```json
  {
    "module_dependency_graph": {
      "nodes": ["module1", "module2", "module3"],
      "edges": [
        {"source": "module1", "target": "module2"},
        {"source": "module1", "target": "module3"},
        {"source": "module2", "target": "module3"}
      ]
    }
  }
  ```

## Symbol Level Metrics

### Function Parameter Analysis
- **Description**: Analysis of function parameters in the codebase
- **Interpretation**: Shows how functions are parameterized
- **Example**: 
  ```json
  {
    "function_parameter_analysis": {
      "avg_parameters": 2.5,
      "max_parameters": 8,
      "functions_with_many_parameters": [
        {"name": "complex_function", "parameters": 8, "file": "src/file.py"}
      ]
    }
  }
  ```

### Return Type Analysis
- **Description**: Analysis of function return types in the codebase
- **Interpretation**: Shows how functions return values
- **Example**: 
  ```json
  {
    "return_type_analysis": {
      "return_type_distribution": {
        "int": 25,
        "str": 30,
        "bool": 15,
        "None": 10,
        "other": 7
      }
    }
  }
  ```

### Function Complexity Metrics
- **Description**: Metrics related to function complexity
- **Interpretation**: High complexity can indicate maintainability issues
- **Example**: 
  ```json
  {
    "function_complexity_metrics": {
      "avg_cyclomatic_complexity": 3.2,
      "max_cyclomatic_complexity": 12,
      "complex_functions": [
        {"name": "complex_function", "complexity": 12, "file": "src/file.py"}
      ]
    }
  }
  ```

### Call Site Tracking
- **Description**: Tracking of function call sites in the codebase
- **Interpretation**: Shows how functions are used
- **Example**: 
  ```json
  {
    "call_site_tracking": {
      "function1": {
        "call_count": 5,
        "call_sites": [
          {"file": "src/file1.py", "line": 10},
          {"file": "src/file2.py", "line": 20}
        ]
      }
    }
  }
  ```

### Async Function Detection
- **Description**: Detection of asynchronous functions in the codebase
- **Interpretation**: Shows the use of asynchronous programming
- **Example**: 
  ```json
  {
    "async_function_detection": {
      "async_function_count": 15,
      "async_function_percentage": 17.2
    }
  }
  ```

### Function Overload Analysis
- **Description**: Analysis of function overloads in the codebase
- **Interpretation**: Shows the use of function overloading
- **Example**: 
  ```json
  {
    "function_overload_analysis": {
      "overloaded_functions": [
        {
          "name": "process",
          "overloads": [
            {"parameters": ["int"], "file": "src/file.py", "line": 10},
            {"parameters": ["str"], "file": "src/file.py", "line": 20}
          ]
        }
      ]
    }
  }
  ```

### Inheritance Hierarchy
- **Description**: The inheritance hierarchy of classes in the codebase
- **Interpretation**: Shows how classes inherit from each other
- **Example**: 
  ```json
  {
    "inheritance_hierarchy": {
      "BaseClass": {
        "DerivedClass1": {},
        "DerivedClass2": {
          "DerivedClass3": {}
        }
      }
    }
  }
  ```

### Method Analysis
- **Description**: Analysis of methods in the codebase
- **Interpretation**: Shows how methods are used
- **Example**: 
  ```json
  {
    "method_analysis": {
      "avg_methods_per_class": 4.2,
      "max_methods_per_class": 12,
      "classes_with_many_methods": [
        {"name": "LargeClass", "method_count": 12, "file": "src/file.py"}
      ]
    }
  }
  ```

### Attribute Analysis
- **Description**: Analysis of attributes in the codebase
- **Interpretation**: Shows how attributes are used
- **Example**: 
  ```json
  {
    "attribute_analysis": {
      "avg_attributes_per_class": 5.3,
      "max_attributes_per_class": 15,
      "classes_with_many_attributes": [
        {"name": "DataClass", "attribute_count": 15, "file": "src/file.py"}
      ]
    }
  }
  ```

### Constructor Analysis
- **Description**: Analysis of constructors in the codebase
- **Interpretation**: Shows how objects are constructed
- **Example**: 
  ```json
  {
    "constructor_analysis": {
      "avg_constructor_parameters": 3.1,
      "max_constructor_parameters": 10,
      "classes_with_complex_constructors": [
        {"name": "ComplexClass", "constructor_parameters": 10, "file": "src/file.py"}
      ]
    }
  }
  ```

## Dependency Flow Metrics

### Function Call Relationships
- **Description**: Relationships between function calls in the codebase
- **Interpretation**: Shows how functions call each other
- **Example**: 
  ```json
  {
    "function_call_relationships": {
      "function1": ["function2", "function3"],
      "function2": ["function3"],
      "function3": []
    }
  }
  ```

### Call Hierarchy Visualization
- **Description**: Visualization of the call hierarchy in the codebase
- **Interpretation**: Shows the call hierarchy in a visual format
- **Example**: 
  ```json
  {
    "call_hierarchy_visualization": {
      "nodes": ["function1", "function2", "function3"],
      "edges": [
        {"source": "function1", "target": "function2"},
        {"source": "function1", "target": "function3"},
        {"source": "function2", "target": "function3"}
      ]
    }
  }
  ```

### Entry Point Analysis
- **Description**: Analysis of entry points to the codebase
- **Interpretation**: Shows how the codebase is entered
- **Example**: 
  ```json
  {
    "entry_point_analysis": {
      "entry_points": [
        {"name": "main", "file": "src/main.py"},
        {"name": "api_handler", "file": "src/api.py"}
      ]
    }
  }
  ```

### Dead Code Detection
- **Description**: Detection of dead code in the codebase
- **Interpretation**: Dead code can be removed to improve maintainability
- **Example**: 
  ```json
  {
    "dead_code_detection": {
      "dead_functions": [
        {"name": "unused_function", "file": "src/utils.py"}
      ],
      "dead_classes": [
        {"name": "UnusedClass", "file": "src/models.py"}
      ]
    }
  }
  ```

### Variable Usage Tracking
- **Description**: Tracking of variable usage in the codebase
- **Interpretation**: Shows how variables are used
- **Example**: 
  ```json
  {
    "variable_usage_tracking": {
      "variable1": {
        "read_count": 5,
        "write_count": 2,
        "read_sites": [
          {"file": "src/file1.py", "line": 10},
          {"file": "src/file2.py", "line": 20}
        ],
        "write_sites": [
          {"file": "src/file1.py", "line": 5},
          {"file": "src/file3.py", "line": 15}
        ]
      }
    }
  }
  ```

## Code Quality Metrics

### Unused Functions
- **Description**: Functions that are defined but never called
- **Interpretation**: Unused functions can be removed to improve maintainability
- **Example**: 
  ```json
  {
    "unused_functions": [
      {"name": "unused_function", "file": "src/utils.py"}
    ]
  }
  ```

### Unused Classes
- **Description**: Classes that are defined but never instantiated
- **Interpretation**: Unused classes can be removed to improve maintainability
- **Example**: 
  ```json
  {
    "unused_classes": [
      {"name": "UnusedClass", "file": "src/models.py"}
    ]
  }
  ```

### Unused Variables
- **Description**: Variables that are defined but never used
- **Interpretation**: Unused variables can be removed to improve maintainability
- **Example**: 
  ```json
  {
    "unused_variables": [
      {"name": "unused_var", "file": "src/utils.py", "line": 10}
    ]
  }
  ```

### Similar Function Detection
- **Description**: Detection of similar functions in the codebase
- **Interpretation**: Similar functions can be refactored to improve maintainability
- **Example**: 
  ```json
  {
    "similar_function_detection": {
      "similar_pairs": [
        {
          "function1": {"name": "process_data", "file": "src/utils.py"},
          "function2": {"name": "handle_data", "file": "src/handlers.py"},
          "similarity": 0.85
        }
      ]
    }
  }
  ```

### Repeated Code Patterns
- **Description**: Detection of repeated code patterns in the codebase
- **Interpretation**: Repeated code can be refactored to improve maintainability
- **Example**: 
  ```json
  {
    "repeated_code_patterns": {
      "patterns": [
        {
          "pattern": "if x is None: return default",
          "occurrences": [
            {"file": "src/utils.py", "line": 10},
            {"file": "src/handlers.py", "line": 20}
          ]
        }
      ]
    }
  }
  ```

### Refactoring Opportunities
- **Description**: Identification of refactoring opportunities in the codebase
- **Interpretation**: Refactoring can improve maintainability
- **Example**: 
  ```json
  {
    "refactoring_opportunities": {
      "extract_method": [
        {
          "function": "large_function",
          "file": "src/utils.py",
          "start_line": 10,
          "end_line": 20,
          "reason": "Complex block that could be extracted"
        }
      ],
      "extract_class": [
        {
          "class": "LargeClass",
          "file": "src/models.py",
          "reason": "Class has too many responsibilities"
        }
      ]
    }
  }
  ```

### Cyclomatic Complexity
- **Description**: Measure of code complexity based on control flow
- **Interpretation**: High complexity can indicate maintainability issues
- **Example**: 
  ```json
  {
    "cyclomatic_complexity": {
      "avg_complexity": 3.2,
      "max_complexity": 12,
      "complex_functions": [
        {"name": "complex_function", "complexity": 12, "file": "src/file.py"}
      ]
    }
  }
  ```

### Cognitive Complexity
- **Description**: Measure of code complexity based on readability
- **Interpretation**: High complexity can indicate maintainability issues
- **Example**: 
  ```json
  {
    "cognitive_complexity": {
      "avg_complexity": 5.7,
      "max_complexity": 18,
      "complex_functions": [
        {"name": "complex_function", "complexity": 18, "file": "src/file.py"}
      ]
    }
  }
  ```

### Nesting Depth Analysis
- **Description**: Analysis of nesting depth in the codebase
- **Interpretation**: Deep nesting can indicate maintainability issues
- **Example**: 
  ```json
  {
    "nesting_depth_analysis": {
      "avg_max_nesting": 2.5,
      "max_nesting": 6,
      "deeply_nested_functions": [
        {"name": "nested_function", "max_nesting": 6, "file": "src/file.py"}
      ]
    }
  }
  ```

### Function Size Metrics
- **Description**: Metrics related to function size
- **Interpretation**: Large functions can indicate maintainability issues
- **Example**: 
  ```json
  {
    "function_size_metrics": {
      "avg_function_length": 15.3,
      "max_function_length": 100,
      "function_size_distribution": {
        "small": 50,
        "medium": 30,
        "large": 5,
        "very_large": 2
      },
      "largest_functions": [
        {"name": "large_function", "lines": 100, "file": "src/file.py"}
      ]
    }
  }
  ```

### Naming Convention Consistency
- **Description**: Analysis of naming convention consistency in the codebase
- **Interpretation**: Inconsistent naming can indicate maintainability issues
- **Example**: 
  ```json
  {
    "naming_convention_consistency": {
      "function_naming": {
        "snake_case": 80,
        "camel_case": 5,
        "pascal_case": 2,
        "consistency": 0.92
      },
      "variable_naming": {
        "snake_case": 120,
        "camel_case": 10,
        "consistency": 0.92
      },
      "class_naming": {
        "pascal_case": 20,
        "consistency": 1.0
      }
    }
  }
  ```

### Comment Coverage
- **Description**: Analysis of comment coverage in the codebase
- **Interpretation**: Low comment coverage can indicate documentation issues
- **Example**: 
  ```json
  {
    "comment_coverage": {
      "comment_lines": 500,
      "code_lines": 2000,
      "comment_ratio": 0.25,
      "files_without_comments": [
        "src/utils.py",
        "src/handlers.py"
      ]
    }
  }
  ```

### Documentation Completeness
- **Description**: Analysis of documentation completeness in the codebase
- **Interpretation**: Incomplete documentation can indicate documentation issues
- **Example**: 
  ```json
  {
    "documentation_completeness": {
      "documented_functions": 70,
      "total_functions": 87,
      "coverage_percentage": 80.5,
      "undocumented_functions": [
        {"name": "helper_function", "file": "src/utils.py"}
      ]
    }
  }
  ```

## Language Specific Metrics

### Decorator Usage Analysis
- **Description**: Analysis of decorator usage in Python codebases
- **Interpretation**: Shows how decorators are used
- **Example**: 
  ```json
  {
    "decorator_usage_analysis": {
      "decorator_counts": {
        "@property": 15,
        "@staticmethod": 10,
        "@classmethod": 8,
        "@custom_decorator": 5
      },
      "most_decorated_functions": [
        {"name": "decorated_function", "decorators": ["@property", "@custom_decorator"], "file": "src/models.py"}
      ]
    }
  }
  ```

### Type Hint Coverage
- **Description**: Analysis of type hint coverage in Python codebases
- **Interpretation**: Shows how type hints are used
- **Example**: 
  ```json
  {
    "type_hint_coverage": {
      "functions_with_type_hints": 60,
      "total_functions": 87,
      "coverage_percentage": 69.0,
      "functions_without_type_hints": [
        {"name": "untyped_function", "file": "src/utils.py"}
      ]
    }
  }
  ```

### JSX/TSX Component Analysis
- **Description**: Analysis of JSX/TSX components in React codebases
- **Interpretation**: Shows how React components are structured
- **Example**: 
  ```json
  {
    "jsx_tsx_component_analysis": {
      "total_components": 25,
      "functional_components": 20,
      "class_components": 5,
      "components_with_hooks": 15,
      "most_complex_components": [
        {"name": "ComplexComponent", "complexity": 12, "file": "src/components/Complex.tsx"}
      ]
    }
  }
  ```

## Code Metrics

### Monthly Commits
- **Description**: The number of commits per month
- **Interpretation**: Shows the development activity over time
- **Example**: 
  ```json
  {
    "monthly_commits": {
      "2025-01": 50,
      "2025-02": 45,
      "2025-03": 60,
      "2025-04": 55,
      "2025-05": 40
    }
  }
  ```

### Cyclomatic Complexity
- **Description**: Measure of code complexity based on control flow
- **Interpretation**: High complexity can indicate maintainability issues
- **Example**: 
  ```json
  {
    "cyclomatic_complexity": {
      "avg_complexity": 3.2,
      "max_complexity": 12,
      "complex_functions": [
        {"name": "complex_function", "complexity": 12, "file": "src/file.py"}
      ]
    }
  }
  ```

### Halstead Volume
- **Description**: Measure of code size based on operators and operands
- **Interpretation**: High volume can indicate maintainability issues
- **Example**: 
  ```json
  {
    "halstead_volume": {
      "avg_volume": 500.3,
      "max_volume": 2000.5,
      "high_volume_functions": [
        {"name": "complex_function", "volume": 2000.5, "file": "src/file.py"}
      ]
    }
  }
  ```

### Maintainability Index
- **Description**: Measure of code maintainability
- **Interpretation**: Low index can indicate maintainability issues
- **Example**: 
  ```json
  {
    "maintainability_index": {
      "avg_maintainability": 75.5,
      "min_maintainability": 45.2,
      "low_maintainability_functions": [
        {"name": "complex_function", "maintainability": 45.2, "file": "src/file.py"}
      ]
    }
  }
  ```

## Conclusion

This document has provided a comprehensive overview of the analysis categories and metrics available in the Codebase Analysis Viewer. By understanding these metrics and their interpretation, you can gain valuable insights into your codebase's structure, quality, and characteristics.

