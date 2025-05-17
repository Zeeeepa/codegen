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


def test_codemod_run_type():
    """Test CodemodRunType enum."""
    # Check that the enum has the expected values
    assert CodemodRunType.DIFF == "diff"
    assert CodemodRunType.PR == "pr"
    
    # Check that the enum can be converted to and from strings
    assert CodemodRunType("diff") == CodemodRunType.DIFF
    assert CodemodRunType("pr") == CodemodRunType.PR
    
    # Check that invalid values raise an error
    with pytest.raises(ValueError):
        CodemodRunType("invalid")


def test_run_codemod_input():
    """Test RunCodemodInput model."""
    # Create a valid input
    input_data = RunCodemodInput(
        input=RunCodemodInput.BaseRunCodemodInput(
            codemod_name="test_codemod",
            repo_full_name="test-owner/test-repo",
            codemod_run_type=CodemodRunType.DIFF,
            codemod_source="def test_codemod():\n    pass",
            template_context={"key": "value"},
        )
    )
    
    # Check that the input is valid
    assert input_data.input.codemod_name == "test_codemod"
    assert input_data.input.repo_full_name == "test-owner/test-repo"
    assert input_data.input.codemod_run_type == CodemodRunType.DIFF
    assert input_data.input.codemod_source == "def test_codemod():\n    pass"
    assert input_data.input.template_context == {"key": "value"}
    
    # Check that the model can be converted to a dict
    data_dict = input_data.model_dump()
    assert data_dict["input"]["codemod_name"] == "test_codemod"
    assert data_dict["input"]["repo_full_name"] == "test-owner/test-repo"
    assert data_dict["input"]["codemod_run_type"] == "diff"
    assert data_dict["input"]["codemod_source"] == "def test_codemod():\n    pass"
    assert data_dict["input"]["template_context"] == {"key": "value"}


def test_run_codemod_output():
    """Test RunCodemodOutput model."""
    # Create a valid output
    output_data = RunCodemodOutput(result="Success")
    
    # Check that the output is valid
    assert output_data.result == "Success"
    
    # Check that the model can be converted to a dict
    data_dict = output_data.model_dump()
    assert data_dict["result"] == "Success"


def test_docs_input():
    """Test DocsInput model."""
    # Create a valid input
    input_data = DocsInput(
        docs_input=DocsInput.BaseDocsInput(
            repo_full_name="test-owner/test-repo",
        )
    )
    
    # Check that the input is valid
    assert input_data.docs_input.repo_full_name == "test-owner/test-repo"
    
    # Check that the model can be converted to a dict
    data_dict = input_data.model_dump()
    assert data_dict["docs_input"]["repo_full_name"] == "test-owner/test-repo"


def test_docs_response():
    """Test DocsResponse model."""
    # Create a valid response
    response_data = DocsResponse(docs="Documentation")
    
    # Check that the response is valid
    assert response_data.docs == "Documentation"
    
    # Check that the model can be converted to a dict
    data_dict = response_data.model_dump()
    assert data_dict["docs"] == "Documentation"


def test_ask_expert_input():
    """Test AskExpertInput model."""
    # Create a valid input
    input_data = AskExpertInput(
        input=AskExpertInput.BaseAskExpertInput(
            query="How do I use codegen?",
        )
    )
    
    # Check that the input is valid
    assert input_data.input.query == "How do I use codegen?"
    
    # Check that the model can be converted to a dict
    data_dict = input_data.model_dump()
    assert data_dict["input"]["query"] == "How do I use codegen?"


def test_ask_expert_response():
    """Test AskExpertResponse model."""
    # Create a valid response
    response_data = AskExpertResponse(answer="This is the answer.")
    
    # Check that the response is valid
    assert response_data.answer == "This is the answer."
    
    # Check that the model can be converted to a dict
    data_dict = response_data.model_dump()
    assert data_dict["answer"] == "This is the answer."


