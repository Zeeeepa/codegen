import os
from unittest.mock import patch

import pytest

from codegen.cli.api.endpoints import (
    get_base_url,
    CREATE_ENDPOINT,
    DEPLOY_ENDPOINT,
    DOCS_ENDPOINT,
    EXPERT_ENDPOINT,
    IDENTIFY_ENDPOINT,
    IMPROVE_ENDPOINT,
    LOOKUP_ENDPOINT,
    PR_LOOKUP_ENDPOINT,
    RUN_ENDPOINT,
    RUN_ON_PR_ENDPOINT,
)


def test_get_base_url_default():
    """Test get_base_url with default environment."""
    # Ensure CODEGEN_API_URL is not set
    with patch.dict(os.environ, {}, clear=True):
        base_url = get_base_url()
        
        # Check that the base URL is the production URL
        assert "api.codegen.sh" in base_url


def test_get_base_url_custom():
    """Test get_base_url with custom environment."""
    # Set CODEGEN_API_URL
    with patch.dict(os.environ, {"CODEGEN_API_URL": "https://custom-api.example.com"}):
        base_url = get_base_url()
        
        # Check that the base URL is the custom URL
        assert base_url == "https://custom-api.example.com"


def test_endpoints():
    """Test that all endpoints are defined."""
    # Check that all endpoints are strings
    assert isinstance(CREATE_ENDPOINT, str)
    assert isinstance(DEPLOY_ENDPOINT, str)
    assert isinstance(DOCS_ENDPOINT, str)
    assert isinstance(EXPERT_ENDPOINT, str)
    assert isinstance(IDENTIFY_ENDPOINT, str)
    assert isinstance(IMPROVE_ENDPOINT, str)
    assert isinstance(LOOKUP_ENDPOINT, str)
    assert isinstance(PR_LOOKUP_ENDPOINT, str)
    assert isinstance(RUN_ENDPOINT, str)
    assert isinstance(RUN_ON_PR_ENDPOINT, str)
    
    # Check that all endpoints contain the base URL
    base_url = get_base_url()
    assert base_url in CREATE_ENDPOINT
    assert base_url in DEPLOY_ENDPOINT
    assert base_url in DOCS_ENDPOINT
    assert base_url in EXPERT_ENDPOINT
    assert base_url in IDENTIFY_ENDPOINT
    assert base_url in IMPROVE_ENDPOINT
    assert base_url in LOOKUP_ENDPOINT
    assert base_url in PR_LOOKUP_ENDPOINT
    assert base_url in RUN_ENDPOINT
    assert base_url in RUN_ON_PR_ENDPOINT

