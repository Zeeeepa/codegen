from setuptools import setup, find_packages

setup(
    name="codegen-on-oss",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "networkx",
        "platformdirs",
        "pydantic-settings",
        "fastapi",
        "requests",
        "sqlalchemy",
        "uvicorn",
        "websockets",
        "types-requests",
    ],
    extras_require={
        "dev": [
            "mypy",
            "black",
            "isort",
            "pytest",
        ]
    },
)

