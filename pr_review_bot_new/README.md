# PR Review Bot

A GitHub PR review bot that monitors repositories, reviews pull requests, and provides notifications.

## Installation

### Option 1: Install as a package

```bash
# Install the package in development mode
pip install -e .
```

### Option 2: Run directly

```bash
# Make sure you're in the pr_review_bot_new directory
python run.py
```

## Configuration

Create a `.env` file with your GitHub token:

```
GITHUB_TOKEN=your_github_token_here
SLACK_TOKEN=your_slack_token_here  # Optional
SLACK_NOTIFICATION_CHANNEL=your_channel_here  # Optional
NGROK_AUTH_TOKEN=your_ngrok_token_here  # Optional, for webhook tunneling
```

## Usage

```bash
# Run with default settings
pr-review-bot

# Run with custom settings
pr-review-bot --port 8080 --monitor-prs --monitor-branches --slack-channel general
```

## Command Line Options

- `--port`: Port to run the server on (default: 8000)
- `--use-ngrok`: Use ngrok to expose the server
- `--webhook-url`: Webhook URL to use (overrides ngrok)
- `--monitor-interval`: Interval in seconds for monitoring repositories (default: 300)
- `--monitor-prs`: Enable PR monitoring
- `--monitor-branches`: Enable branch monitoring
- `--threads`: Number of threads to use for parallel processing (default: 10)
- `--show-merges`: Show recent merges on startup
- `--show-projects`: Show project implementation stats on startup
- `--slack-channel`: Slack channel to send notifications to
- `--skip-empty-branches`: Skip branches with no commits
- `--log-file`: Path to the log file (default: pr_review_bot.log)
- `--log-level`: Logging level (default: INFO)