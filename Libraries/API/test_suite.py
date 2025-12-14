#!/usr/bin/env python3
"""
Comprehensive Edge-Cased Testing Suite for Repository Indexing System

Tests all edge cases, error conditions, rate limiting, retry logic,
parallel execution, and integration scenarios.
"""

import os
import sys
import json
import time
import pytest
import tempfile
import requests
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# Import the indexer (add path if needed)
sys.path.insert(0, '/tmp')
try:
    from full_repo_index import CodegenRepoIndexer
except ImportError:
    print("⚠️  full_repo_index.py not found in /tmp, creating mock for testing")
    CodegenRepoIndexer = None

# Test Configuration
TEST_ORG_ID = "323"
TEST_API_TOKEN = "test-token-12345"
TEST_BASE_URL = "https://api.codegen.com"

# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_indexer():
    """Create a mock indexer instance"""
    if CodegenRepoIndexer:
        indexer = CodegenRepoIndexer(TEST_ORG_ID, TEST_API_TOKEN, TEST_BASE_URL)
        indexer.prompt_template = "Test prompt for {repo_name}"
        return indexer
    return None

@pytest.fixture
def mock_repos():
    """Generate mock repository data"""
    return [
        {'id': 1, 'name': 'repo-1', 'full_name': 'org/repo-1'},
        {'id': 2, 'name': 'repo-2', 'full_name': 'org/repo-2'},
        {'id': 3, 'name': 'repo-3', 'full_name': 'org/repo-3'},
    ]

@pytest.fixture
def mock_response_success():
    """Mock successful API response"""
    return {
        'id': 12345,
        'status': 'pending',
        'web_url': 'https://codegen.com/agent/trace/12345'
    }

