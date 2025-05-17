# Authentication Module

The Authentication module handles user authentication, session management, and token handling for the Codegen SDK.

## Overview

This module provides the following functionality:

1. **Token Management**: Secure storage and retrieval of authentication tokens
1. **Session Management**: Handling of user sessions and repository context
1. **Authentication Flow**: User-friendly authentication process
1. **Decorators**: Utilities to ensure authenticated access to protected resources

## Components

### Constants (`constants.py`)

Defines the paths and directories used by the authentication module:

- `CONFIG_DIR`: Base configuration directory (`~/.config/codegen-sh`)
- `AUTH_FILE`: Location of the authentication token file
- Other directory constants for the Codegen SDK

### Token Manager (`token_manager.py`)

Handles the secure storage and retrieval of authentication tokens:

- `TokenManager`: Class for managing authentication tokens
  - `authenticate_token()`: Validates a token with the API
  - `save_token()`: Securely saves a token to disk
  - `get_token()`: Retrieves a token from disk
  - `clear_token()`: Securely removes a stored token
- `get_current_token()`: Helper function to get the current token

### Login (`login.py`)

Provides the authentication flow for users:

- `login_routine()`: Guides the user through the login process
  - Checks for token in arguments or environment variables
  - Opens browser for web-based authentication if needed
  - Validates and stores the token

### Decorators (`decorators.py`)

Provides utilities for ensuring authenticated access:

- `requires_auth`: Decorator that ensures a user is authenticated
  - Checks for an active session
  - Verifies token validity
  - Initiates login flow if needed
  - Injects the session into the decorated function

### Session (`session.py`)

Manages user sessions and repository context:

- `CodegenSession`: Class representing an authenticated session
  - Stores repository information
  - Validates GitHub tokens
  - Manages configuration

## Security Measures

The Authentication module implements several security measures:

1. **Secure Token Storage**:

   - Tokens are stored with 0600 permissions (read/write for owner only)
   - The config directory is created with 0700 permissions (read/write/execute for owner only)
   - Tokens are written atomically to prevent partial writes

1. **Token Validation**:

   - Tokens are validated with the API before use
   - Invalid or expired tokens trigger re-authentication

1. **Secure Token Removal**:

   - Token files are overwritten with null bytes before deletion
   - This prevents recovery of tokens from disk

1. **Error Handling**:

   - Comprehensive error handling for authentication failures
   - Detailed logging for troubleshooting

## Usage

### Authenticating a User

```python
from codegen.cli.auth.login import login_routine

# Authenticate with a provided token
token = login_routine(token="your-token")

# Or let the login_routine guide the user through authentication
token = login_routine()
```

### Requiring Authentication for a Function

```python
from codegen.cli.auth.decorators import requires_auth


@requires_auth
def protected_function(session, *args, **kwargs):
    # This function will only be called if the user is authenticated
    # The session parameter is automatically injected
    print(f"Authenticated as {session.config.repository.user_name}")
```

### Managing Tokens Directly

```python
from codegen.cli.auth.token_manager import TokenManager

# Create a token manager
token_manager = TokenManager()

# Save a token
token_manager.save_token("your-token")

# Get the current token
token = token_manager.get_token()

# Clear the token
token_manager.clear_token()
```

## Error Handling

The Authentication module defines several error types:

- `AuthError`: Base class for authentication errors
- `InvalidTokenError`: Raised when a token is invalid
- `NoTokenError`: Raised when no token is provided

These errors are handled gracefully by the `requires_auth` decorator and the `login_routine` function.
