# SWE-Bench Agent Run

This example demonstrates how to run Codegen agents on the SWE-Bench benchmark using Modal.

## Prerequisites

Before you begin, ensure you have the following installed:
- Python 3.10+
- [Modal CLI](https://modal.com/docs/guide/cli-reference)
- [Codegen SDK](https://docs.codegen.com) version 0.52.19
- [SWE-Bench](https://github.com/princeton-nlp/SWE-bench) dependencies

## Setup

1. Install the required dependencies:

```bash
pip install modal codegen==0.52.19
pip install -e .
```

2. Authenticate with Modal:

```bash
modal token new
```

3. Configure your environment variables:

```bash
cp .env.template .env
```

Edit the `.env` file and add your API keys:

```
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
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

Deploy modal app

```bash
./deploy.sh
```

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
