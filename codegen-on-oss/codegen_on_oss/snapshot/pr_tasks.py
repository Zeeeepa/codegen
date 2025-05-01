import logging

from codegen.extensions.github.types.pull_request import PullRequestLabeledEvent
from codegen.sdk.core.codebase import Codebase

logging.basicConfig(level=logging.INFO, force=True)
logger = logging.getLogger(__name__)


def _check_for_dev_imports(file_path: str, file_content: str) -> list[tuple[int, str]]:
    """
    Check a file for development imports.

    Args:
        file_path: Path to the file
        file_content: Content of the file

    Returns:
        List of tuples containing line number and violation message
    """
    violations = []
    lines = file_content.splitlines()

    # Skip checking in test files, stories, etc.
    if any(pattern in file_path for pattern in ["/test/", "/tests/", "/stories/", "/mocks/"]):
        return violations

    # Check for react-dev-overlay imports
    for i, line in enumerate(lines):
        line_num = i + 1
        if "react-dev-overlay" in line and "import" in line:
            violations.append(
                (line_num, "Development import 'react-dev-overlay' found in production code")
            )

    return violations

def lint_for_dev_import_violations(codebase: Codebase, event: PullRequestLabeledEvent):
    """
    Next.js codemod to detect imports of the react-dev-overlay module in production code.

    Args:
        codebase: The codebase to analyze
        event: The PR event that triggered this task
    """
    violations = []

    # Get the files changed in the PR
    changed_files = codebase.get_changed_files(
        base_commit=event.pull_request.base.sha,
        head_commit=event.pull_request.head.sha,
    )

    # Check each changed file for violations
    for file_path in changed_files:
        # Skip non-JS/TS files
        if not file_path.endswith((".js", ".jsx", ".ts", ".tsx")):
            continue

        try:
            file_content = codebase.get_file_content(file_path)
            file_violations = _check_for_dev_imports(file_path, file_content)
            violations.extend([(file_path, *v) for v in file_violations])
        except Exception as e:
            print(f"Error checking file {file_path}: {e}")

    # If violations found, comment on the PR
    if violations:
        comment = "## Development Import Violations Found\n\n"
        comment += "The following files contain imports of development modules that should not be used in production code:\n\n"

        for file_path, line_num, message in violations:
            comment += f"- `{file_path}` (line {line_num}): {message}\n"

        comment += "\nPlease remove these imports before merging this PR."

        # Add the comment to the PR
        codebase.github_client.create_pr_comment(
            pr_number=event.pull_request.number,
            body=comment,
        )

        return {
            "status": "failure",
            "message": "Development imports found in production code",
            "violations": violations,
        }

    return {
        "status": "success",
        "message": "No development imports found",
    }
