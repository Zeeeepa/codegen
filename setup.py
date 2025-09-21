#!/usr/bin/env python3
"""
Setup script for graph-sitter tools package
"""

import os
from setuptools import setup, find_packages

setup(
    name="graph-sitter-tools",
    version="1.0.0",
    description="Comprehensive Graph-Sitter analysis tools with AI integration",
    long_description=open("README.md").read() if os.path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    author="Graph-Sitter Tools Team",
    packages=find_packages(where="tools"),
    package_dir={"": "tools"},
    install_requires=[
        # AI and web dependencies
        "openai>=1.0.0",
        "fastapi>=0.104.0",
        "uvicorn[standard]>=0.24.0",
        "pydantic>=2.0.0",
        "networkx>=3.0",
        "pathspec>=0.11.0",
        "rich>=13.0.0",
        "tree-sitter>=0.20.0",
        "requests>=2.25.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "mypy>=1.5.0",
        ],
        "viz": [
            "matplotlib>=3.7.0",
            "seaborn>=0.12.0",
            "pandas>=2.0.0",
        ],
        "all": [
            "anthropic>=0.7.0",
            "tree-sitter>=0.20.0",
            "tree-sitter-python>=0.20.0",
            "pygments>=2.16.0",
        ]
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    entry_points={
        "console_scripts": [
            "graph-sitter-backend=graph_sitter_backend:main",
            "graph-sitter-analyze=graph_sitter_analysis:main",
        ],
    },
)