# Codebase Analyzer

The Codebase Analyzer is a comprehensive static code analysis tool that provides detailed insights into a codebase's structure, dependencies, code quality, and more.

## Installation

The Codebase Analyzer is included in the codegen-on-oss package. To install it, run:

```bash
pip install codegen-on-oss
```

## Usage

### Command Line Interface

The Codebase Analyzer can be used from the command line:

```bash
# Analyze a repository by URL
cgparse analyze --repo-url https://github.com/username/repo

# Analyze a local repository
cgparse analyze --repo-path /path/to/local/repo

# Specify output format and file
cgparse analyze --repo-url https://github.com/username/repo --output-format html --output-file report.html

# Analyze specific categories
cgparse analyze --repo-url https://github.com/username/repo --categories codebase_structure code_quality
```

### Python API

The Codebase Analyzer can also be used as a Python library:

```python
from codegen_on_oss.analysis import CodebaseAnalyzer

# Initialize the analyzer
analyzer = CodebaseAnalyzer(repo_url="https://github.com/username/repo")

# Perform the analysis
results = analyzer.analyze(
    categories=["codebase_structure", "code_quality"],
    output_format="json",
    output_file="analysis.json"
)

# Access the results
print(results["metadata"]["repo_name"])
print(results["categories"]["codebase_structure"]["file_count"])
```

## Analysis Categories

The Codebase Analyzer provides analysis in the following categories:

### Codebase Structure

Analyzes the overall structure of the codebase, including:

- File count and distribution
- Language distribution
- Directory structure
- Symbol count and distribution
- Import dependencies
- Module coupling and cohesion
- Package structure
- Module dependency graph

### Symbol Level

Analyzes individual symbols (functions, classes, etc.) in the codebase, including:

- Function parameter analysis
- Return type analysis
- Function complexity metrics
- Call site tracking
- Async function detection
- Function overload analysis
- Inheritance hierarchy
- Method analysis
- Attribute analysis
- Constructor analysis
- Interface implementation verification
- Access modifier usage
- Type inference
- Usage tracking
- Scope analysis
- Constant vs. mutable usage
- Global variable detection
- Type alias resolution
- Generic type usage
- Type consistency checking
- Union/intersection type analysis

### Dependency Flow

Analyzes the flow of dependencies in the codebase, including:

- Function call relationships
- Call hierarchy visualization
- Entry point analysis
- Dead code detection
- Variable usage tracking
- Data transformation paths
- Input/output parameter analysis
- Conditional branch analysis
- Loop structure analysis
- Exception handling paths
- Return statement analysis
- Symbol reference tracking
- Usage frequency metrics
- Cross-file symbol usage

### Code Quality

Analyzes the quality of the code, including:

- Unused functions, classes, and variables
- Similar function detection
- Repeated code patterns
- Refactoring opportunities
- Cyclomatic complexity
- Cognitive complexity
- Nesting depth analysis
- Function size metrics
- Naming convention consistency
- Comment coverage
- Documentation completeness
- Code formatting consistency

### Visualization

Provides visualizations of the codebase, including:

- Module dependency visualization
- Symbol dependency visualization
- Import relationship graphs
- Function call visualization
- Call hierarchy trees
- Entry point flow diagrams
- Class hierarchy visualization
- Symbol relationship diagrams
- Package structure visualization
- Code complexity heat maps
- Usage frequency visualization
- Change frequency analysis

### Language Specific

Provides language-specific analysis, including:

- Decorator usage analysis
- Dynamic attribute access detection
- Type hint coverage
- Magic method usage
- Interface implementation verification
- Type definition completeness
- JSX/TSX component analysis
- Type narrowing pattern detection

### Code Metrics

Provides code metrics, including:

- Monthly commits
- Cyclomatic complexity
- Halstead volume
- Maintainability index
- Lines of code

## Performance Optimization

The Codebase Analyzer includes several optimizations for analyzing large codebases:

1. **Caching**: The analyzer caches intermediate results to avoid redundant calculations.
2. **Lazy Loading**: The analyzer uses lazy loading to only load the parts of the codebase that are needed for the requested analysis.
3. **Incremental Analysis**: The analyzer supports incremental analysis to only analyze changes since the last analysis.
4. **Parallel Processing**: The analyzer uses parallel processing for independent analysis tasks.
5. **Memory Optimization**: The analyzer uses memory-efficient data structures and algorithms to minimize memory usage.

## Extending the Analyzer

The Codebase Analyzer is designed to be extensible. You can add new analysis methods by:

1. Adding a new method to the `CodebaseAnalyzer` class
2. Adding the method to the appropriate category in the `METRICS_CATEGORIES` dictionary
3. Implementing the method to return a dictionary of analysis results

For example, to add a new method for analyzing function names:

```python
def get_function_name_analysis(self) -> Dict[str, Any]:
    """Analyze function names in the codebase."""
    functions = list(self.codebase.functions)
    name_analysis = {
        "avg_name_length": 0,
        "name_patterns": {},
        "common_prefixes": {},
        "common_suffixes": {}
    }
    
    # Implement the analysis
    # ...
    
    return name_analysis
```

Then add it to the appropriate category:

```python
METRICS_CATEGORIES = {
    "code_quality": [
        # ... existing methods ...
        "get_function_name_analysis",
    ],
    # ... other categories ...
}
```

## Troubleshooting

### Common Issues

1. **Memory Errors**: If you encounter memory errors when analyzing large codebases, try:
   - Analyzing specific categories instead of all categories
   - Using a machine with more memory
   - Reducing the depth of analysis

2. **Slow Analysis**: If the analysis is slow, try:
   - Analyzing specific categories instead of all categories
   - Using a faster machine
   - Reducing the depth of analysis

3. **Import Errors**: If you encounter import errors, make sure:
   - The Codegen SDK is installed
   - All dependencies are installed
   - The Python path is correctly set

### Getting Help

If you encounter issues with the Codebase Analyzer, please:

1. Check the documentation
2. Check the GitHub issues for similar problems
3. Create a new issue with a detailed description of the problem

## Contributing

Contributions to the Codebase Analyzer are welcome! Please see the [contributing guidelines](CONTRIBUTING.md) for more information.

