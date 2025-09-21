# 🚀 Graph-Sitter Tools Installation Guide

This guide helps you install the graph-sitter tools and their dependencies correctly from the GitHub repositories.

## 📋 Prerequisites

- Python 3.8 or higher
- Git
- pip (latest version recommended)

## 🔧 Installation Methods

### Method 1: Using Requirements File (Recommended)

```bash
# Install all dependencies from requirements.txt
pip install -r requirements.txt
```

### Method 2: Using Setup Script

```bash
# Make the script executable and run it
chmod +x install_dependencies.sh
./install_dependencies.sh
```

### Method 3: Manual Installation

```bash
# 1. Install main graph-sitter repository
pip install -e git+https://github.com/Zeeeepa/graph-sitter.git@develop#egg=graph-sitter

# 2. Install autogenlib extension
pip install -e git+https://github.com/Zeeeepa/graph-sitter.git@develop#subdirectory=src/graph_sitter/extensions/autogenlib&egg=autogenlib

# 3. Install solidlsp extension
pip install -e git+https://github.com/Zeeeepa/graph-sitter.git@develop#subdirectory=src/graph_sitter/extensions/lsp/solidlsp&egg=solidlsp

# 4. Install other dependencies
pip install openai fastapi uvicorn networkx pydantic pathspec rich
```

### Method 4: Development Installation

```bash
# Install as editable package for development
pip install -e .
```

## 🔑 Environment Configuration

Set up your environment variables:

```bash
# Required for AI functionality
export OPENAI_API_KEY="your-openai-api-key-here"

# Optional: Custom OpenAI base URL
export OPENAI_API_BASE_URL="https://api.openai.com/v1"

# Optional: Custom model
export OPENAI_MODEL="gpt-4o"
```

## ✅ Verification

Test your installation:

```bash
# Run the comprehensive test suite
python3 test_all_tools.py

# Test individual imports
python3 -c "
import graph_sitter
import autogenlib
import solidlsp
import openai
import fastapi
import networkx
print('✅ All imports successful!')
"
```

## 🎯 Quick Start

1. **Start the API backend**:
   ```bash
   python3 tools/graph_sitter_backend.py
   ```

2. **Run analysis on your codebase**:
   ```bash
   python3 tools/graph_sitter_analysis.py /path/to/your/code
   ```

3. **Use LSP diagnostics**:
   ```bash
   python3 tools/lsp_diagnostics.py --project /path/to/project
   ```

## 🐛 Troubleshooting

### Common Issues:

1. **Import errors**:
   - Ensure you're using the correct GitHub URLs
   - Check that the `develop` branch exists
   - Try installing with `--force-reinstall`

2. **Permission errors**:
   - Use `pip install --user` if needed
   - Consider using a virtual environment

3. **Network issues**:
   - Check GitHub access
   - Try using SSH URLs: `git+ssh://git@github.com/`

### Virtual Environment (Recommended):

```bash
# Create and activate virtual environment
python3 -m venv graph-sitter-env
source graph-sitter-env/bin/activate  # On Windows: graph-sitter-env\Scripts\activate

# Install in virtual environment
pip install -r requirements.txt
```

## 📚 Repository Structure

The tools expect this repository structure:
```
graph-sitter/
├── src/
│   └── graph_sitter/
│       ├── extensions/
│       │   ├── autogenlib/
│       │   └── lsp/
│       │       └── solidlsp/
│       └── tools/
└── develop branch
```

## 🔄 Updates

To update the tools:

```bash
# Update all packages
pip install --upgrade -r requirements.txt

# Or update individual packages
pip install --upgrade --force-reinstall git+https://github.com/Zeeeepa/graph-sitter.git@develop
```

## 📞 Support

If you encounter issues:
1. Check the GitHub repository issues
2. Verify the repository structure matches expectations
3. Ensure you're using the `develop` branch
4. Test with a clean virtual environment