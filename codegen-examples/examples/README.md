# Codegen Examples

This directory contains examples of how to use the Codegen SDK for various tasks.

## Modal Deployment Examples

These examples demonstrate how to deploy Codegen applications using Modal:

- [hello_world](./hello_world): A simple Modal app with web endpoint and scheduled function
- [modal_repo_analytics](./modal_repo_analytics): Analyze GitHub repositories using Codegen
- [modal_repo_rag](./modal_repo_rag): RAG-based code Q&A using Codegen's VectorIndex
- [linear_webhooks](./linear_webhooks): Handle Linear webhooks and analyze mentioned repos
- [swebench_agent_run](./swebench_agent_run): Run Codegen agents on the SWE-Bench benchmark

## Code Transformation Examples

These examples demonstrate how to use Codegen for code transformation tasks:

- [flask_to_fastapi_migration](./flask_to_fastapi_migration): Migrate a Flask app to FastAPI
- [python2_to_python3](./python2_to_python3): Convert Python 2 code to Python 3
- [promises_to_async_await](./promises_to_async_await): Convert JavaScript Promises to async/await
- [sqlalchemy_1.6_to_2.0](./sqlalchemy_1.6_to_2.0): Migrate SQLAlchemy 1.6 code to 2.0
- [freezegun_to_timemachine_migration](./freezegun_to_timemachine_migration): Migrate from freezegun to timemachine
- [unittest_to_pytest](./unittest_to_pytest): Convert unittest tests to pytest

## Code Analysis Examples

These examples demonstrate how to use Codegen for code analysis tasks:

- [cyclomatic_complexity](./cyclomatic_complexity): Calculate cyclomatic complexity of code
- [deep_code_research](./deep_code_research): Perform deep research on codebases
- [modules_dependencies](./modules_dependencies): Analyze module dependencies
- [repo_analytics](./repo_analytics): Extract analytics from repositories
- [visualize_codebases](./visualize_codebases): Create visualizations of codebases

## Code Generation Examples

These examples demonstrate how to use Codegen for code generation tasks:

- [document_functions](./document_functions): Generate documentation for functions
- [generate_training_data](./generate_training_data): Generate training data for ML models
- [openapi_decorators](./openapi_decorators): Generate OpenAPI decorators for API endpoints

## Code Cleanup Examples

These examples demonstrate how to use Codegen for code cleanup tasks:

- [delete_dead_code](./delete_dead_code): Identify and remove dead code
- [removing_import_loops_in_pytorch](./removing_import_loops_in_pytorch): Fix import loops
- [sqlalchemy_soft_delete](./sqlalchemy_soft_delete): Implement soft delete in SQLAlchemy
- [sqlalchemy_type_annotations](./sqlalchemy_type_annotations): Add type annotations to SQLAlchemy models

## Integration Examples

These examples demonstrate how to integrate Codegen with other tools:

- [github_checks](./github_checks): Integrate Codegen with GitHub Checks
- [langchain_agent](./langchain_agent): Use Codegen with LangChain agents
- [pr_review_bot](./pr_review_bot): Create a PR review bot with Codegen
- [slack_chatbot](./slack_chatbot): Build a Slack chatbot with Codegen
- [ticket-to-pr](./ticket-to-pr): Automate PR creation from tickets

## Prerequisites

Before running these examples, ensure you have:

1. Python 3.10+ installed
1. Codegen SDK installed: `pip install codegen==0.52.19`
1. For Modal examples, Modal CLI installed: `pip install modal`

## Using the Deployer Script

The `Deployer.sh` script allows you to interactively select and deploy multiple Modal examples concurrently.

To use it:

1. Make sure the script is executable:

   ```bash
   chmod +x Deployer.sh
   ```

1. Run the script:

   ```bash
   ./Deployer.sh
   ```

1. Select the examples you want to deploy when prompted:

   - Enter the numbers of the examples (space-separated)
   - Or enter 'all' to deploy all examples

1. Confirm your selection

The script will deploy the selected examples concurrently and show the deployment status.

## Additional Resources

- [Codegen Documentation](https://docs.codegen.com)
- [Modal Documentation](https://modal.com/docs/guide)
- [Codegen GitHub Repository](https://github.com/Zeeeepa/codegen)
