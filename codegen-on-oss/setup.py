from setuptools import find_packages, setup

setup(
    name="codegen-on-oss",
    version="0.1.0",
    description="Enhanced Codegen-on-OSS Architecture",
    long_description=open("README_ENHANCED.md").read(),
    long_description_content_type="text/markdown",
    author="Codegen",
    author_email="info@codegen.sh",
    url="https://github.com/Zeeeepa/codegen",
    packages=find_packages(),
    python_requires=">=3.11",
    install_requires=[
        "networkx",
        "platformdirs",
        "pydantic-settings",
        "fastapi",
        "requests",
        "sqlalchemy",
        "uvicorn",
        "websockets",
    ],
    extras_require={
        "dev": [
            "mypy",
            "black",
            "isort",
            "pytest",
            "ruff",
            "pre-commit",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
    ],
)
