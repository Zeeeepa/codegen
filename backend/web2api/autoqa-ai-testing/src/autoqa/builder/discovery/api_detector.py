"""
API/XHR detection for intelligent test generation.

Provides:
- Network request interception and cataloging
- API endpoint identification
- GraphQL vs REST detection
- API validation test generation
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from enum import StrEnum, auto
from typing import TYPE_CHECKING, Any
from urllib.parse import parse_qs, urlparse

import structlog

if TYPE_CHECKING:
    from owl_browser import BrowserContext

logger = structlog.get_logger(__name__)


@dataclass
class APIConfig:
    """Configuration for API detector."""

    intercept_fetch: bool = True
    """Whether to intercept Fetch API calls."""

    intercept_xhr: bool = True
    """Whether to intercept XMLHttpRequest calls."""

    detect_graphql: bool = True
    """Whether to detect GraphQL endpoints."""

    detect_websocket: bool = True
    """Whether to detect WebSocket connections."""

    ignore_static_resources: bool = True
    """Whether to ignore static resource requests."""

    static_extensions: frozenset[str] = frozenset({
        ".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".svg",
        ".woff", ".woff2", ".ttf", ".eot", ".ico", ".map"
    })
    """File extensions to treat as static resources."""

    capture_request_body: bool = True
    """Whether to capture request bodies."""

    capture_response_body: bool = True
    """Whether to capture response bodies."""

    max_body_size: int = 10240
    """Maximum body size to capture in bytes."""


class RequestMethod(StrEnum):
    """HTTP request methods."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    OPTIONS = "OPTIONS"
    HEAD = "HEAD"


class APIType(StrEnum):
    """Types of APIs."""

    REST = auto()
    GRAPHQL = auto()
    WEBSOCKET = auto()
    GRPC = auto()
    UNKNOWN = auto()


class ContentType(StrEnum):
    """Content types."""

    JSON = "application/json"
    FORM = "application/x-www-form-urlencoded"
    MULTIPART = "multipart/form-data"
    XML = "application/xml"
    TEXT = "text/plain"
    HTML = "text/html"
    UNKNOWN = "unknown"


@dataclass
class RequestParameter:
    """API request parameter."""

    name: str
    location: str  # query, path, header, body
    value_type: str
    example_value: str | None = None
    is_required: bool = False
    description: str = ""


@dataclass
class APIEndpoint:
    """Detected API endpoint."""

    url: str
    method: RequestMethod
    api_type: APIType
    path: str
    parameters: list[RequestParameter]
    request_body_schema: dict[str, Any] | None = None
    response_status: int = 200
    response_body_sample: Any = None
    content_type: ContentType = ContentType.JSON
    headers: dict[str, str] = field(default_factory=dict)
    is_authenticated: bool = False
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class APIValidationTest:
    """Generated API validation test."""

    name: str
    endpoint: APIEndpoint
    test_type: str  # smoke, positive, negative, boundary
    request_data: dict[str, Any]
    expected_status: int
    expected_response: dict[str, Any] | None = None
    assertions: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class APIDetectionResult:
    """Result of API detection."""

    endpoints: list[APIEndpoint]
    api_type: APIType
    base_url: str | None = None
    authentication_endpoints: list[APIEndpoint] = field(default_factory=list)
    graphql_operations: list[dict[str, Any]] = field(default_factory=list)
    validation_tests: list[APIValidationTest] = field(default_factory=list)


