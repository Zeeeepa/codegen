#!/usr/bin/env python3
"""
Codebase AI Module

This module provides AI-powered code analysis and generation capabilities,
including system prompt generation, context generation for AI models,
and guidelines for generating and modifying code.
"""

import logging
from typing import Any, TypeVar

try:
    from codegen.sdk.core.file import File
    from codegen.sdk.core.interfaces.editable import Editable
except ImportError:
    # Define fallback classes for when SDK is not available
    class Editable:
        @property
        def extended_source(self) -> str:
            return ""

    class File:
        @property
        def source(self) -> str:
            return ""


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Type variable for context
T = TypeVar("T", bound=str | Editable | File | list[Any] | dict[str, Any])


def generate_system_prompt(
    target: Editable | None = None, context: T | None = None
) -> str:
    """
    Generate a system prompt for AI-powered code analysis and generation.

    Args:
        target: The target code to analyze or modify
        context: Additional context for the analysis

    Returns:
        A system prompt string for AI models
    """
    # Start with a base prompt
    prompt = """
You are an expert software engineer with deep knowledge of code analysis, refactoring, and development best practices.
You have been tasked with analyzing and potentially modifying code to improve its quality, readability, and maintainability.

Your task is to carefully analyze the provided code and context, and then provide thoughtful insights and recommendations.
You should consider:

1. Code structure and organization
2. Potential bugs or edge cases
3. Performance optimizations
4. Adherence to best practices and design patterns
5. Documentation and code comments
6. Test coverage and quality

When suggesting modifications:
- Be specific about what should be changed and why
- Provide concrete examples of how the code could be improved
- Consider the impact of your changes on the rest of the codebase
- Maintain the original functionality unless explicitly instructed otherwise
- Respect the existing coding style and conventions

Guidelines for generating code:
- Write clean, maintainable code that follows best practices
- Include appropriate error handling and edge case management
- Add clear comments explaining complex logic or design decisions
- Ensure new code integrates well with existing code
- Follow the principle of least surprise - make code behave as expected

Guidelines for modifying existing code:
- Make minimal changes to achieve the desired outcome
- Preserve existing behavior unless explicitly instructed to change it
- Maintain or improve test coverage
- Document significant changes and the reasoning behind them
- Consider backward compatibility and potential side effects

Guidelines for handling docstrings and comments:
- Preserve existing docstrings and update them to reflect changes
- Maintain the existing docstring style and format
- Add or update comments for complex or non-obvious code
- Remove comments that are redundant or no longer accurate

REMEMBER: When giving the final answer, you must use the set_answer tool to provide your response.
"""

    # Add target-specific instructions if a target is provided
    if target:
        prompt += """
You have been provided with a specific target to analyze or modify. Focus your analysis on this target,
but consider its interactions with the rest of the codebase as needed.
"""

    # Add context-specific instructions if context is provided
    if context:
        prompt += """
You have been provided with additional context to help with your analysis. Use this context to better
understand the code, its purpose, and how it fits into the larger system.
"""

    return prompt


def generate_flag_system_prompt(
    target: Editable, context: T | None = None
) -> str:
    """
    Generate a system prompt for determining whether to flag a code element.

    Args:
        target: The target code to analyze
        context: Additional context for the analysis

    Returns:
        A system prompt string for AI models
    """
    prompt = """
You are an expert code reviewer with deep knowledge of code quality, security, and best practices.
Your task is to analyze the provided code and determine whether it should be flagged for review or modification.

You should flag code that:
1. Contains potential bugs or logical errors
2. Has security vulnerabilities
3. Violates best practices or coding standards
4. Is overly complex or difficult to maintain
5. Lacks proper error handling or edge case management
6. Has performance issues or inefficiencies
7. Contains duplicated logic that could be refactored
8. Has poor or missing documentation
9. Lacks appropriate test coverage

When analyzing the code, consider:
- The code's purpose and functionality
- Its interactions with other parts of the system
- The potential impact of issues on the overall system
- The severity and priority of any identified issues

Your response should be a clear YES or NO, followed by a brief explanation of your reasoning.
If you flag the code (YES), provide specific details about the issues you've identified and
suggestions for how they could be addressed.

REMEMBER: Use the flag_code tool to provide your final answer.
"""

    # Add context-specific instructions if context is provided
    if context:
        prompt += """
You have been provided with additional context to help with your analysis. Use this context to better
understand the code, its purpose, and how it fits into the larger system.
"""

    return prompt


