# Codegen Examples

This directory contains examples of how to use the Codegen SDK with Modal for various use cases. Each example is a standalone application that can be deployed to Modal.

## Prerequisites

- [Modal](https://modal.com/) account
- [Python](https://www.python.org/) 3.13 or higher
- [Codegen SDK](https://github.com/Zeeeepa/codegen) version 0.52.19 or higher

## Getting Started

1. Clone the repository:

   ```bash
   git clone https://github.com/Zeeeepa/codegen.git
   cd codegen/codegen-examples/examples
   ```

1. Install Modal CLI:

   ```bash
   pip install modal
   ```

1. Authenticate with Modal:

   ```bash
   modal token new
   ```

## Using the Deployer

The `Deployer.sh` script allows you to interactively select and deploy multiple examples concurrently.

```bash
# Make the script executable
chmod +x Deployer.sh

# Run the deployer
./Deployer.sh
```

The deployer will show you a list of available examples and allow you to select which ones to deploy. You can select multiple examples by entering their numbers separated by spaces, or select all deployable examples by entering `all`.

## Available Examples

Here's a list of the available examples:

1. **swebench_agent_run**: Run SWEBench agent tasks using Codegen and Modal.
1. **snapshot_event_handler**: Handle snapshot events from GitHub.
1. **slack_chatbot**: Create a Slack chatbot using Codegen and Modal.
1. **repo_analytics**: Analyze GitHub repositories and generate insights.
1. **pr_review_bot**: Automatically review pull requests on GitHub.
1. **github_checks**: Create GitHub checks for your repositories.
1. **linear_webhooks**: Handle Linear webhook events.
1. **modal_repo_analytics**: Analyze Modal repositories.
1. **deep_code_research**: Perform deep code research using Codegen.
1. **cyclomatic_complexity**: Calculate cyclomatic complexity of code.
1. **delete_dead_code**: Identify and delete dead code in repositories.
1. **document_functions**: Automatically document functions in code.
1. **codegen-mcp-server**: Run a Model Context Protocol server.
1. **codegen_app**: Create a Codegen application.
1. **ai_impact_analysis**: Analyze the impact of AI on code.

Each example has its own README.md file with detailed instructions on how to set it up and use it.

## Deploying Individual Examples

Each example has a `deploy.sh` script that can be used to deploy it to Modal. To deploy an individual example:

```bash
cd example_name
./deploy.sh
```

## Customizing Examples

You can customize the examples by modifying the code in each example directory. The examples are designed to be simple and easy to understand, so you can use them as a starting point for your own applications.

## Troubleshooting

If you encounter issues with the examples, check the following:

- Make sure you have the correct version of the Codegen SDK installed (0.52.19 or higher).
- Make sure you have authenticated with Modal using `modal token new`.
- Check the logs of your Modal deployment using `modal app logs app_name`.
- Make sure you have set up any required environment variables or configuration files.

## Contributing

If you have ideas for new examples or improvements to existing ones, please open an issue or pull request on the [Codegen repository](https://github.com/Zeeeepa/codegen).
