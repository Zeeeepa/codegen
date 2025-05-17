# Codegen CLI API Client

This module provides a high-level interface for communicating with the Codegen API services from the CLI.

## Overview

The CLI API client is a wrapper around the OpenAPI client that provides a more user-friendly interface for interacting with the Codegen API. It includes methods for common operations like running codemods, deploying codemods, and looking up codemods.

## Components

The CLI API client consists of the following components:

- **RestAPI**: The main client class that handles authentication, request formatting, and response parsing.
- **Endpoints**: Constants defining the API endpoints.
- **Schemas**: Pydantic models for request and response data.

## Authentication

The CLI API client uses a bearer token for authentication. You can provide a token when creating the client:

```python
from codegen.cli.api.client import RestAPI

rest_api = RestAPI(auth_token="your_api_token")
```

## API Operations

The CLI API client supports the following operations:

### Run a Codemod

Run a codemod transformation on a repository:

```python
from codegen.cli.api.client import RestAPI
from codegen.cli.api.schemas import CodemodRunType
from codegen.cli.utils.codemods import Codemod

# Create a REST API client
rest_api = RestAPI(auth_token="your_api_token")

# Run a codemod
result = rest_api.run(
    function=my_codemod,
    include_source=True,
    run_type=CodemodRunType.DIFF,
    template_context={"key": "value"},
)

print(f"Codemod run success: {result.success}")
print(f"Web link: {result.web_link}")
```

### Get Documentation

Get documentation for a repository:

```python
from codegen.cli.api.client import RestAPI

# Create a REST API client
rest_api = RestAPI(auth_token="your_api_token")

# Get documentation
result = rest_api.get_docs()

print(f"Documentation: {result.docs}")
```

### Ask an Expert

Ask the expert system a question:

```python
from codegen.cli.api.client import RestAPI

# Create a REST API client
rest_api = RestAPI(auth_token="your_api_token")

# Ask an expert
result = rest_api.ask_expert("How do I use the API?")

print(f"Expert response: {result.response}")
```

### Create a Codemod

Get AI-generated starter code for a codemod:

```python
from codegen.cli.api.client import RestAPI

# Create a REST API client
rest_api = RestAPI(auth_token="your_api_token")

# Create a codemod
result = rest_api.create(
    name="my_codemod",
    query="Create a codemod that adds type hints to functions",
)

print(f"Generated codemod: {result.codemod}")
```

### Identify a Codemod

Identify the user's codemod:

```python
from codegen.cli.api.client import RestAPI

# Create a REST API client
rest_api = RestAPI(auth_token="your_api_token")

# Identify a codemod
result = rest_api.identify()

print(f"Identified codemod: {result.codemod_name}")
```

### Deploy a Codemod

Deploy a codemod to the Modal backend:

```python
from codegen.cli.api.client import RestAPI

# Create a REST API client
rest_api = RestAPI(auth_token="your_api_token")

# Deploy a codemod
result = rest_api.deploy(
    codemod_name="my_codemod",
    codemod_source="def my_codemod(): pass",
    lint_mode=True,
    lint_user_whitelist=["user1", "user2"],
    message="Initial deployment",
    arguments_schema={"arg1": "string"},
)

print(f"Deployed codemod ID: {result.codemod_id}")
```

### Look Up a Codemod

Look up a codemod by name:

```python
from codegen.cli.api.client import RestAPI

# Create a REST API client
rest_api = RestAPI(auth_token="your_api_token")

# Look up a codemod
result = rest_api.lookup("my_codemod")

print(f"Codemod source: {result.codemod_source}")
```

### Run on PR

Test a webhook against a specific PR:

```python
from codegen.cli.api.client import RestAPI

# Create a REST API client
rest_api = RestAPI(auth_token="your_api_token")

# Run on PR
result = rest_api.run_on_pr(
    codemod_name="my_codemod",
    repo_full_name="owner/repo",
    github_pr_number=123,
    language="python",
)

print(f"PR run result: {result.message}")
```

### Look Up PR

Look up a PR by repository and PR number:

```python
from codegen.cli.api.client import RestAPI

# Create a REST API client
rest_api = RestAPI(auth_token="your_api_token")

# Look up a PR
result = rest_api.lookup_pr(
    repo_full_name="owner/repo",
    github_pr_number=123,
)

print(f"PR data: {result.pr_data}")
```

### Improve Codemod

Improve a codemod:

```python
from codegen.cli.api.client import RestAPI
from codegen.shared.enums.programming_language import ProgrammingLanguage

# Create a REST API client
rest_api = RestAPI(auth_token="your_api_token")

# Improve a codemod
result = rest_api.improve_codemod(
    codemod="def my_codemod(): pass",
    task="Add error handling",
    concerns=["performance", "readability"],
    context={"file": "test.py"},
    language=ProgrammingLanguage.PYTHON,
)

print(f"Improved codemod: {result.improved_codemod}")
```

## Error Handling

The CLI API client provides robust error handling for various error scenarios:

- **InvalidTokenError**: Raised when the authentication token is invalid or expired.
- **ServerError**: Raised when the server encounters an error while processing the request.

Example:

```python
from codegen.cli.api.client import RestAPI
from codegen.cli.errors import InvalidTokenError, ServerError

try:
    rest_api = RestAPI(auth_token="invalid_token")
    result = rest_api.run(my_codemod)
except InvalidTokenError as e:
    print(f"Authentication error: {e}")
except ServerError as e:
    print(f"Server error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Debugging

You can enable debug logging to troubleshoot API client issues by setting the `DEBUG` flag in the global environment:

```python
from codegen.cli.env.global_env import global_env

global_env.DEBUG = True
```

This will log detailed information about API requests and responses.

## Contributing

If you find any issues or have suggestions for improvements, please open an issue or submit a pull request.

