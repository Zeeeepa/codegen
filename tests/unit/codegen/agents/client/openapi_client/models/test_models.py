"""Unit tests for the OpenAPI client models."""

import pytest

from codegen.agents.client.openapi_client.models.agent_run_response import AgentRunResponse
from codegen.agents.client.openapi_client.models.create_agent_run_input import CreateAgentRunInput
from codegen.agents.client.openapi_client.models.http_validation_error import HTTPValidationError
from codegen.agents.client.openapi_client.models.organization_response import OrganizationResponse
from codegen.agents.client.openapi_client.models.organization_settings import OrganizationSettings
from codegen.agents.client.openapi_client.models.page_organization_response import PageOrganizationResponse
from codegen.agents.client.openapi_client.models.page_user_response import PageUserResponse
from codegen.agents.client.openapi_client.models.user_response import UserResponse
from codegen.agents.client.openapi_client.models.validation_error import ValidationError
from codegen.agents.client.openapi_client.models.validation_error_loc_inner import ValidationErrorLocInner


class TestModels:
    """Tests for the OpenAPI client models."""

    def test_agent_run_response(self):
        """Test AgentRunResponse model."""
        # Create a model instance
        model = AgentRunResponse(
            id="test_id",
            status="running",
            result="Test result",
            error="Test error",
        )

        # Verify the model attributes
        assert model.id == "test_id"
        assert model.status == "running"
        assert model.result == "Test result"
        assert model.error == "Test error"

        # Test to_dict method
        model_dict = model.to_dict()
        assert model_dict["id"] == "test_id"
        assert model_dict["status"] == "running"
        assert model_dict["result"] == "Test result"
        assert model_dict["error"] == "Test error"

        # Test from_dict method
        model2 = AgentRunResponse.from_dict(model_dict)
        assert model2.id == "test_id"
        assert model2.status == "running"
        assert model2.result == "Test result"
        assert model2.error == "Test error"

    def test_create_agent_run_input(self):
        """Test CreateAgentRunInput model."""
        # Create a model instance
        model = CreateAgentRunInput(
            prompt="Test prompt",
            model="gpt-4",
            temperature=0.7,
        )

        # Verify the model attributes
        assert model.prompt == "Test prompt"
        assert model.model == "gpt-4"
        assert model.temperature == 0.7

        # Test to_dict method
        model_dict = model.to_dict()
        assert model_dict["prompt"] == "Test prompt"
        assert model_dict["model"] == "gpt-4"
        assert model_dict["temperature"] == 0.7

        # Test from_dict method
        model2 = CreateAgentRunInput.from_dict(model_dict)
        assert model2.prompt == "Test prompt"
        assert model2.model == "gpt-4"
        assert model2.temperature == 0.7

    def test_organization_response(self):
        """Test OrganizationResponse model."""
        # Create a model instance
        model = OrganizationResponse(
            id=123,
            name="Test Org",
            settings=OrganizationSettings(github_pr_creation=True),
        )

        # Verify the model attributes
        assert model.id == 123
        assert model.name == "Test Org"
        assert isinstance(model.settings, OrganizationSettings)
        assert model.settings.github_pr_creation is True

        # Test to_dict method
        model_dict = model.to_dict()
        assert model_dict["id"] == 123
        assert model_dict["name"] == "Test Org"
        assert model_dict["settings"]["github_pr_creation"] is True

        # Test from_dict method
        model2 = OrganizationResponse.from_dict(model_dict)
        assert model2.id == 123
        assert model2.name == "Test Org"
        assert isinstance(model2.settings, OrganizationSettings)
        assert model2.settings.github_pr_creation is True

    def test_organization_settings(self):
        """Test OrganizationSettings model."""
        # Create a model instance
        model = OrganizationSettings(
            github_pr_creation=True,
            custom_model="gpt-4",
        )

        # Verify the model attributes
        assert model.github_pr_creation is True
        assert model.custom_model == "gpt-4"

        # Test to_dict method
        model_dict = model.to_dict()
        assert model_dict["github_pr_creation"] is True
        assert model_dict["custom_model"] == "gpt-4"

        # Test from_dict method
        model2 = OrganizationSettings.from_dict(model_dict)
        assert model2.github_pr_creation is True
        assert model2.custom_model == "gpt-4"

    def test_page_organization_response(self):
        """Test PageOrganizationResponse model."""
        # Create model instances
        org1 = OrganizationResponse(
            id=123,
            name="Test Org 1",
            settings=OrganizationSettings(github_pr_creation=True),
        )
        org2 = OrganizationResponse(
            id=456,
            name="Test Org 2",
            settings=OrganizationSettings(github_pr_creation=False),
        )

        # Create a page model instance
        model = PageOrganizationResponse(
            items=[org1, org2],
            total=2,
            page=1,
            size=10,
        )

        # Verify the model attributes
        assert len(model.items) == 2
        assert model.items[0].id == 123
        assert model.items[1].id == 456
        assert model.total == 2
        assert model.page == 1
        assert model.size == 10

        # Test to_dict method
        model_dict = model.to_dict()
        assert len(model_dict["items"]) == 2
        assert model_dict["items"][0]["id"] == 123
        assert model_dict["items"][1]["id"] == 456
        assert model_dict["total"] == 2
        assert model_dict["page"] == 1
        assert model_dict["size"] == 10

        # Test from_dict method
        model2 = PageOrganizationResponse.from_dict(model_dict)
        assert len(model2.items) == 2
        assert model2.items[0].id == 123
        assert model2.items[1].id == 456
        assert model2.total == 2
        assert model2.page == 1
        assert model2.size == 10

    def test_user_response(self):
        """Test UserResponse model."""
        # Create a model instance
        model = UserResponse(
            id=123,
            email="user@example.com",
            name="Test User",
        )

        # Verify the model attributes
        assert model.id == 123
        assert model.email == "user@example.com"
        assert model.name == "Test User"

        # Test to_dict method
        model_dict = model.to_dict()
        assert model_dict["id"] == 123
        assert model_dict["email"] == "user@example.com"
        assert model_dict["name"] == "Test User"

        # Test from_dict method
        model2 = UserResponse.from_dict(model_dict)
        assert model2.id == 123
        assert model2.email == "user@example.com"
        assert model2.name == "Test User"

    def test_page_user_response(self):
        """Test PageUserResponse model."""
        # Create model instances
        user1 = UserResponse(
            id=123,
            email="user1@example.com",
            name="Test User 1",
        )
        user2 = UserResponse(
            id=456,
            email="user2@example.com",
            name="Test User 2",
        )

        # Create a page model instance
        model = PageUserResponse(
            items=[user1, user2],
            total=2,
            page=1,
            size=10,
        )

        # Verify the model attributes
        assert len(model.items) == 2
        assert model.items[0].id == 123
        assert model.items[1].id == 456
        assert model.total == 2
        assert model.page == 1
        assert model.size == 10

        # Test to_dict method
        model_dict = model.to_dict()
        assert len(model_dict["items"]) == 2
        assert model_dict["items"][0]["id"] == 123
        assert model_dict["items"][1]["id"] == 456
        assert model_dict["total"] == 2
        assert model_dict["page"] == 1
        assert model_dict["size"] == 10

        # Test from_dict method
        model2 = PageUserResponse.from_dict(model_dict)
        assert len(model2.items) == 2
        assert model2.items[0].id == 123
        assert model2.items[1].id == 456
        assert model2.total == 2
        assert model2.page == 1
        assert model2.size == 10

    def test_http_validation_error(self):
        """Test HTTPValidationError model."""
        # Create model instances
        error_loc1 = ValidationErrorLocInner("body")
        error_loc2 = ValidationErrorLocInner("query")
        validation_error = ValidationError(
            loc=[error_loc1, error_loc2],
            msg="Field required",
            type="value_error.missing",
        )

        # Create a model instance
        model = HTTPValidationError(
            detail=[validation_error],
        )

        # Verify the model attributes
        assert len(model.detail) == 1
        assert len(model.detail[0].loc) == 2
        assert model.detail[0].loc[0].local_var_data == "body"
        assert model.detail[0].loc[1].local_var_data == "query"
        assert model.detail[0].msg == "Field required"
        assert model.detail[0].type == "value_error.missing"

        # Test to_dict method
        model_dict = model.to_dict()
        assert len(model_dict["detail"]) == 1
        assert len(model_dict["detail"][0]["loc"]) == 2
        assert model_dict["detail"][0]["loc"][0] == "body"
        assert model_dict["detail"][0]["loc"][1] == "query"
        assert model_dict["detail"][0]["msg"] == "Field required"
        assert model_dict["detail"][0]["type"] == "value_error.missing"

        # Test from_dict method
        model2 = HTTPValidationError.from_dict(model_dict)
        assert len(model2.detail) == 1
        assert len(model2.detail[0].loc) == 2
        assert model2.detail[0].loc[0].local_var_data == "body"
        assert model2.detail[0].loc[1].local_var_data == "query"
        assert model2.detail[0].msg == "Field required"
        assert model2.detail[0].type == "value_error.missing"

