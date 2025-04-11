# Integrated AI Development Workflow

This example demonstrates how to create a complete AI-powered development workflow by integrating multiple components from the Codegen toolkit:

1. **Issue Solver Agent** - Automatically solves coding issues
2. **PR Review Bot** - Reviews pull requests and provides feedback
3. **Slack Chatbot** - Provides a chat interface for interacting with the system
4. **Snapshot Event Handler** - Maintains codebase snapshots for fast analysis
5. **Ticket-to-PR** - Converts tickets to pull requests
6. **Linear Webhooks** - Handles Linear events
7. **Codegen App** - Provides a unified interface for all components

## Architecture

The integrated workflow creates a complete feedback loop:

1. Issues are created in GitHub or Linear
2. Event handlers detect new issues and trigger the Issue Solver Agent
3. The Issue Solver Agent analyzes and fixes the issues
4. Pull requests are created with the solutions
5. The PR Review Bot reviews the PRs and provides feedback
6. Knowledge Transfer Visualization tracks how AI-generated patterns are adopted by developers
7. Slack Chatbot provides a user interface for interacting with the system

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

### Slack Chatbot

The Slack Chatbot provides a chat interface for interacting with the system. It:

- Responds to user commands and questions
- Triggers actions like solving issues or reviewing PRs
- Provides notifications about system events
- Offers a help system for users

### Snapshot Event Handler

The Snapshot Event Handler maintains codebase snapshots for fast analysis. It:

- Creates and updates snapshots of the codebase
- Provides fast access to code structure and dependencies
- Enables quick analysis of code changes
- Improves performance of code analysis tools

### Ticket-to-PR

The Ticket-to-PR component converts tickets to pull requests. It:

- Monitors Linear for new tickets
- Converts tickets with specific labels to GitHub issues
- Triggers the Issue Solver Agent to create solutions
- Updates the ticket with the PR link

### Linear Webhooks

The Linear Webhooks component handles Linear events. It:

- Listens for events from Linear (issue created, updated, etc.)
- Triggers appropriate actions based on the event type
- Synchronizes Linear tickets with GitHub issues
- Provides notifications about Linear events

### Codegen App

The Codegen App provides a unified interface for all components. It:

- Manages connections to external services (GitHub, Slack, Linear)
- Provides a consistent API for all components
- Handles authentication and authorization
- Manages codebase snapshots and analysis

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
python codegen-examples/examples/integrated_workflow/app.py your-org/your-repo
```

### Deployment

Deploy the integrated workflow to Modal:

```bash
modal deploy codegen-examples/examples/integrated_workflow/app.py
```

## Example Workflows

### GitHub Issue to PR

1. A user creates an issue in GitHub: "Fix the authentication bug in login.py"
2. The issue is labeled with "auto-fix"
3. The event handler detects the new issue and triggers the Issue Solver Agent
4. The agent analyzes the issue and identifies the bug in login.py
5. The agent creates a PR with the fix
6. The PR Review Bot reviews the PR and provides feedback
7. The agent updates the PR based on the feedback
8. The PR is merged
9. The Knowledge Transfer Visualization tracks how the pattern used in the fix is adopted by developers

### Linear Ticket to PR

1. A user creates a ticket in Linear: "Implement user profile page"
2. The ticket is labeled with "needs-pr"
3. The Linear webhook detects the new ticket and triggers the Ticket-to-PR component
4. The Ticket-to-PR component creates a GitHub issue
5. The Issue Solver Agent analyzes the issue and implements the user profile page
6. The agent creates a PR with the implementation
7. The PR Review Bot reviews the PR and provides feedback
8. The Linear ticket is updated with the PR link
9. The PR is merged
10. The Knowledge Transfer Visualization tracks how the pattern used in the implementation is adopted by developers

### Slack Command

1. A user sends a message in Slack: "@codegen solve issue 123"
2. The Slack Chatbot detects the command and triggers the Issue Solver Agent
3. The agent analyzes the issue and identifies the bug
4. The agent creates a PR with the fix
5. The PR Review Bot reviews the PR and provides feedback
6. The Slack Chatbot notifies the user that the PR has been created
7. The PR is merged
8. The Knowledge Transfer Visualization tracks how the pattern used in the fix is adopted by developers

## Customization

You can customize the workflow by:

- Adding custom event handlers for specific event types
- Creating specialized agents for different types of issues
- Configuring the PR Review Bot to enforce specific code standards
- Extending the Knowledge Transfer Visualization with additional metrics
- Adding new commands to the Slack Chatbot
- Creating new integrations with other services

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