def generate_context(context: T | None = None) -> str:
    """
    Generate a context string for AI models.

    Args:
        context: The context to format

    Returns:
        A formatted context string
    """
    if context is None:
        return ""

    if isinstance(context, str):
        return context

    if hasattr(context, "extended_source") and callable(getattr(context, "extended_source", None)):
        return context.extended_source

    if hasattr(context, "source") and callable(getattr(context, "source", None)):
        return context.source

    if isinstance(context, list):
        return "\n\n".join(str(item) for item in context)

    if isinstance(context, dict):
        return "\n\n".join(f"{key}: {value}" for key, value in context.items())

    return str(context)


def generate_tools() -> list[dict[str, Any]]:
    """
    Generate a list of tools for AI models.

    Returns:
        A list of tool definitions
    """
    return [
        {
            "name": "set_answer",
            "description": "Set the final answer for the analysis",
            "parameters": {
                "type": "object",
                "properties": {
                    "answer": {
                        "type": "string",
                        "description": "The final answer for the analysis",
                    }
                },
                "required": ["answer"],
            },
        },
        {
            "name": "analyze_code",
            "description": "Analyze a specific part of the code",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "The code to analyze",
                    },
                    "focus": {
                        "type": "string",
                        "description": "The specific aspect to focus on (e.g., 'bugs', 'performance', 'style')",
                    },
                },
                "required": ["code"],
            },
        },
        {
            "name": "suggest_modification",
            "description": "Suggest a modification to the code",
            "parameters": {
                "type": "object",
                "properties": {
                    "original_code": {
                        "type": "string",
                        "description": "The original code",
                    },
                    "modified_code": {
                        "type": "string",
                        "description": "The modified code",
                    },
                    "explanation": {
                        "type": "string",
                        "description": "Explanation of the modification",
                    },
                },
                "required": ["original_code", "modified_code", "explanation"],
            },
        },
    ]


def generate_flag_tools() -> list[dict[str, Any]]:
    """
    Generate a list of tools for flagging code elements.

    Returns:
        A list of tool definitions
    """
    return [
        {
            "name": "flag_code",
            "description": "Flag a code element for review or modification",
            "parameters": {
                "type": "object",
                "properties": {
                    "flag": {
                        "type": "boolean",
                        "description": "Whether to flag the code (true) or not (false)",
                    },
                    "reason": {
                        "type": "string",
                        "description": "The reason for flagging or not flagging the code",
                    },
                    "suggestions": {
                        "type": "string",
                        "description": "Suggestions for addressing the issues (if flagged)",
                    },
                },
                "required": ["flag", "reason"],
            },
        },
        {
            "name": "analyze_issue",
            "description": "Analyze a specific issue in the code",
            "parameters": {
                "type": "object",
                "properties": {
                    "issue_type": {
                        "type": "string",
                        "description": "The type of issue (e.g., 'bug', 'security', 'performance')",
                    },
                    "severity": {
                        "type": "string",
                        "description": "The severity of the issue (e.g., 'low', 'medium', 'high')",
                    },
                    "description": {
                        "type": "string",
                        "description": "Description of the issue",
                    },
                    "location": {
                        "type": "string",
                        "description": "The location of the issue in the code",
                    },
                },
                "required": ["issue_type", "severity", "description"],
            },
        },
    ]


class CodebaseAI:
    """
    A class for AI-powered code analysis and generation.
    """

    def __init__(self):
        """
        Initialize a CodebaseAI instance.
        """
        self.logger = logging.getLogger(__name__)

    def generate_system_prompt(
        self, target: Editable | None = None, context: T | None = None
    ) -> str:
        """
        Generate a system prompt for AI-powered code analysis and generation.

        Args:
            target: The target code to analyze or modify
            context: Additional context for the analysis

        Returns:
            A system prompt string for AI models
        """
        return generate_system_prompt(target, context)

    def generate_flag_system_prompt(
        self, target: Editable, context: T | None = None
    ) -> str:
        """
        Generate a system prompt for determining whether to flag a code element.

        Args:
            target: The target code to analyze
            context: Additional context for the analysis

        Returns:
            A system prompt string for AI models
        """
        return generate_flag_system_prompt(target, context)

    def generate_context(self, context: T | None = None) -> str:
        """
        Generate a context string for AI models.

        Args:
            context: The context to format

        Returns:
            A formatted context string
        """
        return generate_context(context)

    def generate_tools(self) -> list[dict[str, Any]]:
        """
        Generate a list of tools for AI models.

        Returns:
            A list of tool definitions
        """
        return generate_tools()

    def generate_flag_tools(self) -> list[dict[str, Any]]:
        """
        Generate a list of tools for flagging code elements.

        Returns:
            A list of tool definitions
        """
        return generate_flag_tools()

