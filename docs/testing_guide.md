# Codegen SDK Testing Guide

This guide provides best practices and guidelines for writing tests for the Codegen SDK.

## Table of Contents

1. [Testing Philosophy](#testing-philosophy)
2. [Test Structure](#test-structure)
3. [Test Types](#test-types)
4. [Writing Effective Tests](#writing-effective-tests)
5. [Running Tests](#running-tests)
6. [Test Coverage](#test-coverage)
7. [Troubleshooting](#troubleshooting)

## Testing Philosophy

The Codegen SDK testing philosophy is based on the following principles:

- **Comprehensive Coverage**: Aim for high test coverage, especially for critical components.
- **Fast Execution**: Tests should run quickly to encourage frequent testing.
- **Reliability**: Tests should be deterministic and not flaky.
- **Readability**: Tests should be easy to understand and maintain.
- **Isolation**: Tests should be independent of each other and not rely on global state.

## Test Structure

The Codegen SDK test suite is organized as follows:

- `tests/unit/`: Unit tests for individual components
- `tests/integration/`: Integration tests for multiple components working together
- `tests/shared/`: Shared test utilities and fixtures
- `tests/templates/`: Templates for creating new tests

### Naming Conventions

- Test files should be named `test_<module_name>.py`
- Test classes should be named `Test<ModuleName>`
- Test methods should be named `test_<function_name>_<scenario>`

## Test Types

### Unit Tests

Unit tests focus on testing individual components in isolation. They should:

- Test a single function or method
- Mock external dependencies
- Be fast and deterministic
- Cover edge cases and error conditions

Example:

```python
def test_parse_file_valid_input():
    # Arrange
    parser = Parser()
    valid_input = "def example(): pass"
    
    # Act
    result = parser.parse(valid_input)
    
    # Assert
    assert result is not None
    assert len(result.functions) == 1
    assert result.functions[0].name == "example"
```

### Integration Tests

Integration tests verify that multiple components work together correctly. They should:

- Test interactions between components
- Use minimal mocking
- Cover common usage patterns
- Verify end-to-end functionality

Example:

```python
def test_codebase_parse_and_transform():
    # Arrange
    codebase = Codebase.from_directory("test_data/sample_project")
    
    # Act
    codebase.parse()
    functions = codebase.find_functions(name="example")
    functions[0].rename("new_example")
    codebase.save()
    
    # Assert
    assert os.path.exists("test_data/sample_project/new_file.py")
    with open("test_data/sample_project/new_file.py") as f:
        content = f.read()
        assert "def new_example" in content
```

## Writing Effective Tests

### Test Structure

Follow the Arrange-Act-Assert (AAA) pattern:

1. **Arrange**: Set up the test conditions
2. **Act**: Execute the code being tested
3. **Assert**: Verify the results

### Using Fixtures

Use pytest fixtures for common setup and teardown:

```python
@pytest.fixture
def sample_codebase():
    """Create a sample codebase for testing."""
    codebase = Codebase.from_directory("test_data/sample_project")
    codebase.parse()
    return codebase

def test_find_functions(sample_codebase):
    functions = sample_codebase.find_functions(name="example")
    assert len(functions) == 1
```

### Parametrized Tests

Use parametrized tests to test multiple scenarios:

```python
@pytest.mark.parametrize(
    "input_code,expected_function_count",
    [
        ("def example(): pass", 1),
        ("class Example: def method(): pass", 1),
        ("def f1(): pass\ndef f2(): pass", 2),
    ],
)
def test_parse_function_count(input_code, expected_function_count):
    parser = Parser()
    result = parser.parse(input_code)
    assert len(result.functions) == expected_function_count
```

### Mocking

Use mocking to isolate the code being tested:

```python
@patch("codegen.sdk.parser.Parser.parse")
def test_codebase_parse_calls_parser(mock_parse):
    codebase = Codebase.from_directory("test_data/sample_project")
    codebase.parse()
    assert mock_parse.called
```

## Running Tests

### Running All Tests

```bash
# Run all tests
pytest

# Run with coverage
./scripts/run_tests_with_coverage.sh
```

### Running Specific Tests

```bash
# Run tests in a specific file
pytest tests/unit/test_parser.py

# Run tests matching a pattern
pytest -k "parser"

# Run tests in a specific directory
pytest tests/unit/
```

### Running Tests in Parallel

```bash
# Run tests in parallel
pytest -n auto

# Or use the script
./scripts/run_tests_with_coverage.sh --parallel
```

## Test Coverage

### Coverage Goals

- Critical components: 90%+ coverage
- Core modules: 80%+ coverage
- Utility modules: 70%+ coverage

### Checking Coverage

```bash
# Run tests with coverage
./scripts/run_tests_with_coverage.sh

# Generate HTML coverage report
./scripts/run_tests_with_coverage.sh --format html

# Analyze coverage with custom threshold
./scripts/run_tests_with_coverage.sh --threshold 80
```

### Coverage Report

The coverage report will be generated in:
- Text report: console output
- HTML report: `coverage_html_report/`
- Analysis report: `reports/coverage_analysis.md`

## Troubleshooting

### Common Issues

#### Tests Failing with Import Errors

Make sure you're running tests from the project root directory and that the package is installed in development mode:

```bash
pip install -e .
```

#### Slow Tests

Identify slow tests using the pytest-benchmark plugin:

```bash
pytest --benchmark-only
```

Consider using mocks or faster alternatives for slow operations.

#### Flaky Tests

If tests are flaky (sometimes passing, sometimes failing), they may:
- Depend on global state
- Have race conditions
- Depend on external resources

Fix by:
- Isolating tests
- Using proper fixtures
- Mocking external dependencies
- Adding appropriate timeouts

