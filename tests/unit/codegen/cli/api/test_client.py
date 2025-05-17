"""Unit tests for the CLI API client."""

import json
from unittest.mock import MagicMock, patch

import pytest
import requests
from pydantic import BaseModel

from codegen.cli.api.client import RestAPI
from codegen.cli.api.schemas import (
    RunCodemodInput,
    RunCodemodOutput,
    DocsResponse,
    AskExpertResponse,
    CreateResponse,
    IdentifyResponse,
    DeployResponse,
    LookupOutput,
    RunOnPRResponse,
    PRLookupResponse,
    ImproveCodemodResponse,
)
from codegen.cli.errors import InvalidTokenError, ServerError
from codegen.shared.enums.programming_language import ProgrammingLanguage


class TestRestAPI:
    """Tests for the RestAPI class."""

    @pytest.fixture
    def rest_api(self):
        """Create a RestAPI instance with a mock token."""
        return RestAPI(auth_token="test_token")

    @pytest.fixture
    def mock_session(self):
        """Create a mock session for testing."""
        with patch("codegen.cli.api.client.requests.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            yield mock_session

    def test_init(self):
        """Test initialization of RestAPI."""
        api = RestAPI(auth_token="test_token")
        assert api.auth_token == "test_token"

    def test_get_headers(self, rest_api):
        """Test _get_headers method."""
        headers = rest_api._get_headers()
        assert headers == {"Authorization": "Bearer test_token"}

    def test_make_request_success(self, rest_api, mock_session):
        """Test _make_request method with a successful response."""
        # Create a mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "web_link": "https://example.com"}
        mock_session.request.return_value = mock_response

        # Create a mock input and output model
        class MockInput(BaseModel):
            name: str

        # Call the method
        result = rest_api._make_request(
            "POST",
            "https://api.example.com/endpoint",
            MockInput(name="test"),
            RunCodemodOutput,
        )

        # Verify the result
        assert isinstance(result, RunCodemodOutput)
        assert result.success is True
        assert result.web_link == "https://example.com"

        # Verify the request was made correctly
        mock_session.request.assert_called_once_with(
            "POST",
            "https://api.example.com/endpoint",
            json={"name": "test"},
            headers={"Authorization": "Bearer test_token"},
        )

    def test_make_request_auth_error(self, rest_api, mock_session):
        """Test _make_request method with an authentication error."""
        # Create a mock response
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_session.request.return_value = mock_response

        # Create a mock input model
        class MockInput(BaseModel):
            name: str

        # Call the method and expect an exception
        with pytest.raises(InvalidTokenError, match="Invalid or expired authentication token"):
            rest_api._make_request(
                "POST",
                "https://api.example.com/endpoint",
                MockInput(name="test"),
                RunCodemodOutput,
            )

    def test_make_request_server_error(self, rest_api, mock_session):
        """Test _make_request method with a server error."""
        # Create a mock response
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_session.request.return_value = mock_response

        # Create a mock input model
        class MockInput(BaseModel):
            name: str

        # Call the method and expect an exception
        with pytest.raises(ServerError, match="The server encountered an error while processing your request"):
            rest_api._make_request(
                "POST",
                "https://api.example.com/endpoint",
                MockInput(name="test"),
                RunCodemodOutput,
            )

    def test_make_request_other_error(self, rest_api, mock_session):
        """Test _make_request method with another error."""
        # Create a mock response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"detail": "Bad request"}
        mock_session.request.return_value = mock_response

        # Create a mock input model
        class MockInput(BaseModel):
            name: str

        # Call the method and expect an exception
        with pytest.raises(ServerError, match="Error \\(400\\): Bad request"):
            rest_api._make_request(
                "POST",
                "https://api.example.com/endpoint",
                MockInput(name="test"),
                RunCodemodOutput,
            )

    def test_make_request_network_error(self, rest_api, mock_session):
        """Test _make_request method with a network error."""
        # Make the request raise an exception
        mock_session.request.side_effect = requests.RequestException("Network error")

        # Create a mock input model
        class MockInput(BaseModel):
            name: str

        # Call the method and expect an exception
        with pytest.raises(ServerError, match="Network error: Network error"):
            rest_api._make_request(
                "POST",
                "https://api.example.com/endpoint",
                MockInput(name="test"),
                RunCodemodOutput,
            )

    def test_make_request_invalid_response(self, rest_api, mock_session):
        """Test _make_request method with an invalid response format."""
        # Create a mock response with invalid JSON
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"invalid_field": "value"}  # Missing required fields
        mock_session.request.return_value = mock_response

        # Create a mock input model
        class MockInput(BaseModel):
            name: str

        # Call the method and expect an exception
        with pytest.raises(ServerError, match="Invalid response format:"):
            rest_api._make_request(
                "POST",
                "https://api.example.com/endpoint",
                MockInput(name="test"),
                RunCodemodOutput,
            )

    @patch("codegen.cli.api.client.CodegenSession")
    @patch("codegen.cli.api.client.convert_to_ui")
    def test_run(self, mock_convert_to_ui, mock_session, rest_api):
        """Test run method."""
        # Mock dependencies
        mock_function = MagicMock()
        mock_function.name = "test_function"
        mock_function.source = "def test_function(): pass"
        mock_function.get_current_source = MagicMock(return_value="def test_function(): pass")

        mock_session_instance = MagicMock()
        mock_session_instance.config.repository.full_name = "test/repo"
        mock_session.from_active_session.return_value = mock_session_instance

        mock_convert_to_ui.return_value = "converted_source"

        # Mock the _make_request method
        rest_api._make_request = MagicMock()
        rest_api._make_request.return_value = RunCodemodOutput(success=True, web_link="https://example.com")

        # Call the method
        result = rest_api.run(mock_function)

        # Verify the result
        assert result == RunCodemodOutput(success=True, web_link="https://example.com")

        # Verify the _make_request call
        rest_api._make_request.assert_called_once()
        args, kwargs = rest_api._make_request.call_args
        assert args[0] == "POST"
        assert "input" in args[2].model_dump()
        assert args[2].input.codemod_name == "test_function"
        assert args[2].input.repo_full_name == "test/repo"
        assert args[2].input.codemod_source == "converted_source"
        assert args[3] == RunCodemodOutput

    @patch("codegen.cli.api.client.CodegenSession")
    def test_get_docs(self, mock_session, rest_api):
        """Test get_docs method."""
        # Mock dependencies
        mock_session_instance = MagicMock()
        mock_session_instance.config.repository.full_name = "test/repo"
        mock_session.from_active_session.return_value = mock_session_instance

        # Mock the _make_request method
        rest_api._make_request = MagicMock()
        rest_api._make_request.return_value = DocsResponse(success=True, docs="Test docs")

        # Call the method
        result = rest_api.get_docs()

        # Verify the result
        assert result == DocsResponse(success=True, docs="Test docs")

        # Verify the _make_request call
        rest_api._make_request.assert_called_once()
        args, kwargs = rest_api._make_request.call_args
        assert args[0] == "GET"
        assert args[2].docs_input.repo_full_name == "test/repo"
        assert args[3] == DocsResponse

    def test_ask_expert(self, rest_api):
        """Test ask_expert method."""
        # Mock the _make_request method
        rest_api._make_request = MagicMock()
        rest_api._make_request.return_value = AskExpertResponse(success=True, response="Expert response")

        # Call the method
        result = rest_api.ask_expert("How do I use the API?")

        # Verify the result
        assert result == AskExpertResponse(success=True, response="Expert response")

        # Verify the _make_request call
        rest_api._make_request.assert_called_once()
        args, kwargs = rest_api._make_request.call_args
        assert args[0] == "GET"
        assert args[2].input.query == "How do I use the API?"
        assert args[3] == AskExpertResponse

    @patch("codegen.cli.api.client.CodegenSession")
    def test_create(self, mock_session, rest_api):
        """Test create method."""
        # Mock dependencies
        mock_session_instance = MagicMock()
        mock_session_instance.config.repository.language = "python"
        mock_session.from_active_session.return_value = mock_session_instance

        # Mock the _make_request method
        rest_api._make_request = MagicMock()
        rest_api._make_request.return_value = CreateResponse(success=True, codemod="def test(): pass")

        # Call the method
        result = rest_api.create("test_codemod", "Create a test codemod")

        # Verify the result
        assert result == CreateResponse(success=True, codemod="def test(): pass")

        # Verify the _make_request call
        rest_api._make_request.assert_called_once()
        args, kwargs = rest_api._make_request.call_args
        assert args[0] == "GET"
        assert args[2].input.name == "test_codemod"
        assert args[2].input.query == "Create a test codemod"
        assert args[2].input.language == ProgrammingLanguage.PYTHON
        assert args[3] == CreateResponse

    def test_identify(self, rest_api):
        """Test identify method."""
        # Mock the _make_request method
        rest_api._make_request = MagicMock()
        rest_api._make_request.return_value = IdentifyResponse(success=True, codemod_name="test_codemod")

        # Call the method
        result = rest_api.identify()

        # Verify the result
        assert result == IdentifyResponse(success=True, codemod_name="test_codemod")

        # Verify the _make_request call
        rest_api._make_request.assert_called_once()
        args, kwargs = rest_api._make_request.call_args
        assert args[0] == "POST"
        assert args[1] == "https://codegen-sh--cli-identify.modal.run"
        assert args[2] is None
        assert args[3] == IdentifyResponse

    @patch("codegen.cli.api.client.CodegenSession")
    def test_deploy(self, mock_session, rest_api):
        """Test deploy method."""
        # Mock dependencies
        mock_session_instance = MagicMock()
        mock_session_instance.config.repository.full_name = "test/repo"
        mock_session.from_active_session.return_value = mock_session_instance

        # Mock the _make_request method
        rest_api._make_request = MagicMock()
        rest_api._make_request.return_value = DeployResponse(success=True, codemod_id=123)

        # Call the method
        result = rest_api.deploy(
            codemod_name="test_codemod",
            codemod_source="def test(): pass",
            lint_mode=True,
            lint_user_whitelist=["user1", "user2"],
            message="Test message",
            arguments_schema={"arg1": "string"},
        )

        # Verify the result
        assert result == DeployResponse(success=True, codemod_id=123)

        # Verify the _make_request call
        rest_api._make_request.assert_called_once()
        args, kwargs = rest_api._make_request.call_args
        assert args[0] == "POST"
        assert args[2].input.codemod_name == "test_codemod"
        assert args[2].input.codemod_source == "def test(): pass"
        assert args[2].input.repo_full_name == "test/repo"
        assert args[2].input.lint_mode is True
        assert args[2].input.lint_user_whitelist == ["user1", "user2"]
        assert args[2].input.message == "Test message"
        assert args[2].input.arguments_schema == {"arg1": "string"}
        assert args[3] == DeployResponse

    @patch("codegen.cli.api.client.CodegenSession")
    def test_lookup(self, mock_session, rest_api):
        """Test lookup method."""
        # Mock dependencies
        mock_session_instance = MagicMock()
        mock_session_instance.config.repository.full_name = "test/repo"
        mock_session.from_active_session.return_value = mock_session_instance

        # Mock the _make_request method
        rest_api._make_request = MagicMock()
        rest_api._make_request.return_value = LookupOutput(success=True, codemod_source="def test(): pass")

        # Call the method
        result = rest_api.lookup("test_codemod")

        # Verify the result
        assert result == LookupOutput(success=True, codemod_source="def test(): pass")

        # Verify the _make_request call
        rest_api._make_request.assert_called_once()
        args, kwargs = rest_api._make_request.call_args
        assert args[0] == "GET"
        assert args[2].input.codemod_name == "test_codemod"
        assert args[2].input.repo_full_name == "test/repo"
        assert args[3] == LookupOutput

    def test_run_on_pr(self, rest_api):
        """Test run_on_pr method."""
        # Mock the _make_request method
        rest_api._make_request = MagicMock()
        rest_api._make_request.return_value = RunOnPRResponse(success=True, message="PR processed")

        # Call the method
        result = rest_api.run_on_pr("test_codemod", "test/repo", 123, "python")

        # Verify the result
        assert result == RunOnPRResponse(success=True, message="PR processed")

        # Verify the _make_request call
        rest_api._make_request.assert_called_once()
        args, kwargs = rest_api._make_request.call_args
        assert args[0] == "POST"
        assert args[2].input.codemod_name == "test_codemod"
        assert args[2].input.repo_full_name == "test/repo"
        assert args[2].input.github_pr_number == 123
        assert args[2].input.language == "python"
        assert args[3] == RunOnPRResponse

    def test_lookup_pr(self, rest_api):
        """Test lookup_pr method."""
        # Mock the _make_request method
        rest_api._make_request = MagicMock()
        rest_api._make_request.return_value = PRLookupResponse(success=True, pr_data={"number": 123})

        # Call the method
        result = rest_api.lookup_pr("test/repo", 123)

        # Verify the result
        assert result == PRLookupResponse(success=True, pr_data={"number": 123})

        # Verify the _make_request call
        rest_api._make_request.assert_called_once()
        args, kwargs = rest_api._make_request.call_args
        assert args[0] == "GET"
        assert args[2].input.repo_full_name == "test/repo"
        assert args[2].input.github_pr_number == 123
        assert args[3] == PRLookupResponse

    def test_improve_codemod(self, rest_api):
        """Test improve_codemod method."""
        # Mock the _make_request method
        rest_api._make_request = MagicMock()
        rest_api._make_request.return_value = ImproveCodemodResponse(success=True, improved_codemod="def improved(): pass")

        # Call the method
        result = rest_api.improve_codemod(
            codemod="def test(): pass",
            task="Improve the codemod",
            concerns=["performance", "readability"],
            context={"file": "test.py"},
            language=ProgrammingLanguage.PYTHON,
        )

        # Verify the result
        assert result == ImproveCodemodResponse(success=True, improved_codemod="def improved(): pass")

        # Verify the _make_request call
        rest_api._make_request.assert_called_once()
        args, kwargs = rest_api._make_request.call_args
        assert args[0] == "GET"
        assert args[2].input.codemod == "def test(): pass"
        assert args[2].input.task == "Improve the codemod"
        assert args[2].input.concerns == ["performance", "readability"]
        assert args[2].input.context == {"file": "test.py"}
        assert args[2].input.language == ProgrammingLanguage.PYTHON
        assert args[3] == ImproveCodemodResponse

