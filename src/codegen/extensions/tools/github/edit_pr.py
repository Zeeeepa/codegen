"""Tool for editing a PR's title, body, and/or state."""

from typing import TYPE_CHECKING, Optional

from codegen.extensions.tools.observation import Observation
from codegen.sdk.core.codebase import Codebase

if TYPE_CHECKING:
    from github.PullRequest import PullRequest


def edit_pr(
    codebase: Codebase,
    pr_number: int,
    title: Optional[str] = None,
    body: Optional[str] = None,
    state: Optional[str] = None,
) -> Observation:
    """Edit a PR's title, body, and/or state.

    Args:
        codebase: The codebase to operate on
        pr_number: The PR number to edit
        title: The new title for the PR (optional)
        body: The new body/description for the PR (optional)
        state: The new state for the PR (optional, can be 'open', 'closed', 'draft', or 'ready_for_review')

    Returns:
        Observation with the result of the operation
    """
    repo = codebase.git_client.get_repo()
    if not repo:
        return Observation(
            success=False,
            message=f"Failed to get repository for PR #{pr_number}",
        )

    try:
        pr: PullRequest = repo.get_pull(pr_number)
    except Exception as e:
        return Observation(
            success=False,
            message=f"Failed to get PR #{pr_number}: {e}",
        )

    # Track what was updated
    updates = []

    # Update title if provided
    if title is not None:
        pr.edit(title=title)
        updates.append("title")

    # Update body if provided
    if body is not None:
        pr.edit(body=body)
        updates.append("body")

    # Update state if provided
    if state is not None:
        state = state.lower()
        if state == "closed":
            pr.edit(state="closed")
            updates.append("state (closed)")
        elif state == "open":
            pr.edit(state="open")
            updates.append("state (opened)")
        elif state == "draft":
            pr.as_draft()
            updates.append("state (converted to draft)")
        elif state == "ready_for_review":
            pr.ready_for_review()
            updates.append("state (marked ready for review)")
        else:
            return Observation(
                success=False,
                message=f"Invalid state '{state}'. Must be one of: 'open', 'closed', 'draft', or 'ready_for_review'",
            )

    if not updates:
        return Observation(
            success=True,
            message=f"No changes were made to PR #{pr_number}. Please provide at least one of: title, body, or state.",
        )

    return Observation(
        success=True,
        message=f"Successfully updated PR #{pr_number} ({', '.join(updates)}). Note that this tool only updates PR metadata and does not push code changes to the PR branch. To add code changes to a PR, make your edits and then use the `create_pr` tool while on the PR branch.",
        url=pr.html_url,
    )
