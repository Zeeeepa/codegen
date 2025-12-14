# 🧪 Comprehensive Edge-Cased Testing Suite Documentation

## Overview

This testing suite provides comprehensive coverage of the Repository Indexing System, including edge cases, error handling, rate limiting, parallel execution, and integration scenarios.

---

## Test Coverage

### 📊 Test Suite Summary

| Suite | Test Count | Coverage Area |
|-------|------------|---------------|
| **1. Initialization** | 3 tests | Configuration, instantiation, template loading |
| **2. API Success** | 3 tests | Successful API interactions, pagination |
| **3. API Errors** | 6 tests | Network errors, timeouts, HTTP errors (400, 401, 500) |
| **4. Rate Limiting** | 2 tests | 429 handling, sequential delays |
| **5. Retry Logic** | 2 tests | Retry on failure, exhaustion |
| **6. Parallel Execution** | 3 tests | Success, partial failure, exception handling |
| **7. Edge Cases** | 7 tests | Empty lists, Unicode, special chars, malformed data |
| **8. Prompt Template** | 2 tests | Formatting, missing templates |
| **9. Output Handling** | 2 tests | Result structure, JSON serialization |
| **10. Integration** | 2 tests | End-to-end flows (skipped by default) |

**Total**: 32 comprehensive test cases

---

## Test Suites Detailed

### Suite 1: Initialization & Configuration

**Purpose**: Verify proper indexer setup and configuration loading

**Tests**:
1. `test_indexer_creation` - Basic instantiation with correct attributes
2. `test_custom_base_url` - Custom API endpoint configuration
3. `test_prompt_template_loading` - Template file loading and validation

**Edge Cases Covered**:
- ✅ Missing configuration
- ✅ Invalid URLs
- ✅ Template file not found

---

### Suite 2: API Interaction - Success Cases

**Purpose**: Validate successful API communication

**Tests**:
1. `test_fetch_repos_single_page` - Single-page repository fetch
2. `test_fetch_repos_pagination` - Multi-page pagination handling
3. `test_create_agent_run_success` - Successful agent run creation

**Edge Cases Covered**:
- ✅ Empty repository lists
- ✅ Large repository counts (100+ per page)
- ✅ Valid API response structure

---

### Suite 3: API Interaction - Error Cases

**Purpose**: Ensure robust error handling for all failure modes

**Tests**:
1. `test_fetch_repos_network_error` - Network connectivity issues
2. `test_fetch_repos_timeout` - Request timeout handling
3. `test_fetch_repos_http_error` - HTTP errors (404, etc.)
4. `test_create_agent_run_400_error` - Bad request handling
5. `test_create_agent_run_401_unauthorized` - Authentication failures
6. `test_create_agent_run_500_server_error` - Server errors

**Edge Cases Covered**:
- ✅ Connection refused
- ✅ DNS resolution failures
- ✅ Timeout after partial response
- ✅ Invalid request format
- ✅ Expired authentication tokens
- ✅ Server unavailability

---

### Suite 4: Rate Limiting

**Purpose**: Verify compliance with API rate limits

**Tests**:
1. `test_rate_limit_429_handling` - 429 Too Many Requests response
2. `test_rate_limit_delay_sequential` - Proper delays between requests

**Edge Cases Covered**:
- ✅ Exceeding rate limits
- ✅ Retry-After header handling
- ✅ Proper backoff timing

**Official Rate Limits** (from Codegen API):
- Agent creation: **10 requests per minute**
- Standard endpoints: **60 requests per 30 seconds**

---

### Suite 5: Retry Logic

**Purpose**: Test retry mechanisms for transient failures

**Tests**:
1. `test_retry_on_network_error` - Retry on network failures
2. `test_retry_exhaustion` - Behavior when all retries fail

**Edge Cases Covered**:
- ✅ Transient network errors
- ✅ Intermittent server issues
- ✅ Retry count configuration
- ✅ Exponential backoff

**Retry Configuration**:
- Default retry count: **3 attempts**
- Delay between retries: **12 seconds** (2x rate limit)

---

### Suite 6: Parallel Execution

**Purpose**: Validate concurrent execution correctness

**Tests**:
1. `test_parallel_execution_success` - All tasks succeed
2. `test_parallel_execution_partial_failure` - Some tasks fail
3. `test_parallel_execution_exception_handling` - Exception handling

**Edge Cases Covered**:
- ✅ Thread safety
- ✅ Resource contention
- ✅ Partial failure recovery
- ✅ Exception propagation
- ✅ Worker pool exhaustion

**Parallel Configuration**:
- Default workers: **5 concurrent threads**
- Max workers: **10** (recommended)

---

### Suite 7: Edge Cases

**Purpose**: Test boundary conditions and unusual inputs

**Tests**:
1. `test_empty_repo_list` - Empty input
2. `test_single_repo` - Single repository
3. `test_large_repo_count` - 1000+ repositories
4. `test_special_characters_in_repo_name` - Dashes, underscores, dots
5. `test_unicode_in_repo_name` - Japanese, Chinese, Korean characters
6. `test_missing_repo_fields` - Malformed repository data
7. `test_extremely_long_repo_name` - 300+ character names

**Edge Cases Covered**:
- ✅ Empty collections
- ✅ Single item processing
- ✅ Large-scale operations (1000+ items)
- ✅ Special characters: `-`, `_`, `.`, uppercase
- ✅ Unicode characters: 日本語, 中文, 한국어
- ✅ Missing required fields
- ✅ Extremely long names (>255 chars)

---

### Suite 8: Prompt Template

**Purpose**: Verify prompt formatting and template handling

**Tests**:
1. `test_prompt_formatting` - Variable substitution
2. `test_missing_prompt_template` - Fallback behavior

