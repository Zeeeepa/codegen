from setuptools import setup, find_packages

setup(
    name="projector",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "streamlit",
        "python-dotenv",
        "slack-sdk",
        "PyGithub",
        "anthropic",
        "openai",
    ],
    entry_points={
        "console_scripts": [
            "projector=projector.cli:main",
        ],
    },
)
