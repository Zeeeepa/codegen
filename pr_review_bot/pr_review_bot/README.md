# PR Review Bot

A GitHub PR review bot that automatically reviews and merges pull requests.

## Features

- Automatically reviews pull requests
- Checks PRs against requirements
- Monitors branches for changes
- Provides webhook integration
- Sends notifications to Slack
- Supports AI-powered code review (optional)

## Installation

### Basic Installation

```bash
# Clone the repository
git clone https://github.com/your-org/pr-review-bot.git
cd pr-review-bot

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the basic package
pip install -e .
```

### Installation with AI Features

```bash
# Install with AI features
pip install -e ".[ai]"
```

### Installation with Codegen Integration

```bash
# Install with Codegen integration
pip install -e ".[codegen]"
```

### Full Installation

```bash
# Install all features
pip install -e ".[all]"
```

## Configuration

Create a `.env` file with the following variables:

```
# Required
GITHUB_TOKEN=your_github_token

# Optional - for Slack notifications
SLACK_WEBHOOK_URL=your_slack_webhook_url
# OR
SLACK_TOKEN=your_slack_token
SLACK_NOTIFICATION_CHANNEL=your_channel_name

# Optional - for AI-powered reviews
ANTHROPIC_API_KEY=your_anthropic_key
# OR
OPENAI_API_KEY=your_openai_key

# Optional - for ngrok integration
NGROK_AUTH_TOKEN=your_ngrok_token
```

## Usage

### Basic Usage

```bash
# Run the bot with default settings
pr-review-bot
```

### Advanced Usage

```bash
# Run with PR monitoring
pr-review-bot --monitor-prs

# Run with branch monitoring
pr-review-bot --monitor-branches

# Run with ngrok for webhook integration
pr-review-bot --use-ngrok

# Run with custom webhook URL
pr-review-bot --webhook-url https://your-webhook-url.com/webhook

# Run with custom monitoring interval (in seconds)
pr-review-bot --monitor-interval 600

# Run with custom number of threads
pr-review-bot --threads 20

# Run with Slack notifications
pr-review-bot --slack-channel your-channel-name

# Show recent merges on startup
pr-review-bot --show-merges

# Show project implementation stats on startup
pr-review-bot --show-projects

# Skip branches with no commits
pr-review-bot --skip-empty-branches

# Custom log file and level
pr-review-bot --log-file custom.log --log-level DEBUG
```

## Project Structure

```
pr_review_bot/
├── api/              # API endpoints and webhook handlers
├── core/             # Core functionality
├── monitors/         # PR and branch monitors
├── utils/            # Utility functions
├── main.py           # Main entry point
└── run.py            # Run script
```

## Dependencies

- Required:
  - fastapi
  - uvicorn
  - pydantic
  - python-dotenv
  - PyGithub
  - requests
  - markdown
  - beautifulsoup4
  - gitpython
  - schedule

- Optional (AI features):
  - langchain-core
  - langchain-anthropic
  - langchain-openai

- Optional (Codegen integration):
  - codegen

## License

MIT