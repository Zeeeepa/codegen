#!/usr/bin/env bash
set -e

# Check for UV and install if not present
if ! command -v uv &> /dev/null; then
    echo "UV not found. Installing UV..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi

# Install required tools
uv tool install pre-commit --with pre-commit-uv
uv tool install deptry
uv tool update-shell

# Create and activate virtual environment
uv venv
source .venv/bin/activate

# Install dependencies
uv sync --all-extras

# Install pre-commit hooks
pre-commit install
pre-commit install-hooks

echo "Setup completed successfully!"
