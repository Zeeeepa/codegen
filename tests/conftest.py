import os
import asyncio
import logging
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional

import pytest

from src.codegen.sdk.core.unified_config import UnifiedConfiguration, ConfigurationManager
from src.codegen.sdk.core.unified_api import UnifiedCodebaseAPI, from_repo
from src.codegen.sdk.core.project_context import ProjectContext
from src.codegen.sdk.core.adapters.solidlsp_adapter import SolidLSPAdapter
from src.codegen.sdk.core.adapters.serena_adapter import SerenaAdapter
from src.codegen.sdk.core.enhanced_graph_builder import EnhancedGraphBuilder
from src.codegen.sdk.core.diagnostic_collector import DiagnosticCollector
from src.codegen.sdk.core.autogenlib_context_enhancer import AutogenLibContextEnhancer
from src.codegen.sdk.core.error_resolution_engine import ErrorResolutionEngine
from src.codegen.sdk.core.dead_code_detector import DeadCodeDetector

# Configure logging for tests
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def find_dirs_to_ignore(start_dir, prefix):
    dirs_to_ignore = []
    for root, dirs, files in os.walk(start_dir):
        for dir in dirs:
            full_path = os.path.relpath(os.path.join(root, dir), start_dir)
            if any(dd.startswith("original_input") or dd.startswith("output") or dd.startswith("input") or dd.startswith("expected") for dd in dir.split("/")):
                dirs_to_ignore.append(full_path)
    return dirs_to_ignore


def pytest_addoption(parser) -> None:
    parser.addoption(
        "--profile",
        action="store",
        type=bool,
        default=False,
        help="Whether to profile the test",
    )
    parser.addoption(
        "--sync-graph",
        action="store",
        type=str,
        dest="sync-graph",
        default="false",
        help="Whether to sync the graph between tests",
    )
    parser.addoption(
        "--log-parse",
        action="store",
        type=str,
        dest="log-parse",
        default="false",
        help="Whether to log parsing errors for parse tests",
    )
    parser.addoption(
        "--extra-repos",
        type=bool,
        action="store",
        default=False,
        help="Whether to test on extra repos",
    )
    parser.addoption("--token", action="store", default=None, help="Read-only GHA token to access extra repos")

    parser.addoption("--codemod-id", action="store", type=int, default=None, help="Runs db skills test for a specific codemod")

    parser.addoption("--repo-id", action="store", type=int, default=None, help="Runs db skills test for a specific repo")

    parser.addoption("--base-commit", action="store", type=str, default=None, help="Runs db skills test for a specific commit. Argument can be the shortest unique substring.")

    parser.addoption("--cli-api-key", action="store", type=str, default=None, help="Token necessary to access skills.")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        if "NodeJS or npm is not installed" in str(report.longrepr):
            msg = "This test requires NodeJS and npm to be installed. Please install them before running the tests."
            raise RuntimeError(msg)


# Unified Integration Test Fixtures

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory for testing"""
    temp_dir = tempfile.mkdtemp(prefix="codegen_test_")
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_python_project(temp_project_dir):
    """Create a sample Python project for testing"""
    project_dir = temp_project_dir / "sample_project"
    project_dir.mkdir()
    
    # Create main.py
    main_py = project_dir / "main.py"
    main_py.write_text("""
import os
import sys
from typing import List, Optional

def main() -> None:
    \"\"\"Main entry point\"\"\"
    print("Hello, World!")
    unused_function()

def unused_function() -> str:
    \"\"\"This function is not used\"\"\"
    return "unused"

def process_data(data: List[str]) -> Optional[str]:
    \"\"\"Process some data\"\"\"
    if not data:
        return None
    return data[0]

class UnusedClass:
    \"\"\"This class is not used\"\"\"
    def __init__(self):
        self.value = 42

if __name__ == "__main__":
    main()
""")
    
    # Create utils.py
    utils_py = project_dir / "utils.py"
    utils_py.write_text("""
import json  # unused import
from pathlib import Path

def helper_function(x: int) -> int:
    \"\"\"A helper function\"\"\"
    return x * 2

def another_helper() -> None:
    \"\"\"Another helper\"\"\"
    pass
""")
    
    # Create __init__.py
    init_py = project_dir / "__init__.py"
    init_py.write_text("")
    
    # Create pyproject.toml
    pyproject_toml = project_dir / "pyproject.toml"
    pyproject_toml.write_text("""
[build-system]
requires = ["setuptools", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "sample-project"
version = "0.1.0"
description = "A sample project for testing"
""")
    
    return project_dir


@pytest.fixture
def unified_config():
    """Create a unified configuration for testing"""
    return UnifiedConfiguration(
        lspserver=True,
        diagnostics=True,
        errorautoresolve=True,
        enhancedcontext=True
    )


@pytest.fixture
async def unified_codebase_api(unified_config, sample_python_project):
    """Create a unified codebase API for testing"""
    api = UnifiedCodebaseAPI(str(sample_python_project), unified_config)
    await api.initialize()
    yield api
    await api.shutdown()
