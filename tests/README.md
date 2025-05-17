# Codegen SDK Testing Infrastructure

This directory contains the testing infrastructure for the Codegen SDK.

## Directory Structure

- `tests/unit/`: Unit tests for individual components
- `tests/integration/`: Integration tests for multiple components working together
- `tests/shared/`: Shared test utilities and fixtures
- `tests/templates/`: Templates for creating new tests

## Running Tests

### Basic Usage

```bash
# Run all tests
pytest

# Run with coverage
./scripts/run_tests_with_coverage.sh

# Run specific tests
pytest tests/unit/codegen/agents/test_agent.py
```

### Advanced Usage

```bash
# Run tests in parallel
pytest -n auto

# Run with coverage and generate HTML report
./scripts/run_tests_with_coverage.sh --format html

# Run with custom coverage threshold
./scripts/run_tests_with_coverage.sh --threshold 80

# Run specific test path
./scripts/run_tests_with_coverage.sh --path tests/unit/
```

## Test Coverage

The goal is to maintain high test coverage for critical components of the SDK. The coverage report can be generated using:

```bash
./scripts/run_tests_with_coverage.sh
```

This will generate:
- A text report in the console
- An HTML report in `coverage_html_report/`
- An analysis report in `reports/coverage_analysis.md`

## Writing Tests

### Creating New Tests

1. Use the template in `tests/templates/test_template.py` as a starting point
2. Place the test file in the appropriate directory (unit, integration, etc.)
3. Follow the naming convention: `test_<module_name>.py`

### Best Practices

- Follow the Arrange-Act-Assert pattern
- Use pytest fixtures for common setup
- Use parametrized tests for multiple scenarios
- Mock external dependencies
- Write docstrings for test methods

For more detailed guidelines, see the [Testing Guide](../docs/testing_guide.md).

## Test Dependencies

The testing infrastructure uses the following dependencies:

- pytest: Test runner
- pytest-cov: Coverage reporting
- pytest-xdist: Parallel test execution
- pytest-mock: Mocking utilities
- pytest-timeout: Test timeouts
- pytest-asyncio: Async test support

## Continuous Integration

Tests are automatically run in the CI pipeline for:
- Pull requests
- Merges to main branches
- Scheduled runs

## Troubleshooting

If you encounter issues with the tests:

1. Make sure all dependencies are installed: `pip install -e ".[dev]"`
2. Check that you're running from the project root directory
3. Verify that the test configuration in `pyproject.toml` is correct
4. Look for error messages in the test output

For more help, see the [Testing Guide](../docs/testing_guide.md#troubleshooting).

