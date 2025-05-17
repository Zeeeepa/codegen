"""Unit tests for the OpenAPI client configuration."""

import os
from unittest.mock import patch

import pytest

from codegen.agents.client.openapi_client.configuration import Configuration


class TestConfiguration:
    """Tests for the Configuration class."""

    def test_init_default(self):
        """Test initialization with default values."""
        config = Configuration()
        assert config.host == "https://api.codegen.sh"
        assert config.api_key == {}
        assert config.api_key_prefix == {}
        assert config.username is None
        assert config.password is None
        assert config.discard_unknown_keys is False
        assert config.client_side_validation is True
        assert config.server_index is None
        assert config.server_variables == {}
        assert config.server_operation_index is None
        assert config.server_operation_variables == {}
        assert config.ssl_ca_cert is None
        assert config.cert_file is None
        assert config.key_file is None
        assert config.assert_hostname is None
        assert config.connection_pool_maxsize is 100
        assert config.proxy is None
        assert config.proxy_headers is None
        assert config.safe_chars_for_path_param == ""
        assert config.retries is None
        assert config.socket_options is None
        assert config.logger_file is None
        assert config.logger_format is None
        assert config.logger_file_level is None
        assert config.debug is False
        assert config.return_http_data_only is True
        assert config.preload_content is True
        assert config.request_timeout is None
        assert config.check_input_type is True
        assert config.check_return_type is True
        assert config.http_user_agent is None

    def test_get_host_settings(self):
        """Test get_host_settings method."""
        config = Configuration()
        host_settings = config.get_host_settings()
        assert len(host_settings) == 1
        assert host_settings[0]["url"] == "https://api.codegen.sh"
        assert host_settings[0]["description"] == "No description provided"
        assert host_settings[0]["variables"] == {}

    def test_get_host_from_settings(self):
        """Test get_host_from_settings method."""
        config = Configuration()
        host = config.get_host_from_settings(0)
        assert host == "https://api.codegen.sh"

    def test_get_api_key_with_prefix(self):
        """Test get_api_key_with_prefix method."""
        config = Configuration()
        config.api_key["api_key"] = "test_key"
        config.api_key_prefix["api_key"] = "Bearer"

        # Test with prefix
        result = config.get_api_key_with_prefix("api_key")
        assert result == "Bearer test_key"

        # Test without prefix
        config.api_key_prefix = {}
        result = config.get_api_key_with_prefix("api_key")
        assert result == "test_key"

        # Test with missing key
        result = config.get_api_key_with_prefix("missing_key")
        assert result == ""

    def test_auth_settings(self):
        """Test auth_settings method."""
        config = Configuration()
        config.api_key["Authorization"] = "test_token"
        config.api_key_prefix["Authorization"] = "Bearer"

        auth_settings = config.auth_settings()
        assert "Authorization" in auth_settings
        assert auth_settings["Authorization"]["in"] == "header"
        assert auth_settings["Authorization"]["key"] == "Authorization"
        assert auth_settings["Authorization"]["value"] == "Bearer test_token"
        assert auth_settings["Authorization"]["type"] == "api_key"

    def test_to_debug_report(self):
        """Test to_debug_report method."""
        config = Configuration()
        debug_report = config.to_debug_report()
        assert "Python" in debug_report
        assert "Host" in debug_report
        assert "https://api.codegen.sh" in debug_report

    @patch.dict(os.environ, {"CODEGEN_API_KEY": "env_test_token"})
    def test_get_default_with_env_var(self):
        """Test get_default method with environment variable."""
        config = Configuration.get_default()
        assert config.api_key["Authorization"] == "env_test_token"
        assert config.api_key_prefix["Authorization"] == "Bearer"

    def test_get_default_without_env_var(self):
        """Test get_default method without environment variable."""
        with patch.dict(os.environ, {}, clear=True):
            config = Configuration.get_default()
            assert "Authorization" not in config.api_key
            assert config.api_key_prefix["Authorization"] == "Bearer"

