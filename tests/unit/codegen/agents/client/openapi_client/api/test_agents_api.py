"""Unit tests for the Agents API."""

from unittest.mock import MagicMock, patch

import pytest

from codegen.agents.client.openapi_client.api.agents_api import AgentsApi
from codegen.agents.client.openapi_client.api_client import ApiClient
from codegen.agents.client.openapi_client.models.agent_run_response import AgentRunResponse
from codegen.agents.client.openapi_client.models.create_agent_run_input import CreateAgentRunInput


class TestAgentsApi:
    """Tests for the AgentsApi class."""

    @pytest.fixture
    def api_client(self):
        """Create a mock API client."""
        return MagicMock(spec=ApiClient)

    @pytest.fixture
    def agents_api(self, api_client):
        """Create an AgentsApi instance with a mock API client."""
        return AgentsApi(api_client=api_client)

    def test_init_default_client(self):
        """Test initialization with default API client."""
        with patch("codegen.agents.client.openapi_client.api.agents_api.ApiClient") as mock_api_client_class:
            mock_api_client = MagicMock()
            mock_api_client_class.get_default.return_value = mock_api_client

            agents_api = AgentsApi()
            assert agents_api.api_client == mock_api_client

    def test_create_agent_run(self, agents_api, api_client):
        """Test create_agent_run_v1_organizations_org_id_agent_run_post method."""
        # Mock the API client's call_api method
        mock_response = MagicMock()
        api_client.call_api.return_value = mock_response

        # Mock the response_deserialize method
        mock_agent_run_response = AgentRunResponse(id="test_id", status="running")
        api_client.response_deserialize.return_value.data = mock_agent_run_response

        # Create test input
        create_agent_run_input = CreateAgentRunInput(prompt="Test prompt")

        # Call the method
        result = agents_api.create_agent_run_v1_organizations_org_id_agent_run_post(
            org_id=123,
            create_agent_run_input=create_agent_run_input,
        )

        # Verify the result
        assert result == mock_agent_run_response

        # Verify the API client was called correctly
        api_client.call_api.assert_called_once()
        api_client.response_deserialize.assert_called_once_with(
            response_data=mock_response,
            response_types_map={"200": "AgentRunResponse", "422": "HTTPValidationError"},
        )

    def test_create_agent_run_with_http_info(self, agents_api, api_client):
        """Test create_agent_run_v1_organizations_org_id_agent_run_post_with_http_info method."""
        # Mock the API client's call_api method
        mock_response = MagicMock()
        api_client.call_api.return_value = mock_response

        # Mock the response_deserialize method
        mock_agent_run_response = AgentRunResponse(id="test_id", status="running")
        api_client.response_deserialize.return_value = MagicMock(
            data=mock_agent_run_response,
            status_code=200,
            headers={"Content-Type": "application/json"},
        )

        # Create test input
        create_agent_run_input = CreateAgentRunInput(prompt="Test prompt")

        # Call the method
        result = agents_api.create_agent_run_v1_organizations_org_id_agent_run_post_with_http_info(
            org_id=123,
            create_agent_run_input=create_agent_run_input,
        )

        # Verify the result
        assert result.data == mock_agent_run_response
        assert result.status_code == 200
        assert result.headers == {"Content-Type": "application/json"}

        # Verify the API client was called correctly
        api_client.call_api.assert_called_once()
        api_client.response_deserialize.assert_called_once_with(
            response_data=mock_response,
            response_types_map={"200": "AgentRunResponse", "422": "HTTPValidationError"},
        )

    def test_get_agent_run(self, agents_api, api_client):
        """Test get_agent_run_v1_organizations_org_id_agent_run_agent_run_id_get method."""
        # Mock the API client's call_api method
        mock_response = MagicMock()
        api_client.call_api.return_value = mock_response

        # Mock the response_deserialize method
        mock_agent_run_response = AgentRunResponse(id="test_id", status="completed")
        api_client.response_deserialize.return_value.data = mock_agent_run_response

        # Call the method
        result = agents_api.get_agent_run_v1_organizations_org_id_agent_run_agent_run_id_get(
            org_id=123,
            agent_run_id="test_id",
        )

        # Verify the result
        assert result == mock_agent_run_response

        # Verify the API client was called correctly
        api_client.call_api.assert_called_once()
        api_client.response_deserialize.assert_called_once_with(
            response_data=mock_response,
            response_types_map={"200": "AgentRunResponse", "422": "HTTPValidationError"},
        )

    def test_get_agent_run_with_http_info(self, agents_api, api_client):
        """Test get_agent_run_v1_organizations_org_id_agent_run_agent_run_id_get_with_http_info method."""
        # Mock the API client's call_api method
        mock_response = MagicMock()
        api_client.call_api.return_value = mock_response

        # Mock the response_deserialize method
        mock_agent_run_response = AgentRunResponse(id="test_id", status="completed")
        api_client.response_deserialize.return_value = MagicMock(
            data=mock_agent_run_response,
            status_code=200,
            headers={"Content-Type": "application/json"},
        )

        # Call the method
        result = agents_api.get_agent_run_v1_organizations_org_id_agent_run_agent_run_id_get_with_http_info(
            org_id=123,
            agent_run_id="test_id",
        )

        # Verify the result
        assert result.data == mock_agent_run_response
        assert result.status_code == 200
        assert result.headers == {"Content-Type": "application/json"}

        # Verify the API client was called correctly
        api_client.call_api.assert_called_once()
        api_client.response_deserialize.assert_called_once_with(
            response_data=mock_response,
            response_types_map={"200": "AgentRunResponse", "422": "HTTPValidationError"},
        )

