# SWE-bench Agent Runner

This example demonstrates how to use the Codegen SDK with Modal to run and evaluate model fixes using SWE-bench.

## Prerequisites

- [Modal](https://modal.com/) account
- Python 3.12 or higher
- Codegen SDK (version 0.52.19 or higher)

## Setup

### 1. Install Dependencies

```bash
# Clone the repository
git clone https://github.com/Zeeeepa/codegen.git
cd codegen/codegen-examples/examples/swebench_agent_run

# Install dependencies
pip install -e .

# With metrics support
pip install -e ".[metrics]"

# With development tools
pip install -e ".[dev]"

# Install everything
pip install -e ".[all]"
```

### 2. Configure Environment Variables

Create a `.env` file with your credentials:

```
# API Keys
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# Modal configuration (optional)
MODAL_TOKEN_ID=your_modal_token_id
MODAL_TOKEN_SECRET=your_modal_token_secret
```

### 3. Authenticate with Modal

```bash
modal token new
```

## Deployment Commands

### Deploy to Modal

```bash
# Deploy the application to Modal
./deploy.sh
```

This will deploy the application to Modal and provide you with a URL that you can use to access it.

### Get Deployment Status

```bash
# Check the status of your Modal deployment
modal app status swebench-agent-run
```

### View Logs

```bash
# View logs from your Modal deployment
modal app logs swebench-agent-run
```

### Update Deployment

```bash
# Update your Modal deployment after making changes
./deploy.sh
```

### Stop Deployment

```bash
# Stop your Modal deployment
modal app stop swebench-agent-run
```

## Usage

The package provides two main command-line tools:

### Testing SWE CodeAgent

Run the agent on a specific repository:

```bash
# Using the installed command
swe-agent --repo pallets/flask --prompt "Analyze the URL routing system"

# Options
swe-agent --help
Options:
  --agent-class [DefaultAgent|CustomAgent]  Agent class to use
  --repo TEXT                               Repository to analyze (owner/repo)
  --prompt TEXT                             Prompt for the agent
  --help                                    Show this message and exit
```

### Running SWE-Bench Eval

Run evaluations on model fixes:

```bash
# Using the installed command
swe-eval --dataset lite --length 10

# Options
swe-eval --help
Options:
  --use-existing-preds TEXT      Run ID of existing predictions
  --dataset [lite|full|verified|lite_small|lite_medium|lite_large]
  --length INTEGER               Number of examples to process
  --instance-id TEXT             Specific instance ID to process
  --repo TEXT                    Specific repo to evaluate
  --local                        Run evaluation locally
  --instance-ids LIST_OF_STRINGS  The instance IDs of the examples to process.
                                  Example: --instance-ids <instance_id1>,<instance_id2>,...
  --push-metrics                 Push results to metrics database (Requires additional database environment variables)
  --help                         Show this message and exit
```

## Customizing the Application

You can customize the application by modifying the following files:

- `agent_cli.py`: Command-line interface for running the agent
- `eval_cli.py`: Command-line interface for running evaluations
- `swebench_agent_run/modal_harness/entry_point.py`: Modal entry point for the application

## Troubleshooting

- **Deployment issues**: Run `modal app logs swebench-agent-run` to view logs and diagnose issues.
- **Authentication errors**: Check that your API keys are correctly set in your `.env` file.
- **Database connection issues**: If using metrics, ensure your database credentials are correctly configured.

## Additional Resources

- [Codegen Documentation](https://docs.codegen.sh/)
- [Modal Documentation](https://modal.com/docs)
- [SWE-bench Documentation](https://github.com/princeton-nlp/SWE-bench)
