#!/usr/bin/env python3
"""
Setup script for the PR Review Bot.
"""

from setuptools import setup, find_packages

setup(
    name="pr_review_bot_new",
    version="0.1.0",
    description="PR Review Bot for GitHub repositories",
    author="Codegen Team",
    author_email="info@codegen.com",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.68.0",
        "uvicorn>=0.15.0",
        "python-dotenv>=0.19.0",
        "PyGithub>=1.55",
        "requests>=2.26.0",
        "schedule>=1.1.0",
        "pyngrok>=5.1.0",
    ],
    extras_require={
        "ai": [
            "langchain-core>=0.1.0",
            "langchain-anthropic>=0.1.0",
            "langchain-openai>=0.1.0",
        ],
        "codegen": [
            "codegen-sdk>=0.1.0",
        ],
        "all": [
            "langchain-core>=0.1.0",
            "langchain-anthropic>=0.1.0",
            "langchain-openai>=0.1.0",
            "codegen-sdk>=0.1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "pr-review-bot=pr_review_bot_new.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
)