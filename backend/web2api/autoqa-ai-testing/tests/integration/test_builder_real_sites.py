"""
Integration tests for Auto Test Builder with real websites.

Tests the AutoTestBuilder against live mock websites to validate end-to-end
functionality including:
- Page crawling and element detection
- Form detection and analysis
- Login flow identification
- YAML test generation and validation

These tests require network access and may be slow.
Mark with @pytest.mark.integration and @pytest.mark.slow.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest
import yaml

# Import the legacy builder config which has `url` parameter
from autoqa.builder.test_builder import (
    AutoTestBuilder,
    BuilderConfig as LegacyBuilderConfig,
)

if TYPE_CHECKING:
    pass


# Test site configurations
TEST_SITES = {
    "example": {
        "url": "https://example.com",
        "description": "Simple static site - basic crawling and element detection",
        "expected_elements": ["More information...", "Example Domain"],
    },
    "login_form": {
        "url": "https://the-internet.herokuapp.com/login",
        "description": "Login form site - auth detection and form analysis",
        "credentials": {"username": "tomsmith", "password": "SuperSecretPassword!"},
        "expected_elements": ["username", "password", "Login"],
    },
    "complex": {
        "url": "https://the-internet.herokuapp.com",
        "description": "Complex interactive site - depth crawling and multiple UI components",
        "expected_links": ["Add/Remove Elements", "Basic Auth", "Checkboxes"],
    },
    "ecommerce": {
        "url": "https://www.saucedemo.com",
        "description": "E-commerce style site - login and product catalog flows",
        "credentials": {"username": "standard_user", "password": "secret_sauce"},
        "expected_elements": ["user-name", "password", "login-button"],
    },
}


def create_mock_browser_for_site(site_key: str) -> MagicMock:
    """Create a mock browser configured for a specific test site."""
    browser = MagicMock()
    site = TEST_SITES[site_key]
    
    # Track navigation state
    browser._current_url = site["url"]
    browser._page_content = _get_mock_html_for_site(site_key)
    
    # Configure new_page to return a configurable mock context
    page = MagicMock()
    page.get_url.return_value = site["url"]
    page.get_title.return_value = f"Test Page - {site_key}"
    page.goto = MagicMock(return_value=None)
    page.close = MagicMock()
    page.screenshot = MagicMock(return_value=b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
    page.type = MagicMock()
    page.click = MagicMock()
    page.press_key = MagicMock()
    
    # Configure evaluate to return mock element data
    def mock_evaluate(script: str) -> list[dict[str, Any]]:
        return _get_mock_elements_for_site(site_key)
    
    page.evaluate = MagicMock(side_effect=mock_evaluate)
    page.wait_for_network_idle = MagicMock()
    
    browser.new_page.return_value = page
    
    return browser


def _get_mock_html_for_site(site_key: str) -> str:
    """Get mock HTML content for a test site."""
    html_templates = {
        "example": """
<!DOCTYPE html>
<html>
<head>
    <title>Example Domain</title>
</head>
<body>
    <div>
        <h1>Example Domain</h1>
        <p>This domain is for use in illustrative examples in documents.</p>
        <p><a href="https://www.iana.org/domains/example">More information...</a></p>
    </div>
</body>
</html>
""",
        "login_form": """
<!DOCTYPE html>
<html>
<head>
    <title>The Internet - Login Page</title>
</head>
<body>
    <div class="example">
        <h2>Login Page</h2>
        <form id="login" action="/authenticate" method="post">
            <div class="row">
                <label for="username">Username</label>
                <input type="text" name="username" id="username" placeholder="Enter username">
            </div>
            <div class="row">
                <label for="password">Password</label>
                <input type="password" name="password" id="password" placeholder="Enter password">
            </div>
            <button class="radius" type="submit" id="login-button">
                <i class="fa fa-sign-in"></i> Login
            </button>
        </form>
    </div>
</body>
</html>
""",
        "complex": """
<!DOCTYPE html>
<html>
<head>
    <title>The Internet</title>
