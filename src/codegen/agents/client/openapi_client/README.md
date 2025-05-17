# Codegen API Client

This module provides interfaces for communicating with the Codegen API services, handling authentication, request formatting, and response parsing.

## Overview

The API Client module consists of two main components:

1. **OpenAPI Client**: An auto-generated client based on the OpenAPI specification that provides low-level access to the Codegen API.
2. **CLI API Client**: A higher-level client that provides a more user-friendly interface for interacting with the Codegen API.

## Authentication

The API client supports authentication using API keys. You can provide an API key in the following ways:

1. **Environment Variable**: Set the `CODEGEN_API_KEY` environment variable.
2. **Configuration**: Pass an API key directly to the `Configuration` constructor.

Example:

```python
from codegen.agents.client.openapi_client.configuration import Configuration
from codegen.agents.client.openapi_client.api_client import ApiClient

# Using environment variable (recommended)
# export CODEGEN_API_KEY=your_api_key
config = Configuration.get_default()

# Or set the API key directly
config = Configuration()
config.api_key["Authorization"] = "your_api_key"
config.api_key_prefix["Authorization"] = "Bearer"

api_client = ApiClient(configuration=config)
```

## OpenAPI Client

The OpenAPI client provides direct access to the Codegen API endpoints. It includes the following components:

- **ApiClient**: The main client class that handles HTTP requests and responses.
- **Configuration**: Configuration settings for the API client.
- **API Implementations**:
  - **AgentsApi**: API for managing agent runs.
  - **OrganizationsApi**: API for managing organizations.
  - **UsersApi**: API for managing users.
- **Models**: Data models for requests and responses.

Example:

```python
from codegen.agents.client.openapi_client.api.agents_api import AgentsApi
from codegen.agents.client.openapi_client.models.create_agent_run_input import CreateAgentRunInput

# Create an API client
agents_api = AgentsApi()

# Create an agent run
create_agent_run_input = CreateAgentRunInput(prompt="Test prompt")
response = agents_api.create_agent_run_v1_organizations_org_id_agent_run_post(
    org_id=123,
    create_agent_run_input=create_agent_run_input,
)

print(f"Agent run created with ID: {response.id}")
```

## CLI API Client

The CLI API client provides a higher-level interface for interacting with the Codegen API. It includes methods for common operations like running codemods, deploying codemods, and looking up codemods.

Example:

```python
from codegen.cli.api.client import RestAPI
from codegen.cli.api.schemas import CodemodRunType

# Create a REST API client
rest_api = RestAPI(auth_token="your_api_key")

# Run a codemod
result = rest_api.run(
    function=my_codemod,
    include_source=True,
    run_type=CodemodRunType.DIFF,
)

print(f"Codemod run success: {result.success}")
print(f"Web link: {result.web_link}")
```

## Error Handling

The API client provides robust error handling for various error scenarios:

- **Network Errors**: Errors related to network connectivity.
- **Authentication Errors**: Errors related to invalid or expired API keys.
- **Server Errors**: Errors returned by the server.
- **Validation Errors**: Errors related to invalid request data.

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

## API Versioning

The API client supports API versioning through the URL path. The current version is `v1`.

## Customization

You can customize the API client behavior by modifying the `Configuration` object:

- **Host**: Change the API host URL.
- **Timeouts**: Set request timeouts.
- **Retries**: Configure retry behavior.
- **Proxy**: Set up a proxy for API requests.
- **SSL Verification**: Configure SSL certificate verification.

Example:

```python
from codegen.agents.client.openapi_client.configuration import Configuration

config = Configuration()
config.host = "https://custom-api.example.com"
config.retries = 3
config.proxy = "http://proxy.example.com:8080"
config.verify_ssl = False  # Not recommended for production
```

## Debugging

You can enable debug logging to troubleshoot API client issues:

```python
from codegen.agents.client.openapi_client.configuration import Configuration

config = Configuration()
config.debug = True
```

This will log detailed information about API requests and responses.

## Contributing

If you find any issues or have suggestions for improvements, please open an issue or submit a pull request.

