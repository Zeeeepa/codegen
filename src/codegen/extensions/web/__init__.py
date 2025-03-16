"""Web browsing functionality."""

from codegen.extensions.web.web_client import WebClient
from codegen.extensions.web.web import (
    web_browse_page_tool,
    web_search_tool,
    web_extract_images_tool,
)

__all__ = [
    "WebClient",
    "web_browse_page_tool",
    "web_search_tool",
    "web_extract_images_tool",
]