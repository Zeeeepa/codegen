from setuptools import setup, find_packages

setup(
    name="pr_review_bot_new",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests",
        "python-dotenv",
        "fastapi",
        "uvicorn",
        "schedule",
        "pyngrok",
    ],
    entry_points={
        "console_scripts": [
            "pr-review-bot=pr_review_bot_new.run:main",
        ],
    },
)