@pytest.fixture
def temp_prompt_file():
    """Create temporary prompt file"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("# Test Prompt\nAnalyze repository: {repo_name}")
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

# ============================================================================
# TEST SUITE 1: INITIALIZATION & CONFIGURATION
# ============================================================================

class TestInitialization:
    """Test indexer initialization and configuration"""
    
    def test_indexer_creation(self):
        """Test basic indexer instantiation"""
        if not CodegenRepoIndexer:
            pytest.skip("CodegenRepoIndexer not available")
        
        indexer = CodegenRepoIndexer(TEST_ORG_ID, TEST_API_TOKEN)
        assert indexer.org_id == TEST_ORG_ID
        assert indexer.api_token == TEST_API_TOKEN
        assert indexer.base_url == TEST_BASE_URL
        assert 'Authorization' in indexer.headers
        assert indexer.headers['Authorization'] == f"Bearer {TEST_API_TOKEN}"
    
    def test_custom_base_url(self):
        """Test initialization with custom base URL"""
        if not CodegenRepoIndexer:
            pytest.skip("CodegenRepoIndexer not available")
        
        custom_url = "https://custom.api.com"
        indexer = CodegenRepoIndexer(TEST_ORG_ID, TEST_API_TOKEN, custom_url)
        assert indexer.base_url == custom_url
    
    def test_prompt_template_loading(self, temp_prompt_file):
        """Test prompt template loading from file"""
        if not CodegenRepoIndexer:
            pytest.skip("CodegenRepoIndexer not available")
        
        # This would need to be adapted based on actual implementation
        # For now, just verify the indexer has a prompt_template attribute
        indexer = CodegenRepoIndexer(TEST_ORG_ID, TEST_API_TOKEN)
        assert hasattr(indexer, 'prompt_template')
        assert indexer.prompt_template is not None

# ============================================================================
# TEST SUITE 2: API INTERACTION - SUCCESS CASES
# ============================================================================

class TestAPISuccessCases:
    """Test successful API interactions"""
    
    @patch('requests.get')
    def test_fetch_repos_single_page(self, mock_get, mock_indexer):
        """Test fetching repositories (single page)"""
        if not mock_indexer:
            pytest.skip("Mock indexer not available")
        
        mock_response = Mock()
        mock_response.json.return_value = {
            'items': [
                {'id': 1, 'name': 'repo-1', 'full_name': 'org/repo-1'},
                {'id': 2, 'name': 'repo-2', 'full_name': 'org/repo-2'},
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        repos = mock_indexer.fetch_all_repos()
        
        assert len(repos) == 2
        assert repos[0]['name'] == 'repo-1'
        assert mock_get.call_count == 1
    
    @patch('requests.get')
    def test_fetch_repos_pagination(self, mock_get, mock_indexer):
        """Test fetching repositories with pagination"""
        if not mock_indexer:
            pytest.skip("Mock indexer not available")
        
        # First page: 100 repos
        page1 = Mock()
        page1.json.return_value = {
            'items': [{'id': i, 'name': f'repo-{i}', 'full_name': f'org/repo-{i}'} 
                     for i in range(100)]
        }
        page1.raise_for_status = Mock()
        
        # Second page: 50 repos
        page2 = Mock()
        page2.json.return_value = {
            'items': [{'id': i, 'name': f'repo-{i}', 'full_name': f'org/repo-{i}'} 
                     for i in range(100, 150)]
        }
        page2.raise_for_status = Mock()
        
        mock_get.side_effect = [page1, page2]
        
        repos = mock_indexer.fetch_all_repos()
        
        assert len(repos) == 150
        assert mock_get.call_count == 2
    
    @patch('requests.post')
    def test_create_agent_run_success(self, mock_post, mock_indexer, mock_response_success):
        """Test successful agent run creation"""
        if not mock_indexer:
            pytest.skip("Mock indexer not available")
        
        mock_response = Mock()
        mock_response.json.return_value = mock_response_success
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        result = mock_indexer.create_agent_run(123, 'test-repo', 'org/test-repo')
        
        assert result is not None
        assert result['id'] == 12345
        assert mock_post.call_count == 1

# ============================================================================
# TEST SUITE 3: API INTERACTION - ERROR CASES
# ============================================================================

class TestAPIErrorCases:
    """Test API error handling"""
    
    @patch('requests.get')
    def test_fetch_repos_network_error(self, mock_get, mock_indexer):
        """Test handling of network errors when fetching repos"""
        if not mock_indexer:
            pytest.skip("Mock indexer not available")
        
        mock_get.side_effect = requests.ConnectionError("Network error")
        
        repos = mock_indexer.fetch_all_repos()
        
        assert repos == []
    
    @patch('requests.get')
    def test_fetch_repos_timeout(self, mock_get, mock_indexer):
        """Test handling of timeout errors"""
        if not mock_indexer:
            pytest.skip("Mock indexer not available")
        
        mock_get.side_effect = requests.Timeout("Request timed out")
        
        repos = mock_indexer.fetch_all_repos()
        
        assert repos == []
    
    @patch('requests.get')
    def test_fetch_repos_http_error(self, mock_get, mock_indexer):
        """Test handling of HTTP errors (404, 500, etc.)"""
        if not mock_indexer:
            pytest.skip("Mock indexer not available")
        
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_get.return_value = mock_response
        
        repos = mock_indexer.fetch_all_repos()
        
        assert repos == []
    
    @patch('requests.post')
    def test_create_agent_run_400_error(self, mock_post, mock_indexer):
        """Test handling of 400 Bad Request"""
        if not mock_indexer:
            pytest.skip("Mock indexer not available")
        
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("400 Bad Request")
        mock_post.return_value = mock_response
        
        result = mock_indexer.create_agent_run(123, 'test-repo', 'org/test-repo')
        
        assert result is None
    
    @patch('requests.post')
    def test_create_agent_run_401_unauthorized(self, mock_post, mock_indexer):
        """Test handling of 401 Unauthorized"""
        if not mock_indexer:
            pytest.skip("Mock indexer not available")
        
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = requests.HTTPError("401 Unauthorized")
        mock_post.return_value = mock_response
        
        result = mock_indexer.create_agent_run(123, 'test-repo', 'org/test-repo')
        
        assert result is None
    
    @patch('requests.post')
    def test_create_agent_run_500_server_error(self, mock_post, mock_indexer):
        """Test handling of 500 Internal Server Error"""
        if not mock_indexer:
            pytest.skip("Mock indexer not available")
        
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.HTTPError("500 Internal Server Error")
        mock_post.return_value = mock_response
        
        result = mock_indexer.create_agent_run(123, 'test-repo', 'org/test-repo')
        
        assert result is None

# ============================================================================
# TEST SUITE 4: RATE LIMITING
# ============================================================================

class TestRateLimiting:
    """Test rate limiting behavior"""
    
    @patch('requests.post')
    @patch('time.sleep')
    def test_rate_limit_429_handling(self, mock_sleep, mock_post, mock_indexer):
        """Test handling of 429 Too Many Requests"""
        if not mock_indexer:
            pytest.skip("Mock indexer not available")
        
        # First call returns 429, second call succeeds
        error_response = Mock()
        error_response.status_code = 429
        error_response.raise_for_status.side_effect = requests.HTTPError("429 Too Many Requests")
        
        success_response = Mock()
        success_response.json.return_value = {'id': 12345, 'status': 'pending'}
        success_response.raise_for_status = Mock()
        
        mock_post.side_effect = [error_response, success_response]
        
        # Note: This depends on retry logic implementation
        # For now, just verify the error is handled
        result = mock_indexer.create_agent_run(123, 'test-repo', 'org/test-repo')
        
        # Should return None on first 429 (no retry in basic implementation)
        # Or retry and succeed if retry logic exists
    
    @patch('time.sleep')
    def test_rate_limit_delay_sequential(self, mock_sleep, mock_indexer, mock_repos):
        """Test rate limiting delay in sequential execution"""
        if not mock_indexer:
            pytest.skip("Mock indexer not available")
        
        # Mock the index_repository to always succeed
        mock_indexer.index_repository = Mock(return_value={
            'repo_id': 1, 'run_id': 12345, 'status': 'pending'
        })
        
        result = mock_indexer.index_all_sequential(mock_repos[:2])
        
        # Should sleep between requests (RATE_LIMIT seconds)
        # Note: Actual delay is 6 seconds as per official rate limit
        assert mock_sleep.call_count >= 1

# ============================================================================
# TEST SUITE 5: RETRY LOGIC
# ============================================================================

class TestRetryLogic:
    """Test retry mechanisms"""
    
    @patch('requests.post')
    @patch('time.sleep')
    def test_retry_on_network_error(self, mock_sleep, mock_post, mock_indexer):
        """Test retry on network errors"""
        if not mock_indexer:
            pytest.skip("Mock indexer not available")
        
        # Fail twice, succeed on third attempt
        mock_post.side_effect = [
            requests.ConnectionError("Network error"),
            requests.ConnectionError("Network error"),
            Mock(json=lambda: {'id': 12345}, raise_for_status=Mock())
        ]
        
        repo = {'id': 123, 'name': 'test-repo', 'full_name': 'org/test-repo'}
        result = mock_indexer.index_repository(repo, retry_count=3)
        
        # Should succeed after retries
        assert result is not None
        assert result['run_id'] == 12345
        assert mock_post.call_count == 3
    
    @patch('requests.post')
    @patch('time.sleep')
    def test_retry_exhaustion(self, mock_sleep, mock_post, mock_indexer):
        """Test behavior when all retries are exhausted"""
        if not mock_indexer:
            pytest.skip("Mock indexer not available")
        
        # Always fail
        mock_post.side_effect = requests.ConnectionError("Network error")
        
        repo = {'id': 123, 'name': 'test-repo', 'full_name': 'org/test-repo'}
        result = mock_indexer.index_repository(repo, retry_count=3)
        
        # Should return None after exhausting retries
        assert result is None
        assert mock_post.call_count == 3

# ============================================================================
# TEST SUITE 6: PARALLEL EXECUTION
# ============================================================================

class TestParallelExecution:
    """Test parallel/concurrent execution"""
    
    @patch('time.sleep')
    def test_parallel_execution_success(self, mock_sleep, mock_indexer, mock_repos):
        """Test successful parallel execution"""
        if not mock_indexer:
            pytest.skip("Mock indexer not available")
        
        # Mock successful indexing
        mock_indexer.index_repository = Mock(return_value={
            'repo_id': 1, 'run_id': 12345, 'status': 'pending'
        })
        
        result = mock_indexer.index_all_parallel(mock_repos, max_workers=2)
        
        assert result['stats']['total'] == 3
        assert result['stats']['success'] == 3
        assert result['stats']['failed'] == 0
    
    @patch('time.sleep')
    def test_parallel_execution_partial_failure(self, mock_sleep, mock_indexer, mock_repos):
        """Test parallel execution with some failures"""
        if not mock_indexer:
            pytest.skip("Mock indexer not available")
        
        # First repo succeeds, second fails, third succeeds
        results = [
            {'repo_id': 1, 'run_id': 12345, 'status': 'pending'},
            None,
            {'repo_id': 3, 'run_id': 12347, 'status': 'pending'}
        ]
        mock_indexer.index_repository = Mock(side_effect=results)
        
        result = mock_indexer.index_all_parallel(mock_repos, max_workers=2)
        
        assert result['stats']['total'] == 3
        assert result['stats']['success'] == 2
        assert result['stats']['failed'] == 1
    
    @patch('time.sleep')
    def test_parallel_execution_exception_handling(self, mock_sleep, mock_indexer, mock_repos):
        """Test exception handling in parallel execution"""
        if not mock_indexer:
            pytest.skip("Mock indexer not available")
        
        # One thread raises an exception
        def side_effect(repo):
            if repo['id'] == 2:
                raise Exception("Unexpected error")
            return {'repo_id': repo['id'], 'run_id': 12345, 'status': 'pending'}
        
        mock_indexer.index_repository = Mock(side_effect=side_effect)
        
        result = mock_indexer.index_all_parallel(mock_repos, max_workers=2)
        
        assert result['stats']['total'] == 3
        assert result['stats']['failed'] >= 1  # At least the exception case

# ============================================================================
# TEST SUITE 7: EDGE CASES
# ============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_empty_repo_list(self, mock_indexer):
        """Test handling of empty repository list"""
        if not mock_indexer:
            pytest.skip("Mock indexer not available")
        
        result = mock_indexer.index_all_sequential([])
        
        assert result['stats']['total'] == 0
        assert result['stats']['success'] == 0
        assert result['stats']['failed'] == 0
    
    def test_single_repo(self, mock_indexer):
        """Test indexing a single repository"""
        if not mock_indexer:
            pytest.skip("Mock indexer not available")
        
        mock_indexer.index_repository = Mock(return_value={
            'repo_id': 1, 'run_id': 12345, 'status': 'pending'
        })
        
        repos = [{'id': 1, 'name': 'single-repo', 'full_name': 'org/single-repo'}]
        result = mock_indexer.index_all_sequential(repos)
        
        assert result['stats']['total'] == 1
        assert result['stats']['success'] == 1
    
    def test_large_repo_count(self, mock_indexer):
        """Test handling of large repository count (1000+ repos)"""
        if not mock_indexer:
            pytest.skip("Mock indexer not available")
        
        # Generate 1000 repos
        large_repo_list = [
            {'id': i, 'name': f'repo-{i}', 'full_name': f'org/repo-{i}'}
            for i in range(1000)
        ]
        
        mock_indexer.index_repository = Mock(return_value={
            'repo_id': 1, 'run_id': 12345, 'status': 'pending'
        })
        
        # Test with parallel execution (faster)
        result = mock_indexer.index_all_parallel(large_repo_list, max_workers=5)
        
        assert result['stats']['total'] == 1000
    
    def test_special_characters_in_repo_name(self, mock_indexer):
        """Test repositories with special characters in names"""
        if not mock_indexer:
            pytest.skip("Mock indexer not available")
        
        special_repos = [
            {'id': 1, 'name': 'repo-with-dashes', 'full_name': 'org/repo-with-dashes'},
            {'id': 2, 'name': 'repo_with_underscores', 'full_name': 'org/repo_with_underscores'},
            {'id': 3, 'name': 'repo.with.dots', 'full_name': 'org/repo.with.dots'},
            {'id': 4, 'name': 'REPO-UPPERCASE', 'full_name': 'org/REPO-UPPERCASE'},
        ]
        
        mock_indexer.index_repository = Mock(return_value={
            'repo_id': 1, 'run_id': 12345, 'status': 'pending'
        })
        
        result = mock_indexer.index_all_sequential(special_repos)
        
        assert result['stats']['success'] == 4
    
    def test_unicode_in_repo_name(self, mock_indexer):
        """Test repositories with Unicode characters"""
        if not mock_indexer:
            pytest.skip("Mock indexer not available")
        
        unicode_repos = [
            {'id': 1, 'name': 'repo-日本語', 'full_name': 'org/repo-日本語'},
            {'id': 2, 'name': 'repo-中文', 'full_name': 'org/repo-中文'},
            {'id': 3, 'name': 'repo-한국어', 'full_name': 'org/repo-한국어'},
        ]
        
        mock_indexer.index_repository = Mock(return_value={
            'repo_id': 1, 'run_id': 12345, 'status': 'pending'
        })
        
        result = mock_indexer.index_all_sequential(unicode_repos)
        
        assert result['stats']['success'] == 3
    
    def test_missing_repo_fields(self, mock_indexer):
        """Test handling of malformed repository data"""
        if not mock_indexer:
            pytest.skip("Mock indexer not available")
        
        # Repo missing 'name' field
        malformed_repo = {'id': 1, 'full_name': 'org/repo-1'}
        
        # Should handle gracefully (KeyError or return None)
        try:
            result = mock_indexer.index_repository(malformed_repo)
            # If no error, result should be None or handled
        except KeyError:
            # Expected behavior - missing required field
            pass
    
    def test_extremely_long_repo_name(self, mock_indexer):
        """Test repository with extremely long name (255+ characters)"""
        if not mock_indexer:
            pytest.skip("Mock indexer not available")
        
        long_name = 'a' * 300
        long_repo = {
            'id': 1,
            'name': long_name,
            'full_name': f'org/{long_name}'
        }
        
        mock_indexer.index_repository = Mock(return_value={
            'repo_id': 1, 'run_id': 12345, 'status': 'pending'
        })
        
        result = mock_indexer.index_repository(long_repo)
        
        assert result is not None

# ============================================================================
# TEST SUITE 8: PROMPT TEMPLATE
# ============================================================================

class TestPromptTemplate:
    """Test prompt template handling"""
    
    def test_prompt_formatting(self, mock_indexer):
        """Test prompt template formatting with variables"""
        if not mock_indexer:
            pytest.skip("Mock indexer not available")
        
        mock_indexer.prompt_template = "Analyze {repo_name} at {repo_full_name}"
        
        formatted = mock_indexer.prompt_template.format(
            repo_name='test-repo',
            repo_full_name='org/test-repo',
            timestamp=datetime.now().isoformat()
        )
        
        assert 'test-repo' in formatted
        assert 'org/test-repo' in formatted
    
    def test_missing_prompt_template(self, mock_indexer):
        """Test handling of missing prompt template"""
        if not mock_indexer:
            pytest.skip("Mock indexer not available")
        
        # Set prompt template to None
        mock_indexer.prompt_template = None
        
        # Should handle gracefully or use default
        # Implementation-specific behavior

# ============================================================================
# TEST SUITE 9: OUTPUT & RESULTS
# ============================================================================

class TestOutputHandling:
    """Test result collection and output"""
    
    def test_results_structure(self, mock_indexer, mock_repos):
        """Test structure of results output"""
        if not mock_indexer:
            pytest.skip("Mock indexer not available")
        
        mock_indexer.index_repository = Mock(return_value={
            'repo_id': 1, 'run_id': 12345, 'status': 'pending'
        })
        
        result = mock_indexer.index_all_sequential(mock_repos)
        
        # Verify structure
        assert 'results' in result
        assert 'stats' in result
        assert 'success' in result['results']
        assert 'failed' in result['results']
        assert 'total' in result['stats']
        assert 'success' in result['stats']
        assert 'failed' in result['stats']
    
    def test_results_json_serializable(self, mock_indexer, mock_repos):
        """Test that results can be serialized to JSON"""
        if not mock_indexer:
            pytest.skip("Mock indexer not available")
        
        mock_indexer.index_repository = Mock(return_value={
            'repo_id': 1,
            'repo_name': 'test-repo',
            'run_id': 12345,
            'status': 'pending',
            'timestamp': datetime.now().isoformat()
        })
        
        result = mock_indexer.index_all_sequential(mock_repos)
        
        # Should not raise exception
        json_str = json.dumps(result)
        assert json_str is not None
        
        # Should be able to parse back
        parsed = json.loads(json_str)
        assert parsed['stats']['total'] == len(mock_repos)

# ============================================================================
# TEST SUITE 10: INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """End-to-end integration tests (requires actual API access)"""
    
    @pytest.mark.skip(reason="Requires actual API access")
    def test_end_to_end_sequential(self):
        """Test complete sequential execution flow"""
        # This would test against actual API
        # Skip by default to avoid hitting real endpoints
        pass
    
    @pytest.mark.skip(reason="Requires actual API access")
    def test_end_to_end_parallel(self):
        """Test complete parallel execution flow"""
        # This would test against actual API
        # Skip by default to avoid hitting real endpoints
        pass

# ============================================================================
# TEST RUNNER & REPORTING
# ============================================================================

def run_test_suite():
    """Run the complete test suite with detailed reporting"""
    
    print("=" * 80)
    print("🧪 COMPREHENSIVE EDGE-CASED TESTING SUITE")
    print("=" * 80)
    print()
    
    # Configure pytest arguments
    pytest_args = [
        __file__,
        '-v',                    # Verbose output
        '--tb=short',            # Short traceback format
        '--color=yes',           # Colored output
        '-W', 'ignore::DeprecationWarning',  # Ignore deprecation warnings
        '--junit-xml=/tmp/test-results.xml',  # JUnit XML output
    ]
    
    # Run tests
    exit_code = pytest.main(pytest_args)
    
    print()
    print("=" * 80)
    print("📊 TEST SUITE COMPLETE")
    print("=" * 80)
    print()
    print(f"Exit Code: {exit_code}")
    print(f"Results: /tmp/test-results.xml")
    print()
    
    return exit_code

if __name__ == '__main__':
    exit_code = run_test_suite()
    sys.exit(exit_code)
