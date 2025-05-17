from unittest.mock import patch

import pytest
import rich_click as click

from codegen.cli.auth.login import login_routine
from codegen.cli.errors import AuthError


class TestLoginRoutine:
    def test_login_with_provided_token(self):
        """Test login with a token provided as an argument."""
        test_token = "test_token_123"

        with patch("codegen.cli.auth.token_manager.TokenManager") as mock_token_manager_class:
            mock_token_manager = mock_token_manager_class.return_value

            # Call login_routine with a token
            result = login_routine(token=test_token)

            # Verify the token was authenticated
            mock_token_manager.authenticate_token.assert_called_once_with(test_token)
            assert result == test_token

    def test_login_with_env_token(self):
        """Test login with a token from environment variable."""
        env_token = "env_token_456"

        with patch("codegen.cli.auth.token_manager.TokenManager") as mock_token_manager_class:
            mock_token_manager = mock_token_manager_class.return_value

            with patch("codegen.cli.env.global_env.global_env") as mock_global_env:
                mock_global_env.CODEGEN_USER_ACCESS_TOKEN = env_token

                # Call login_routine without a token argument
                result = login_routine()

                # Verify the environment token was used
                mock_token_manager.authenticate_token.assert_called_once_with(env_token)
                assert result == env_token

    def test_login_with_browser_flow(self):
        """Test login with browser flow when no token is provided."""
        browser_token = "browser_token_789"

        with patch("codegen.cli.auth.token_manager.TokenManager") as mock_token_manager_class:
            mock_token_manager = mock_token_manager_class.return_value

            with patch("codegen.cli.env.global_env.global_env") as mock_global_env:
                mock_global_env.CODEGEN_USER_ACCESS_TOKEN = None

                with patch("webbrowser.open_new") as mock_open_browser:
                    with patch("rich_click.prompt", return_value=browser_token) as mock_prompt:
                        # Call login_routine without a token
                        result = login_routine()

                        # Verify the browser was opened
                        mock_open_browser.assert_called_once()

                        # Verify the user was prompted for a token
                        mock_prompt.assert_called_once()

                        # Verify the token was authenticated
                        mock_token_manager.authenticate_token.assert_called_once_with(browser_token)
                        assert result == browser_token

    def test_login_with_empty_browser_token(self):
        """Test login fails when user provides empty token in browser flow."""
        with patch("codegen.cli.auth.token_manager.TokenManager") as mock_token_manager_class:
            with patch("codegen.cli.env.global_env.global_env") as mock_global_env:
                mock_global_env.CODEGEN_USER_ACCESS_TOKEN = None

                with patch("webbrowser.open_new"):
                    with patch("rich_click.prompt", return_value=""):
                        # Should raise a ClickException
                        with pytest.raises(click.ClickException, match="Token must be provided"):
                            login_routine()

                        # Verify the token was not authenticated
                        mock_token_manager_class.return_value.authenticate_token.assert_not_called()

    def test_login_with_invalid_token(self):
        """Test login fails with invalid token."""
        invalid_token = "invalid_token"

        with patch("codegen.cli.auth.token_manager.TokenManager") as mock_token_manager_class:
            mock_token_manager = mock_token_manager_class.return_value
            mock_token_manager.authenticate_token.side_effect = AuthError("Invalid token")

            # Should raise a ClickException
            with pytest.raises(click.ClickException, match="Error: Invalid token"):
                login_routine(token=invalid_token)