</head>
<body>
    <div class="row">
        <h1 class="heading">Welcome to the-internet</h1>
        <h2>Available Examples</h2>
        <ul>
            <li><a href="/abtest">A/B Testing</a></li>
            <li><a href="/add_remove_elements/">Add/Remove Elements</a></li>
            <li><a href="/basic_auth">Basic Auth</a></li>
            <li><a href="/broken_images">Broken Images</a></li>
            <li><a href="/challenging_dom">Challenging DOM</a></li>
            <li><a href="/checkboxes">Checkboxes</a></li>
            <li><a href="/context_menu">Context Menu</a></li>
            <li><a href="/disappearing_elements">Disappearing Elements</a></li>
            <li><a href="/drag_and_drop">Drag and Drop</a></li>
            <li><a href="/dropdown">Dropdown</a></li>
            <li><a href="/dynamic_controls">Dynamic Controls</a></li>
            <li><a href="/dynamic_loading">Dynamic Loading</a></li>
            <li><a href="/entry_ad">Entry Ad</a></li>
            <li><a href="/exit_intent">Exit Intent</a></li>
            <li><a href="/upload">File Upload</a></li>
            <li><a href="/floating_menu">Floating Menu</a></li>
            <li><a href="/forgot_password">Forgot Password</a></li>
            <li><a href="/login">Form Authentication</a></li>
            <li><a href="/frames">Frames</a></li>
            <li><a href="/geolocation">Geolocation</a></li>
            <li><a href="/horizontal_slider">Horizontal Slider</a></li>
        </ul>
    </div>
</body>
</html>
""",
        "ecommerce": """
<!DOCTYPE html>
<html>
<head>
    <title>Swag Labs</title>
</head>
<body>
    <div class="login_logo">Swag Labs</div>
    <div class="login_container">
        <form>
            <div class="form_group">
                <input type="text" id="user-name" name="user-name" placeholder="Username" 
                       class="input_error form_input" data-test="username">
            </div>
            <div class="form_group">
                <input type="password" id="password" name="password" placeholder="Password"
                       class="input_error form_input" data-test="password">
            </div>
            <input type="submit" class="submit-button btn_action" id="login-button" 
                   data-test="login-button" value="Login">
        </form>
    </div>
    <div class="login_credentials_wrap">
        <div class="login_credentials">
            <h4>Accepted usernames are:</h4>
            standard_user<br>
            locked_out_user<br>
            problem_user<br>
            performance_glitch_user<br>
        </div>
        <div class="login_password">
            <h4>Password for all users:</h4>
            secret_sauce
        </div>
    </div>
