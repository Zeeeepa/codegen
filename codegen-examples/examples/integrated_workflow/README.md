# Integrated AI Development Workflow

This example demonstrates how to create a complete AI-powered development workflow by integrating multiple components from the Codegen toolkit:

1. **Issue Solver Agent** - Automatically solves coding issues
2. **PR Review Bot** - Reviews pull requests and provides feedback
3. **Event Handlers** - Responds to events from GitHub, Slack, and Linear
4. **Knowledge Transfer Visualization** - Visualizes how AI-generated patterns spread through the codebase

## Architecture

The integrated workflow creates a complete feedback loop:

1. Issues are created in GitHub or Linear
2. Event handlers detect new issues and trigger the Issue Solver Agent
3. The Issue Solver Agent analyzes and fixes the issues
4. Pull requests are created with the solutions
5. The PR Review Bot reviews the PRs and provides feedback
6. Knowledge Transfer Visualization tracks how AI-generated patterns are adopted by developers

![Integrated Workflow Architecture](./architecture.png)

## Components

### Issue Solver Agent

The Issue Solver Agent is responsible for automatically solving coding issues. It:

- Analyzes issue descriptions to understand the problem
- Examines the codebase to identify the root cause
- Generates and tests solutions
- Creates pull requests with the fixes

### PR Review Bot

The PR Review Bot reviews pull requests and provides feedback. It:

- Analyzes code changes for quality, style, and potential issues
- Provides line-by-line feedback on the PR
- Suggests improvements and alternatives
- Checks for test coverage and documentation

### Event Handlers

The Event Handlers respond to events from GitHub, Slack, and Linear. They:

- Listen for new issues, PRs, and comments
- Trigger the appropriate agents based on the event type
- Maintain codebase snapshots for fast analysis
- Post results back to the originating platform

### Knowledge Transfer Visualization

The Knowledge Transfer Visualization tracks how AI-generated patterns are adopted by developers. It:

- Analyzes commit history to identify pattern origins
- Tracks pattern adoption across the codebase
- Visualizes knowledge transfer between AI and human developers
- Provides insights into effective AI-human collaboration

## Setup

### Prerequisites

- Python 3.9+
- Modal account (for deployment)
- GitHub, Slack, and Linear API tokens

### Installation

```bash
pip install -e ".[dev]"
```

### Configuration

Create a `.env` file with the following variables:

```
GITHUB_TOKEN=your_github_token
SLACK_BOT_TOKEN=your_slack_bot_token
SLACK_APP_TOKEN=your_slack_app_token
LINEAR_API_KEY=your_linear_api_key
MODAL_TOKEN_ID=your_modal_token_id
MODAL_TOKEN_SECRET=your_modal_token_secret
```

## Usage

### Local Development

Run the integrated workflow locally:

```bash
python codegen-examples/examples/integrated_workflow/app.py
```

### Deployment

Deploy the integrated workflow to Modal:

```bash
modal deploy codegen-examples/examples/integrated_workflow/app.py
```

## Example Workflow

1. A user creates an issue in GitHub: "Fix the authentication bug in login.py"
2. The event handler detects the new issue and triggers the Issue Solver Agent
3. The Issue Solver Agent analyzes the issue and identifies the bug in login.py
4. The agent creates a PR with the fix
5. The PR Review Bot reviews the PR and provides feedback
6. The agent updates the PR based on the feedback
7. The PR is merged
8. The Knowledge Transfer Visualization tracks how the pattern used in the fix is adopted by developers

## Customization

You can customize the workflow by:

- Adding custom event handlers for specific event types
- Creating specialized agents for different types of issues
- Configuring the PR Review Bot to enforce specific code standards
- Extending the Knowledge Transfer Visualization with additional metrics

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
