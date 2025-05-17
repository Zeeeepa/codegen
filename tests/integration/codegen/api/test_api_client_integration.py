"""Integration tests for the API client module."""

import os
from unittest.mock import MagicMock, patch

import pytest
import requests
import responses

from codegen.agents.client.openapi_client.api.agents_api import AgentsApi
from codegen.agents.client.openapi_client.api.organizations_api import OrganizationsApi
from codegen.agents.client.openapi_client.api.users_api import UsersApi
from codegen.agents.client.openapi_client.api_client import ApiClient
from codegen.agents.client.openapi_client.configuration import Configuration
from codegen.agents.client.openapi_client.models.agent_run_response import AgentRunResponse
from codegen.agents.client.openapi_client.models.create_agent_run_input import CreateAgentRunInput
from codegen.agents.client.openapi_client.models.organization_response import OrganizationResponse
from codegen.agents.client.openapi_client.models.organization_settings import OrganizationSettings
from codegen.agents.client.openapi_client.models.user_response import UserResponse
from codegen.cli.api.client import RestAPI
from codegen.cli.api.endpoints import RUN_ENDPOINT
from codegen.cli.api.schemas import RunCodemodInput, RunCodemodOutput, CodemodRunType
from codegen.cli.errors import InvalidTokenError, ServerError


class TestApiClientIntegration:
    """Integration tests for the API client module."""

    @pytest.fixture
    def api_configuration(self):
        """Create a Configuration instance for testing."""
        config = Configuration()
        config.host = "https://api.example.com"
        config.api_key = {"Authorization": "test_token"}
        config.api_key_prefix = {"Authorization": "Bearer"}
        return config

    @pytest.fixture
    def api_client(self, api_configuration):
        """Create an ApiClient instance for testing."""
        return ApiClient(configuration=api_configuration)

    @pytest.fixture
    def rest_api(self):
        """Create a RestAPI instance for testing."""
        return RestAPI(auth_token="test_token")

    @responses.activate
    def test_agents_api_create_agent_run(self, api_client):
        """Test creating an agent run using the Agents API."""
        # Mock the API response
        responses.add(
            responses.POST,
            "https://api.example.com/v1/organizations/123/agent_run",
            json={"id": "test_id", "status": "running"},
            status=200,
        )

        # Create the API instance
        agents_api = AgentsApi(api_client=api_client)

        # Create test input
        create_agent_run_input = CreateAgentRunInput(prompt="Test prompt")

        # Call the method
        result = agents_api.create_agent_run_v1_organizations_org_id_agent_run_post(
            org_id=123,
            create_agent_run_input=create_agent_run_input,
        )

        # Verify the result
        assert isinstance(result, AgentRunResponse)
        assert result.id == "test_id"
        assert result.status == "running"

    @responses.activate
    def test_organizations_api_get_organization(self, api_client):
        """Test getting an organization using the Organizations API."""
        # Mock the API response
        responses.add(
            responses.GET,
            "https://api.example.com/v1/organizations/123",
            json={
                "id": 123,
                "name": "Test Org",
                "settings": {"github_pr_creation": True},
            },
            status=200,
        )

        # Create the API instance
        organizations_api = OrganizationsApi(api_client=api_client)

        # Call the method
        result = organizations_api.get_organization_v1_organizations_org_id_get(org_id=123)

        # Verify the result
        assert isinstance(result, OrganizationResponse)
        assert result.id == 123
        assert result.name == "Test Org"
        assert isinstance(result.settings, OrganizationSettings)
        assert result.settings.github_pr_creation is True

    @responses.activate
    def test_users_api_get_current_user(self, api_client):
        """Test getting the current user using the Users API."""
        # Mock the API response
        responses.add(
            responses.GET,
            "https://api.example.com/v1/users/me",
            json={
                "id": 123,
                "email": "user@example.com",
                "name": "Test User",
            },
            status=200,
        )

        # Create the API instance
        users_api = UsersApi(api_client=api_client)

        # Call the method
        result = users_api.get_current_user_v1_users_me_get()

        # Verify the result
        assert isinstance(result, UserResponse)
        assert result.id == 123
        assert result.email == "user@example.com"
        assert result.name == "Test User"

    @responses.activate
    @patch("codegen.cli.api.client.CodegenSession")
    @patch("codegen.cli.api.client.convert_to_ui")
    def test_rest_api_run(self, mock_convert_to_ui, mock_session, rest_api):
        """Test the run method of RestAPI."""
        # Mock dependencies
        mock_function = MagicMock()
        mock_function.name = "test_function"
        mock_function.source = "def test_function(): pass"

        mock_session_instance = MagicMock()
        mock_session_instance.config.repository.full_name = "test/repo"
        mock_session.from_active_session.return_value = mock_session_instance

        mock_convert_to_ui.return_value = "converted_source"

        # Mock the API response
        responses.add(
            responses.POST,
            RUN_ENDPOINT,
            json={"success": True, "web_link": "https://example.com"},
            status=200,
        )

        # Call the method
        result = rest_api.run(mock_function)

        # Verify the result
        assert isinstance(result, RunCodemodOutput)
        assert result.success is True
        assert result.web_link == "https://example.com"

        # Verify the request was made correctly
        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == RUN_ENDPOINT
        assert "Authorization" in responses.calls[0].request.headers
        assert responses.calls[0].request.headers["Authorization"] == "Bearer test_token"

    @responses.activate
    def test_rest_api_auth_error(self, rest_api):
        """Test handling of authentication errors in RestAPI."""
        # Mock the API response
        responses.add(
            responses.POST,
            RUN_ENDPOINT,
            json={"detail": "Invalid token"},
            status=401,
        )

        # Mock dependencies
        mock_function = MagicMock()
        mock_function.name = "test_function"
        mock_function.source = "def test_function(): pass"

        # Patch dependencies to avoid actual API calls
        with patch("codegen.cli.api.client.CodegenSession"), patch("codegen.cli.api.client.convert_to_ui"):
            # Call the method and expect an exception
            with pytest.raises(InvalidTokenError, match="Invalid or expired authentication token"):
                rest_api.run(mock_function)

    @responses.activate
    def test_rest_api_server_error(self, rest_api):
        """Test handling of server errors in RestAPI."""
        # Mock the API response
        responses.add(
            responses.POST,
            RUN_ENDPOINT,
            json={"detail": "Internal server error"},
            status=500,
        )

        # Mock dependencies
        mock_function = MagicMock()
        mock_function.name = "test_function"
        mock_function.source = "def test_function(): pass"

        # Patch dependencies to avoid actual API calls
        with patch("codegen.cli.api.client.CodegenSession"), patch("codegen.cli.api.client.convert_to_ui"):
            # Call the method and expect an exception
            with pytest.raises(ServerError, match="The server encountered an error while processing your request"):
                rest_api.run(mock_function)

    @responses.activate
    def test_rest_api_network_error(self, rest_api):
        """Test handling of network errors in RestAPI."""
        # Make the request raise an exception
        responses.add(
            responses.POST,
            RUN_ENDPOINT,
            body=requests.RequestException("Network error"),
        )

        # Mock dependencies
        mock_function = MagicMock()
        mock_function.name = "test_function"
        mock_function.source = "def test_function(): pass"

        # Patch dependencies to avoid actual API calls
        with patch("codegen.cli.api.client.CodegenSession"), patch("codegen.cli.api.client.convert_to_ui"):
            # Call the method and expect an exception
            with pytest.raises(ServerError, match="Network error: Network error"):
                rest_api.run(mock_function)

