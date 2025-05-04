"""
Error classes for the codegen-on-oss package.

This module defines custom error classes used throughout the package.
"""

class CodegenError(Exception):
    """Base class for all codegen-on-oss errors."""
    pass


class RepositoryError(CodegenError):
    """Error raised when there is an issue with a repository."""
    pass


class SnapshotError(CodegenError):
    """Error raised when there is an issue with a codebase snapshot."""
    pass


class AnalysisError(CodegenError):
    """Error raised when there is an issue with code analysis."""
    pass


class ValidationError(CodegenError):
    """Error raised when there is an issue with code validation."""
    pass


class ComparisonError(CodegenError):
    """Error raised when there is an issue with code comparison."""
    pass


class PRAnalysisError(CodegenError):
    """Error raised when there is an issue with PR analysis."""
    pass


class WSLServerError(CodegenError):
    """Error raised when there is an issue with the WSL server."""
    pass


class WSLClientError(CodegenError):
    """Error raised when there is an issue with the WSL client."""
    pass


class WSLDeploymentError(CodegenError):
    """Error raised when there is an issue with WSL deployment."""
    pass


class IntegrationError(CodegenError):
    """Error raised when there is an issue with external integrations."""
    pass


class TimeoutError(CodegenError):
    """Error raised when an operation times out."""
    pass


class RateLimitError(CodegenError):
    """Error raised when a rate limit is exceeded."""
    pass


class AuthenticationError(CodegenError):
    """Error raised when there is an authentication issue."""
    pass


class ConfigurationError(CodegenError):
    """Error raised when there is a configuration issue."""
    pass

