"""Unit tests for the Organizations API."""

from unittest.mock import MagicMock, patch

import pytest

from codegen.agents.client.openapi_client.api.organizations_api import OrganizationsApi
from codegen.agents.client.openapi_client.api_client import ApiClient
from codegen.agents.client.openapi_client.models.organization_response import OrganizationResponse
from codegen.agents.client.openapi_client.models.organization_settings import OrganizationSettings
from codegen.agents.client.openapi_client.models.page_organization_response import PageOrganizationResponse


class TestOrganizationsApi:
    """Tests for the OrganizationsApi class."""

    @pytest.fixture
    def api_client(self):
        """Create a mock API client."""
        return MagicMock(spec=ApiClient)

    @pytest.fixture
    def organizations_api(self, api_client):
        """Create an OrganizationsApi instance with a mock API client."""
        return OrganizationsApi(api_client=api_client)

    def test_init_default_client(self):
        """Test initialization with default API client."""
        with patch("codegen.agents.client.openapi_client.api.organizations_api.ApiClient") as mock_api_client_class:
            mock_api_client = MagicMock()
            mock_api_client_class.get_default.return_value = mock_api_client

            organizations_api = OrganizationsApi()
            assert organizations_api.api_client == mock_api_client

    def test_get_organization(self, organizations_api, api_client):
        """Test get_organization_v1_organizations_org_id_get method."""
        # Mock the API client's call_api method
        mock_response = MagicMock()
        api_client.call_api.return_value = mock_response

        # Mock the response_deserialize method
        mock_org_response = OrganizationResponse(
            id=123,
            name="Test Org",
            settings=OrganizationSettings(github_pr_creation=True),
        )
        api_client.response_deserialize.return_value.data = mock_org_response

        # Call the method
        result = organizations_api.get_organization_v1_organizations_org_id_get(org_id=123)

        # Verify the result
        assert result == mock_org_response

        # Verify the API client was called correctly
        api_client.call_api.assert_called_once()
        api_client.response_deserialize.assert_called_once_with(
            response_data=mock_response,
            response_types_map={"200": "OrganizationResponse", "422": "HTTPValidationError"},
        )

    def test_get_organization_with_http_info(self, organizations_api, api_client):
        """Test get_organization_v1_organizations_org_id_get_with_http_info method."""
        # Mock the API client's call_api method
        mock_response = MagicMock()
        api_client.call_api.return_value = mock_response

        # Mock the response_deserialize method
        mock_org_response = OrganizationResponse(
            id=123,
            name="Test Org",
            settings=OrganizationSettings(github_pr_creation=True),
        )
        api_client.response_deserialize.return_value = MagicMock(
            data=mock_org_response,
            status_code=200,
            headers={"Content-Type": "application/json"},
        )

        # Call the method
        result = organizations_api.get_organization_v1_organizations_org_id_get_with_http_info(org_id=123)

        # Verify the result
        assert result.data == mock_org_response
        assert result.status_code == 200
        assert result.headers == {"Content-Type": "application/json"}

        # Verify the API client was called correctly
        api_client.call_api.assert_called_once()
        api_client.response_deserialize.assert_called_once_with(
            response_data=mock_response,
            response_types_map={"200": "OrganizationResponse", "422": "HTTPValidationError"},
        )

    def test_list_organizations(self, organizations_api, api_client):
        """Test list_organizations_v1_organizations_get method."""
        # Mock the API client's call_api method
        mock_response = MagicMock()
        api_client.call_api.return_value = mock_response

        # Mock the response_deserialize method
        mock_org1 = OrganizationResponse(
            id=123,
            name="Test Org 1",
            settings=OrganizationSettings(github_pr_creation=True),
        )
        mock_org2 = OrganizationResponse(
            id=456,
            name="Test Org 2",
            settings=OrganizationSettings(github_pr_creation=False),
        )
        mock_page_response = PageOrganizationResponse(
            items=[mock_org1, mock_org2],
            total=2,
            page=1,
            size=10,
        )
        api_client.response_deserialize.return_value.data = mock_page_response

        # Call the method
        result = organizations_api.list_organizations_v1_organizations_get(page=1, size=10)

        # Verify the result
        assert result == mock_page_response
        assert len(result.items) == 2
        assert result.items[0].name == "Test Org 1"
        assert result.items[1].name == "Test Org 2"

        # Verify the API client was called correctly
        api_client.call_api.assert_called_once()
        api_client.response_deserialize.assert_called_once_with(
            response_data=mock_response,
            response_types_map={"200": "PageOrganizationResponse", "422": "HTTPValidationError"},
        )

    def test_list_organizations_with_http_info(self, organizations_api, api_client):
        """Test list_organizations_v1_organizations_get_with_http_info method."""
        # Mock the API client's call_api method
        mock_response = MagicMock()
        api_client.call_api.return_value = mock_response

        # Mock the response_deserialize method
        mock_org1 = OrganizationResponse(
            id=123,
            name="Test Org 1",
            settings=OrganizationSettings(github_pr_creation=True),
        )
        mock_org2 = OrganizationResponse(
            id=456,
            name="Test Org 2",
            settings=OrganizationSettings(github_pr_creation=False),
        )
        mock_page_response = PageOrganizationResponse(
            items=[mock_org1, mock_org2],
            total=2,
            page=1,
            size=10,
        )
        api_client.response_deserialize.return_value = MagicMock(
            data=mock_page_response,
            status_code=200,
            headers={"Content-Type": "application/json"},
        )

        # Call the method
        result = organizations_api.list_organizations_v1_organizations_get_with_http_info(page=1, size=10)

        # Verify the result
        assert result.data == mock_page_response
        assert result.status_code == 200
        assert result.headers == {"Content-Type": "application/json"}

        # Verify the API client was called correctly
        api_client.call_api.assert_called_once()
        api_client.response_deserialize.assert_called_once_with(
            response_data=mock_response,
            response_types_map={"200": "PageOrganizationResponse", "422": "HTTPValidationError"},
        )