def test_create_input():
    """Test CreateInput model."""
    # Create a valid input
    input_data = CreateInput(
        input=CreateInput.BaseCreateInput(
            name="test_codemod",
            query="Create a codemod that does something",
            language=ProgrammingLanguage.PYTHON,
        )
    )
    
    # Check that the input is valid
    assert input_data.input.name == "test_codemod"
    assert input_data.input.query == "Create a codemod that does something"
    assert input_data.input.language == ProgrammingLanguage.PYTHON
    
    # Check that the model can be converted to a dict
    data_dict = input_data.model_dump()
    assert data_dict["input"]["name"] == "test_codemod"
    assert data_dict["input"]["query"] == "Create a codemod that does something"
    assert data_dict["input"]["language"] == "PYTHON"


def test_create_response():
    """Test CreateResponse model."""
    # Create a valid response
    response_data = CreateResponse(codemod="def test_codemod():\n    pass")
    
    # Check that the response is valid
    assert response_data.codemod == "def test_codemod():\n    pass"
    
    # Check that the model can be converted to a dict
    data_dict = response_data.model_dump()
    assert data_dict["codemod"] == "def test_codemod():\n    pass"


def test_identify_response():
    """Test IdentifyResponse model."""
    # Create a valid response
    response_data = IdentifyResponse(
        codemod_name="test_codemod",
        codemod_source="def test_codemod():\n    pass",
    )
    
    # Check that the response is valid
    assert response_data.codemod_name == "test_codemod"
    assert response_data.codemod_source == "def test_codemod():\n    pass"
    
    # Check that the model can be converted to a dict
    data_dict = response_data.model_dump()
    assert data_dict["codemod_name"] == "test_codemod"
    assert data_dict["codemod_source"] == "def test_codemod():\n    pass"


def test_deploy_input():
    """Test DeployInput model."""
    # Create a valid input
    input_data = DeployInput(
        input=DeployInput.BaseDeployInput(
            codemod_name="test_codemod",
            codemod_source="def test_codemod():\n    pass",
            repo_full_name="test-owner/test-repo",
            lint_mode=True,
            lint_user_whitelist=["user1", "user2"],
            message="Deployment message",
            arguments_schema={"type": "object", "properties": {"key": {"type": "string"}}},
        )
    )
    
    # Check that the input is valid
    assert input_data.input.codemod_name == "test_codemod"
    assert input_data.input.codemod_source == "def test_codemod():\n    pass"
    assert input_data.input.repo_full_name == "test-owner/test-repo"
    assert input_data.input.lint_mode is True
    assert input_data.input.lint_user_whitelist == ["user1", "user2"]
    assert input_data.input.message == "Deployment message"
    assert input_data.input.arguments_schema == {"type": "object", "properties": {"key": {"type": "string"}}}
    
    # Check that the model can be converted to a dict
    data_dict = input_data.model_dump()
    assert data_dict["input"]["codemod_name"] == "test_codemod"
    assert data_dict["input"]["codemod_source"] == "def test_codemod():\n    pass"
    assert data_dict["input"]["repo_full_name"] == "test-owner/test-repo"
    assert data_dict["input"]["lint_mode"] is True
    assert data_dict["input"]["lint_user_whitelist"] == ["user1", "user2"]
    assert data_dict["input"]["message"] == "Deployment message"
    assert data_dict["input"]["arguments_schema"] == {"type": "object", "properties": {"key": {"type": "string"}}}


def test_deploy_response():
    """Test DeployResponse model."""
    # Create a valid response
    response_data = DeployResponse(
        success=True,
        message="Deployment successful",
    )
    
    # Check that the response is valid
    assert response_data.success is True
    assert response_data.message == "Deployment successful"
    
    # Check that the model can be converted to a dict
    data_dict = response_data.model_dump()
    assert data_dict["success"] is True
    assert data_dict["message"] == "Deployment successful"

