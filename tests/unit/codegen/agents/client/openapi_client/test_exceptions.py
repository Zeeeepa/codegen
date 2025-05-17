"""Unit tests for the OpenAPI client exceptions."""

from unittest.mock import MagicMock

import pytest

from codegen.agents.client.openapi_client.exceptions import ApiException, ApiTypeError, ApiValueError


class TestExceptions:
    """Tests for the OpenAPI client exceptions."""

    def test_api_exception(self):
        """Test ApiException class."""
        # Test with status and reason
        exception = ApiException(status=400, reason="Bad Request")
        assert exception.status == 400
        assert exception.reason == "Bad Request"
        assert str(exception) == "(400)\nReason: Bad Request\n"

        # Test with headers
        headers = {"Content-Type": "application/json"}
        exception = ApiException(status=400, reason="Bad Request", headers=headers)
        assert exception.headers == headers
        assert "HTTP response headers" in str(exception)

        # Test with body
        body = '{"error": "Invalid input"}'
        exception = ApiException(status=400, reason="Bad Request", body=body)
        assert exception.body == body
        assert "HTTP response body" in str(exception)

    def test_api_exception_from_response(self):
        """Test ApiException.from_response method."""
        # Create a mock response
        response = MagicMock()
        response.status = 400
        response.reason = "Bad Request"
        response.data = b'{"error": "Invalid input"}'
        response.getheaders.return_value = {"Content-Type": "application/json"}

        # Create an exception from the response
        exception = ApiException.from_response(response)
        assert exception.status == 400
        assert exception.reason == "Bad Request"
        assert exception.body == '{"error": "Invalid input"}'
        assert exception.headers == {"Content-Type": "application/json"}

    def test_api_type_error(self):
        """Test ApiTypeError class."""
        exception = ApiTypeError("Expected int, got str")
        assert str(exception) == "Expected int, got str"

    def test_api_value_error(self):
        """Test ApiValueError class."""
        exception = ApiValueError("Invalid value")
        assert str(exception) == "Invalid value"

