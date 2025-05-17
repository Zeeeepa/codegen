from unittest.mock import patch

import pytest

from codegen.cli.api.schemas import CodemodRunType
from codegen.cli.commands.run.main import run_command


@pytest.fixture
def mock_run_local():
    """Mocks the run_local function."""
    with patch("codegen.cli.commands.run.main.run_local") as mock:
        yield mock


@pytest.fixture
def mock_run_cloud():
    """Mocks the run_cloud function."""
    with patch("codegen.cli.commands.run.main.run_cloud") as mock:
        yield mock


@pytest.fixture
def mock_run_daemon():
    """Mocks the run_daemon function."""
    with patch("codegen.cli.commands.run.main.run_daemon") as mock:
        yield mock


def test_run_command_local(runner, mock_run_local, mock_run_cloud, mock_run_daemon):
    """Test run command with local mode."""
    result = runner.invoke(run_command, ["--local", "test_codemod"])

    # Check that the command executed successfully
    assert result.exit_code == 0

    # Check that run_local was called with the correct arguments
    mock_run_local.assert_called_once()
    args, kwargs = mock_run_local.call_args
    assert args[0] == "test_codemod"
    assert kwargs["run_type"] == CodemodRunType.DIFF

    # Check that run_cloud and run_daemon were not called
    mock_run_cloud.assert_not_called()
    mock_run_daemon.assert_not_called()


def test_run_command_cloud(runner, mock_run_local, mock_run_cloud, mock_run_daemon):
    """Test run command with cloud mode."""
    result = runner.invoke(run_command, ["--cloud", "test_codemod"])

    # Check that the command executed successfully
    assert result.exit_code == 0

    # Check that run_cloud was called with the correct arguments
    mock_run_cloud.assert_called_once()
    args, kwargs = mock_run_cloud.call_args
    assert args[0] == "test_codemod"
    assert kwargs["run_type"] == CodemodRunType.DIFF

    # Check that run_local and run_daemon were not called
    mock_run_local.assert_not_called()
    mock_run_daemon.assert_not_called()


def test_run_command_daemon(runner, mock_run_local, mock_run_cloud, mock_run_daemon):
    """Test run command with daemon mode."""
    result = runner.invoke(run_command, ["--daemon", "test_codemod"])

    # Check that the command executed successfully
    assert result.exit_code == 0

    # Check that run_daemon was called with the correct arguments
    mock_run_daemon.assert_called_once()
    args, kwargs = mock_run_daemon.call_args
    assert args[0] == "test_codemod"
    assert kwargs["run_type"] == CodemodRunType.DIFF

    # Check that run_local and run_cloud were not called
    mock_run_local.assert_not_called()
    mock_run_cloud.assert_not_called()


def test_run_command_pr_mode(runner, mock_run_local, mock_run_cloud, mock_run_daemon):
    """Test run command with PR mode."""
    result = runner.invoke(run_command, ["--local", "--pr", "test_codemod"])

    # Check that the command executed successfully
    assert result.exit_code == 0

    # Check that run_local was called with the correct arguments
    mock_run_local.assert_called_once()
    args, kwargs = mock_run_local.call_args
    assert args[0] == "test_codemod"
    assert kwargs["run_type"] == CodemodRunType.PR

    # Check that run_cloud and run_daemon were not called
    mock_run_cloud.assert_not_called()
    mock_run_daemon.assert_not_called()


def test_run_command_with_context(runner, mock_run_local, mock_run_cloud, mock_run_daemon):
    """Test run command with context variables."""
    result = runner.invoke(run_command, ["--local", "--context", "key1=value1", "--context", "key2=value2", "test_codemod"])

    # Check that the command executed successfully
    assert result.exit_code == 0

    # Check that run_local was called with the correct arguments
    mock_run_local.assert_called_once()
    args, kwargs = mock_run_local.call_args
    assert args[0] == "test_codemod"
    assert kwargs["template_context"] == {"key1": "value1", "key2": "value2"}

    # Check that run_cloud and run_daemon were not called
    mock_run_cloud.assert_not_called()
    mock_run_daemon.assert_not_called()


def test_run_command_no_mode_specified(runner, mock_run_local, mock_run_cloud, mock_run_daemon):
    """Test run command with no mode specified (should default to local)."""
    result = runner.invoke(run_command, ["test_codemod"])

    # Check that the command executed successfully
    assert result.exit_code == 0

    # Check that run_local was called with the correct arguments
    mock_run_local.assert_called_once()
    args, kwargs = mock_run_local.call_args
    assert args[0] == "test_codemod"

    # Check that run_cloud and run_daemon were not called
    mock_run_cloud.assert_not_called()
    mock_run_daemon.assert_not_called()


def test_run_command_multiple_modes(runner, mock_run_local, mock_run_cloud, mock_run_daemon):
    """Test run command with multiple modes specified (should fail)."""
    result = runner.invoke(run_command, ["--local", "--cloud", "test_codemod"])

    # Check that the command failed
    assert result.exit_code != 0

    # Check that none of the run functions were called
    mock_run_local.assert_not_called()
    mock_run_cloud.assert_not_called()
    mock_run_daemon.assert_not_called()
