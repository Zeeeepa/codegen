"""
Base controller for MCP.

This module defines the base controller class that all other controllers inherit from.
"""

from typing import Any, Dict, Optional


class BaseController:
    """Base controller class for all MCP controllers."""

    def __init__(self, codebase=None):
        """Initialize the base controller.

        Args:
            codebase: The codebase to operate on.
        """
        self.codebase = codebase

    def validate_params(self, params: Dict[str, Any], required: list) -> bool:
        """Validate that required parameters are present.

        Args:
            params (Dict[str, Any]): Parameters to validate.
            required (list): List of required parameter names.

        Returns:
            bool: True if all required parameters are present, False otherwise.
        """
        return all(param in params for param in required)

    def handle_error(self, message: str, error_code: int = 400) -> Dict[str, Any]:
        """Handle an error by returning an error response.

        Args:
            message (str): Error message.
            error_code (int, optional): HTTP error code. Defaults to 400.

        Returns:
            Dict[str, Any]: Error response.
        """
        return {
            "success": False,
            "error": {
                "message": message,
                "code": error_code,
            },
        }

    def handle_success(self, data: Any = None) -> Dict[str, Any]:
        """Handle a successful operation by returning a success response.

        Args:
            data (Any, optional): Response data. Defaults to None.

        Returns:
            Dict[str, Any]: Success response.
        """
        response = {"success": True}
        if data is not None:
            response["data"] = data
        return response
