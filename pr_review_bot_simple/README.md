# PR Review Bot

A simple GitHub PR review bot using codegen libraries. This bot can review PRs automatically using AI and provide detailed feedback.

## Features

- Review PRs using the codegen library
- Run as a webhook server to automatically review PRs
- Run as a CLI tool to review specific PRs
- Properly uses codegen libraries for all functionality

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/pr_review_bot.git
cd pr_review_bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file from the template:
```bash
cp .env.template .env
```

4. Edit the `.env` file with your GitHub token and optional API keys.

## Usage

### CLI Mode

Review a specific PR:
```bash
python app.py review owner/repo 123
```

Where:
- `owner/repo` is the repository name (e.g., `codegen-sh/codegen`)
- `123` is the PR number

### Server Mode

Start the webhook server:
```bash
python app.py server --port 8000
```

The server will listen for GitHub webhook events on the specified port.

## Setting up GitHub Webhooks

1. Go to your repository settings on GitHub
2. Click on "Webhooks" and then "Add webhook"
3. Set the Payload URL to your server URL (e.g., `https://your-server.com/webhook`)
4. Set the Content type to `application/json`
5. Select "Let me select individual events" and choose "Pull requests"
6. Click "Add webhook"

## How It Works

The PR Review Bot uses the codegen library to:

1. Fetch PR details from GitHub
2. Analyze the code changes
3. Generate a detailed review using AI
4. Post comments on the PR with feedback

When a PR is labeled with "review", "codegen", or "bot-review", the bot will automatically review it.

## Requirements

- Python 3.8+
- GitHub token with repo scope
- Optional: Anthropic API key for Claude models
- Optional: OpenAI API key for GPT models

## License

MIT