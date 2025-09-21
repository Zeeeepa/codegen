#!/bin/bash
"""
Installation script for graph-sitter tools and dependencies
Sets up the complete environment for the analyzed tools
"""

echo "🚀 Setting up Graph-Sitter Tools Environment"
echo "============================================="

# Install main graph-sitter repository with extensions
echo "📦 Installing graph-sitter from GitHub repository..."
pip install -e git+https://github.com/Zeeeepa/graph-sitter.git@develop#egg=graph-sitter

# Install autogenlib extension as separate package
echo "🔧 Installing autogenlib extension..."
pip install -e git+https://github.com/Zeeeepa/graph-sitter.git@develop#subdirectory=src/graph_sitter/extensions/autogenlib&egg=autogenlib

# Install solidlsp extension as separate package  
echo "🔍 Installing solidlsp extension..."
pip install -e git+https://github.com/Zeeeepa/graph-sitter.git@develop#subdirectory=src/graph_sitter/extensions/lsp/solidlsp&egg=solidlsp

# Install other required dependencies
echo "📚 Installing additional dependencies..."
pip install openai
pip install fastapi
pip install uvicorn
pip install networkx
pip install pydantic
pip install pathspec
pip install asyncio-mqtt  # For any async messaging needs

echo ""
echo "✅ Installation complete!"
echo ""
echo "🧪 Testing imports..."
python3 -c "
try:
    import graph_sitter
    print('✓ graph_sitter imported successfully')
except ImportError as e:
    print(f'✗ graph_sitter import failed: {e}')

try:
    import autogenlib
    print('✓ autogenlib imported successfully')
except ImportError as e:
    print(f'✗ autogenlib import failed: {e}')

try:
    import solidlsp
    print('✓ solidlsp imported successfully')
except ImportError as e:
    print(f'✗ solidlsp import failed: {e}')

try:
    import openai
    print('✓ openai imported successfully')
except ImportError as e:
    print(f'✗ openai import failed: {e}')

try:
    import fastapi
    print('✓ fastapi imported successfully')
except ImportError as e:
    print(f'✗ fastapi import failed: {e}')

try:
    import networkx
    print('✓ networkx imported successfully')
except ImportError as e:
    print(f'✗ networkx import failed: {e}')
"

echo ""
echo "🎯 Next steps:"
echo "1. Set your OpenAI API key: export OPENAI_API_KEY='your-key-here'"
echo "2. Test the tools: python3 test_all_tools.py"
echo "3. Run the backend API: python3 tools/graph_sitter_backend.py"
echo ""
echo "📖 Documentation:"
echo "- Graph-Sitter: https://github.com/Zeeeepa/graph-sitter"
echo "- AutoGenLib extensions: https://github.com/Zeeeepa/graph-sitter/tree/develop/src/graph_sitter/extensions/autogenlib"
echo "- SolidLSP extensions: https://github.com/Zeeeepa/graph-sitter/tree/develop/src/graph_sitter/extensions/lsp/solidlsp"