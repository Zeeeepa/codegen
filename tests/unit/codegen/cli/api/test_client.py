import json
from unittest.mock import patch, MagicMock

import pytest
import requests
from pydantic import BaseModel

from codegen.cli.api.client import RestAPI
from codegen.cli.api.schemas import RunCodemodOutput, DocsResponse, AskExpertResponse
from codegen.cli.errors import InvalidTokenError, ServerError
from codegen.cli.utils.codemods import Codemod
from codegen.cli.utils.function_finder import DecoratedFunction


class MockResponse:
    """Mock response for requests."""
    
    def __init__(self, status_code, json_data=None, text=""):
        self.status_code = status_code
        self._json_data = json_data
        self.text = text
    
    def json(self):
        return self._json_data
    
    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP Error: {self.status_code}")


@pytest.fixture
def mock_session():
    """Mocks the requests.Session."""
    with patch("codegen.cli.api.client.requests.Session") as mock:
        session_instance = MagicMock()
        mock.return_value = session_instance
        yield session_instance


@pytest.fixture
def api_client():
    """Creates a RestAPI client with a mock token."""
    return RestAPI(auth_token="mock-token")


def test_get_headers(api_client):
    """Test the _get_headers method."""
    headers = api_client._get_headers()
    assert headers == {"Authorization": "Bearer mock-token"}


def test_make_request_success(api_client, mock_session):
    """Test successful API request."""
    # Create a mock input and output model
    class MockInput(BaseModel):
        field: str
    
    class MockOutput(BaseModel):
        result: str
    
    # Set up the mock response
    mock_response = MockResponse(200, json_data={"result": "success"})
    mock_session.request.return_value = mock_response
    
    # Make the request
    input_data = MockInput(field="test")
    result = api_client._make_request("GET", "https://api.example.com/endpoint", input_data, MockOutput)
    
    # Check the result
    assert isinstance(result, MockOutput)
    assert result.result == "success"
    
    # Check that the request was made with the correct arguments
    mock_session.request.assert_called_once_with(
        "GET",
        "https://api.example.com/endpoint",
        json={"field": "test"},
        headers={"Authorization": "Bearer mock-token"},
    )


def test_make_request_unauthorized(api_client, mock_session):
    """Test API request with 401 unauthorized response."""
    # Set up the mock response
    mock_response = MockResponse(401, json_data={"detail": "Unauthorized"})
    mock_session.request.return_value = mock_response
    
    # Make the request and check that it raises the expected exception
    with pytest.raises(InvalidTokenError, match="Invalid or expired authentication token"):
        api_client._make_request("GET", "https://api.example.com/endpoint", None, BaseModel)


def test_make_request_server_error(api_client, mock_session):
    """Test API request with 500 server error response."""
    # Set up the mock response
    mock_response = MockResponse(500, json_data={"detail": "Internal Server Error"})
    mock_session.request.return_value = mock_response
    
    # Make the request and check that it raises the expected exception
    with pytest.raises(ServerError, match="The server encountered an error while processing your request"):
        api_client._make_request("GET", "https://api.example.com/endpoint", None, BaseModel)


def test_make_request_other_error(api_client, mock_session):
    """Test API request with other error response."""
    # Set up the mock response
    mock_response = MockResponse(400, json_data={"detail": "Bad Request"})
    mock_session.request.return_value = mock_response
    
    # Make the request and check that it raises the expected exception
    with pytest.raises(ServerError, match="Error \\(400\\): Bad Request"):
        api_client._make_request("GET", "https://api.example.com/endpoint", None, BaseModel)


def test_make_request_network_error(api_client, mock_session):
    """Test API request with network error."""
    # Set up the mock to raise a RequestException
    mock_session.request.side_effect = requests.RequestException("Network error")
    
    # Make the request and check that it raises the expected exception
    with pytest.raises(ServerError, match="Network error: Network error"):
        api_client._make_request("GET", "https://api.example.com/endpoint", None, BaseModel)


def test_run_with_function(api_client, mock_session, mock_codegen_session):
    """Test the run method with a DecoratedFunction."""
    # Create a mock function
    mock_function = MagicMock(spec=DecoratedFunction)
    mock_function.name = "test_function"
    mock_function.source = "def test_function():\n    pass"
    
    # Set up the mock response
    mock_response = MockResponse(200, json_data={"result": "success"})
    mock_session.request.return_value = mock_response
    
    # Mock the output model validation
    with patch.object(RunCodemodOutput, "model_validate", return_value=RunCodemodOutput(result="success")):
        # Call the run method
        result = api_client.run(mock_function)
        
        # Check the result
        assert isinstance(result, RunCodemodOutput)
        assert result.result == "success"


def test_run_with_codemod(api_client, mock_session, mock_codegen_session):
    """Test the run method with a Codemod."""
    # Create a mock codemod
    mock_codemod = MagicMock(spec=Codemod)
    mock_codemod.name = "test_codemod"
    mock_codemod.get_current_source.return_value = "def test_codemod():\n    pass"
    
    # Set up the mock response
    mock_response = MockResponse(200, json_data={"result": "success"})
    mock_session.request.return_value = mock_response
    
    # Mock the output model validation
    with patch.object(RunCodemodOutput, "model_validate", return_value=RunCodemodOutput(result="success")):
        # Call the run method
        result = api_client.run(mock_codemod)
        
        # Check the result
        assert isinstance(result, RunCodemodOutput)
        assert result.result == "success"


def test_get_docs(api_client, mock_session, mock_codegen_session):
    """Test the get_docs method."""
    # Set up the mock response
    mock_response = MockResponse(200, json_data={"docs": "documentation"})
    mock_session.request.return_value = mock_response
    
    # Mock the output model validation
    with patch.object(DocsResponse, "model_validate", return_value=DocsResponse(docs="documentation")):
        # Call the get_docs method
        result = api_client.get_docs()
        
        # Check the result
        assert isinstance(result, DocsResponse)
        assert result.docs == "documentation"


def test_ask_expert(api_client, mock_session):
    """Test the ask_expert method."""
    # Set up the mock response
    mock_response = MockResponse(200, json_data={"answer": "expert answer"})
    mock_session.request.return_value = mock_response
    
    # Mock the output model validation
    with patch.object(AskExpertResponse, "model_validate", return_value=AskExpertResponse(answer="expert answer")):
        # Call the ask_expert method
        result = api_client.ask_expert("What is codegen?")
        
        # Check the result
        assert isinstance(result, AskExpertResponse)
        assert result.answer == "expert answer"

