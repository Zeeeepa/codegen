class ParseRunError(Exception):
    """Base exception for parsing errors in codegen-on-oss."""
    def __init__(self, message="An error occurred during parsing", details=None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class PostValidationError(ParseRunError):
    """Exception raised when post-validation fails."""
    def __init__(self, validation_status, message=None, details=None):
        self.validation_status = validation_status
        message = message or f"Post-validation failed with status: {validation_status}"
        super().__init__(message, details)


class RepositoryError(ParseRunError):
    """Exception raised for repository-related errors."""
    pass


class InvalidInputError(Exception):
    """Exception raised when input validation fails."""
    def __init__(self, message="Invalid input provided", param_name=None, details=None):
        self.param_name = param_name
        self.details = details or {}
        if param_name:
            message = f"{message}: {param_name}"
        super().__init__(message)


class AnalysisError(Exception):
    """Base exception for analysis errors in codegen-on-oss."""
    def __init__(self, message="An error occurred during analysis", details=None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class CodebaseNotFoundError(AnalysisError):
    """Exception raised when a codebase is not found."""
    pass


class SymbolNotFoundError(AnalysisError):
    """Exception raised when a symbol is not found."""
    pass


class FileNotFoundError(AnalysisError):
    """Exception raised when a file is not found."""
    pass
