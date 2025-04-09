# Agent Test Runner

This is a unified test runner for all agent tests in the Codegen project. It runs all agent tests and collects errors, displaying them in a table format. It will continue running tests even if some fail, to provide a comprehensive report.

## Features

- Runs all agent tests in a single command
- Displays results in a table format
- Collects and displays errors
- Continues running tests even if some fail
- Provides a summary of test results

## Usage

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Run the test runner:

```bash
python test_all_agents.py
```

## Output

The test runner will display:

1. A table with test results for each agent
2. A summary of all test results
3. Detailed error messages for any failed tests

Example output:

```
=== Running Agent Tests ===

Running tests for base_agent...
Running tests for chat_agent...
Running tests for code_agent...
Running tests for mcp_agent...
Running tests for planning_agent...
Running tests for pr_review_agent...
Running tests for reflection_agent...
Running tests for research_agent...
Running tests for toolcall_agent...

=== Test Results ===

+---------------+------+-------+--------+--------+--------+---------+
| Agent         | Status | Total | Passed | Failed | Errors | Skipped |
+===============+========+=======+========+========+========+=========+
| base_agent    | PASS   | 10    | 10     | 0      | 0      | 0       |
+---------------+--------+-------+--------+--------+--------+---------+
| chat_agent    | PASS   | 8     | 8      | 0      | 0      | 0       |
+---------------+--------+-------+--------+--------+--------+---------+
| code_agent    | PASS   | 12    | 12     | 0      | 0      | 0       |
+---------------+--------+-------+--------+--------+--------+---------+
| mcp_agent     | PASS   | 6     | 6      | 0      | 0      | 0       |
+---------------+--------+-------+--------+--------+--------+---------+
| planning_agent| PASS   | 9     | 9      | 0      | 0      | 0       |
+---------------+--------+-------+--------+--------+--------+---------+
| pr_review_agent| PASS  | 7     | 7      | 0      | 0      | 0       |
+---------------+--------+-------+--------+--------+--------+---------+
| reflection_agent| PASS | 5     | 5      | 0      | 0      | 0       |
+---------------+--------+-------+--------+--------+--------+---------+
| research_agent| PASS   | 4     | 4      | 0      | 0      | 0       |
+---------------+--------+-------+--------+--------+--------+---------+
| toolcall_agent| PASS   | 11    | 11     | 0      | 0      | 0       |
+---------------+--------+-------+--------+--------+--------+---------+

=== Summary ===
Total tests: 72
Passed: 72
Failed: 0
Errors: 0
Skipped: 0
```

If there are errors, they will be displayed in detail at the end of the output.
