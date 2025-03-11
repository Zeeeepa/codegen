"""Tool for viewing commit history with URLs."""

from typing import ClassVar, List

from pydantic import Field

from codegen.sdk.core.codebase import Codebase

from ..observation import Observation


class CommitHistoryObservation(Observation):
    """Response from viewing commit history."""

    commits: List[dict] = Field(
        description="List of commits with their details including URLs",
    )

    str_template: ClassVar[str] = "Found {total} commits"

    @property
    def total(self) -> int:
        return len(self.commits)


def view_commit_history(
    codebase: Codebase,
    max_results: int = 20,
    path: str = None,
) -> CommitHistoryObservation:
    """Get the commit history for a repository or specific path.

    Args:
        codebase: The codebase to operate on
        max_results: Maximum number of commits to return
        path: Optional path to filter commits by
    """
    try:
        # Get the GitHub repo object
        repo = codebase._op.remote_git_repo

        # Get commits
        commits_data = []
        commits = repo.repo.get_commits(path=path)
        
        for commit in commits[:max_results]:
            commit_data = {
                "sha": commit.sha,
                "message": commit.commit.message,
                "author": commit.commit.author.name,
                "date": commit.commit.author.date.isoformat(),
                "url": commit.html_url,  # Include the URL for linking
            }
            commits_data.append(commit_data)

        return CommitHistoryObservation(
            status="success",
            commits=commits_data,
        )

    except Exception as e:
        return CommitHistoryObservation(
            status="error",
            error=f"Failed to get commit history: {e!s}",
            commits=[],
        )
