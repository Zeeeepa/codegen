"""Tests for the ExternalLogger protocol in the agents module."""

from typing import Protocol

import pytest

from codegen.agents.data import UserMessage
from codegen.agents.loggers import ExternalLogger


class TestExternalLogger:
    """Tests for the ExternalLogger protocol."""

    def test_external_logger_protocol(self):
        """Test that a class implementing the ExternalLogger protocol works correctly."""
        # Create a concrete implementation of the ExternalLogger protocol
        class ConcreteLogger:
            def __init__(self):
                self.logs = []

            def log(self, data):
                self.logs.append(data)

        # Create an instance of the concrete logger
        logger = ConcreteLogger()
        
        # Check that it can be used as an ExternalLogger
        assert isinstance(logger, ExternalLogger)
        
        # Test logging a message
        message = UserMessage(content="Test message")
        logger.log(message)
        
        # Check that the message was logged
        assert len(logger.logs) == 1
        assert logger.logs[0] == message

    def test_external_logger_with_multiple_message_types(self):
        """Test that an ExternalLogger can handle different message types."""
        # Create a concrete implementation of the ExternalLogger protocol
        class ConcreteLogger:
            def __init__(self):
                self.logs = []

            def log(self, data):
                self.logs.append(data)

        # Create an instance of the concrete logger
        logger = ConcreteLogger()
        
        # Test logging different message types
        from codegen.agents.data import (
            UserMessage,
            SystemMessageData,
            AssistantMessage,
            ToolMessageData,
            FunctionMessageData,
            UnknownMessage,
        )
        
        messages = [
            UserMessage(content="User message"),
            SystemMessageData(content="System message"),
            AssistantMessage(content="Assistant message"),
            ToolMessageData(content="Tool message"),
            FunctionMessageData(content="Function message"),
            UnknownMessage(content="Unknown message"),
        ]
        
        # Log each message
        for message in messages:
            logger.log(message)
        
        # Check that all messages were logged
        assert len(logger.logs) == len(messages)
        for i, message in enumerate(messages):
            assert logger.logs[i] == message

