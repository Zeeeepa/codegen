"""Tests for Linear tools with team_id parameter."""

import os

import pytest

from codegen.extensions.linear.linear_client import LinearClient
from codegen.extensions.tools.linear.linear import (
    linear_create_issue_tool,
    linear_get_teams_tool,
)


@pytest.fixture
def client() -> LinearClient:
    """Create a Linear client for testing."""
    token = os.getenv("LINEAR_ACCESS_TOKEN")
    if not token:
        pytest.skip("LINEAR_ACCESS_TOKEN environment variable not set")
    # Note: We're not setting team_id here to test explicit team_id passing
    return LinearClient(token)


def test_create_issue_with_explicit_team_id(client: LinearClient) -> None:
    """Test creating an issue with an explicit team_id."""
    # First, get available teams
    teams_result = linear_get_teams_tool(client)
    assert teams_result.status == "success"
    assert len(teams_result.teams) > 0

    # Use the first team's ID for our test
    team_id = teams_result.teams[0]["id"]
    team_name = teams_result.teams[0]["name"]

    # Create an issue with explicit team_id
    title = f"Test Issue in {team_name} - Explicit Team ID"
    description = f"This is a test issue created in team {team_name} with explicit team_id"

    result = linear_create_issue_tool(client, title, description, team_id)
    assert result.status == "success"
    assert result.title == title
    assert result.team_id == team_id
    assert result.issue_data["title"] == title
    assert result.issue_data["description"] == description

    # If there are multiple teams, test with a different team
    if len(teams_result.teams) > 1:
        second_team_id = teams_result.teams[1]["id"]
        second_team_name = teams_result.teams[1]["name"]

        title2 = f"Test Issue in {second_team_name} - Explicit Team ID"
        description2 = f"This is a test issue created in team {second_team_name} with explicit team_id"

        result2 = linear_create_issue_tool(client, title2, description2, second_team_id)
        assert result2.status == "success"
        assert result2.title == title2
        assert result2.team_id == second_team_id
        assert result2.issue_data["title"] == title2
        assert result2.issue_data["description"] == description2
