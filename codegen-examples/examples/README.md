# Codegen Examples

This directory contains a collection of examples demonstrating various use cases of the [Codegen](https://codegen.com) SDK.

## Types of Examples

The examples in this directory fall into two main categories:

1. **Code Transformation Examples**: One-time utilities that transform code in various ways (e.g., migrating from one library to another, converting code patterns, etc.)

2. **Modal-based Service Examples**: Applications that can be deployed as services using [Modal](https://modal.com), such as chatbots, webhooks handlers, and analytics tools.

## Using the Modal Deployer

For Modal-based examples, we provide a convenient deployment tool called `Deployer.sh` that allows you to interactively select and deploy multiple examples concurrently.

### Prerequisites

- Python 3.9 or higher
- [Modal](https://modal.com/) account and CLI
- Git

### Running the Deployer

To use the deployer:

```bash
# Navigate to the examples directory
cd examples

# Run the deployer script
bash Deployer.sh
```

The deployer will:

1. Check for required dependencies (Python, Modal)
2. Display a list of deployable examples
3. Allow you to select which examples to deploy
4. Deploy the selected examples concurrently
5. Provide a summary of deployment results
6. Offer options to view logs or status of deployed examples

### Available Modal Examples

The following examples can be deployed using the Deployer.sh script:

- `ai_impact_analysis`: Analyze the impact of AI on codebases
- `codegen-mcp-server`: MCP server implementation
- `codegen_app`: Codegen web application
- `cyclomatic_complexity`: Calculate cyclomatic complexity of code
- `deep_code_research`: Deep research on code repositories
- `delete_dead_code`: Identify and remove dead code
- `document_functions`: Automatically document functions
- `github_checks`: GitHub checks integration
- `linear_webhooks`: Linear webhooks handler
- `modal_repo_analytics`: Repository analytics using Modal
- `pr_review_bot`: PR review automation
- `repo_analytics`: Repository analytics tools
- `slack_chatbot`: Slack chatbot integration
- `snapshot_event_handler`: Event handler for snapshots
- `swebench_agent_run`: SWE benchmark agent
- `ticket-to-pr`: Convert tickets to PRs

Each of these examples has its own `deploy.sh` script and README with specific deployment instructions.

## Running Non-Modal Examples

For examples that don't have a `deploy.sh` script, you can run them locally following the instructions in their respective README files. These examples typically perform one-time code transformations and don't need to be deployed as services.

## Contributing

If you'd like to add a new example, please follow the [Contributing Guide](../CONTRIBUTING.md) for instructions.

## License

All examples are licensed under the [Apache 2.0 license](../LICENSE).

