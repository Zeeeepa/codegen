"""
Error Handler for WSL2 Server

This module provides centralized error handling for the WSL2 server,
including structured error responses, logging, and error tracking.
"""

import logging
import traceback
from typing import Any, Dict, List, Optional, Tuple, Union

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class CodegenError(Exception):
    """Base exception class for Codegen errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a new CodegenError.

        Args:
            message: Error message
            status_code: HTTP status code
            details: Additional error details
        """
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(CodegenError):
    """Exception raised for validation errors."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a new ValidationError.

        Args:
            message: Error message
            details: Additional error details
        """
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class AuthenticationError(CodegenError):
    """Exception raised for authentication errors."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a new AuthenticationError.

        Args:
            message: Error message
            details: Additional error details
        """
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details,
        )


class NotFoundError(CodegenError):
    """Exception raised for not found errors."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a new NotFoundError.

        Args:
            message: Error message
            details: Additional error details
        """
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class ServerError(CodegenError):
    """Exception raised for server errors."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a new ServerError.

        Args:
            message: Error message
            details: Additional error details
        """
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )


class ErrorHandler:
    """Error handler for the WSL2 server."""

    @staticmethod
    async def handle_exception(request: Request, exc: Exception) -> JSONResponse:
        """
        Handle exceptions and return appropriate responses.

        Args:
            request: FastAPI request
            exc: Exception to handle

        Returns:
            JSONResponse with error details
        """
        if isinstance(exc, CodegenError):
            # Handle Codegen errors
            logger.error(
                f"Codegen error: {exc.message}",
                extra={
                    "status_code": exc.status_code,
                    "details": exc.details,
                    "path": request.url.path,
                    "method": request.method,
                },
            )
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "error": exc.message,
                    "details": exc.details,
                    "status_code": exc.status_code,
                },
            )
        elif isinstance(exc, HTTPException):
            # Handle FastAPI HTTP exceptions
            logger.error(
                f"HTTP exception: {exc.detail}",
                extra={
                    "status_code": exc.status_code,
                    "path": request.url.path,
                    "method": request.method,
                },
            )
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "error": str(exc.detail),
                    "status_code": exc.status_code,
                },
            )
        else:
            # Handle unexpected exceptions
            logger.error(
                f"Unexpected error: {str(exc)}",
                extra={
                    "traceback": traceback.format_exc(),
                    "path": request.url.path,
                    "method": request.method,
                },
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "An unexpected error occurred",
                    "details": {"message": str(exc)},
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                },
            )

    @staticmethod
    def log_error(
        message: str,
        exc: Optional[Exception] = None,
        level: str = "error",
        **kwargs: Any,
    ) -> None:
        """
        Log an error with additional context.

        Args:
            message: Error message
            exc: Optional exception
            level: Log level
            **kwargs: Additional logging context
        """
        log_data = {
            "message": message,
            **kwargs,
        }

        if exc:
            log_data["exception"] = str(exc)
            log_data["traceback"] = traceback.format_exc()

        if level == "debug":
            logger.debug(message, extra=log_data)
        elif level == "info":
            logger.info(message, extra=log_data)
        elif level == "warning":
            logger.warning(message, extra=log_data)
        elif level == "error":
            logger.error(message, extra=log_data)
        elif level == "critical":
            logger.critical(message, extra=log_data)
        else:
            logger.error(message, extra=log_data)


def setup_error_handler(app):
    """
    Set up the error handler for a FastAPI application.

    Args:
        app: FastAPI application
    """
    app.add_exception_handler(Exception, ErrorHandler.handle_exception)
    app.add_exception_handler(CodegenError, ErrorHandler.handle_exception)
    app.add_exception_handler(HTTPException, ErrorHandler.handle_exception)

