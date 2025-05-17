from unittest.mock import MagicMock, patch

import click
import pytest

from codegen.cli.auth.decorators import requires_auth
from codegen.cli.auth.session import CodegenSession
from codegen.cli.errors import AuthError


class TestRequiresAuth:
    def test_requires_auth_with_valid_session_and_token(self):
        """Test the requires_auth decorator with a valid session and token."""
        # Create a mock function to decorate
        mock_func = MagicMock()
        decorated_func = requires_auth(mock_func)

        # Mock session and token
        mock_session = MagicMock(spec=CodegenSession)

        with patch("codegen.cli.auth.session.CodegenSession.from_active_session", return_value=mock_session):
            with patch("codegen.cli.auth.decorators.get_current_token", return_value="valid_token"):
                with patch("codegen.cli.auth.decorators.TokenManager") as mock_token_manager_class:
                    mock_token_manager = mock_token_manager_class.return_value

                    # Call the decorated function
                    decorated_func(arg1="test", arg2=123)

                    # Verify the token was authenticated
                    mock_token_manager.authenticate_token.assert_called_once_with("valid_token")

                    # Verify the original function was called with the session and original args
                    mock_func.assert_called_once_with(arg1="test", arg2=123, session=mock_session)

    def test_requires_auth_with_no_session(self):
        """Test the requires_auth decorator with no active session."""
        # Create a mock function to decorate
        mock_func = MagicMock()
        decorated_func = requires_auth(mock_func)

        with patch("codegen.cli.auth.session.CodegenSession.from_active_session", return_value=None):
            with patch("codegen.cli.auth.decorators.pretty_print_error") as mock_print_error:
                # Should raise a click.Abort
                with pytest.raises(click.Abort):
                    decorated_func()

                # Verify the error message was printed
                mock_print_error.assert_called_once()
                assert "no active session" in mock_print_error.call_args[0][0].lower()

    def test_requires_auth_with_no_token(self):
        """Test the requires_auth decorator with no token."""
        # Create a mock function to decorate
        mock_func = MagicMock()
        decorated_func = requires_auth(mock_func)

        # Mock session but no token
        mock_session = MagicMock(spec=CodegenSession)

        with patch("codegen.cli.auth.session.CodegenSession.from_active_session", return_value=mock_session):
            with patch("codegen.cli.auth.decorators.get_current_token", return_value=None):
                with patch("codegen.cli.auth.decorators.login_routine") as mock_login_routine:
                    mock_login_routine.return_value = "new_token"

                    # Call the decorated function
                    decorated_func(arg1="test")

                    # Verify login_routine was called
                    mock_login_routine.assert_called_once()

                    # Verify the original function was called with the session and original args
                    mock_func.assert_called_once_with(arg1="test", session=mock_session)

    def test_requires_auth_with_invalid_token(self):
        """Test the requires_auth decorator with an invalid token."""
        # Create a mock function to decorate
        mock_func = MagicMock()
        decorated_func = requires_auth(mock_func)

        # Mock session but invalid token
        mock_session = MagicMock(spec=CodegenSession)

        with patch("codegen.cli.auth.session.CodegenSession.from_active_session", return_value=mock_session):
            with patch("codegen.cli.auth.decorators.get_current_token", return_value="invalid_token"):
                with patch("codegen.cli.auth.decorators.TokenManager") as mock_token_manager_class:
                    mock_token_manager = mock_token_manager_class.return_value
                    mock_token_manager.authenticate_token.side_effect = AuthError("Invalid token")

                    with patch("codegen.cli.auth.decorators.login_routine") as mock_login_routine:
                        mock_login_routine.return_value = "new_token"

                        # Call the decorated function
                        decorated_func()

                        # Verify authenticate_token was called with the invalid token
                        mock_token_manager.authenticate_token.assert_called_once_with("invalid_token")

                        # Verify login_routine was called
                        mock_login_routine.assert_called_once()

                        # Verify the original function was called with the session
                        mock_func.assert_called_once_with(session=mock_session)
