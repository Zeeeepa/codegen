from unittest.mock import patch

import pytest
from click.testing import CliRunner

from codegen.cli.cli import main


def test_main_help(runner):
    """Test main CLI help command."""
    result = runner.invoke(main, ["--help"])
    
    # Check that the command executed successfully
    assert result.exit_code == 0
    
    # Check that the help text is in the output
    assert "Codegen CLI - Transform your code with AI." in result.output
    
    # Check that all commands are listed in the output
    commands = [
        "agent", "init", "logout", "login", "run", "profile", "create",
        "expert", "list", "deploy", "style-debug", "run-on-pr", "notebook",
        "reset", "update", "config", "lsp", "serve", "start"
    ]
    for command in commands:
        assert command in result.output


def test_main_version(runner):
    """Test main CLI version command."""
    result = runner.invoke(main, ["--version"])
    
    # Check that the command executed successfully
    assert result.exit_code == 0
    
    # Check that the version is in the output
    assert "version" in result.output.lower()


def test_main_no_args(runner):
    """Test main CLI with no arguments."""
    result = runner.invoke(main)
    
    # Check that the command executed successfully
    assert result.exit_code == 0
    
    # Check that the help text is in the output
    assert "Usage:" in result.output

