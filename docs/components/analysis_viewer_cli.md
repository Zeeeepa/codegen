# Analysis Viewer CLI

The Analysis Viewer CLI provides a command-line interface for analyzing and comparing codebases. It offers a user-friendly way to access the functionality of the Codebase Analyzer and Codebase Comparator components.

## Overview

The Analysis Viewer CLI is built on top of the Codebase Analyzer and Codebase Comparator components, providing a convenient command-line interface for analyzing and comparing codebases. It supports multiple commands, including analyzing a single codebase, comparing two codebases, and running in interactive mode.

## Features

- **Multiple Commands**: Supports analyze, compare, interactive, and web commands
- **Flexible Input Options**: Can analyze and compare repositories from URLs or local paths
- **Customizable Output**: Supports multiple output formats and file options
- **Interactive Mode**: Provides an interactive shell for analyzing and comparing codebases
- **Web Interface Launcher**: Can launch the web interface for a graphical experience

## Commands

The Analysis Viewer CLI supports the following commands:

1. **analyze**: Analyze a single codebase
2. **compare**: Compare two codebases
3. **interactive**: Run in interactive mode
4. **web**: Launch the web interface

## Command Reference

### analyze

```
analyze [path] [options]
```

Analyze a single codebase.

Options:
- `--output`: Output file for the analysis results (default: stdout)
- `--format`: Output format (text, json, yaml) (default: text)
- `--categories`: Analysis categories to include (default: all)
- `--language`: Filter analysis to specific programming language
- `--depth`: Depth of analysis (1-3, where 3 is most detailed) (default: 2)

### compare

```
compare [path1] [path2] [options]
```

Compare two codebases.

Options:
- `--output`: Output file for the comparison results (default: stdout)
- `--format`: Output format (text, json, yaml) (default: text)
- `--categories`: Comparison categories to include (default: all)
- `--language`: Filter comparison to specific programming language
- `--depth`: Depth of comparison (1-3, where 3 is most detailed) (default: 2)

### interactive

```
interactive [options]
```

Run in interactive mode.

Options:
- `--path`: Path to the codebase to analyze initially

### web

```
web [options]
```

Launch the web interface.

Options:
- `--port`: Port to run the web interface on (default: 7860)
- `--host`: Host to run the web interface on (default: 127.0.0.1)

## Usage Examples

### Analyzing a Codebase

```bash
# Analyze a repository by path
codegen-on-oss analyze /path/to/repo

# Analyze with specific output format and file
codegen-on-oss analyze /path/to/repo --format json --output analysis.json

# Analyze specific categories
codegen-on-oss analyze /path/to/repo --categories codebase_structure code_quality

# Analyze with specific language filter
codegen-on-oss analyze /path/to/repo --language python

# Analyze with specific depth
codegen-on-oss analyze /path/to/repo --depth 3
```

### Comparing Codebases

```bash
# Compare two repositories by path
codegen-on-oss compare /path/to/repo1 /path/to/repo2

# Compare with specific output format and file
codegen-on-oss compare /path/to/repo1 /path/to/repo2 --format json --output comparison.json

# Compare specific categories
codegen-on-oss compare /path/to/repo1 /path/to/repo2 --categories codebase_structure code_quality

# Compare with specific language filter
codegen-on-oss compare /path/to/repo1 /path/to/repo2 --language python

# Compare with specific depth
codegen-on-oss compare /path/to/repo1 /path/to/repo2 --depth 3
```

### Running in Interactive Mode

```bash
# Run in interactive mode
codegen-on-oss interactive

# Run in interactive mode with initial path
codegen-on-oss interactive --path /path/to/repo
```

### Launching the Web Interface

```bash
# Launch the web interface
codegen-on-oss web

# Launch the web interface on a specific port
codegen-on-oss web --port 8080

# Launch the web interface on a specific host
codegen-on-oss web --host 0.0.0.0
```

## Interactive Mode Commands

When running in interactive mode, the following commands are available:

- `analyze [path] [options]`: Analyze a codebase
- `compare [path1] [path2] [options]`: Compare two codebases
- `set_path [path]`: Set the current path
- `show_results`: Show the last analysis or comparison results
- `save_results [filename] [format]`: Save the last results to a file
- `help`: Show help information
- `exit`: Exit interactive mode

Example interactive session:

```
$ codegen-on-oss interactive
Welcome to the Codebase Analysis Interactive Shell. Type help or ? to list commands.

(analysis) analyze /path/to/repo
... analysis results ...

(analysis) compare /path/to/repo1 /path/to/repo2
... comparison results ...

(analysis) save_results comparison.json json
Results saved to comparison.json

(analysis) exit
```

## Troubleshooting

### Common Issues

1. **Command Not Found**
   - Ensure the package is installed correctly
   - Check that the command is in your PATH

2. **Path Not Found**
   - Ensure the repository path exists
   - Check that you have read access to the path

3. **Invalid Options**
   - Check the command syntax and options
   - Use the help command for more information

4. **Output Format Issues**
   - Ensure the output format is one of: text, json, yaml
   - Check that you have write access to the output file location

5. **Web Interface Issues**
   - Ensure the port is not in use
   - Check that you have permission to bind to the specified port

### Error Messages

- **"Path not found"**: Ensure the repository path exists
- **"Invalid format"**: Ensure the output format is one of: text, json, yaml
- **"Invalid depth"**: Ensure the depth is between 1 and 3
- **"Port already in use"**: Choose a different port for the web interface