**Edge Cases Covered**:
- ✅ Template variable substitution
- ✅ Missing template files
- ✅ Invalid template syntax
- ✅ Special characters in variables

---

### Suite 9: Output Handling

**Purpose**: Validate result structure and serialization

**Tests**:
1. `test_results_structure` - Correct output format
2. `test_results_json_serializable` - JSON compatibility

**Edge Cases Covered**:
- ✅ Result structure validation
- ✅ JSON serialization
- ✅ Timestamp formatting
- ✅ Nested data structures

---

### Suite 10: Integration Tests

**Purpose**: End-to-end system validation

**Tests**:
1. `test_end_to_end_sequential` - Complete sequential flow
2. `test_end_to_end_parallel` - Complete parallel flow

**Note**: These tests are **skipped by default** to avoid hitting actual API endpoints.

**To enable integration tests**:
```bash
pytest /tmp/test_suite.py -v --run-integration
```

---

## Running the Tests

### Prerequisites

```bash
# Install dependencies
pip install pytest pytest-cov requests

# Or with uv
uv pip install pytest pytest-cov requests
```

### Execution Commands

**Run all tests**:
```bash
python3 /tmp/test_suite.py
```

**Run with pytest directly**:
```bash
pytest /tmp/test_suite.py -v
```

**Run specific test suite**:
```bash
pytest /tmp/test_suite.py -v -k "TestEdgeCases"
```

**Run with coverage report**:
```bash
pytest /tmp/test_suite.py --cov=full_repo_index --cov-report=html
```

**Run with detailed output**:
```bash
pytest /tmp/test_suite.py -vv --tb=long
```

---

## Test Output

### Success Example

```
🧪 COMPREHENSIVE EDGE-CASED TESTING SUITE
================================================================================

test_suite.py::TestInitialization::test_indexer_creation PASSED            [  3%]
test_suite.py::TestAPISuccessCases::test_fetch_repos_single_page PASSED    [  6%]
test_suite.py::TestAPIErrorCases::test_fetch_repos_network_error PASSED    [  9%]
...

================================================================================
📊 TEST SUITE COMPLETE
================================================================================

Exit Code: 0
Results: /tmp/test-results.xml

32 passed in 2.45s
```

### Failure Example

```
test_suite.py::TestEdgeCases::test_unicode_in_repo_name FAILED           [ 81%]

FAILED test_suite.py::TestEdgeCases::test_unicode_in_repo_name
  AssertionError: assert 2 == 3
  
  Expected 3 successful indexing operations, got 2
  
  Full traceback available in /tmp/test-results.xml
```

---

## Coverage Goals

### Current Coverage Targets

| Component | Target Coverage | Notes |
|-----------|----------------|-------|
| API Interaction | 100% | Critical path - full coverage required |
| Error Handling | 100% | All error cases must be tested |
| Rate Limiting | 100% | Compliance is mandatory |
| Retry Logic | 100% | Transient failure handling |
| Parallel Execution | 95% | Complex concurrency scenarios |
| Edge Cases | 90% | Unusual but valid inputs |
| Output Handling | 100% | Result correctness is critical |

---

## Known Limitations

1. **Integration Tests Skipped**: By default, integration tests are skipped to avoid API usage
2. **Mock-Heavy**: Most tests use mocks rather than real API calls
3. **Rate Limit Timing**: Rate limit delays are mocked (not real-time)
4. **Concurrent Execution**: Thread safety testing is limited to basic scenarios

---

## Extending the Test Suite

### Adding New Tests

1. **Create a new test class**:
```python
class TestMyFeature:
    """Test description"""
    
    def test_my_feature(self, mock_indexer):
        """Test specific behavior"""
        # Arrange
        mock_indexer.some_method = Mock(return_value=expected)
        
        # Act
        result = mock_indexer.my_feature()
        
        # Assert
        assert result == expected
```

2. **Add fixtures as needed**:
```python
@pytest.fixture
def my_fixture():
    """Fixture description"""
    return test_data
```

3. **Update documentation**:
- Add test count to summary table
- Document edge cases covered
- Update coverage goals

---

## Continuous Integration

### GitHub Actions Example

```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Install dependencies
        run: pip install pytest pytest-cov requests
      - name: Run tests
        run: pytest /tmp/test_suite.py --junit-xml=test-results.xml
      - name: Upload results
        uses: actions/upload-artifact@v2
        with:
          name: test-results
          path: test-results.xml
```

---

## Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'full_repo_index'`
**Solution**: Ensure `/tmp/full_repo_index.py` exists and is importable

**Issue**: `fixture 'mock_indexer' not found`
**Solution**: Run tests via pytest, not directly: `pytest /tmp/test_suite.py`

**Issue**: All tests skipped
**Solution**: Check that `CodegenRepoIndexer` is available and importable

**Issue**: Rate limit tests fail
**Solution**: Verify `time.sleep` is properly mocked in test setup

---

## Test Maintenance

### Regular Updates

- **Weekly**: Review and update edge case coverage
- **Monthly**: Add new test scenarios based on production issues
- **Per Release**: Update integration tests with new API features

### Test Quality Checklist

- [ ] All tests have descriptive names
- [ ] Edge cases are documented
- [ ] Mocks are properly configured
- [ ] Assertions are meaningful
- [ ] Test documentation is updated

---

## References

- **Pytest Documentation**: https://docs.pytest.org/
- **Codegen API Docs**: https://docs.codegen.com/api-reference/overview
- **Official Rate Limits**: 10 agent creations per minute

---

**Last Updated**: 2025-01-15
**Version**: 1.0.0
**Maintainer**: Repository Indexing System Team