class APIDetector:
    """
    Detects and catalogs API endpoints from network requests.

    Features:
    - Network request interception
    - REST and GraphQL detection
    - Parameter extraction
    - Validation test generation
    """

    # GraphQL indicators
    GRAPHQL_INDICATORS = frozenset({
        "graphql", "gql", "/api/graphql", "/graphql",
    })

    # Common API path patterns
    API_PATH_PATTERNS = [
        r"/api/v?\d*/",
        r"/rest/",
        r"/v\d+/",
        r"\.json$",
        r"/graphql",
    ]

    # Authentication endpoint patterns
    AUTH_PATTERNS = [
        r"/auth/",
        r"/login",
        r"/token",
        r"/oauth",
        r"/session",
    ]

    def __init__(self, config: APIConfig | None = None) -> None:
        self.config = config or APIConfig()
        self._log = logger.bind(component="api_detector")
        self._captured_requests: list[dict[str, Any]] = []
        self._endpoints: dict[str, APIEndpoint] = {}

    async def start_capture(self, page: BrowserContext) -> None:
        """
        Start capturing network requests.

        Note: This requires browser-level network interception support.
        """
        self._log.info("Starting API capture")
        self._captured_requests = []

        # Inject request interceptor
        # Note: Actual implementation depends on browser capabilities
        script = """
        window.__capturedRequests = window.__capturedRequests || [];
        window.__originalFetch = window.__originalFetch || window.fetch;

        window.fetch = async function(...args) {
            const url = typeof args[0] === 'string' ? args[0] : args[0].url;
            const options = args[1] || {};

            const request = {
                url: url,
                method: options.method || 'GET',
                headers: options.headers || {},
                body: options.body,
                timestamp: Date.now()
            };

            try {
                const response = await window.__originalFetch.apply(this, args);

                // Clone response for reading
                const cloned = response.clone();
                let responseBody = null;
                try {
                    const contentType = response.headers.get('content-type') || '';
                    if (contentType.includes('json')) {
                        responseBody = await cloned.json();
                    } else {
                        responseBody = await cloned.text();
                    }
                } catch (e) {}

                request.response = {
                    status: response.status,
                    statusText: response.statusText,
                    contentType: response.headers.get('content-type'),
                    body: responseBody
                };

                window.__capturedRequests.push(request);
                return response;
            } catch (e) {
                request.error = e.message;
                window.__capturedRequests.push(request);
                throw e;
            }
        };

        // Also intercept XMLHttpRequest
        window.__originalXHR = window.__originalXHR || window.XMLHttpRequest;
        window.XMLHttpRequest = function() {
            const xhr = new window.__originalXHR();
            const originalOpen = xhr.open;
            const originalSend = xhr.send;

            let requestData = {};

            xhr.open = function(method, url, ...rest) {
                requestData = { method, url, timestamp: Date.now() };
                return originalOpen.apply(xhr, [method, url, ...rest]);
            };

            xhr.send = function(body) {
                requestData.body = body;

                xhr.addEventListener('load', function() {
                    let responseBody = null;
                    try {
                        responseBody = JSON.parse(xhr.responseText);
                    } catch (e) {
                        responseBody = xhr.responseText;
                    }

                    requestData.response = {
                        status: xhr.status,
                        statusText: xhr.statusText,
                        contentType: xhr.getResponseHeader('content-type'),
                        body: responseBody
                    };
                    window.__capturedRequests.push(requestData);
                });

                return originalSend.apply(xhr, [body]);
            };

            return xhr;
        };
        """

        page.expression(script)

    async def stop_capture(self, page: BrowserContext) -> list[dict[str, Any]]:
        """Stop capturing and return captured requests."""
        self._log.info("Stopping API capture")

        # Get captured requests
        script = "window.__capturedRequests || []"
        self._captured_requests = page.expression(script)

        # Restore original fetch
        restore_script = """
        if (window.__originalFetch) {
            window.fetch = window.__originalFetch;
        }
        if (window.__originalXHR) {
            window.XMLHttpRequest = window.__originalXHR;
        }
        """
        page.expression(restore_script)

        return self._captured_requests

    async def detect_apis(
        self,
        page: BrowserContext,
        captured_requests: list[dict[str, Any]] | None = None,
    ) -> APIDetectionResult:
        """
        Detect APIs from captured requests or page analysis.

        Args:
            page: Browser context
            captured_requests: Optional pre-captured requests

        Returns:
            API detection result
        """
        requests = captured_requests or self._captured_requests

        self._log.info("Detecting APIs", request_count=len(requests))

        # Filter to API requests
        api_requests = [r for r in requests if self._is_api_request(r)]

        # Detect API type
        api_type = self._detect_api_type(api_requests)

        # Extract endpoints
        endpoints: list[APIEndpoint] = []
        for request in api_requests:
            endpoint = self._extract_endpoint(request, api_type)
            if endpoint:
                endpoints.append(endpoint)

        # Deduplicate endpoints
        endpoints = self._deduplicate_endpoints(endpoints)

        # Identify authentication endpoints
        auth_endpoints = [e for e in endpoints if self._is_auth_endpoint(e)]

        # Extract GraphQL operations if applicable
        graphql_ops: list[dict[str, Any]] = []
        if api_type == APIType.GRAPHQL:
            graphql_ops = self._extract_graphql_operations(api_requests)

        # Determine base URL
        base_url = self._detect_base_url(endpoints)

        # Generate validation tests
        validation_tests = self._generate_validation_tests(endpoints)

        result = APIDetectionResult(
            endpoints=endpoints,
            api_type=api_type,
            base_url=base_url,
            authentication_endpoints=auth_endpoints,
            graphql_operations=graphql_ops,
            validation_tests=validation_tests,
        )

        self._log.info(
            "API detection complete",
            endpoints=len(endpoints),
            api_type=api_type.value,
            auth_endpoints=len(auth_endpoints),
        )

        return result

    def _is_api_request(self, request: dict[str, Any]) -> bool:
        """Check if request is an API request."""
        url = request.get("url", "")

        # Check URL patterns
        for pattern in self.API_PATH_PATTERNS:
            if re.search(pattern, url, re.IGNORECASE):
                return True

        # Check content type
        response = request.get("response", {})
        content_type = response.get("contentType", "")
        if "json" in content_type.lower():
            return True

        # Skip static resources
        static_extensions = (".js", ".css", ".png", ".jpg", ".gif", ".svg", ".woff", ".ttf")
        if any(url.lower().endswith(ext) for ext in static_extensions):
            return False

        return False

    def _detect_api_type(self, requests: list[dict[str, Any]]) -> APIType:
        """Detect the type of API from requests."""
        for request in requests:
            url = request.get("url", "").lower()
            body = request.get("body", "")

            # Check for GraphQL
            if any(ind in url for ind in self.GRAPHQL_INDICATORS):
                return APIType.GRAPHQL

            # Check request body for GraphQL query
            if body and isinstance(body, str):
                try:
                    parsed = json.loads(body)
                    if "query" in parsed or "mutation" in parsed:
                        return APIType.GRAPHQL
                except (json.JSONDecodeError, TypeError):
                    pass

        return APIType.REST

    def _extract_endpoint(
        self,
        request: dict[str, Any],
        api_type: APIType,
    ) -> APIEndpoint | None:
        """Extract endpoint information from request."""
        url = request.get("url", "")
        if not url:
            return None

        parsed = urlparse(url)
        method = RequestMethod(request.get("method", "GET").upper())

        # Extract parameters
        parameters: list[RequestParameter] = []

        # Query parameters
        query_params = parse_qs(parsed.query)
        for name, values in query_params.items():
            parameters.append(RequestParameter(
                name=name,
                location="query",
                value_type=self._infer_type(values[0] if values else ""),
                example_value=values[0] if values else None,
            ))

        # Path parameters (detect placeholders like /users/{id})
        path_params = re.findall(r"\{(\w+)\}|:(\w+)", parsed.path)
        for match in path_params:
            param_name = match[0] or match[1]
            parameters.append(RequestParameter(
                name=param_name,
                location="path",
                value_type="string",
                is_required=True,
            ))

        # Request body
        body = request.get("body")
        body_schema = None
        if body:
            body_schema = self._extract_body_schema(body)

        # Response
        response = request.get("response", {})
        response_status = response.get("status", 200)
        response_body = response.get("body")

        # Content type
        content_type = ContentType.JSON
        ct_header = response.get("contentType", "")
        if "form" in ct_header:
            content_type = ContentType.FORM
        elif "xml" in ct_header:
            content_type = ContentType.XML

        # Check authentication
        headers = request.get("headers", {})
        is_authenticated = any(
            h.lower() in ("authorization", "x-api-key", "x-auth-token")
            for h in headers
        )

        # Generate tags
        tags = self._generate_endpoint_tags(parsed.path, method)

        return APIEndpoint(
            url=url,
            method=method,
            api_type=api_type,
            path=parsed.path,
            parameters=parameters,
            request_body_schema=body_schema,
            response_status=response_status,
            response_body_sample=response_body,
            content_type=content_type,
            headers=headers,
            is_authenticated=is_authenticated,
            tags=tags,
        )

    def _extract_body_schema(self, body: Any) -> dict[str, Any] | None:
        """Extract schema from request body."""
        if not body:
            return None

        if isinstance(body, str):
            try:
                body = json.loads(body)
            except json.JSONDecodeError:
                return {"type": "string", "example": body[:100]}

        if isinstance(body, dict):
            schema: dict[str, Any] = {"type": "object", "properties": {}}
            for key, value in body.items():
                schema["properties"][key] = {
                    "type": self._infer_type(value),
                    "example": value if not isinstance(value, (dict, list)) else None,
                }
            return schema

        if isinstance(body, list):
            return {"type": "array", "items": {}}

        return None

    def _infer_type(self, value: Any) -> str:
        """Infer JSON schema type from value."""
        if value is None:
            return "null"
        if isinstance(value, bool):
            return "boolean"
        if isinstance(value, int):
            return "integer"
        if isinstance(value, float):
            return "number"
        if isinstance(value, str):
            # Check for common formats
            if re.match(r"^\d{4}-\d{2}-\d{2}", value):
                return "date"
            if re.match(r"^[\w.+-]+@[\w.-]+\.\w+$", value):
                return "email"
            return "string"
        if isinstance(value, list):
            return "array"
        if isinstance(value, dict):
            return "object"
        return "string"

    def _is_auth_endpoint(self, endpoint: APIEndpoint) -> bool:
        """Check if endpoint is authentication-related."""
        for pattern in self.AUTH_PATTERNS:
            if re.search(pattern, endpoint.path, re.IGNORECASE):
                return True
        return False

    def _extract_graphql_operations(
        self,
        requests: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Extract GraphQL operations from requests."""
        operations: list[dict[str, Any]] = []

        for request in requests:
            body = request.get("body")
            if not body:
                continue

            if isinstance(body, str):
                try:
                    body = json.loads(body)
                except json.JSONDecodeError:
                    continue

            if isinstance(body, dict):
                query = body.get("query", "")
                operation_name = body.get("operationName")
                variables = body.get("variables", {})

                # Detect operation type
                op_type = "query"
                if query.strip().startswith("mutation"):
                    op_type = "mutation"
                elif query.strip().startswith("subscription"):
                    op_type = "subscription"

                operations.append({
                    "type": op_type,
                    "name": operation_name,
                    "query": query,
                    "variables": variables,
                    "response": request.get("response", {}).get("body"),
                })

        return operations

    def _detect_base_url(self, endpoints: list[APIEndpoint]) -> str | None:
        """Detect common base URL from endpoints."""
        if not endpoints:
            return None

        # Extract hosts
        hosts: dict[str, int] = {}
        for endpoint in endpoints:
            parsed = urlparse(endpoint.url)
            base = f"{parsed.scheme}://{parsed.netloc}"
            hosts[base] = hosts.get(base, 0) + 1

        # Return most common host
        if hosts:
            return max(hosts, key=hosts.get)  # type: ignore
        return None

    def _deduplicate_endpoints(
        self, endpoints: list[APIEndpoint]
    ) -> list[APIEndpoint]:
        """Remove duplicate endpoints."""
        seen: set[str] = set()
        unique: list[APIEndpoint] = []

        for endpoint in endpoints:
            # Create signature from method and path (normalized)
            normalized_path = re.sub(r"/\d+", "/{id}", endpoint.path)
            signature = f"{endpoint.method}:{normalized_path}"

            if signature not in seen:
                seen.add(signature)
                unique.append(endpoint)

        return unique

    def _generate_endpoint_tags(
        self,
        path: str,
        method: RequestMethod,
    ) -> list[str]:
        """Generate tags for endpoint."""
        tags: list[str] = []

        # Tag based on path segments
        segments = [s for s in path.split("/") if s and not s.startswith("{")]
        if segments:
            tags.append(segments[-1])

        # Tag based on method
        method_tags = {
            RequestMethod.GET: "read",
            RequestMethod.POST: "create",
            RequestMethod.PUT: "update",
            RequestMethod.PATCH: "update",
            RequestMethod.DELETE: "delete",
        }
        if method in method_tags:
            tags.append(method_tags[method])

        # Tag based on common patterns
        if "/user" in path:
            tags.append("user")
        if "/auth" in path or "/login" in path:
            tags.append("authentication")
        if "/admin" in path:
            tags.append("admin")

        return list(set(tags))

    def _generate_validation_tests(
        self,
        endpoints: list[APIEndpoint],
    ) -> list[APIValidationTest]:
        """Generate validation tests for endpoints."""
        tests: list[APIValidationTest] = []

        for endpoint in endpoints:
            # Smoke test - basic request
            tests.append(APIValidationTest(
                name=f"Smoke: {endpoint.method} {endpoint.path}",
                endpoint=endpoint,
                test_type="smoke",
                request_data={},
                expected_status=endpoint.response_status,
                assertions=[
                    {"type": "status_code", "expected": endpoint.response_status},
                    {"type": "content_type", "contains": "json"},
                ],
            ))

            # Positive test with sample data
            if endpoint.request_body_schema:
                sample_data = self._generate_sample_data(endpoint.request_body_schema)
                tests.append(APIValidationTest(
                    name=f"Positive: {endpoint.method} {endpoint.path}",
                    endpoint=endpoint,
                    test_type="positive",
                    request_data=sample_data,
                    expected_status=endpoint.response_status,
                    assertions=[
                        {"type": "status_code", "expected": endpoint.response_status},
                    ],
                ))

            # Negative test - missing required fields
            if endpoint.method in (RequestMethod.POST, RequestMethod.PUT):
                tests.append(APIValidationTest(
                    name=f"Negative (empty body): {endpoint.method} {endpoint.path}",
                    endpoint=endpoint,
                    test_type="negative",
                    request_data={},
                    expected_status=400,
                    assertions=[
                        {"type": "status_code", "expected": [400, 422]},
                    ],
                ))

        return tests

    def _generate_sample_data(self, schema: dict[str, Any]) -> dict[str, Any]:
        """Generate sample data from schema."""
        sample: dict[str, Any] = {}

        properties = schema.get("properties", {})
        for name, prop in properties.items():
            prop_type = prop.get("type", "string")
            example = prop.get("example")

            if example is not None:
                sample[name] = example
            elif prop_type == "string":
                sample[name] = f"test_{name}"
            elif prop_type == "integer":
                sample[name] = 1
            elif prop_type == "number":
                sample[name] = 1.0
            elif prop_type == "boolean":
                sample[name] = True
            elif prop_type == "array":
                sample[name] = []
            elif prop_type == "object":
                sample[name] = {}

        return sample