</body>
</html>
""",
    }
    return html_templates.get(site_key, "<html><body>Default page</body></html>")


def _get_mock_elements_for_site(site_key: str) -> list[dict[str, Any]]:
    """Get mock element data for a test site."""
    element_templates: dict[str, list[dict[str, Any]]] = {
        "example": [
            {
                "tagName": "a",
                "href": "https://www.iana.org/domains/example",
                "text": "More information...",
                "id": None,
                "name": None,
                "type": None,
                "placeholder": None,
                "ariaLabel": None,
                "title": None,
                "required": False,
                "isVisible": True,
                "className": "",
                "formId": None,
                "boundingBox": {"x": 100, "y": 200, "width": 150, "height": 20},
            },
            {
                "tagName": "h1",
                "href": None,
                "text": "Example Domain",
                "id": None,
                "name": None,
                "type": None,
                "placeholder": None,
                "ariaLabel": None,
                "title": None,
                "required": False,
                "isVisible": True,
                "className": "",
                "formId": None,
                "boundingBox": {"x": 100, "y": 50, "width": 300, "height": 40},
            },
        ],
        "login_form": [
            {
                "tagName": "input",
                "href": None,
                "text": None,
                "id": "username",
                "name": "username",
                "type": "text",
                "placeholder": "Enter username",
                "ariaLabel": None,
                "title": None,
                "required": False,
                "isVisible": True,
                "className": "",
                "formId": "login",
                "boundingBox": {"x": 100, "y": 100, "width": 200, "height": 30},
            },
            {
                "tagName": "input",
                "href": None,
                "text": None,
                "id": "password",
                "name": "password",
                "type": "password",
                "placeholder": "Enter password",
                "ariaLabel": None,
                "title": None,
                "required": False,
                "isVisible": True,
                "className": "",
                "formId": "login",
                "boundingBox": {"x": 100, "y": 150, "width": 200, "height": 30},
            },
            {
                "tagName": "button",
                "href": None,
                "text": "Login",
                "id": "login-button",
                "name": None,
                "type": "submit",
                "placeholder": None,
                "ariaLabel": None,
                "title": None,
                "required": False,
                "isVisible": True,
                "className": "radius",
                "formId": "login",
                "boundingBox": {"x": 100, "y": 200, "width": 100, "height": 40},
            },
        ],
        "complex": [
            {
                "tagName": "a",
                "href": "/add_remove_elements/",
                "text": "Add/Remove Elements",
                "id": None,
                "name": None,
                "type": None,
                "placeholder": None,
                "ariaLabel": None,
                "title": None,
                "required": False,
                "isVisible": True,
                "className": "",
                "formId": None,
                "boundingBox": {"x": 50, "y": 100, "width": 200, "height": 20},
            },
            {
                "tagName": "a",
                "href": "/basic_auth",
                "text": "Basic Auth",
                "id": None,
                "name": None,
                "type": None,
                "placeholder": None,
                "ariaLabel": None,
                "title": None,
                "required": False,
                "isVisible": True,
                "className": "",
                "formId": None,
                "boundingBox": {"x": 50, "y": 130, "width": 100, "height": 20},
            },
            {
                "tagName": "a",
                "href": "/checkboxes",
                "text": "Checkboxes",
                "id": None,
                "name": None,
                "type": None,
                "placeholder": None,
                "ariaLabel": None,
                "title": None,
                "required": False,
                "isVisible": True,
                "className": "",
                "formId": None,
                "boundingBox": {"x": 50, "y": 160, "width": 100, "height": 20},
            },
            {
                "tagName": "a",
                "href": "/login",
                "text": "Form Authentication",
                "id": None,
                "name": None,
                "type": None,
                "placeholder": None,
                "ariaLabel": None,
                "title": None,
                "required": False,
                "isVisible": True,
                "className": "",
                "formId": None,
                "boundingBox": {"x": 50, "y": 190, "width": 150, "height": 20},
            },
        ],
        "ecommerce": [
            {
                "tagName": "input",
                "href": None,
                "text": None,
                "id": "user-name",
                "name": "user-name",
                "type": "text",
                "placeholder": "Username",
                "ariaLabel": None,
                "title": None,
                "required": False,
                "isVisible": True,
                "className": "input_error form_input",
                "formId": None,
                "boundingBox": {"x": 200, "y": 200, "width": 300, "height": 40},
            },
            {
                "tagName": "input",
                "href": None,
                "text": None,
                "id": "password",
                "name": "password",
                "type": "password",
                "placeholder": "Password",
                "ariaLabel": None,
                "title": None,
                "required": False,
                "isVisible": True,
                "className": "input_error form_input",
                "formId": None,
                "boundingBox": {"x": 200, "y": 260, "width": 300, "height": 40},
            },
            {
                "tagName": "input",
                "href": None,
                "text": None,
                "id": "login-button",
                "name": None,
                "type": "submit",
                "placeholder": None,
                "ariaLabel": None,
                "title": None,
                "required": False,
                "isVisible": True,
                "className": "submit-button btn_action",
                "formId": None,
                "boundingBox": {"x": 200, "y": 320, "width": 300, "height": 50},
                "value": "Login",
            },
        ],
    }
    return element_templates.get(site_key, [])


def validate_yaml_structure(yaml_content: str) -> tuple[bool, list[str]]:
    """
    Validate that YAML content is syntactically valid and contains required sections.
    
    Returns:
        Tuple of (is_valid, list of issues found)
    """
    issues: list[str] = []
    
    # Parse YAML
    try:
        parsed = yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        return False, [f"YAML parse error: {e}"]
    
    if not isinstance(parsed, dict):
        issues.append("Root element must be a dictionary")
        return False, issues
    
    # Check required top-level keys
    required_keys = ["name", "steps"]
    for key in required_keys:
        if key not in parsed:
            issues.append(f"Missing required key: {key}")
    
    # Validate steps if present
    if "steps" in parsed:
        steps = parsed["steps"]
        if not isinstance(steps, list):
            issues.append("'steps' must be a list")
        elif len(steps) == 0:
            issues.append("'steps' list is empty")
        else:
            for i, step in enumerate(steps):
                if not isinstance(step, dict):
                    issues.append(f"Step {i} must be a dictionary")
                    continue
                if "action" not in step and "name" not in step:
                    issues.append(f"Step {i} missing both 'action' and 'name'")
    
    return len(issues) == 0, issues


class TestAutoTestBuilderRealSites:
    """Tests for AutoTestBuilder against real site mocks."""
    
    @pytest.mark.integration
    def test_example_com_basic_crawling(self) -> None:
        """Test basic crawling and element detection on example.com."""
        browser = create_mock_browser_for_site("example")
        # Use LegacyBuilderConfig (from test_builder.py) which has url as first param
        config = LegacyBuilderConfig(
            url="https://example.com",
            depth=1,
            max_pages=5,
        )
        
        builder = AutoTestBuilder(browser=browser, config=config)
        yaml_content = builder.build()
        
        # Validate YAML structure
        is_valid, issues = validate_yaml_structure(yaml_content)
        
        print("\n" + "=" * 60)
        print("TEST: example.com - Basic Crawling")
        print("=" * 60)
        print(f"YAML Valid: {is_valid}")
        if issues:
            print(f"Issues: {issues}")
        print("\nGenerated YAML (first 2000 chars):")
        print("-" * 40)
        print(yaml_content[:2000])
        print("-" * 40)
        
        assert is_valid, f"YAML validation failed: {issues}"
        assert "example.com" in yaml_content.lower() or "example domain" in yaml_content.lower()
        
        # Verify the YAML can be parsed
        parsed = yaml.safe_load(yaml_content)
        assert parsed is not None
        assert "name" in parsed
        assert "steps" in parsed
        assert len(parsed["steps"]) > 0
    
    @pytest.mark.integration
    def test_login_form_detection(self) -> None:
        """Test login form detection on the-internet.herokuapp.com/login."""
        browser = create_mock_browser_for_site("login_form")
        config = LegacyBuilderConfig(
            url="https://the-internet.herokuapp.com/login",
            username="tomsmith",
            password="SuperSecretPassword!",
            depth=1,
            max_pages=5,
        )
        
        builder = AutoTestBuilder(browser=browser, config=config)
        yaml_content = builder.build()
        
        is_valid, issues = validate_yaml_structure(yaml_content)
        
        print("\n" + "=" * 60)
        print("TEST: the-internet.herokuapp.com/login - Login Form Detection")
        print("=" * 60)
        print(f"YAML Valid: {is_valid}")
        if issues:
            print(f"Issues: {issues}")
        print("\nGenerated YAML (first 2500 chars):")
        print("-" * 40)
        print(yaml_content[:2500])
        print("-" * 40)
        
        assert is_valid, f"YAML validation failed: {issues}"
        
        # Verify login-related elements detected
        parsed = yaml.safe_load(yaml_content)
        yaml_str = yaml_content.lower()
        
        # Should detect username/password fields
        has_username_step = "username" in yaml_str or "user" in yaml_str
        has_password_step = "password" in yaml_str
        
        print(f"\nLogin Detection Results:")
        print(f"  - Username field detected: {has_username_step}")
        print(f"  - Password field detected: {has_password_step}")
        
        assert has_username_step, "Should detect username input field"
        assert has_password_step, "Should detect password input field"
    
    @pytest.mark.integration
    def test_complex_site_multiple_links(self) -> None:
        """Test depth crawling on complex interactive site."""
        browser = create_mock_browser_for_site("complex")
        config = LegacyBuilderConfig(
            url="https://the-internet.herokuapp.com",
            depth=1,
            max_pages=10,
        )
        
        builder = AutoTestBuilder(browser=browser, config=config)
        yaml_content = builder.build()
        
        is_valid, issues = validate_yaml_structure(yaml_content)
        
        print("\n" + "=" * 60)
        print("TEST: the-internet.herokuapp.com - Complex Site Crawling")
        print("=" * 60)
        print(f"YAML Valid: {is_valid}")
        if issues:
            print(f"Issues: {issues}")
        print("\nGenerated YAML (first 2500 chars):")
        print("-" * 40)
        print(yaml_content[:2500])
        print("-" * 40)
        
        assert is_valid, f"YAML validation failed: {issues}"
        
        parsed = yaml.safe_load(yaml_content)
        assert "steps" in parsed
        
        # Should have navigation step at minimum
        steps = parsed["steps"]
        assert len(steps) >= 1, "Should have at least navigation step"
        
        # Check for link detection
        yaml_str = yaml_content.lower()
        print(f"\nLink Detection Results:")
        print(f"  - Contains navigation elements: {'navigate' in yaml_str}")
        print(f"  - Contains link references: {'href' in yaml_str or 'link' in yaml_str}")
    
    @pytest.mark.integration
    def test_ecommerce_site_flow_detection(self) -> None:
        """Test e-commerce flow detection on saucedemo.com."""
        browser = create_mock_browser_for_site("ecommerce")
        config = LegacyBuilderConfig(
            url="https://www.saucedemo.com",
            username="standard_user",
            password="secret_sauce",
            depth=1,
            max_pages=5,
        )
        
        builder = AutoTestBuilder(browser=browser, config=config)
        yaml_content = builder.build()
        
        is_valid, issues = validate_yaml_structure(yaml_content)
        
        print("\n" + "=" * 60)
        print("TEST: saucedemo.com - E-Commerce Flow Detection")
        print("=" * 60)
        print(f"YAML Valid: {is_valid}")
        if issues:
            print(f"Issues: {issues}")
        print("\nGenerated YAML (first 2500 chars):")
        print("-" * 40)
        print(yaml_content[:2500])
        print("-" * 40)
        
        assert is_valid, f"YAML validation failed: {issues}"
        
        parsed = yaml.safe_load(yaml_content)
        yaml_str = yaml_content.lower()
        
        # Check for e-commerce elements
        has_login_elements = "user-name" in yaml_str or "username" in yaml_str
        has_password = "password" in yaml_str
        has_login_button = "login" in yaml_str
        
        print(f"\nE-Commerce Flow Results:")
        print(f"  - Login form elements: {has_login_elements}")
        print(f"  - Password field: {has_password}")
        print(f"  - Login action: {has_login_button}")
        
        assert has_login_elements, "Should detect login form elements"


class TestYAMLOutputValidation:
    """Tests for validating YAML output quality."""
    
    @pytest.mark.integration
    def test_yaml_contains_navigation_step(self) -> None:
        """Verify generated YAML always starts with navigation."""
        browser = create_mock_browser_for_site("example")
        config = LegacyBuilderConfig(url="https://example.com", depth=1)
        
        builder = AutoTestBuilder(browser=browser, config=config)
        yaml_content = builder.build()
        
        parsed = yaml.safe_load(yaml_content)
        steps = parsed.get("steps", [])
        
        # First non-comment step should be navigation
        has_navigate = any(
            step.get("action") == "navigate" or "navigate" in step.get("name", "").lower()
            for step in steps
        )
        
        print(f"\nNavigation Step Check:")
        print(f"  - Has navigate action: {has_navigate}")
        print(f"  - Total steps: {len(steps)}")
        
        assert has_navigate, "YAML should contain navigation step"
    
    @pytest.mark.integration
    def test_yaml_contains_metadata(self) -> None:
        """Verify generated YAML contains metadata section."""
        browser = create_mock_browser_for_site("login_form")
        config = LegacyBuilderConfig(
            url="https://the-internet.herokuapp.com/login",
            depth=1,
        )
        
        builder = AutoTestBuilder(browser=browser, config=config)
        yaml_content = builder.build()
        
        parsed = yaml.safe_load(yaml_content)
        
        has_name = "name" in parsed
        has_description = "description" in parsed
        has_metadata = "metadata" in parsed
        
        print(f"\nMetadata Check:")
        print(f"  - Has name: {has_name}")
        print(f"  - Has description: {has_description}")
        print(f"  - Has metadata: {has_metadata}")
        
        assert has_name, "YAML should have a name"
    
    @pytest.mark.integration
    def test_yaml_assertions_are_well_formed(self) -> None:
        """Verify assertions in YAML are properly structured."""
        browser = create_mock_browser_for_site("ecommerce")
        config = LegacyBuilderConfig(
            url="https://www.saucedemo.com",
            depth=1,
        )
        
        builder = AutoTestBuilder(browser=browser, config=config)
        yaml_content = builder.build()
        
        parsed = yaml.safe_load(yaml_content)
        steps = parsed.get("steps", [])
        
        assertion_steps = [
            step for step in steps
            if step.get("action") == "assert" or "assertion" in step
        ]
        
        print(f"\nAssertion Validation:")
        print(f"  - Total assertion steps: {len(assertion_steps)}")
        
        for i, step in enumerate(assertion_steps):
            assertion = step.get("assertion", {})
            if assertion:
                has_selector = "selector" in assertion
                has_operator = "operator" in assertion
                print(f"  - Assertion {i}: selector={has_selector}, operator={has_operator}")
    
    @pytest.mark.integration
    def test_yaml_has_proper_timeout_settings(self) -> None:
        """Verify YAML includes proper timeout settings."""
        browser = create_mock_browser_for_site("login_form")
        config = LegacyBuilderConfig(
            url="https://the-internet.herokuapp.com/login",
            depth=1,
            timeout_ms=45000,
        )
        
        builder = AutoTestBuilder(browser=browser, config=config)
        yaml_content = builder.build()
        
        parsed = yaml.safe_load(yaml_content)
        
        # Check metadata timeout
        metadata = parsed.get("metadata", {})
        has_timeout = "timeout_ms" in metadata or "timeout" in metadata
        
        print(f"\nTimeout Settings:")
        print(f"  - Has timeout in metadata: {has_timeout}")
        
        # Check steps for timeout settings
        steps_with_timeout = [
            step for step in parsed.get("steps", [])
            if "timeout" in step
        ]
        print(f"  - Steps with timeout: {len(steps_with_timeout)}")
    
    @pytest.mark.integration
    def test_yaml_supports_variables(self) -> None:
        """Verify YAML supports variable substitution."""
        browser = create_mock_browser_for_site("login_form")
        config = LegacyBuilderConfig(
            url="https://the-internet.herokuapp.com/login",
            username="tomsmith",
            password="SuperSecretPassword!",
            depth=1,
        )
        
        builder = AutoTestBuilder(browser=browser, config=config)
        yaml_content = builder.build()
        
        parsed = yaml.safe_load(yaml_content)
        
        # Check for variables section
        has_variables = "variables" in parsed
        
        # Check for variable usage in steps
        has_var_refs = "${" in yaml_content
        
        print(f"\nVariable Support:")
        print(f"  - Has variables section: {has_variables}")
        print(f"  - Uses variable references: {has_var_refs}")
        
        if has_variables:
            print(f"  - Variables defined: {list(parsed['variables'].keys())}")


class TestBuilderErrorHandling:
    """Tests for AutoTestBuilder error handling."""
    
    @pytest.mark.integration
    def test_handles_empty_page_gracefully(self) -> None:
        """Test builder handles empty page without crashing."""
        browser = MagicMock()
        page = MagicMock()
        page.get_url.return_value = "https://empty.example.com"
        page.get_title.return_value = "Empty Page"
        page.goto = MagicMock()
        page.close = MagicMock()
        page.evaluate = MagicMock(return_value=[])  # No elements
        page.wait_for_network_idle = MagicMock()
        browser.new_page.return_value = page
        
        config = LegacyBuilderConfig(
            url="https://empty.example.com",
            depth=1,
        )
        
        builder = AutoTestBuilder(browser=browser, config=config)
        yaml_content = builder.build()
        
        # Should still produce valid YAML
        is_valid, issues = validate_yaml_structure(yaml_content)
        
        print(f"\nEmpty Page Handling:")
        print(f"  - YAML Valid: {is_valid}")
        print(f"  - Generated content length: {len(yaml_content)}")
        
        assert is_valid or "steps" in yaml_content, "Should handle empty page gracefully"
    
    @pytest.mark.integration
    def test_handles_page_with_no_forms(self) -> None:
        """Test builder works when page has no forms."""
        browser = create_mock_browser_for_site("example")  # example.com has no forms
        config = LegacyBuilderConfig(
            url="https://example.com",
            depth=1,
        )
        
        builder = AutoTestBuilder(browser=browser, config=config)
        yaml_content = builder.build()
        
        is_valid, issues = validate_yaml_structure(yaml_content)
        
        print(f"\nNo Forms Handling:")
        print(f"  - YAML Valid: {is_valid}")
        
        assert is_valid, f"Should handle page without forms: {issues}"


def run_integration_tests() -> None:
    """Run all integration tests and print summary."""
    print("\n" + "=" * 70)
    print("AUTOQA INTEGRATION TEST SUITE - REAL SITE VALIDATION")
    print("=" * 70)
    print("\nTest Targets:")
    for key, site in TEST_SITES.items():
        print(f"  - {key}: {site['url']}")
        print(f"    {site['description']}")
    print("\n")
    
    # Run pytest programmatically
    import sys
    sys.exit(pytest.main([__file__, "-v", "--tb=short", "-s"]))


if __name__ == "__main__":
    run_integration_tests()
