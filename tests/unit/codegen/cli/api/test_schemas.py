"""Unit tests for the CLI API schemas."""

import pytest
from pydantic import ValidationError

from codegen.cli.api.schemas import (
    AskExpertInput,
    AskExpertResponse,
    CodemodRunType,
    CreateInput,
    CreateResponse,
    DeployInput,
    DeployResponse,
    DocsInput,
    DocsResponse,
    IdentifyResponse,
    ImproveCodemodInput,
    ImproveCodemodResponse,
    LookupInput,
    LookupOutput,
    PRLookupInput,
    PRLookupResponse,
    RunCodemodInput,
    RunCodemodOutput,
    RunOnPRInput,
    RunOnPRResponse,
)
from codegen.shared.enums.programming_language import ProgrammingLanguage


class TestSchemas:
    """Tests for the CLI API schemas."""

    def test_codemod_run_type_enum(self):
        """Test CodemodRunType enum."""
        assert CodemodRunType.DIFF == "diff"
        assert CodemodRunType.PR == "pr"

    def test_run_codemod_input(self):
        """Test RunCodemodInput schema."""
        # Test with minimal fields
        input_data = RunCodemodInput(
            input=RunCodemodInput.BaseRunCodemodInput(
                repo_full_name="test/repo",
                codemod_name="test_codemod",
            )
        )
        assert input_data.input.repo_full_name == "test/repo"
        assert input_data.input.codemod_name == "test_codemod"
        assert input_data.input.codemod_id is None
        assert input_data.input.codemod_source is None
        assert input_data.input.codemod_run_type == CodemodRunType.DIFF
        assert input_data.input.template_context == {}

        # Test with all fields
        input_data = RunCodemodInput(
            input=RunCodemodInput.BaseRunCodemodInput(
                repo_full_name="test/repo",
                codemod_id=123,
                codemod_name="test_codemod",
                codemod_source="def test(): pass",
                codemod_run_type=CodemodRunType.PR,
                template_context={"key": "value"},
            )
        )
        assert input_data.input.repo_full_name == "test/repo"
        assert input_data.input.codemod_id == 123
        assert input_data.input.codemod_name == "test_codemod"
        assert input_data.input.codemod_source == "def test(): pass"
        assert input_data.input.codemod_run_type == CodemodRunType.PR
        assert input_data.input.template_context == {"key": "value"}

    def test_run_codemod_output(self):
        """Test RunCodemodOutput schema."""
        # Test with minimal fields
        output_data = RunCodemodOutput()
        assert output_data.success is False
        assert output_data.web_link is None
        assert output_data.logs is None
        assert output_data.observation is None
        assert output_data.error is None

        # Test with all fields
        output_data = RunCodemodOutput(
            success=True,
            web_link="https://example.com",
            logs="Test logs",
            observation="Test observation",
            error="Test error",
        )
        assert output_data.success is True
        assert output_data.web_link == "https://example.com"
        assert output_data.logs == "Test logs"
        assert output_data.observation == "Test observation"
        assert output_data.error == "Test error"

    def test_ask_expert_input(self):
        """Test AskExpertInput schema."""
        input_data = AskExpertInput(
            input=AskExpertInput.BaseAskExpertInput(
                query="How do I use the API?",
            )
        )
        assert input_data.input.query == "How do I use the API?"

    def test_ask_expert_response(self):
        """Test AskExpertResponse schema."""
        # Test with minimal fields
        response_data = AskExpertResponse()
        assert response_data.success is False
        assert response_data.response is None
        assert response_data.error is None

        # Test with all fields
        response_data = AskExpertResponse(
            success=True,
            response="Expert response",
            error="Test error",
        )
        assert response_data.success is True
        assert response_data.response == "Expert response"
        assert response_data.error == "Test error"

    def test_docs_input(self):
        """Test DocsInput schema."""
        input_data = DocsInput(
            docs_input=DocsInput.BaseDocsInput(
                repo_full_name="test/repo",
            )
        )
        assert input_data.docs_input.repo_full_name == "test/repo"

    def test_docs_response(self):
        """Test DocsResponse schema."""
        # Test with minimal fields
        response_data = DocsResponse()
        assert response_data.success is False
        assert response_data.docs is None
        assert response_data.error is None

        # Test with all fields
        response_data = DocsResponse(
            success=True,
            docs="Test docs",
            error="Test error",
        )
        assert response_data.success is True
        assert response_data.docs == "Test docs"
        assert response_data.error == "Test error"

    def test_create_input(self):
        """Test CreateInput schema."""
        input_data = CreateInput(
            input=CreateInput.BaseCreateInput(
                name="test_codemod",
                query="Create a test codemod",
                language=ProgrammingLanguage.PYTHON,
            )
        )
        assert input_data.input.name == "test_codemod"
        assert input_data.input.query == "Create a test codemod"
        assert input_data.input.language == ProgrammingLanguage.PYTHON

    def test_create_response(self):
        """Test CreateResponse schema."""
        # Test with minimal fields
        response_data = CreateResponse()
        assert response_data.success is False
        assert response_data.codemod is None
        assert response_data.error is None

        # Test with all fields
        response_data = CreateResponse(
            success=True,
            codemod="def test(): pass",
            error="Test error",
        )
        assert response_data.success is True
        assert response_data.codemod == "def test(): pass"
        assert response_data.error == "Test error"

    def test_identify_response(self):
        """Test IdentifyResponse schema."""
        # Test with minimal fields
        response_data = IdentifyResponse()
        assert response_data.success is False
        assert response_data.codemod_name is None
        assert response_data.error is None

        # Test with all fields
        response_data = IdentifyResponse(
            success=True,
            codemod_name="test_codemod",
            error="Test error",
        )
        assert response_data.success is True
        assert response_data.codemod_name == "test_codemod"
        assert response_data.error == "Test error"

    def test_deploy_input(self):
        """Test DeployInput schema."""
        input_data = DeployInput(
            input=DeployInput.BaseDeployInput(
                codemod_name="test_codemod",
                codemod_source="def test(): pass",
                repo_full_name="test/repo",
                lint_mode=True,
                lint_user_whitelist=["user1", "user2"],
                message="Test message",
                arguments_schema={"arg1": "string"},
            )
        )
        assert input_data.input.codemod_name == "test_codemod"
        assert input_data.input.codemod_source == "def test(): pass"
        assert input_data.input.repo_full_name == "test/repo"
        assert input_data.input.lint_mode is True
        assert input_data.input.lint_user_whitelist == ["user1", "user2"]
        assert input_data.input.message == "Test message"
        assert input_data.input.arguments_schema == {"arg1": "string"}

    def test_deploy_response(self):
        """Test DeployResponse schema."""
        # Test with minimal fields
        response_data = DeployResponse()
        assert response_data.success is False
        assert response_data.codemod_id is None
        assert response_data.error is None

        # Test with all fields
        response_data = DeployResponse(
            success=True,
            codemod_id=123,
            error="Test error",
        )
        assert response_data.success is True
        assert response_data.codemod_id == 123
        assert response_data.error == "Test error"

    def test_lookup_input(self):
        """Test LookupInput schema."""
        input_data = LookupInput(
            input=LookupInput.BaseLookupInput(
                codemod_name="test_codemod",
                repo_full_name="test/repo",
            )
        )
        assert input_data.input.codemod_name == "test_codemod"
        assert input_data.input.repo_full_name == "test/repo"

    def test_lookup_output(self):
        """Test LookupOutput schema."""
        # Test with minimal fields
        output_data = LookupOutput()
        assert output_data.success is False
        assert output_data.codemod_source is None
        assert output_data.error is None

        # Test with all fields
        output_data = LookupOutput(
            success=True,
            codemod_source="def test(): pass",
            error="Test error",
        )
        assert output_data.success is True
        assert output_data.codemod_source == "def test(): pass"
        assert output_data.error == "Test error"

    def test_run_on_pr_input(self):
        """Test RunOnPRInput schema."""
        input_data = RunOnPRInput(
            input=RunOnPRInput.BaseRunOnPRInput(
                codemod_name="test_codemod",
                repo_full_name="test/repo",
                github_pr_number=123,
                language="python",
            )
        )
        assert input_data.input.codemod_name == "test_codemod"
        assert input_data.input.repo_full_name == "test/repo"
        assert input_data.input.github_pr_number == 123
        assert input_data.input.language == "python"

    def test_run_on_pr_response(self):
        """Test RunOnPRResponse schema."""
        # Test with minimal fields
        response_data = RunOnPRResponse()
        assert response_data.success is False
        assert response_data.message is None
        assert response_data.error is None

        # Test with all fields
        response_data = RunOnPRResponse(
            success=True,
            message="PR processed",
            error="Test error",
        )
        assert response_data.success is True
        assert response_data.message == "PR processed"
        assert response_data.error == "Test error"

    def test_pr_lookup_input(self):
        """Test PRLookupInput schema."""
        input_data = PRLookupInput(
            input=PRLookupInput.BasePRLookupInput(
                repo_full_name="test/repo",
                github_pr_number=123,
            )
        )
        assert input_data.input.repo_full_name == "test/repo"
        assert input_data.input.github_pr_number == 123

    def test_pr_lookup_response(self):
        """Test PRLookupResponse schema."""
        # Test with minimal fields
        response_data = PRLookupResponse()
        assert response_data.success is False
        assert response_data.pr_data is None
        assert response_data.error is None

        # Test with all fields
        response_data = PRLookupResponse(
            success=True,
            pr_data={"number": 123},
            error="Test error",
        )
        assert response_data.success is True
        assert response_data.pr_data == {"number": 123}
        assert response_data.error == "Test error"

    def test_improve_codemod_input(self):
        """Test ImproveCodemodInput schema."""
        input_data = ImproveCodemodInput(
            input=ImproveCodemodInput.BaseImproveCodemodInput(
                codemod="def test(): pass",
                task="Improve the codemod",
                concerns=["performance", "readability"],
                context={"file": "test.py"},
                language=ProgrammingLanguage.PYTHON,
            )
        )
        assert input_data.input.codemod == "def test(): pass"
        assert input_data.input.task == "Improve the codemod"
        assert input_data.input.concerns == ["performance", "readability"]
        assert input_data.input.context == {"file": "test.py"}
        assert input_data.input.language == ProgrammingLanguage.PYTHON

    def test_improve_codemod_response(self):
        """Test ImproveCodemodResponse schema."""
        # Test with minimal fields
        response_data = ImproveCodemodResponse()
        assert response_data.success is False
        assert response_data.improved_codemod is None
        assert response_data.error is None

        # Test with all fields
        response_data = ImproveCodemodResponse(
            success=True,
            improved_codemod="def improved(): pass",
            error="Test error",
        )
        assert response_data.success is True
        assert response_data.improved_codemod == "def improved(): pass"
        assert response_data.error == "Test error"

