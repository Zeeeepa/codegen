"""
Setup script for the PR static analysis system.
"""

from setuptools import find_packages, setup

setup(
    name="pr-static-analysis",
    version="0.1.0",
    description="A flexible rule-based system for analyzing pull requests",
    author="Codegen",
    author_email="info@codegen.sh",
    packages=find_packages(),
    install_requires=[
        "pyyaml>=5.1",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.7",
)
