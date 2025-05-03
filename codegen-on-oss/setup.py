"""
Setup script for codegen-on-oss.
"""

from setuptools import setup, find_packages

setup(
    name="codegen-on-oss",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "sqlalchemy>=2.0.0",
        "fastapi>=0.100.0",
        "pydantic>=2.0.0",
        "redis>=4.5.0",
        "alembic>=1.10.0",
        "graphene>=3.2.0",
        "websockets>=11.0.0",
    ],
    entry_points={
        "console_scripts": [
            "codegen-on-oss=codegen_on_oss.cli:main",
        ],
    },
)

