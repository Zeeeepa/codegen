"""
Tests for the analysis_viewer_cli module.
"""

import os
import json
import tempfile
from pathlib import Path
from unittest import mock

import pytest
from click.testing import CliRunner

from codegen_on_oss.analysis_viewer_cli import (
    CodebaseAnalysisViewer,
    cli,
    analyze,
    compare,
    interactive,
    list_categories,
)


class MockCodebaseAnalyzer:
    """Mock CodebaseAnalyzer for testing."""
    
    def __init__(self, repo_url=None, repo_path=None, language=None):
        self.repo_url = repo_url
        self.repo_path = repo_path
        self.language = language
        self.analyze_called = False
        self.analyze_args = None
    
    def analyze(self, categories=None, output_format="json", output_file=None):
        """Mock analyze method."""
        self.analyze_called = True
        self.analyze_args = {
            "categories": categories,
            "output_format": output_format,
            "output_file": output_file,
        }
        
        # Return mock results
        return {
            "metadata": {
                "repo_name": self.repo_url or self.repo_path or "mock_repo",
                "analysis_time": "2023-01-01 00:00:00",
                "language": self.language or "python",
            },
            "categories": {
                "codebase_structure": {
                    "get_file_count": 100,
                    "get_files_by_language": {"python": 80, "javascript": 20},
                },
                "code_quality": {
                    "get_cyclomatic_complexity": {"avg": 5.0, "max": 15},
                    "get_function_size_metrics": {"avg_function_length": 20.5},
                },
            }
        }


@pytest.fixture
def mock_codebase_analyzer(monkeypatch):
    """Fixture to mock the CodebaseAnalyzer class."""
    mock_analyzer = MockCodebaseAnalyzer
    monkeypatch.setattr("codegen_on_oss.analysis_viewer_cli.CodebaseAnalyzer", mock_analyzer)
    return mock_analyzer


@pytest.fixture
def cli_runner():
    """Fixture to create a Click CLI runner."""
    return CliRunner()


def test_analyze_command(cli_runner, mock_codebase_analyzer):
    """Test the analyze command."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = os.path.join(tmpdir, "analysis.json")
        
        result = cli_runner.invoke(
            analyze,
            [
                "https://github.com/username/repo",
                "--language", "python",
                "--categories", "codebase_structure,code_quality",
                "--output-format", "json",
                "--output-file", output_file,
                "--no-progress",
            ]
        )
        
        assert result.exit_code == 0
        assert "Analysis complete!" in result.output
        
        # Check that the output file was created
        assert os.path.exists(output_file)


def test_compare_command(cli_runner, mock_codebase_analyzer):
    """Test the compare command."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = os.path.join(tmpdir, "comparison.json")
        
        result = cli_runner.invoke(
            compare,
            [
                "https://github.com/username/repo1",
                "https://github.com/username/repo2",
                "--language1", "python",
                "--language2", "javascript",
                "--categories", "codebase_structure,code_quality",
                "--output-format", "json",
                "--output-file", output_file,
                "--no-progress",
            ]
        )
        
        assert result.exit_code == 0
        assert "Comparison complete!" in result.output
        
        # Check that the output file was created
        assert os.path.exists(output_file)


def test_list_categories_command(cli_runner):
    """Test the list-categories command."""
    result = cli_runner.invoke(list_categories)
    
    assert result.exit_code == 0
    assert "Available Analysis Categories" in result.output


def test_interactive_command(cli_runner):
    """Test the interactive command."""
    # Mock the run_interactive_mode method
    with mock.patch.object(CodebaseAnalysisViewer, "run_interactive_mode") as mock_run:
        result = cli_runner.invoke(interactive)
        
        assert result.exit_code == 0
        assert mock_run.called


def test_codebase_analysis_viewer_analyze_codebase(mock_codebase_analyzer):
    """Test the CodebaseAnalysisViewer.analyze_codebase method."""
    viewer = CodebaseAnalysisViewer()
    
    # Test with URL
    results = viewer.analyze_codebase(
        repo_source="https://github.com/username/repo",
        language="python",
        categories=["codebase_structure", "code_quality"],
        output_format="json",
        output_file=None,
        show_progress=False
    )
    
    assert "metadata" in results
    assert "categories" in results
    assert "codebase_structure" in results["categories"]
    assert "code_quality" in results["categories"]
    
    # Test with local path
    results = viewer.analyze_codebase(
        repo_source="/path/to/local/repo",
        language="javascript",
        categories=["codebase_structure"],
        output_format="json",
        output_file=None,
        show_progress=False
    )
    
    assert "metadata" in results
    assert "categories" in results
    assert "codebase_structure" in results["categories"]


def test_codebase_analysis_viewer_compare_codebases(mock_codebase_analyzer):
    """Test the CodebaseAnalysisViewer.compare_codebases method."""
    viewer = CodebaseAnalysisViewer()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = os.path.join(tmpdir, "comparison.json")
        
        results = viewer.compare_codebases(
            repo_source1="https://github.com/username/repo1",
            repo_source2="https://github.com/username/repo2",
            language1="python",
            language2="javascript",
            categories=["codebase_structure", "code_quality"],
            output_format="json",
            output_file=output_file,
            show_progress=False
        )
        
        assert "metadata" in results
        assert "categories" in results
        assert os.path.exists(output_file)
        
        # Check the content of the output file
        with open(output_file, "r") as f:
            file_content = json.load(f)
            assert "metadata" in file_content
            assert "categories" in file_content


def test_compute_differences():
    """Test the _compute_differences method."""
    viewer = CodebaseAnalysisViewer()
    
    # Test with dictionaries
    value1 = {"a": 1, "b": 2, "c": 3}
    value2 = {"a": 1, "b": 3, "d": 4}
    
    differences = viewer._compute_differences(value1, value2)
    
    assert "b" in differences
    assert differences["b"]["repo1"] == 2
    assert differences["b"]["repo2"] == 3
    assert "c" in differences
    assert differences["c"]["repo1"] == 3
    assert differences["c"]["repo2"] is None
    assert "d" in differences
    assert differences["d"]["repo1"] is None
    assert differences["d"]["repo2"] == 4
    
    # Test with lists
    value1 = [1, 2, 3]
    value2 = [4, 5]
    
    differences = viewer._compute_differences(value1, value2)
    
    assert differences["repo1_count"] == 3
    assert differences["repo2_count"] == 2
    assert differences["count_difference"] == 1
    
    # Test with simple values
    value1 = 10
    value2 = 5
    
    differences = viewer._compute_differences(value1, value2)
    
    assert differences["repo1"] == 10
    assert differences["repo2"] == 5
    assert differences["difference"] == 5

