"""Pytest fixtures for AutoQA tests."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_test_spec() -> str:
    """Sample test specification YAML."""
    return '''
name: Sample Login Test
description: Test user login functionality
metadata:
  tags:
    - smoke
    - auth
  priority: high
  owner: qa-team

variables:
  base_url: https://example.com
  username: testuser

steps:
  - name: Navigate to login page
    action: navigate
    url: ${base_url}/login
    wait_until: networkidle

  - name: Enter username
    action: type
    selector: "#username"
    text: ${username}

  - name: Enter password
    action: type
    selector: "#password"
    text: ${env:TEST_PASSWORD}

  - name: Click login button
    action: click
    selector: "button[type='submit']"

  - name: Verify dashboard
    action: assert
    assertion:
      selector: ".dashboard"
      operator: is_visible
      message: Dashboard should be visible after login
'''


@pytest.fixture
def sample_test_suite() -> str:
    """Sample test suite YAML."""
    return '''
name: E2E Test Suite
description: End-to-end test suite
metadata:
  tags:
    - e2e
  priority: critical

parallel_execution: true
max_parallel: 3
fail_fast: false

tests:
  - name: Homepage Test
    steps:
      - name: Navigate to homepage
        action: navigate
        url: https://example.com

      - name: Verify title
        action: assert
        assertion:
          selector: h1
          operator: contains
          expected: Welcome

  - name: About Page Test
    steps:
      - name: Navigate to about
        action: navigate
        url: https://example.com/about

      - name: Verify content
        action: assert
        assertion:
          selector: ".about-content"
          operator: exists
'''


@pytest.fixture
def mock_browser() -> MagicMock:
    """Create a mock browser instance."""
    browser = MagicMock()
    page = MagicMock()

    browser.new_page.return_value = page
    page.goto.return_value = None
    page.click.return_value = None
    page.type.return_value = None
    page.is_visible.return_value = True
    page.is_enabled.return_value = True
    page.extract_text.return_value = "Sample text"
    page.screenshot.return_value = b"fake_image_data"
    page.get_network_log.return_value = []
    page.get_console_log.return_value = []

    return browser


@pytest.fixture
def mock_page(mock_browser: MagicMock) -> MagicMock:
    """Get mock page from mock browser."""
    return mock_browser.new_page()
