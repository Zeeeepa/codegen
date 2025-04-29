# Codegen SDK Analysis Features

This document provides a comprehensive overview of the analysis capabilities available in the Codegen SDK. These features enable developers to gain deep insights into their codebase structure, complexity, and quality.

## Core Analysis Functions

The Codegen SDK provides the following analysis functions:

| Function                          | Description                                                                                   |
| --------------------------------- | --------------------------------------------------------------------------------------------- |
| `calculate_cyclomatic_complexity` | Calculates the cyclomatic complexity of a function by analyzing control flow statements       |
| `cc_rank`                         | Converts a cyclomatic complexity value into a letter grade (A-F)                              |
| `get_operators_and_operands`      | Extracts operators and operands from a function for Halstead complexity metrics               |
| `calculate_halstead_volume`       | Calculates Halstead volume based on operators and operands                                    |
| `count_lines`                     | Counts different types of lines in source code (total, logical, source, comments)             |
| `calculate_maintainability_index` | Calculates the maintainability index based on Halstead volume, cyclomatic complexity, and LOC |
| `get_maintainability_rank`        | Converts a maintainability index into a letter grade                                          |
| `calculate_doi`                   | Calculates the depth of inheritance for a given class                                         |

## Analysis Categories

### 1. Codebase Structure Analysis

#### File Statistics

- Total file count
- Files by language/extension
- File size distribution
- Directory structure analysis

#### Symbol Tree Analysis

- Total symbol count
- Symbol type distribution (classes, functions, variables, interfaces)
- Symbol hierarchy visualization
- Top-level vs nested symbol analysis

#### Import/Export Analysis

- Import dependency mapping
- External vs internal dependency analysis
- Circular import detection
- Unused import identification

#### Module Organization

- Module coupling metrics
- Module cohesion analysis
- Package structure visualization
- Module dependency graphs

### 2. Symbol-Level Analysis

#### Function Analysis

- Parameter analysis (count, types, defaults)
- Return type analysis
- Function complexity metrics
- Call site tracking
- Async function detection
- Function overload analysis

#### Class Analysis

- Inheritance hierarchy mapping
- Method analysis
- Attribute analysis
- Constructor analysis
- Interface implementation verification
- Access modifier usage (public/private)

#### Variable Analysis

- Type inference
- Usage tracking
- Scope analysis
- Constant vs mutable usage
- Global variable detection

#### Type Analysis

- Type alias resolution
- Generic type usage
- Type consistency checking
- Union/intersection type analysis

### 3. Dependency and Flow Analysis

#### Call Graph Generation

- Function call relationships
- Call hierarchy visualization
- Entry point analysis
- Dead code detection

#### Data Flow Analysis

- Variable usage tracking
- Data transformation paths
- Input/output parameter analysis

#### Control Flow Analysis

- Conditional branch analysis
- Loop structure analysis
- Exception handling paths
- Return statement analysis

#### Symbol Usage Analysis

- Symbol reference tracking
- Usage frequency metrics
- Cross-file symbol usage

### 4. Code Quality Analysis

#### Unused Code Detection

- Unused functions
- Unused classes
- Unused variables
- Unused imports

#### Code Duplication Analysis

- Similar function detection
- Repeated code patterns
- Refactoring opportunities

#### Complexity Metrics

- Cyclomatic complexity
- Cognitive complexity
- Nesting depth analysis
- Function size metrics

#### Style and Convention Analysis

- Naming convention consistency
- Comment coverage
- Documentation completeness
- Code formatting consistency

### 5. Visualization Capabilities

#### Dependency Graphs

- Module dependency visualization
- Symbol dependency visualization
- Import relationship graphs

#### Call Graphs

- Function call visualization
- Call hierarchy trees
- Entry point flow diagrams

#### Symbol Trees

- Class hierarchy visualization
- Symbol relationship diagrams
- Package structure visualization

#### Heat Maps

- Code complexity heat maps
- Usage frequency visualization
- Change frequency analysis

### 6. Language-Specific Analysis

#### Python-Specific Analysis

- Decorator usage analysis
- Dynamic attribute access detection
- Type hint coverage
- Magic method usage

#### TypeScript-Specific Analysis

- Interface implementation verification
- Type definition completeness
- JSX/TSX component analysis
- Type narrowing pattern detection

## Using the Analysis Features

The Codegen SDK provides a simple and intuitive API for accessing these analysis features. Here's a basic example:

```python
from codegen import Codebase

# Initialize a codebase
codebase = Codebase.from_repo("owner/repo")

# Get basic codebase statistics
print(f"Files: {len(codebase.files)}")
print(f"Functions: {len(codebase.functions)}")
print(f"Classes: {len(codebase.classes)}")

# Analyze a specific function
for func in codebase.functions:
    complexity = calculate_cyclomatic_complexity(func)
    operators, operands = get_operators_and_operands(func)
    volume = calculate_halstead_volume(operators, operands)
    loc = len(func.code_block.source.splitlines())
    mi_score = calculate_maintainability_index(volume, complexity, loc)

    print(f"Function: {func.name}")
    print(f"  Cyclomatic Complexity: {complexity} (Rank: {cc_rank(complexity)})")
    print(f"  Maintainability Index: {mi_score}")
    print(f"  Lines of Code: {loc}")
```

## Integration with Static Analysis Tools

The Codegen SDK can be integrated with other static analysis tools to provide a comprehensive view of your codebase. This allows you to:

1. Perform full analysis when prompted
1. Track changes in code quality over time
1. Identify potential issues before they become problems
1. Visualize complex relationships within your codebase

By leveraging these analysis capabilities, you can gain valuable insights into your codebase and make informed decisions about refactoring, optimization, and architecture.

