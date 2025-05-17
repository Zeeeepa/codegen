"""Unit tests for the Users API."""

from unittest.mock import MagicMock, patch

import pytest

from codegen.agents.client.openapi_client.api.users_api import UsersApi
from codegen.agents.client.openapi_client.api_client import ApiClient
from codegen.agents.client.openapi_client.models.page_user_response import PageUserResponse
from codegen.agents.client.openapi_client.models.user_response import UserResponse


class TestUsersApi:
    """Tests for the UsersApi class."""

    @pytest.fixture
    def api_client(self):
        """Create a mock API client."""
        return MagicMock(spec=ApiClient)

    @pytest.fixture
    def users_api(self, api_client):
        """Create a UsersApi instance with a mock API client."""
        return UsersApi(api_client=api_client)

    def test_init_default_client(self):
        """Test initialization with default API client."""
        with patch("codegen.agents.client.openapi_client.api.users_api.ApiClient") as mock_api_client_class:
            mock_api_client = MagicMock()
            mock_api_client_class.get_default.return_value = mock_api_client

            users_api = UsersApi()
            assert users_api.api_client == mock_api_client

    def test_get_current_user(self, users_api, api_client):
        """Test get_current_user_v1_users_me_get method."""
        # Mock the API client's call_api method
        mock_response = MagicMock()
        api_client.call_api.return_value = mock_response

        # Mock the response_deserialize method
        mock_user_response = UserResponse(
            id=123,
            email="user@example.com",
            name="Test User",
        )
        api_client.response_deserialize.return_value.data = mock_user_response

        # Call the method
        result = users_api.get_current_user_v1_users_me_get()

        # Verify the result
        assert result == mock_user_response
        assert result.email == "user@example.com"
        assert result.name == "Test User"

        # Verify the API client was called correctly
        api_client.call_api.assert_called_once()
        api_client.response_deserialize.assert_called_once_with(
            response_data=mock_response,
            response_types_map={"200": "UserResponse"},
        )

    def test_get_current_user_with_http_info(self, users_api, api_client):
        """Test get_current_user_v1_users_me_get_with_http_info method."""
        # Mock the API client's call_api method
        mock_response = MagicMock()
        api_client.call_api.return_value = mock_response

        # Mock the response_deserialize method
        mock_user_response = UserResponse(
            id=123,
            email="user@example.com",
            name="Test User",
        )
        api_client.response_deserialize.return_value = MagicMock(
            data=mock_user_response,
            status_code=200,
            headers={"Content-Type": "application/json"},
        )

        # Call the method
        result = users_api.get_current_user_v1_users_me_get_with_http_info()

        # Verify the result
        assert result.data == mock_user_response
        assert result.status_code == 200
        assert result.headers == {"Content-Type": "application/json"}

        # Verify the API client was called correctly
        api_client.call_api.assert_called_once()
        api_client.response_deserialize.assert_called_once_with(
            response_data=mock_response,
            response_types_map={"200": "UserResponse"},
        )

    def test_get_user(self, users_api, api_client):
        """Test get_user_v1_users_user_id_get method."""
        # Mock the API client's call_api method
        mock_response = MagicMock()
        api_client.call_api.return_value = mock_response

        # Mock the response_deserialize method
        mock_user_response = UserResponse(
            id=123,
            email="user@example.com",
            name="Test User",
        )
        api_client.response_deserialize.return_value.data = mock_user_response

        # Call the method
        result = users_api.get_user_v1_users_user_id_get(user_id=123)

        # Verify the result
        assert result == mock_user_response
        assert result.email == "user@example.com"
        assert result.name == "Test User"

        # Verify the API client was called correctly
        api_client.call_api.assert_called_once()
        api_client.response_deserialize.assert_called_once_with(
            response_data=mock_response,
            response_types_map={"200": "UserResponse", "422": "HTTPValidationError"},
        )

    def test_get_user_with_http_info(self, users_api, api_client):
        """Test get_user_v1_users_user_id_get_with_http_info method."""
        # Mock the API client's call_api method
        mock_response = MagicMock()
        api_client.call_api.return_value = mock_response

        # Mock the response_deserialize method
        mock_user_response = UserResponse(
            id=123,
            email="user@example.com",
            name="Test User",
        )
        api_client.response_deserialize.return_value = MagicMock(
            data=mock_user_response,
            status_code=200,
            headers={"Content-Type": "application/json"},
        )

        # Call the method
        result = users_api.get_user_v1_users_user_id_get_with_http_info(user_id=123)

        # Verify the result
        assert result.data == mock_user_response
        assert result.status_code == 200
        assert result.headers == {"Content-Type": "application/json"}

        # Verify the API client was called correctly
        api_client.call_api.assert_called_once()
        api_client.response_deserialize.assert_called_once_with(
            response_data=mock_response,
            response_types_map={"200": "UserResponse", "422": "HTTPValidationError"},
        )

    def test_list_organization_users(self, users_api, api_client):
        """Test list_organization_users_v1_organizations_org_id_users_get method."""
        # Mock the API client's call_api method
        mock_response = MagicMock()
        api_client.call_api.return_value = mock_response

        # Mock the response_deserialize method
        mock_user1 = UserResponse(
            id=123,
            email="user1@example.com",
            name="Test User 1",
        )
        mock_user2 = UserResponse(
            id=456,
            email="user2@example.com",
            name="Test User 2",
        )
        mock_page_response = PageUserResponse(
            items=[mock_user1, mock_user2],
            total=2,
            page=1,
            size=10,
        )
        api_client.response_deserialize.return_value.data = mock_page_response

        # Call the method
        result = users_api.list_organization_users_v1_organizations_org_id_users_get(
            org_id=789,
            page=1,
            size=10,
        )

        # Verify the result
        assert result == mock_page_response
        assert len(result.items) == 2
        assert result.items[0].email == "user1@example.com"
        assert result.items[1].email == "user2@example.com"

        # Verify the API client was called correctly
        api_client.call_api.assert_called_once()
        api_client.response_deserialize.assert_called_once_with(
            response_data=mock_response,
            response_types_map={"200": "PageUserResponse", "422": "HTTPValidationError"},
        )

    def test_list_organization_users_with_http_info(self, users_api, api_client):
        """Test list_organization_users_v1_organizations_org_id_users_get_with_http_info method."""
        # Mock the API client's call_api method
        mock_response = MagicMock()
        api_client.call_api.return_value = mock_response

        # Mock the response_deserialize method
        mock_user1 = UserResponse(
            id=123,
            email="user1@example.com",
            name="Test User 1",
        )
        mock_user2 = UserResponse(
            id=456,
            email="user2@example.com",
            name="Test User 2",
        )
        mock_page_response = PageUserResponse(
            items=[mock_user1, mock_user2],
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
        result = users_api.list_organization_users_v1_organizations_org_id_users_get_with_http_info(
            org_id=789,
            page=1,
            size=10,
        )

        # Verify the result
        assert result.data == mock_page_response
        assert result.status_code == 200
        assert result.headers == {"Content-Type": "application/json"}

        # Verify the API client was called correctly
        api_client.call_api.assert_called_once()
        api_client.response_deserialize.assert_called_once_with(
            response_data=mock_response,
            response_types_map={"200": "PageUserResponse", "422": "HTTPValidationError"},
        )

