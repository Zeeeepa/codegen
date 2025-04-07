# PR Review Bot

A GitHub PR review bot that automatically reviews and optionally merges pull requests.

## Features

- Monitors repositories for new pull requests
- Reviews PRs using AI (optional)
- Checks PRs against requirements
- Automatically merges PRs that pass checks
- Sends notifications to Slack
- Exposes a webhook endpoint for GitHub events

## Installation

### Basic Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/pr_review_bot_new.git
cd pr_review_bot_new

# Install the package
pip install -e .
```

### Installation with AI Features

```bash
pip install -e ".[ai]"
```

### Installation with Codegen SDK

```bash
pip install -e ".[codegen]"
```

### Full Installation

```bash
pip install -e ".[all]"
```

## Configuration

Create a `.env` file in the root directory with the following variables:

```
# Required
GITHUB_TOKEN=your_github_token

# Optional - for AI features
ANTHROPIC_API_KEY=your_anthropic_api_key
# OR
OPENAI_API_KEY=your_openai_api_key

# Optional - for Slack notifications
SLACK_WEBHOOK_URL=your_slack_webhook_url
# OR
SLACK_TOKEN=your_slack_token
SLACK_NOTIFICATION_CHANNEL=your_slack_channel

# Optional - for ngrok
NGROK_AUTH_TOKEN=your_ngrok_auth_token
```

## Usage

### Running the Bot

```bash
# Using the installed command
pr-review-bot

# OR using the run script
python run.py
```

### Command Line Options

```
usage: pr-review-bot [-h] [--port PORT] [--use-ngrok] [--webhook-url WEBHOOK_URL]
                    [--monitor-interval MONITOR_INTERVAL] [--monitor-prs]
                    [--monitor-branches] [--threads THREADS] [--show-merges]
                    [--show-projects] [--slack-channel SLACK_CHANNEL]
                    [--skip-empty-branches] [--log-file LOG_FILE]
                    [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}]

PR Review Bot

optional arguments:
  -h, --help            show this help message and exit
  --port PORT           Port to run the server on
  --use-ngrok           Use ngrok to expose the server
  --webhook-url WEBHOOK_URL
                        Webhook URL to use (overrides ngrok)
  --monitor-interval MONITOR_INTERVAL
                        Interval in seconds for monitoring repositories
  --monitor-prs         Enable PR monitoring
  --monitor-branches    Enable branch monitoring
  --threads THREADS     Number of threads to use for parallel processing
  --show-merges         Show recent merges on startup
  --show-projects       Show project implementation stats on startup
  --slack-channel SLACK_CHANNEL
                        Slack channel to send notifications to
  --skip-empty-branches
                        Skip branches with no commits
  --log-file LOG_FILE   Path to the log file
  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Logging level
```

## API Endpoints

The bot exposes the following API endpoints:

- `POST /webhook`: GitHub webhook endpoint
- `GET /api/merges`: Get recent merges
- `GET /api/projects`: Get project implementation stats
- `GET /api/status`: Get status report

## Dependencies

The bot has the following dependencies:

### Core Dependencies
- FastAPI
- Uvicorn
- PyGithub
- Requests
- Python-dotenv
- Schedule
- Pyngrok

### Optional Dependencies
- LangChain (for AI features)
- Codegen SDK (for advanced code analysis)

## License

MIT