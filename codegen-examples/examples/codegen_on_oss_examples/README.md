# Codegen-on-OSS Examples

This directory contains examples demonstrating how to use the `codegen-on-oss` component for various code analysis tasks.

## Examples

1. **Basic Analysis Example** (`basic_analysis.py`)
   - Demonstrates the use of the unified analysis module
   - Shows how to use the CodeAnalyzer and CodeMetrics classes

2. **Server Example** (`server_example.py`)
   - Shows how to interact with the analysis server
   - Includes a client implementation for making API requests

3. **Enhanced Server Example** (`enhanced_server_example.py`)
   - Demonstrates the enhanced analysis server for PR validation
   - Includes project management functionality

4. **Commit Analysis Example** (`commit_example.py`)
   - Shows how to analyze git commits
   - Includes examples of commit-based code analysis

5. **SWE Harness Example** (`swe_harness_example.py`)
   - Demonstrates the SWE harness agent for analyzing commits and PRs
   - Shows integration with the snapshot functionality

6. **Code Integrity Analysis Example** (`analyze_code_integrity.py`)
   - Provides a command-line interface for analyzing code integrity
   - Shows how to generate reports and compare branches

## Usage

Each example can be run independently. See the individual files for specific usage instructions.

```python
# Example usage
python -m codegen-examples.examples.codegen_on_oss_examples.basic_analysis
```

## Dependencies

These examples require the `codegen-on-oss` component to be installed.

