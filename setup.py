from setuptools import setup, find_packages

setup(
    name="projector",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "streamlit",
        "python-dotenv",
    ],
)
