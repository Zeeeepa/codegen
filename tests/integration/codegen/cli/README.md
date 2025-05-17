# CLI Module Integration Tests

This directory contains integration tests for the Codegen CLI module.

## Test Structure

The integration tests focus on testing the CLI commands in a more realistic environment, with actual file system operations and command execution.

```
tests/integration/codegen/cli/
├── commands/             # Tests for CLI commands
│   ├── conftest.py       # Common test fixtures for integration tests
│   └── test_reset.py     # Integration test for the reset command
└── README.md             # This file
```

## Running Tests

To run all CLI module integration tests:

```bash
pytest tests/integration/codegen/cli
```

To run specific test files:

```bash
pytest tests/integration/codegen/cli/commands/test_reset.py
```

## Test Fixtures

Common test fixtures for integration tests are defined in `commands/conftest.py`:

- `sample_repository`: Creates a temporary git repository for testing
- `runner`: A Click CLI test runner
- `initialized_repo`: A repository initialized with Codegen

## Adding New Tests

When adding new integration tests:

1. Focus on testing end-to-end workflows
2. Use the fixtures defined in `conftest.py` where appropriate
3. Test realistic user scenarios
4. Clean up temporary files and directories after tests
5. Be mindful of test performance and resource usage

## Integration vs. Unit Tests

- **Unit Tests**: Test individual components in isolation with mocked dependencies
- **Integration Tests**: Test how components work together in a more realistic environment

Integration tests are valuable for ensuring that the CLI commands work correctly in real-world scenarios, but they are typically slower and more resource-intensive than unit tests.

