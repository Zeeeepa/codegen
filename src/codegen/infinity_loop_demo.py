"""
Demo mode responses for Infinity Loop agents.
Used when DEMO_MODE=true to demonstrate system functionality.
"""

RESEARCH_RESPONSE = """## Research Report

### Current State Analysis
The system shows potential for optimization in code quality and security practices.

### Improvement Opportunities
1. **Security Enhancement**: Remove hardcoded credentials from version control
2. **Code Quality**: Eliminate dead code and unused imports  
3. **Type Safety**: Improve error handling for dynamic result types

### Proposed Changes PRD
Implement environment-based configuration management, clean up codebase by removing unused code, and add robust type checking for API responses.

### Expected Benefits
- 40% reduction in security vulnerabilities
- 15% improvement in code maintainability
- Better error resilience

### References
- OWASP Security Best Practices
- Python typing module documentation
- Clean Code principles"""

ANALYSIS_RESPONSE = """## Analysis Report

### Feasibility Assessment
The proposed changes are technically feasible and align with industry best practices.

### Impact Estimation
- Effort: 3-4 hours
- Complexity: Medium
- Risk Level: Low

### Implementation Plan
1. Replace hardcoded credentials with environment variables
2. Remove unused imports (json, uuid, Path, Callable, field)
3. Add isinstance() checks for task.result handling
4. Update function signatures (models → num_agents)
5. Run full test suite

### Success Metrics
- Zero hardcoded credentials in codebase
- All tests passing
- No unused imports detected by linter
- Type errors reduced to zero

### Risks & Mitigation
- **Risk**: Breaking existing functionality
- **Mitigation**: Comprehensive test coverage before deployment"""

IMPLEMENTATION_RESPONSE = """## Implementation Complete

### Changes Made
1. ✅ Replaced hardcoded API keys with os.environ.get()
2. ✅ Removed unused imports: json, uuid, Path, Callable, field
3. ✅ Added type handling for task.result (str/dict)
4. ✅ Updated function parameters: models → num_agents
5. ✅ Cleaned up misleading docstring claims

### Files Modified
- src/codegen/orchestration.py (security fixes, type safety)
- src/codegen/infinity_loop.py (new implementation)
- README_INFINITY_LOOP.md (documentation)

### Tests Added
- Unit tests for type handling
- Integration tests for orchestration
- State persistence tests

### Documentation
Complete README with usage examples, architecture diagrams, and configuration options."""

TEST_RESPONSE_PASS = """## Test Report

### Unit Tests
- Passed: 47/47
- Failed: 0
- Coverage: 94%

### Performance Tests
- Execution time: 1.2s (baseline: 1.5s) ✅ 20% faster
- Memory usage: 45MB (baseline: 52MB) ✅ 13% reduction
- CPU usage: Normal

### Security Scan
- Trufflehog: ✅ No secrets detected
- Bandit: ✅ No security issues
- Safety: ✅ All dependencies secure

### Code Quality
- Pylint: 9.8/10 ✅
- Mypy: ✅ No type errors
- Flake8: ✅ No style violations

### Overall Result
✅ **PASS** - All tests successful, ready for integration"""

TEST_RESPONSE_FAIL = """## Test Report

### Unit Tests
- Passed: 45/47
- Failed: 2
- Coverage: 94%

**Failures:**
1. test_orchestration_timeout - AssertionError on line 234
2. test_state_persistence - Connection timeout

### Performance Tests
- ⚠️ Execution time: 1.8s (baseline: 1.5s) - 20% slower

### Security Scan
- ✅ No issues

### Code Quality
- ✅ All checks pass

### Overall Result
❌ **FAIL** - 2 test failures need fixing"""

FIX_RESPONSE = """## Fix Applied

### Issues Addressed
1. **test_orchestration_timeout**: Increased timeout from 5s to 10s
2. **test_state_persistence**: Added connection retry logic with exponential backoff

### Changes Made
- Updated timeout configuration in orchestration.py
- Added retry decorator to database connection method
- Improved error handling in state manager

### Validation
Re-ran failed tests:
- test_orchestration_timeout: ✅ PASS
- test_state_persistence: ✅ PASS

All tests now passing."""

BENCHMARK_RESPONSE = """## Benchmark Report

### Performance Metrics
| Metric | Baseline | New | Change |
|--------|----------|-----|--------|
| Response Time | 1.5s | 1.2s | **-20%** ⬇️ |
| Memory Usage | 52MB | 45MB | **-13%** ⬇️ |
| CPU Usage | 45% | 40% | **-11%** ⬇️ |
| Error Rate | 0.5% | 0.1% | **-80%** ⬇️ |

### Resource Usage
- CPU: Within normal range
- Memory: Improved efficiency
- I/O: No significant change

### Overall Improvement
**Performance: +8.2%**  
**Efficiency: +12.5%**

### Regression Check
✅ No regressions detected

### Recommendation
**INTEGRATE** - Significant improvements with no downsides"""

INTEGRATION_RESPONSE_APPROVE = """{
    "decision": true,
    "improvement_pct": 8.2,
    "reasoning": "Performance improved by 8.2%, exceeding the 5% threshold. No regressions detected. Code quality metrics all positive. Security vulnerabilities reduced. Ready for production.",
    "action": "merge_pr",
    "learnings": [
        "Environment variable approach improved security",
        "Type safety prevented runtime errors",
        "Dead code removal improved performance",
        "Mock mode enables testing without backend"
    ]
}"""

INTEGRATION_RESPONSE_REJECT = """{
    "decision": false,
    "improvement_pct": 2.1,
    "reasoning": "Performance improvement of 2.1% is below the 5% threshold required for integration. While code quality improved, the performance gains are insufficient to justify the merge.",
    "action": "close_pr",
    "learnings": [
        "Small optimizations don't always meet threshold",
        "Need more substantial changes for integration",
        "Consider bundling multiple improvements"
    ]
}"""


def get_demo_response(agent_type: str, context: str = "") -> str:
    """Get appropriate demo response for agent type."""
    responses = {
        "research": RESEARCH_RESPONSE,
        "analysis": ANALYSIS_RESPONSE,
        "implementation": IMPLEMENTATION_RESPONSE,
        "test": TEST_RESPONSE_PASS,  # Always pass in demo mode
        "fix": FIX_RESPONSE,
        "benchmark": BENCHMARK_RESPONSE,
        "integration": INTEGRATION_RESPONSE_APPROVE,  # Always approve in demo mode
    }
    
    # Always return successful responses in demo mode for smooth experience
    return responses.get(agent_type, f"Demo response for {agent_type}")
