# PR Review Bot

A simple bot for reviewing GitHub pull requests using the codegen library. This bot can be run in two modes:

1. **CLI mode**: Review a specific PR
2. **Server mode**: Start a webhook server to listen for PR events

## Features

- Automated PR code review using AI (when API keys are available)
- Integration with GitHub PR system
- Webhook support for automatic PR reviews
- Simple CLI for reviewing specific PRs

## Prerequisites

Before running this application, you'll need:

- GitHub API Token
- (Optional) Anthropic API Token or OpenAI API Token for AI-powered reviews

## Installation

1. Clone the repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

Create a `.env` file with your API tokens:

```env
# Required
GITHUB_TOKEN=your_github_token

# Optional - for AI-powered reviews
ANTHROPIC_API_KEY=your_anthropic_token
# OR
OPENAI_API_KEY=your_openai_token

# Optional - for webhook security
GITHUB_WEBHOOK_SECRET=your_webhook_secret
```

## Usage

### CLI Mode

To review a specific PR:

```bash
python app.py review owner/repo 123
```

Where:
- `owner/repo` is the repository name (e.g., `codegen-sh/codegen`)
- `123` is the PR number

### Server Mode

To start the webhook server:

```bash
python app.py server --port 8000
```

Then configure a GitHub webhook to send events to `http://your-server:8000/webhook`.

## How It Works

The PR Review Bot uses the codegen library to:

1. Fetch the PR details from GitHub
2. Analyze the code changes
3. Generate a review using AI (if API keys are available)
4. Post the review as comments on the PR

If AI API keys are not available, the bot will perform a basic review that lists the changed files and provides a simple summary.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.