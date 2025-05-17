"""Unit tests for the OpenAPI client API response."""

import pytest

from codegen.agents.client.openapi_client.api_response import ApiResponse


class TestApiResponse:
    """Tests for the ApiResponse class."""

    def test_init(self):
        """Test initialization of ApiResponse."""
        # Test with all parameters
        response = ApiResponse(
            status_code=200,
            headers={"Content-Type": "application/json"},
            data={"success": True},
            raw_data=b'{"success": true}',
        )
        assert response.status_code == 200
        assert response.headers == {"Content-Type": "application/json"}
        assert response.data == {"success": True}
        assert response.raw_data == b'{"success": true}'

        # Test with minimal parameters
        response = ApiResponse(status_code=200, data=None)
        assert response.status_code == 200
        assert response.headers == {}
        assert response.data is None
        assert response.raw_data is None

    def test_repr(self):
        """Test __repr__ method."""
        response = ApiResponse(
            status_code=200,
            headers={"Content-Type": "application/json"},
            data={"success": True},
        )
        repr_str = repr(response)
        assert "ApiResponse" in repr_str
        assert "status_code=200" in repr_str
        assert "headers={'Content-Type': 'application/json'}" in repr_str
        assert "data={'success': True}" in repr_str

    def test_str(self):
        """Test __str__ method."""
        response = ApiResponse(
            status_code=200,
            headers={"Content-Type": "application/json"},
            data={"success": True},
        )
        str_str = str(response)
        assert "ApiResponse" in str_str
        assert "status_code=200" in str_str
        assert "headers={'Content-Type': 'application/json'}" in str_str
        assert "data={'success': True}" in str_str

    def test_eq(self):
        """Test __eq__ method."""
        response1 = ApiResponse(
            status_code=200,
            headers={"Content-Type": "application/json"},
            data={"success": True},
        )
        response2 = ApiResponse(
            status_code=200,
            headers={"Content-Type": "application/json"},
            data={"success": True},
        )
        response3 = ApiResponse(
            status_code=400,
            headers={"Content-Type": "application/json"},
            data={"success": False},
        )

        # Test equality
        assert response1 == response2
        assert response1 != response3
        assert response1 != "not_an_api_response"

