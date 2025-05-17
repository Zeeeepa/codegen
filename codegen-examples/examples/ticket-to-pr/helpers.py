from codegen import Codebase
from codegen.extensions.clients.linear import LinearClient
from codegen.shared.enums.programming_language import ProgrammingLanguage
from codegen.extensions.linear.types import LinearEvent, LinearIssue, LinearComment, LinearUser, LinearLabel

from typing import Any, Dict, List, Optional, cast
import os
from pydantic import BaseModel


class LinearIssueUpdateEvent(BaseModel):
    issue_id: str
    issue_url: str
    title: str
    description: Optional[str] = None
    identifier: Optional[str] = None


def process_update_event(data: Any) -> LinearIssueUpdateEvent:
    """Process a Linear webhook event and extract issue information."""
    # Extract issue data from the event
    issue_data = cast(Dict[str, Any], data.get("data", {}))
    
    # Extract issue ID and URL
    issue_id = issue_data.get("id", "")
    issue_url = issue_data.get("url", "")
    
    # Extract labels
    labels = cast(List[LinearLabel], issue_data.get("labels", []))
    team = cast(Dict[str, Any], issue_data.get("team", {}))
    
    # Extract issue title, description, and identifier
    title = issue_data.get("title", "")
    description = issue_data.get("description", "")
    identifier = f"{team.get('key', '')}-{issue_data.get('number', '')}"
    
    # Create and return the event object
    return LinearIssueUpdateEvent(
        issue_id=issue_id,
        issue_url=issue_url,
        title=title,
        description=description,
        identifier=identifier,
    )


def has_codegen_label(data: dict) -> bool:
    """Check if the issue has the 'Codegen' label."""
    issue_data = data.get("data", {})
    labels = issue_data.get("labels", [])
    
    return any(label.get("name") == "Codegen" for label in labels)


def format_linear_message(title: str, description: Optional[str]) -> str:
    """Format a Linear issue title and description into a message for the agent."""
    message = f"Create a PR that implements: {title}"
    
    if description:
        message += f"\n\nDetails:\n{description}"
    
    return message


def create_codebase(repo_name: str, language: ProgrammingLanguage) -> Codebase:
    """Create a Codebase instance for the specified repository."""
    from codegen.config import Config
    
    config = Config()
    config.secrets.github_token = os.environ["GITHUB_TOKEN"]
    
    return Codebase.from_repo(repo_name, language=language, tmp_dir="/root", config=config)

