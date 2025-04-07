# PR Review Bot - Simple

A simple, locally hostable PR review bot that uses the codegen libraries to review pull requests on GitHub.

## Features

- Review pull requests using AI-powered code analysis
- List open PRs in a repository
- Review all open PRs in a repository
- Interactive command-line interface
- Fully automated PR reviews

## Prerequisites

Before running this application, you'll need the following:

- Python 3.8 or higher
- GitHub API Token
- Anthropic API Token (recommended) or OpenAI API Token
- Codegen library installed

## Installation

1. Clone the repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Set up your environment variables in a `.env` file:

```env
GITHUB_TOKEN=your_github_token
ANTHROPIC_API_KEY=your_anthropic_token
# OR
OPENAI_API_KEY=your_openai_token
```

## Usage

### Basic Usage

```bash
python app.py --repo owner/repo --pr 123
```

This will review PR #123 in the specified repository.

### List Open PRs

```bash
python app.py --repo owner/repo --list
```

This will list all open PRs in the specified repository.

### Review All Open PRs

```bash
python app.py --repo owner/repo --review-all
```

This will review all open PRs in the specified repository.

### Interactive Mode

```bash
python app.py
```

This will start the bot in interactive mode, prompting you for the repository and PR to review.

## How It Works

The PR Review Bot uses the codegen library to:

1. Connect to the GitHub repository
2. Analyze the pull request changes
3. Generate a comprehensive review using AI
4. Post the review as comments on the PR

The bot uses the CodeAgent from codegen to perform the review, which provides a detailed analysis of the code changes.

## Dependencies

- codegen: For code analysis and AI-powered review
- PyGithub: For GitHub API integration
- python-dotenv: For environment variable management
- argparse: For command-line argument parsing

## License

MIT