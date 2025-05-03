# Codegen Analysis Module

A comprehensive code analysis module for the Codegen-on-OSS project that provides a unified interface for analyzing codebases.

## Overview

The Analysis Module integrates various specialized analysis components into a cohesive system, allowing for:

- Code complexity analysis
- Import dependency analysis
- Documentation generation
- Symbol attribution
- Visualization of module dependencies
- Comprehensive code quality metrics

## Components

The module consists of the following key components:

- **CodeAnalyzer**: Central class that orchestrates all analysis functionality
- **Metrics Integration**: Connection with the CodeMetrics class for comprehensive metrics
- **Import Analysis**: Tools for analyzing import relationships and cycles
- **Documentation Tools**: Functions for generating documentation for code
- **Visualization**: Tools for visualizing dependencies and relationships

## Usage

### Basic Usage

```python
from codegen import Codebase
from codegen_on_oss.analysis.analysis import CodeAnalyzer
from codegen_on_oss.metrics import CodeMetrics

# Load a codebase
codebase = Codebase.from_repo("owner/repo")

# Create analyzer instance
analyzer = CodeAnalyzer(codebase)

# Get codebase summary
summary = analyzer.get_codebase_summary()
print(summary)

# Analyze complexity
complexity_results = analyzer.analyze_complexity()
print(f"Average cyclomatic complexity: {complexity_results['cyclomatic_complexity']['average']}")

# Analyze imports
import_analysis = analyzer.analyze_imports()
print(f"Found {len(import_analysis['import_cycles'])} import cycles")

# Create metrics instance
metrics = CodeMetrics(codebase)

# Get code quality summary
quality_summary = metrics.get_code_quality_summary()
print(quality_summary)
```

### Web API

The module also provides a FastAPI web interface for analyzing repositories:

```bash
# Run the API server
python -m codegen_on_oss.analysis.analysis
```

Then you can make POST requests to `/analyze_repo` with a JSON body:

```json
{
  "repo_url": "owner/repo"
}
```

## Key Features

### Code Complexity Analysis

- Cyclomatic complexity calculation
- Halstead complexity metrics
- Maintainability index
- Line metrics (LOC, LLOC, SLOC, comments)

### Import Analysis

- Detect import cycles
- Identify problematic import loops
- Visualize module dependencies

### Documentation Generation

- Generate documentation for functions
- Create MDX documentation for classes
- Extract context for symbols

### Symbol Attribution

- Track symbol authorship
- Analyze AI contribution

### Dependency Analysis

- Create dependency graphs
- Find central files
- Identify dependency cycles

## Integration with Metrics

The Analysis Module is fully integrated with the CodeMetrics class, which provides:

- Comprehensive code quality metrics
- Functions to find problematic code areas
- Dependency analysis
- Documentation generation

## Example

See `example.py` for a complete demonstration of the analysis module's capabilities.

