"""
Error classes for the codegen-on-oss package.

This module defines custom error classes used throughout the codegen-on-oss package.
"""

class CodegenOnOssError(Exception):
    """Base class for all codegen-on-oss errors."""
    pass


class AnalysisError(CodegenOnOssError):
    """Error raised when analysis fails."""
    pass


class FileNotFoundError(CodegenOnOssError):
    """Error raised when a file is not found."""
    pass


class SymbolNotFoundError(CodegenOnOssError):
    """Error raised when a symbol is not found."""
    pass


class InvalidInputError(CodegenOnOssError):
    """Error raised when input validation fails."""
    
    def __init__(self, message: str, parameter_name: str | None = None):
        """
        Initialize an InvalidInputError.
        
        Args:
            message: The error message
            parameter_name: The name of the parameter that failed validation
        """
        self.parameter_name = parameter_name
        super().__init__(message)
