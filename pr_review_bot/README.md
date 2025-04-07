# AI-Powered Pull Request Review Bot

This project implements an AI-powered bot that automatically reviews GitHub Pull Requests and monitors repositories for new branches. The bot analyzes code changes and their dependencies to provide comprehensive code reviews using AI, considering both direct modifications and their impact on the codebase. It can also automatically merge valid PRs to the main branch.

## Features

- Automated PR code review using AI
- Deep dependency analysis of code changes
- Context-aware feedback generation
- Structured review format with actionable insights
- Integration with GitHub PR system
- Automatic merging of valid PRs
- Webhook support for all repositories
- Ngrok integration for local development
- Monitoring of all repositories in an account
- New PR monitoring
- New branch monitoring
- PR auto-review with merging to main if OK
- New branch auto-review with merging to main if OK
- Validation against REQUIREMENTS.md in project's root
- Slack notifications for merged PRs

## Prerequisites

Before running this application, you'll need the following:

- GitHub API Token with `repo` and `admin:repo_hook` scopes
- Anthropic API Token (recommended) or OpenAI API Token
- Ngrok account and auth token (for local development)
- Python 3.10 or higher
- Slack API Token or Webhook URL (for notifications)

## Setup

1. Clone the repository
2. Navigate to the PR review bot directory:
   ```
   cd pr_review_bot
   ```
3. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
5. Create a `.env` file based on the `.env.example` template:
   ```
   cp .env.example .env
   ```
6. Edit the `.env` file with your API tokens and configuration

## Usage

### Running Locally with Ngrok

To run the bot locally with Ngrok for webhook forwarding:

```bash
python run.py --use-ngrok --monitor-prs --monitor-branches
```

This will:
1. Start a local server
2. Create an Ngrok tunnel to expose it to the internet
3. Set up webhooks for all your GitHub repositories
4. Start monitoring for new PRs and branches
5. Start listening for webhook events

### Running with a Custom Webhook URL

If you already have a publicly accessible URL:

```bash
python run.py --webhook-url https://your-domain.com/webhook --monitor-prs --monitor-branches
```

### Running on a Custom Port

```bash
python run.py --port 9000 --use-ngrok --monitor-prs --monitor-branches
```

### Running with Custom Monitor Interval

```bash
python run.py --use-ngrok --monitor-prs --monitor-branches --monitor-interval 600
```

### Enabling Slack Notifications

To enable Slack notifications for merged PRs:

```bash
python run.py --use-ngrok --monitor-prs --monitor-branches --slack-channel C08LUHUCXD4
```

You can also set the `SLACK_NOTIFICATION_CHANNEL` environment variable in your `.env` file:

```
SLACK_NOTIFICATION_CHANNEL=C08LUHUCXD4
```

## How It Works

1. The bot sets up webhooks on your GitHub repositories
2. It monitors all repositories for new PRs and branches
3. When a PR is created or updated, GitHub sends a webhook event
4. The bot processes the event and analyzes the PR
5. It uses AI capabilities to review the code
6. The review is posted as comments on the PR
7. If the PR is valid and meets requirements, it can be automatically merged
8. When a PR is merged, a notification is sent to the configured Slack channel

## Webhook Events

The bot responds to the following GitHub webhook events:

- `pull_request:opened` - When a new PR is created
- `pull_request:synchronize` - When a PR is updated with new commits
- `pull_request:reopened` - When a closed PR is reopened
- `pull_request:labeled` - When a PR is labeled (specifically for the "Codegen" label)
- `pull_request:unlabeled` - When a label is removed from a PR
- `push` - When code is pushed to a branch
- `repository:created` - When a new repository is created

## Configuration

The bot can be configured through environment variables in the `.env` file:

- `GITHUB_TOKEN` - GitHub API token
- `WEBHOOK_SECRET` - Secret for GitHub webhook verification
- `NGROK_AUTH_TOKEN` - Ngrok authentication token
- `ANTHROPIC_API_KEY` - Anthropic API key for Claude models
- `OPENAI_API_KEY` - OpenAI API key (fallback if Anthropic is not available)
- `SLACK_TOKEN` - Slack API token for sending notifications
- `SLACK_WEBHOOK_URL` - Slack webhook URL (alternative to token)
- `SLACK_NOTIFICATION_CHANNEL` - Slack channel ID to send notifications to

## Project Structure

```
pr_review_bot/
├── pr_review_bot/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── app.py
│   │   └── webhook_handler.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── github_client.py
│   │   └── pr_reviewer.py
│   ├── monitors/
│   │   ├── __init__.py
│   │   ├── branch_monitor.py
│   │   └── pr_monitor.py
│   └── utils/
│       ├── __init__.py
│       ├── ngrok_manager.py
│       ├── slack_notifier.py
│       └── webhook_manager.py
├── run.py
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
