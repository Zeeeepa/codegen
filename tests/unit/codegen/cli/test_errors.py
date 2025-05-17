import pytest

from codegen.cli.errors import InvalidTokenError, ServerError


def test_invalid_token_error():
    """Test InvalidTokenError."""
    error = InvalidTokenError("Invalid token")
    assert str(error) == "Invalid token"
    assert isinstance(error, Exception)


def test_server_error():
    """Test ServerError."""
    error = ServerError("Server error")
    assert str(error) == "Server error"
    assert isinstance(error, Exception)

