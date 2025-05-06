from setuptools import setup, find_packages

setup(
    name="pr-static-analysis",
    version="0.1.0",
    description="A flexible rule-based system for analyzing pull requests",
    author="Codegen",
    author_email="info@codegen.sh",
    packages=find_packages(),
    install_requires=[
        "pyyaml>=6.0",
    ],
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)

