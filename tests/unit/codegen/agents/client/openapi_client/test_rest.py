"""Unit tests for the OpenAPI client REST module."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from codegen.agents.client.openapi_client.configuration import Configuration
from codegen.agents.client.openapi_client.exceptions import ApiException
from codegen.agents.client.openapi_client.rest import RESTClientObject, RESTResponse


class TestRESTClientObject:
    """Tests for the RESTClientObject class."""

    @pytest.fixture
    def configuration(self):
        """Create a Configuration instance for testing."""
        return Configuration()

    @pytest.fixture
    def rest_client(self, configuration):
        """Create a RESTClientObject instance for testing."""
        return RESTClientObject(configuration)

    def test_init(self, configuration):
        """Test initialization of RESTClientObject."""
        client = RESTClientObject(configuration)
        assert client.configuration == configuration
        assert client.pool_manager is not None
        assert client.proxy_manager is None

    def test_request_success(self, rest_client):
        """Test request method with a successful response."""
        # Mock the requests.request method
        with patch("requests.request") as mock_request:
            # Create a mock response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {"Content-Type": "application/json"}
            mock_response.content = b'{"success": true}'
            mock_request.return_value = mock_response

            # Call the method
            response = rest_client.request(
                "GET",
                "https://api.example.com/endpoint",
                headers={"Authorization": "Bearer test_token"},
                query_params=[("param", "value")],
            )

            # Verify the response
            assert isinstance(response, RESTResponse)
            assert response.status == 200
            assert response.data == b'{"success": true}'
            assert response.getheader("Content-Type") == "application/json"

            # Verify the request was made correctly
            mock_request.assert_called_once_with(
                "GET",
                "https://api.example.com/endpoint?param=value",
                headers={"Authorization": "Bearer test_token"},
                timeout=None,
                data=None,
                json=None,
                files=None,
                auth=None,
                cookies=None,
                proxies=None,
                verify=None,
                cert=None,
            )

    def test_request_error(self, rest_client):
        """Test request method with an error response."""
        # Mock the requests.request method
        with patch("requests.request") as mock_request:
            # Create a mock response
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.reason = "Bad Request"
            mock_response.headers = {"Content-Type": "application/json"}
            mock_response.content = b'{"error": "Invalid input"}'
            mock_request.return_value = mock_response

            # Call the method
            response = rest_client.request(
                "POST",
                "https://api.example.com/endpoint",
                headers={"Authorization": "Bearer test_token"},
                body={"data": "value"},
            )

            # Verify the response
            assert isinstance(response, RESTResponse)
            assert response.status == 400
            assert response.data == b'{"error": "Invalid input"}'
            assert response.getheader("Content-Type") == "application/json"

            # Verify the request was made correctly
            mock_request.assert_called_once_with(
                "POST",
                "https://api.example.com/endpoint",
                headers={"Authorization": "Bearer test_token"},
                timeout=None,
                data=None,
                json={"data": "value"},
                files=None,
                auth=None,
                cookies=None,
                proxies=None,
                verify=None,
                cert=None,
            )

    def test_request_exception(self, rest_client):
        """Test request method with an exception."""
        # Mock the requests.request method
        with patch("requests.request") as mock_request:
            # Make the request raise an exception
            mock_request.side_effect = requests.RequestException("Network error")

            # Call the method and expect an exception
            with pytest.raises(ApiException, match="Network error"):
                rest_client.request(
                    "GET",
                    "https://api.example.com/endpoint",
                )

    def test_request_with_timeout(self, rest_client):
        """Test request method with a timeout."""
        # Mock the requests.request method
        with patch("requests.request") as mock_request:
            # Create a mock response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_request.return_value = mock_response

            # Call the method with a timeout
            rest_client.request(
                "GET",
                "https://api.example.com/endpoint",
                _request_timeout=30,
            )

            # Verify the request was made with the timeout
            mock_request.assert_called_once()
            assert mock_request.call_args[1]["timeout"] == 30

    def test_request_with_proxy(self, configuration, rest_client):
        """Test request method with a proxy."""
        # Set a proxy in the configuration
        configuration.proxy = "http://proxy.example.com:8080"

        # Mock the requests.request method
        with patch("requests.request") as mock_request:
            # Create a mock response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_request.return_value = mock_response

            # Call the method
            rest_client.request(
                "GET",
                "https://api.example.com/endpoint",
            )

            # Verify the request was made with the proxy
            mock_request.assert_called_once()
            assert mock_request.call_args[1]["proxies"] == {
                "http": "http://proxy.example.com:8080",
                "https": "http://proxy.example.com:8080",
            }

    def test_request_with_ssl_cert(self, configuration, rest_client):
        """Test request method with SSL certificate."""
        # Set SSL certificate in the configuration
        configuration.ssl_ca_cert = "/path/to/ca.crt"
        configuration.cert_file = "/path/to/cert.crt"
        configuration.key_file = "/path/to/key.key"

        # Mock the requests.request method
        with patch("requests.request") as mock_request:
            # Create a mock response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_request.return_value = mock_response

            # Call the method
            rest_client.request(
                "GET",
                "https://api.example.com/endpoint",
            )

            # Verify the request was made with the SSL certificate
            mock_request.assert_called_once()
            assert mock_request.call_args[1]["verify"] == "/path/to/ca.crt"
            assert mock_request.call_args[1]["cert"] == ("/path/to/cert.crt", "/path/to/key.key")


class TestRESTResponse:
    """Tests for the RESTResponse class."""

    @pytest.fixture
    def response(self):
        """Create a RESTResponse instance for testing."""
        # Create a mock requests.Response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json", "X-Request-ID": "123"}
        mock_response.content = b'{"success": true}'

        # Create a RESTResponse instance
        return RESTResponse(mock_response)

    def test_init(self, response):
        """Test initialization of RESTResponse."""
        assert response.status == 200
        assert response.reason is None
        assert response.data == b'{"success": true}'
        assert response.headers == {"Content-Type": "application/json", "X-Request-ID": "123"}

    def test_getheaders(self, response):
        """Test getheaders method."""
        headers = response.getheaders()
        assert headers == {"Content-Type": "application/json", "X-Request-ID": "123"}

    def test_getheader(self, response):
        """Test getheader method."""
        # Test with existing header
        header = response.getheader("Content-Type")
        assert header == "application/json"

        # Test with non-existing header
        header = response.getheader("X-Non-Existent")
        assert header is None

        # Test with non-existing header and default value
        header = response.getheader("X-Non-Existent", "default")
        assert header == "default"

    def test_read(self, response):
        """Test read method."""
        data = response.read()
        assert data == b'{"success": true}'

