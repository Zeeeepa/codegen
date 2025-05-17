# CLI Module Tests

This directory contains unit tests for the Codegen CLI module.

## Test Structure

The tests are organized to mirror the structure of the CLI module:

```
tests/unit/codegen/cli/
├── api/                  # Tests for API client and schemas
├── auth/                 # Tests for authentication and session management
├── commands/             # Tests for CLI commands
│   ├── agent/
│   ├── config/
│   ├── create/
│   ├── deploy/
│   ├── expert/
│   ├── init/
│   ├── list/
│   ├── login/
│   ├── logout/
│   ├── lsp/
│   ├── notebook/
│   ├── profile/
│   ├── reset/
│   ├── run/
│   ├── run_on_pr/
│   ├── serve/
│   ├── start/
│   ├── style_debug/
│   └── update/
├── codemod/              # Tests for codemod utilities
├── rich/                 # Tests for rich formatting utilities
├── utils/                # Tests for utility functions
├── conftest.py           # Common test fixtures
├── run_tests.py          # Test runner script
├── test_cli.py           # Tests for the main CLI module
└── test_errors.py        # Tests for error handling
```

## Running Tests

To run all CLI module tests:

```bash
python -m tests.unit.codegen.cli.run_tests
```

To run specific test files:

```bash
pytest tests/unit/codegen/cli/commands/login/test_login.py
```

## Test Coverage

The test suite aims to provide comprehensive coverage of the CLI module, including:

1. Command argument parsing and validation
2. Authentication and session management
3. API client integration
4. Error handling and user feedback
5. File operations and codemod management

## Adding New Tests

When adding new tests:

1. Follow the existing structure and naming conventions
2. Use the fixtures defined in `conftest.py` where appropriate
3. Mock external dependencies to ensure tests are isolated and repeatable
4. Test both success and failure cases
5. Test edge cases and error handling

## Test Fixtures

Common test fixtures are defined in `conftest.py`:

- `runner`: A Click CLI test runner
- `mock_repo_path`: A temporary directory for a mock repository
- `mock_git_repo`: A mock git repository
- `mock_token`: A mock GitHub token
- `mock_api_token`: A mock API token
- `mock_session`: A mock CodegenSession
- `mock_rest_api`: A mock RestAPI client
- `mock_get_current_token`: A mock for the get_current_token function

