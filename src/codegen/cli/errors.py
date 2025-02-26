# TODO: refactor this file out


class AuthError(Exception):
    """Error raised if authed user cannot be established."""

    pass


class InvalidTokenError(AuthError):
    """Error raised if the token is invalid."""

    pass


class CodegenError(Exception):
    """Base class for Codegen-specific errors."""

    pass


class ServerError(CodegenError):
    """Error raised when the server encounters an error."""

    pass
