"""Tests for the global environment module."""

import os
from unittest.mock import patch

import pytest

from codegen.cli.env.global_env import global_env


def test_global_env_defaults():
    """Test global_env default values."""
    # Check that the default values are set correctly
    assert global_env.DEBUG is False
    assert global_env.VERBOSE is False
    assert global_env.QUIET is False


def test_global_env_debug_from_env():
    """Test setting global_env.DEBUG from environment variable."""
    # Set the environment variable
    with patch.dict(os.environ, {"CODEGEN_DEBUG": "1"}):
        # Reload the module
        from importlib import reload
        from codegen.cli.env import global_env as env_module
        reload(env_module)
        
        # Check that DEBUG is True
        assert env_module.global_env.DEBUG is True
        
    # Reset the module
    reload(env_module)


def test_global_env_verbose_from_env():
    """Test setting global_env.VERBOSE from environment variable."""
    # Set the environment variable
    with patch.dict(os.environ, {"CODEGEN_VERBOSE": "1"}):
        # Reload the module
        from importlib import reload
        from codegen.cli.env import global_env as env_module
        reload(env_module)
        
        # Check that VERBOSE is True
        assert env_module.global_env.VERBOSE is True
        
    # Reset the module
    reload(env_module)


def test_global_env_quiet_from_env():
    """Test setting global_env.QUIET from environment variable."""
    # Set the environment variable
    with patch.dict(os.environ, {"CODEGEN_QUIET": "1"}):
        # Reload the module
        from importlib import reload
        from codegen.cli.env import global_env as env_module
        reload(env_module)
        
        # Check that QUIET is True
        assert env_module.global_env.QUIET is True
        
    # Reset the module
    reload(env_module)

