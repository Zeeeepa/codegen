# PR Review Bot

A simple, locally hostable PR review bot that uses the codegen libraries to automatically review pull requests.

## Features

- Review pull requests using AI-powered code analysis
- Run as a webhook server to automatically review PRs when labeled
- Run as a CLI tool to review specific PRs on demand
- Properly integrates with codegen libraries

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

3. Create a `.env` file with your GitHub token:
```bash
GITHUB_TOKEN=your_github_token
ANTHROPIC_API_KEY=your_anthropic_api_key  # Optional, for enhanced reviews
OPENAI_API_KEY=your_openai_api_key  # Optional, for enhanced reviews
```

## Usage

### CLI Mode

To review a specific PR:

```bash
python app.py review owner/repo 123
```

Where:
- `owner/repo` is the repository name (e.g., `codegen-sh/codegen`)
- `123` is the PR number to review

### Server Mode

To run as a webhook server:

```bash
python app.py server --port 8000
```

Then configure a GitHub webhook to send PR events to `http://your-server:8000/webhook`.

The bot will automatically review PRs when they are labeled with "review".

## How It Works

1. The bot uses the codegen library to analyze the PR
2. It creates a comment to notify that a review is in progress
3. It uses CodeAgent to perform a thorough review of the code changes
4. It adds comments to the PR with suggestions and feedback
5. It removes the notification comment when done

## Requirements

- Python 3.8+
- GitHub token with repo access
- Optional: Anthropic or OpenAI API key for enhanced reviews

## Configuration

You can configure the bot by setting environment variables in a `.env` file:

- `GITHUB_TOKEN`: Your GitHub token (required)
- `ANTHROPIC_API_KEY`: Your Anthropic API key (optional)
- `OPENAI_API_KEY`: Your OpenAI API key (optional)
- `LOG_LEVEL`: Logging level (default: INFO)

## License

MIT