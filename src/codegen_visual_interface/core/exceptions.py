"""
Exception Classes for Codegen Visual Interface

This module defines all custom exceptions used throughout the visual interface,
providing clear error handling and debugging capabilities.
"""

from typing import Optional, Dict, Any


class CodegenVisualInterfaceError(Exception):
    """Base exception for all visual interface errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        """Initialize the exception."""
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "details": self.details
        }


class APIIntegrationError(CodegenVisualInterfaceError):
    """Exception for API integration failures."""
    
    def __init__(self, message: str, api_name: str, status_code: Optional[int] = None, 
                 response_data: Optional[Dict[str, Any]] = None):
        """Initialize API integration error."""
        details = {
            "api_name": api_name,
            "status_code": status_code,
            "response_data": response_data
        }
        super().__init__(message, error_code="API_INTEGRATION_ERROR", details=details)
        self.api_name = api_name
        self.status_code = status_code
        self.response_data = response_data


class OrchestrationError(CodegenVisualInterfaceError):
    """Exception for orchestration failures."""
    
    def __init__(self, message: str, orchestrator: str, task_id: Optional[str] = None,
                 workflow_id: Optional[str] = None):
        """Initialize orchestration error."""
        details = {
            "orchestrator": orchestrator,
            "task_id": task_id,
            "workflow_id": workflow_id
        }
        super().__init__(message, error_code="ORCHESTRATION_ERROR", details=details)
        self.orchestrator = orchestrator
        self.task_id = task_id
        self.workflow_id = workflow_id


class TraceRetrievalError(CodegenVisualInterfaceError):
    """Exception for trace retrieval failures."""
    
    def __init__(self, message: str, trace_id: Optional[str] = None, 
                 agent_run_id: Optional[str] = None):
        """Initialize trace retrieval error."""
        details = {
            "trace_id": trace_id,
            "agent_run_id": agent_run_id
        }
        super().__init__(message, error_code="TRACE_RETRIEVAL_ERROR", details=details)
        self.trace_id = trace_id
        self.agent_run_id = agent_run_id


class ConfigurationError(CodegenVisualInterfaceError):
    """Exception for configuration errors."""
    
    def __init__(self, message: str, config_section: Optional[str] = None,
                 config_key: Optional[str] = None):
        """Initialize configuration error."""
        details = {
            "config_section": config_section,
            "config_key": config_key
        }
        super().__init__(message, error_code="CONFIGURATION_ERROR", details=details)
        self.config_section = config_section
        self.config_key = config_key


class AuthenticationError(CodegenVisualInterfaceError):
    """Exception for authentication failures."""
    
    def __init__(self, message: str, auth_type: str = "api_token"):
        """Initialize authentication error."""
        details = {"auth_type": auth_type}
        super().__init__(message, error_code="AUTHENTICATION_ERROR", details=details)
        self.auth_type = auth_type


class AuthorizationError(CodegenVisualInterfaceError):
    """Exception for authorization failures."""
    
    def __init__(self, message: str, resource: Optional[str] = None, 
                 required_permission: Optional[str] = None):
        """Initialize authorization error."""
        details = {
            "resource": resource,
            "required_permission": required_permission
        }
        super().__init__(message, error_code="AUTHORIZATION_ERROR", details=details)
        self.resource = resource
        self.required_permission = required_permission


class ValidationError(CodegenVisualInterfaceError):
    """Exception for validation failures."""
    
    def __init__(self, message: str, field: Optional[str] = None, 
                 validation_type: Optional[str] = None):
        """Initialize validation error."""
        details = {
            "field": field,
            "validation_type": validation_type
        }
        super().__init__(message, error_code="VALIDATION_ERROR", details=details)
        self.field = field
        self.validation_type = validation_type


class WorkflowError(CodegenVisualInterfaceError):
    """Exception for workflow execution errors."""
    
    def __init__(self, message: str, workflow_id: str, step_id: Optional[str] = None,
                 step_name: Optional[str] = None):
        """Initialize workflow error."""
        details = {
            "workflow_id": workflow_id,
            "step_id": step_id,
            "step_name": step_name
        }
        super().__init__(message, error_code="WORKFLOW_ERROR", details=details)
        self.workflow_id = workflow_id
        self.step_id = step_id
        self.step_name = step_name


class AgentError(CodegenVisualInterfaceError):
    """Exception for agent-related errors."""
    
    def __init__(self, message: str, agent_type: str, agent_id: Optional[str] = None,
                 operation: Optional[str] = None):
        """Initialize agent error."""
        details = {
            "agent_type": agent_type,
            "agent_id": agent_id,
            "operation": operation
        }
        super().__init__(message, error_code="AGENT_ERROR", details=details)
        self.agent_type = agent_type
        self.agent_id = agent_id
        self.operation = operation


class SandboxError(CodegenVisualInterfaceError):
    """Exception for sandbox-related errors."""
    
    def __init__(self, message: str, sandbox_id: Optional[str] = None,
                 operation: Optional[str] = None):
        """Initialize sandbox error."""
        details = {
            "sandbox_id": sandbox_id,
            "operation": operation
        }
        super().__init__(message, error_code="SANDBOX_ERROR", details=details)
        self.sandbox_id = sandbox_id
        self.operation = operation


class StorageError(CodegenVisualInterfaceError):
    """Exception for storage-related errors."""
    
    def __init__(self, message: str, storage_type: str, operation: Optional[str] = None,
                 key: Optional[str] = None):
        """Initialize storage error."""
        details = {
            "storage_type": storage_type,
            "operation": operation,
            "key": key
        }
        super().__init__(message, error_code="STORAGE_ERROR", details=details)
        self.storage_type = storage_type
        self.operation = operation
        self.key = key


class UIError(CodegenVisualInterfaceError):
    """Exception for UI-related errors."""
    
    def __init__(self, message: str, component: Optional[str] = None,
                 operation: Optional[str] = None):
        """Initialize UI error."""
        details = {
            "component": component,
            "operation": operation
        }
        super().__init__(message, error_code="UI_ERROR", details=details)
        self.component = component
        self.operation = operation


class ChatError(CodegenVisualInterfaceError):
    """Exception for chat interface errors."""
    
    def __init__(self, message: str, chat_session_id: Optional[str] = None,
                 message_id: Optional[str] = None):
        """Initialize chat error."""
        details = {
            "chat_session_id": chat_session_id,
            "message_id": message_id
        }
        super().__init__(message, error_code="CHAT_ERROR", details=details)
        self.chat_session_id = chat_session_id
        self.message_id = message_id


class ProjectError(CodegenVisualInterfaceError):
    """Exception for project management errors."""
    
    def __init__(self, message: str, project_id: Optional[str] = None,
                 operation: Optional[str] = None):
        """Initialize project error."""
        details = {
            "project_id": project_id,
            "operation": operation
        }
        super().__init__(message, error_code="PROJECT_ERROR", details=details)
        self.project_id = project_id
        self.operation = operation


class RateLimitError(CodegenVisualInterfaceError):
    """Exception for rate limiting errors."""
    
    def __init__(self, message: str, api_name: str, limit: int, window: int,
                 retry_after: Optional[int] = None):
        """Initialize rate limit error."""
        details = {
            "api_name": api_name,
            "limit": limit,
            "window": window,
            "retry_after": retry_after
        }
        super().__init__(message, error_code="RATE_LIMIT_ERROR", details=details)
        self.api_name = api_name
        self.limit = limit
        self.window = window
        self.retry_after = retry_after


class TimeoutError(CodegenVisualInterfaceError):
    """Exception for timeout errors."""
    
    def __init__(self, message: str, operation: str, timeout_seconds: int):
        """Initialize timeout error."""
        details = {
            "operation": operation,
            "timeout_seconds": timeout_seconds
        }
        super().__init__(message, error_code="TIMEOUT_ERROR", details=details)
        self.operation = operation
        self.timeout_seconds = timeout_seconds


class NetworkError(CodegenVisualInterfaceError):
    """Exception for network-related errors."""
    
    def __init__(self, message: str, endpoint: Optional[str] = None,
                 network_error_type: Optional[str] = None):
        """Initialize network error."""
        details = {
            "endpoint": endpoint,
            "network_error_type": network_error_type
        }
        super().__init__(message, error_code="NETWORK_ERROR", details=details)
        self.endpoint = endpoint
        self.network_error_type = network_error_type


class ResourceNotFoundError(CodegenVisualInterfaceError):
    """Exception for resource not found errors."""
    
    def __init__(self, message: str, resource_type: str, resource_id: str):
        """Initialize resource not found error."""
        details = {
            "resource_type": resource_type,
            "resource_id": resource_id
        }
        super().__init__(message, error_code="RESOURCE_NOT_FOUND_ERROR", details=details)
        self.resource_type = resource_type
        self.resource_id = resource_id


class InternalError(CodegenVisualInterfaceError):
    """Exception for internal system errors."""
    
    def __init__(self, message: str, component: Optional[str] = None,
                 original_exception: Optional[Exception] = None):
        """Initialize internal error."""
        details = {
            "component": component,
            "original_exception": str(original_exception) if original_exception else None
        }
        super().__init__(message, error_code="INTERNAL_ERROR", details=details)
        self.component = component
        self.original_exception = original_exception


# Exception mapping for easy lookup
EXCEPTION_MAP = {
    "API_INTEGRATION_ERROR": APIIntegrationError,
    "ORCHESTRATION_ERROR": OrchestrationError,
    "TRACE_RETRIEVAL_ERROR": TraceRetrievalError,
    "CONFIGURATION_ERROR": ConfigurationError,
    "AUTHENTICATION_ERROR": AuthenticationError,
    "AUTHORIZATION_ERROR": AuthorizationError,
    "VALIDATION_ERROR": ValidationError,
    "WORKFLOW_ERROR": WorkflowError,
    "AGENT_ERROR": AgentError,
    "SANDBOX_ERROR": SandboxError,
    "STORAGE_ERROR": StorageError,
    "UI_ERROR": UIError,
    "CHAT_ERROR": ChatError,
    "PROJECT_ERROR": ProjectError,
    "RATE_LIMIT_ERROR": RateLimitError,
    "TIMEOUT_ERROR": TimeoutError,
    "NETWORK_ERROR": NetworkError,
    "RESOURCE_NOT_FOUND_ERROR": ResourceNotFoundError,
    "INTERNAL_ERROR": InternalError
}


def create_exception_from_dict(error_data: Dict[str, Any]) -> CodegenVisualInterfaceError:
    """Create an exception from dictionary data."""
    error_type = error_data.get("error_type", "CodegenVisualInterfaceError")
    message = error_data.get("message", "Unknown error")
    error_code = error_data.get("error_code")
    details = error_data.get("details", {})
    
    exception_class = EXCEPTION_MAP.get(error_code, CodegenVisualInterfaceError)
    
    try:
        # Try to create the specific exception with its parameters
        if error_code == "API_INTEGRATION_ERROR":
            return exception_class(
                message, 
                details.get("api_name", "unknown"),
                details.get("status_code"),
                details.get("response_data")
            )
        elif error_code == "ORCHESTRATION_ERROR":
            return exception_class(
                message,
                details.get("orchestrator", "unknown"),
                details.get("task_id"),
                details.get("workflow_id")
            )
        elif error_code == "TRACE_RETRIEVAL_ERROR":
            return exception_class(
                message,
                details.get("trace_id"),
                details.get("agent_run_id")
            )
        else:
            # For other exceptions, create with basic parameters
            return exception_class(message, error_code=error_code, details=details)
    
    except Exception:
        # Fallback to base exception if specific creation fails
        return CodegenVisualInterfaceError(message, error_code=error_code, details=details)
