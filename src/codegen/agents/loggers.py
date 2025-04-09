from typing import Protocol


from codegen.agents.data import AgentRunMessage


# Define the interface for ExternalLogger
class ExternalLogger(Protocol):
    """Protocol for external loggers that can be used to log agent runs."""

    def log_message(self, message: AgentRunMessage) -> None:
        """Log a message from an agent run."""
        ...
