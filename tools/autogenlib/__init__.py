"""Automatic code generation library using Z.ai and OpenAI."""

import sys
from ._finder import AutoLibFinder
from ._exception_handler import setup_exception_handler

# Import z.ai client functionality
try:
    from ._z_ai_client import get_z_ai_client, is_zai_available, test_zai_connection
    ZAI_SUPPORT = True
except ImportError:
    ZAI_SUPPORT = False


_sentinel = object()


def init(desc=_sentinel, enable_exception_handler=None, enable_caching=None):
    """Initialize autogenlib with a description of the functionality needed.

    Args:
        desc (str): A description of the library you want to generate.
        enable_exception_handler (bool): Whether to enable the global exception handler
            that sends exceptions to LLM for fix suggestions. Default is True.
        enable_caching (bool): Whether to enable caching of generated code. Default is False.
    """
    # Update the global description
    from . import _state

    if desc is not _sentinel:
        _state.description = desc
    if enable_exception_handler is not None:
        _state.exception_handler_enabled = enable_exception_handler
    if enable_caching is not None:
        _state.caching_enabled = enable_caching

    # Set up exception handler if enabled
    if _state.exception_handler_enabled:
        from ._exception_handler import setup_exception_handler

        setup_exception_handler()

    # Add our custom finder to sys.meta_path if it's not already there
    for finder in sys.meta_path:
        if isinstance(finder, AutoLibFinder):
            return
    sys.meta_path.insert(0, AutoLibFinder())


def set_exception_handler(enabled=True):
    """Enable or disable the exception handler.

    Args:
        enabled (bool): Whether to enable the exception handler. Default is True.
    """
    from . import _state

    _state.exception_handler_enabled = enabled


def set_caching(enabled=True):
    """Enable or disable caching.

    Args:
        enabled (bool): Whether to enable caching. Default is True.
    """
    from . import _state

    _state.caching_enabled = enabled


def get_ai_client():
    """Get the configured AI client (Z.ai preferred, OpenAI fallback)."""
    if ZAI_SUPPORT and is_zai_available():
        return get_z_ai_client()
    else:
        # Fallback to OpenAI or return None
        try:
            import openai
            import os
            api_key = os.environ.get("OPENAI_API_KEY")
            if api_key:
                return openai.OpenAI(api_key=api_key)
        except ImportError:
            pass
    return None


def check_ai_availability():
    """Check which AI services are available and configured."""
    status = {
        "zai_available": False,
        "openai_available": False,
        "recommended": None,
        "active": None
    }
    
    if ZAI_SUPPORT:
        zai_status = test_zai_connection()
        status["zai_available"] = zai_status["status"] == "success"
        if status["zai_available"]:
            status["active"] = "z.ai"
            status["recommended"] = "z.ai"
    
    # Check OpenAI
    try:
        import openai
        import os
        if os.environ.get("OPENAI_API_KEY"):
            status["openai_available"] = True
            if not status["active"]:
                status["active"] = "openai"
            if not status["recommended"]:
                status["recommended"] = "openai"
    except ImportError:
        pass
    
    return status


# Add z.ai functions to exports if available
if ZAI_SUPPORT:
    __all__ = ["init", "set_exception_handler", "setup_exception_handler", "set_caching", 
               "get_ai_client", "check_ai_availability", "get_z_ai_client", "is_zai_available"]
else:
    __all__ = ["init", "set_exception_handler", "setup_exception_handler", "set_caching",
               "get_ai_client", "check_ai_availability"]

init()
