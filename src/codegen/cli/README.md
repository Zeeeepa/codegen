# Codegen CLI

A comprehensive command-line interface for interacting with the Codegen SDK, allowing users to create, configure, and deploy AI-powered code generation agents.

## Installation

The CLI is installed as part of the Codegen SDK package:

```bash
pip install codegen
```

## Getting Started

Initialize a new Codegen project in your repository:

```bash
codegen init
```

This will set up the necessary configuration files and directories for using Codegen in your project.

## Authentication

Before using most Codegen features, you need to authenticate:

```bash
codegen login
```

To log out and clear your authentication token:

```bash
codegen logout
```

## Commands

### Core Commands

- `init`: Initialize a new Codegen project in a repository
- `login`: Authenticate with the Codegen API
- `logout`: Clear authentication token
- `config`: View and modify configuration settings

### Agent Management

- `create`: Generate a new codemod from a description
- `deploy`: Deploy a codemod to the cloud
- `list`: List all available codemods
- `run`: Run a codemod locally or in the cloud

### Advanced Features

- `agent`: Manage AI agents
- `expert`: Ask the expert system a question
- `profile`: Manage user profiles
- `run-on-pr`: Test a codemod against a specific PR
- `notebook`: Open a Jupyter notebook for interactive development
- `reset`: Reset the Codegen environment
- `update`: Update the Codegen SDK
- `lsp`: Language Server Protocol integration
- `serve`: Start a local server for Codegen
- `start`: Start Codegen services

## Command Details

### `codegen init`

Initialize a new Codegen project in a repository.

```bash
codegen init [--path PATH] [--token TOKEN]
```

Options:
- `--path PATH`: Path to the repository (default: current directory)
- `--token TOKEN`: GitHub token for authentication

### `codegen login`

Authenticate with the Codegen API.

```bash
codegen login [--token TOKEN]
```

Options:
- `--token TOKEN`: API token for authentication

### `codegen logout`

Clear authentication token.

```bash
codegen logout
```

### `codegen config`

View and modify configuration settings.

```bash
codegen config [get|set|list] [KEY] [VALUE]
```

Operations:
- `get KEY`: Get the value of a configuration key
- `set KEY VALUE`: Set the value of a configuration key
- `list`: List all configuration settings

### `codegen create`

Generate a new codemod from a description.

```bash
codegen create NAME DESCRIPTION
```

Arguments:
- `NAME`: Name of the codemod to create
- `DESCRIPTION`: Description of what the codemod should do

### `codegen deploy`

Deploy a codemod to the cloud.

```bash
codegen deploy NAME [--message MESSAGE] [--lint]
```

Arguments:
- `NAME`: Name of the codemod to deploy

Options:
- `--message MESSAGE`: Deployment message
- `--lint`: Enable lint mode

### `codegen list`

List all available codemods.

```bash
codegen list
```

### `codegen run`

Run a codemod locally or in the cloud.

```bash
codegen run [--local|--cloud|--daemon] [--pr] [--context KEY=VALUE] NAME
```

Arguments:
- `NAME`: Name of the codemod to run

Options:
- `--local`: Run the codemod locally (default)
- `--cloud`: Run the codemod in the cloud
- `--daemon`: Run the codemod in daemon mode
- `--pr`: Generate a pull request
- `--context KEY=VALUE`: Set context variables for the codemod

### `codegen expert`

Ask the expert system a question.

```bash
codegen expert QUERY
```

Arguments:
- `QUERY`: Question to ask the expert system

## Best Practices

- Each folder in `cli` corresponds to a command group
- Command group folders should have a `main.py` file where the CLI commands are defined
- Store utils specific to a CLI command group within its folder
- Store shared utils in `cli/utils`

## Dependencies

- [codegen.sdk](https://github.com/codegen-sh/codegen-sdk/tree/develop/src/codegen/sdk)
- [codegen.shared](https://github.com/codegen-sh/codegen-sdk/tree/develop/src/codegen/shared)

## Development

To contribute to the CLI module:

1. Clone the repository
2. Install development dependencies
3. Run tests to ensure everything is working correctly

```bash
# Run tests
pytest tests/unit/codegen/cli
pytest tests/integration/codegen/cli
```

