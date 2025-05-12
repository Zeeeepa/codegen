"""Utility functions for documentation generation."""

import re
import textwrap
from typing import Optional


def sanitize_docstring_for_markdown(docstring: Optional[str]) -> str:
    """Sanitize the docstring for MDX.
    
    Args:
        docstring: The docstring to sanitize.
        
    Returns:
        The sanitized docstring.
    """
    if docstring is None:
        return ""
    docstring_lines = docstring.splitlines()
    if len(docstring_lines) > 1:
        docstring_lines[1:] = [textwrap.dedent(line) for line in docstring_lines[1:]]
    docstring = "\n".join(docstring_lines)
    if docstring.startswith('"""'):
        docstring = docstring[3:]
    if docstring.endswith('"""'):
        docstring = docstring[:-3]
    return docstring


def sanitize_mdx_mintlify_description(content: str) -> str:
    """Mintlify description field needs to have string escaped, which content doesn't need.
    
    Args:
        content: The content to sanitize.
        
    Returns:
        The sanitized content.
    """
    content = sanitize_docstring_for_markdown(content)
    # make sure all `< />` components are properly escaped with a `` inline-block
    # if the string already has the single-quote then this is a no-op
    content = re.sub(r"(?<!`)(<[^>]+>)(?!`)", r"`\1`", content)

    # escape double quote characters
    if re.search(r'\\"', content):
        return content  # No-op if already escaped
    return re.sub(r'(")', r"\\\1", content)


def sanitize_html_for_mdx(html_string: str) -> str:
    """Sanitize HTML string for MDX by escaping double quotes in attribute values.

    Args:
        html_string: The input HTML string to sanitize

    Returns:
        The sanitized HTML string with escaped quotes
    """
    # Replace double quotes with &quot; but only in HTML attributes
    return re.sub(r'"', "&quot;", html_string)


def extract_class_description(docstring: str) -> str:
    """Extract the class description from a docstring, excluding the attributes section.

    Args:
        docstring: The class docstring to parse

    Returns:
        The class description with whitespace normalized
    """
    if not docstring:
        return ""

    # Split by "Attributes:" and take only the first part
    parts = docstring.split("Attributes:")
    description = parts[0]

    # Normalize whitespace
    lines = [line.strip() for line in description.strip().splitlines()]
    return " ".join(filter(None, lines))
