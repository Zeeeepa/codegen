ARG PYTHON_VERSION=3.13
ARG CODEGEN_BOT_GHE_TOKEN=""
FROM ghcr.io/astral-sh/uv:python${PYTHON_VERSION}-bookworm-slim AS base_uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
ENV GITHUB_WORKSPACE=/workspace

# Change the working directory to the `codegen-sdk` directory
FROM base_uv AS install-tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    ca-certificates \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js using the official setup script
RUN curl -fsSL https://deb.nodesource.com/setup_23.x -o nodesource_setup.sh \
    && bash nodesource_setup.sh \
    && apt-get update && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/* \
    && corepack enable

# Install Python tools with caching
RUN --mount=type=cache,target=/root/.cache/uv uv pip install --system coverage
RUN --mount=type=cache,target=/root/.cache/uv uv tool install codecov-cli --python 3.10
RUN --mount=type=cache,target=/root/.cache/uv uv tool install pre-commit --with pre-commit-uv

WORKDIR /codegen-sdk
ENTRYPOINT [ "uv", "run", "--frozen", "/bin/bash"]

FROM install-tools AS base-image
# Install dependencies with caching
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=hatch.toml,target=hatch.toml \
    uv sync --frozen --no-install-workspace --all-extras

ADD . /codegen-sdk
# Sync the project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --all-extras

FROM base-image AS pre-commit
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=cache,target=/root/.cache/pre-commit \
    uv run pre-commit install-hooks

FROM base-image AS extra-repos
ARG CODEGEN_BOT_GHE_TOKEN=""
RUN uv run python -m tests.shared.codemod.commands clone-repos --clean-cache --extra-repos --token ${CODEGEN_BOT_GHE_TOKEN}

FROM base-image AS oss-repos
ARG CODEGEN_BOT_GHE_TOKEN=""
RUN uv run python -m tests.shared.codemod.commands clone-repos --clean-cache --token ${CODEGEN_BOT_GHE_TOKEN}
