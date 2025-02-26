from typing import Literal

from pydantic import BaseModel

from ..base import GitHubRepository, GitHubUser
from ..enterprise import GitHubEnterprise
from ..installation import GitHubInstallation
from ..label import GitHubLabel
from ..organization import GitHubOrganization
from ..pull_request import PullRequest


class User(BaseModel):
    id: int
    login: str


class Label(BaseModel):
    id: int
    node_id: str
    url: str
    name: str
    description: str | None = None
    color: str
    default: bool


class PullRequestLabeledEvent(BaseModel):
    """Simplified version of the PR labeled event for testing"""

    action: Literal["labeled"]
    number: int
    pull_request: PullRequest
    label: Label
    repository: dict  # Simplified for now
    sender: User


class PullRequestUnlabeledEvent(BaseModel):
    action: str
    number: int
    pull_request: PullRequest
    label: GitHubLabel
    repository: GitHubRepository
    organization: GitHubOrganization
    enterprise: GitHubEnterprise
    sender: GitHubUser
    installation: GitHubInstallation
