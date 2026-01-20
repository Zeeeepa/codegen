"""
Automatic authentication detection and analysis.

Detects login forms, authentication methods, and CAPTCHA requirements
using AI-powered page analysis.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import re

import structlog

from autoqa.adapters.owl import OwlBrowserAdapter

logger = structlog.get_logger(__name__)


@dataclass
class AuthFieldConfig:
    """Configuration for a single authentication field."""
    selector: str
    field_type: str  # email, password, text, etc.
    name: str
    required: bool = True
    placeholder: Optional[str] = None


@dataclass
class AuthFlowConfig:
    """Complete authentication flow configuration."""
    auth_method: str  # form_login, oauth, sso, api_key
    login_url: str
    fields: List[AuthFieldConfig]
    submit_selector: str
    has_captcha: bool = False
    captcha_type: Optional[str] = None  # text, image, recaptcha, hcaptcha
    success_indicators: List[str] = None
    requires_2fa: bool = False
    extra_steps: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.success_indicators is None:
            self.success_indicators = []
        if self.extra_steps is None:
            self.extra_steps = []


class AuthDetector:
    """
    Automatic authentication detection for web services.

    Usage:
        detector = AuthDetector(browser_adapter)

        auth_config = detector.detect_auth_method(
            base_url="https://k2think.ai"
        )

        if auth_config:
            print(f"Found {auth_config.auth_method} at {auth_config.login_url}")
    """

    def __init__(self, browser_adapter: OwlBrowserAdapter):
        """
        Initialize auth detector.

        Args:
            browser_adapter: Owl-Browser adapter instance
        """
        self._browser = browser_adapter
        self._log = logger.bind(component="auth_detector")

        # Common patterns for authentication elements
        self._email_patterns = [
            r"input.*type.*email",
            r"input.*name.*['\"]email['\"]",
            r"input.*id.*['\"]email['\"]",
            r"input.*placeholder.*['\"].*@.*['\"]",
        ]

        self._password_patterns = [
            r"input.*type.*password",
            r"input.*name.*['\"]password['\"]",
            r"input.*id.*['\"]password['\"]",
        ]

        self._submit_patterns = [
            r"button.*type.*submit",
            r"button.*text.*['\"]login['\"]",
            r"button.*text.*['\"]sign.?in['\"]",
            r"input.*type.*submit",
        ]

        self._captcha_patterns = [
            r"iframe.*src.*google\.com/recaptcha",
            r"div.*g-recaptcha",
            r"div.*h-captcha",
            r"iframe.*src.*hcaptcha",
        ]

    def detect_auth_method(
        self,
        base_url: str,
        credentials: Optional[Dict[str, str]] = None
    ) -> Optional[AuthFlowConfig]:
        """
        Detect authentication method for a service.

        Args:
            base_url: Service base URL
            credentials: Optional credentials for testing login

        Returns:
            AuthFlowConfig if authentication detected, None otherwise
        """
        try:
            # Try common login paths
            login_paths = [
                "/login",
                "/signin",
                "/auth/login",
                "/account/login",
                "/user/login",
                "/users/sign_in",
            ]

            auth_config = None

            for path in login_paths:
                login_url = f"{base_url.rstrip('/')}{path}"

                try:
                    self._browser.navigate(login_url)

                    # Check if page has login form
                    config = self._analyze_login_page(login_url)

                    if config:
                        auth_config = config
                        self._log.info(
                            "Authentication detected",
                            url=login_url,
                            method=config.auth_method
                        )
                        break

                except Exception as e:
                    self._log.debug("Login path not found", path=path, error=str(e))
                    continue

            return auth_config

        except Exception as e:
            self._log.error("Auth detection failed", base_url=base_url, error=str(e))
            return None

    def _analyze_login_page(self, url: str) -> Optional[AuthFlowConfig]:
        """
        Analyze login page and extract configuration.

        Args:
            url: Login page URL

        Returns:
            AuthFlowConfig if login form detected
        """
        try:
            # Get page HTML
            html = self._browser.get_html()

            # Detect login form
            fields = []
            submit_selector = None

            # Find email field
            email_selector = self._find_field(self._email_patterns, html)
            if email_selector:
                fields.append(AuthFieldConfig(
                    selector=email_selector,
                    field_type="email",
                    name="email",
                    required=True
                ))

            # Find password field
            password_selector = self._find_field(self._password_patterns, html)
            if password_selector:
                fields.append(AuthFieldConfig(
                    selector=password_selector,
                    field_type="password",
                    name="password",
                    required=True
                ))

            # If no email/password fields found, not a login form
            if not fields:
                return None

            # Find submit button
            submit_selector = self._find_submit_button(html)

            # Detect CAPTCHA
            has_captcha, captcha_type = self._detect_captcha(html)

            # Determine auth method
            if len(fields) >= 2 and any(f.field_type == "password" for f in fields):
                auth_method = "form_login"
            else:
                auth_method = "unknown"

            # Success indicators
            success_indicators = self._detect_success_indicators()

            config = AuthFlowConfig(
                auth_method=auth_method,
                login_url=url,
                fields=fields,
                submit_selector=submit_selector or "button[type='submit']",
                has_captcha=has_captcha,
                captcha_type=captcha_type,
                success_indicators=success_indicators
            )

            self._log.info(
                "Login form analyzed",
                url=url,
                fields_count=len(fields),
                has_captcha=has_captcha
            )

            return config

        except Exception as e:
            self._log.error("Failed to analyze login page", url=url, error=str(e))
            return None

    def _find_field(self, patterns: List[str], html: str) -> Optional[str]:
        """
        Find input field using regex patterns.

        Args:
            patterns: List of regex patterns
            html: Page HTML

        Returns:
            CSS selector if found
        """
        for pattern in patterns:
            if re.search(pattern, html, re.IGNORECASE):
                # Try to convert to selector
                match = re.search(r"(?:id|name)=['\"]([^'\"]+)['\"]", html, re.IGNORECASE)
                if match:
                    attr_value = match.group(1)
                    # Return as CSS selector
                    if f"id='{attr_value}'" in html or f'id="{attr_value}"' in html:
                        return f"#{attr_value}"
                    else:
                        return f"[name='{attr_value}']"

        return None

    def _find_submit_button(self, html: str) -> Optional[str]:
        """
        Find submit button selector.

        Args:
            html: Page HTML

        Returns:
            CSS selector if found
        """
        # Try button elements
        if "type='submit'" in html or 'type="submit"' in html:
            return "button[type='submit']"

        # Try by text content
        for text in ["login", "sign in", "signin", "log in"]:
            if text in html.lower():
                # Would need more sophisticated parsing
                return f"button:contains('{text}')"

        return "button[type='submit']"

    def _detect_captcha(self, html: str) -> tuple[bool, Optional[str]]:
        """
        Detect CAPTCHA presence and type.

        Args:
            html: Page HTML

        Returns:
            (has_captcha, captcha_type)
        """
        # Check for reCAPTCHA
        if "recaptcha" in html.lower():
            return True, "recaptcha"

        # Check for hCaptcha
        if "hcaptcha" in html.lower():
            return True, "hcaptcha"

        # Check for text/image CAPTCHA patterns
        if any(pattern in html.lower() for pattern in ["captcha", "verify", "human"]):
            return True, "unknown"

        return False, None

    def _detect_success_indicators(self) -> List[str]:
        """
        Detect indicators of successful login.

        Returns:
            List of CSS selectors that indicate success
        """
        # Common post-login elements
        indicators = [
            ".dashboard",
            ".user-profile",
            ".user-menu",
            "[data-testid='user-menu']",
            ".logout",
            "button:contains('Logout')",
        ]

        # Filter by visibility
        visible_indicators = []
        for indicator in indicators:
            try:
                if self._browser.is_visible(indicator):
                    visible_indicators.append(indicator)
            except:
                continue

        return visible_indicators

    def classify_captcha(self) -> Optional[str]:
        """
        Classify CAPTCHA type using AI analysis.

        Returns:
            CAPTCHA type: text, image, recaptcha_v2, recaptcha_v3, hcaptcha, etc.
        """
        try:
            # Use AI to analyze CAPTCHA
            # For now, simple heuristic based classification

            html = self._browser.get_html()

            if "api2/anchor" in html or "g-recaptcha" in html:
                return "recaptcha_v2"
            elif "api.js" in html and "recaptcha" in html:
                return "recaptcha_v3"
            elif "hcaptcha" in html:
                return "hcaptcha"
            else:
                return "unknown"

        except Exception as e:
            self._log.error("CAPTCHA classification failed", error=str(e))
            return None
