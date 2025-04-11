# PR Review Bot

A locally hostable backend for reviewing PRs and new branches, validating them against documentation and codebase patterns, and providing detailed feedback.

## Features

- **Automated PR Reviews**: Automatically review PRs when they are created or updated
- **Documentation Validation**: Validate PR changes against requirements in documentation files (README.md, STRUCTURE.md, PLAN.md)
- **AI-Powered Code Analysis**: Use LLMs (Claude or GPT-4) to analyze code quality, identify issues, and suggest improvements
- **GitHub Integration**: Seamless integration with GitHub webhooks and API
- **Slack Notifications**: Send notifications about PR review results to Slack
- **Configurable Validation Rules**: Customize validation rules to match your project's requirements
- **Local Hosting**: Host the agent locally or in your own infrastructure
- **Insights Storage**: Save insights from failed validations for future reference

## Quick Start (One-Liner Setup)

### Using Docker (Recommended)

```bash
# Clone the repository and start the PR Review Bot
git clone https://github.com/Zeeeepa/codegen.git && \
cd codegen/pr_review_bot && \
cp pr_review_bot/.env.example pr_review_bot/.env && \
nano pr_review_bot/.env && \
docker-compose up -d
```

### Using Python

```bash
# Clone the repository and start the PR Review Bot
git clone https://github.com/Zeeeepa/codegen.git && \
cd codegen/pr_review_bot && \
python -m venv venv && \
source venv/bin/activate && \
pip install -r requirements.txt && \
cp pr_review_bot/.env.example pr_review_bot/.env && \
nano pr_review_bot/.env && \
python -m pr_review_bot.main
```

## Architecture

The PR Review Bot consists of the following components:

1. **PR Review Controller**: The main orchestrator that coordinates the workflow
2. **Documentation Validator**: Validates PR changes against documentation requirements
3. **AI Service**: Generates AI-powered code reviews
4. **GitHub Client**: Interacts with GitHub API
5. **Slack Notifier**: Sends notifications to Slack
6. **Storage Manager**: Stores review results and insights
7. **FastAPI Application**: Provides API endpoints for webhooks and manual reviews

## Installation

### Prerequisites

- Python 3.10 or higher
- Git
- Docker (optional, for containerized deployment)

### Option 1: Local Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Zeeeepa/codegen.git
   cd codegen/pr_review_bot
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your configuration:
   ```bash
   cp pr_review_bot/.env.example pr_review_bot/.env
   # Edit .env with your tokens and keys
   ```

5. Start the agent:
   ```bash
   python -m pr_review_bot.main
   ```

### Option 2: Docker Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Zeeeepa/codegen.git
   cd codegen/pr_review_bot
   ```

2. Create a `.env` file with your configuration:
   ```bash
   cp pr_review_bot/.env.example pr_review_bot/.env
   # Edit .env with your tokens and keys
   ```

3. Build and start the container:
   ```bash
   docker-compose up -d
   ```

## Configuration

The PR Review Bot is configured using a YAML file and environment variables. The default configuration file is located at `pr_review_bot/config.yaml`.

### Configuration Options

```yaml
github:
  token: ""  # GitHub API token
  webhook_secret: ""  # Webhook secret for verification
  auto_merge: false  # Auto-merge PRs that pass validation
  auto_review: true  # Auto-review PRs when created/updated
  review_label: "needs-review"  # Label to trigger review

validation:
  documentation:
    enabled: true  # Enable documentation validation
    files:  # Documentation files to validate against
      - README.md
      - STRUCTURE.md
      - PLAN.md
    required: false  # Require documentation validation to pass

  code_quality:
    enabled: true  # Enable code quality validation
    linters:  # Linters to use
      - flake8
      - eslint
    threshold: 0.8  # Quality threshold (0-1)

  tests:
    enabled: true  # Enable test validation
    required: false  # Require tests to pass
    coverage_threshold: 0.7  # Coverage threshold (0-1)

notification:
  slack:
    enabled: false  # Enable Slack notifications
    token: ""  # Slack API token
    channel: ""  # Slack channel

storage:
  type: "local"  # Storage type (local, s3, etc.)
  path: "data"  # Storage path

ai:
  provider: "anthropic"  # AI provider (anthropic, openai)
  model: "claude-3-opus-20240229"  # Model to use
  api_key: ""  # API key
  temperature: 0.2  # Temperature for generation
  max_tokens: 4000  # Max tokens for generation

server:
  host: "0.0.0.0"  # Server host
  port: 8000  # Server port
  workers: 4  # Number of workers
  cors_origins: ["*"]  # CORS origins
```

### Environment Variables

You can override configuration options using environment variables:

- `GITHUB_TOKEN`: GitHub API token
- `GITHUB_WEBHOOK_SECRET`: Webhook secret for verification
- `ANTHROPIC_API_KEY`: Anthropic API key
- `OPENAI_API_KEY`: OpenAI API key
- `SLACK_BOT_TOKEN`: Slack bot token
- `SLACK_CHANNEL`: Slack channel for notifications

## Usage

### Setting Up GitHub Webhook

1. Go to your GitHub repository settings
2. Click on "Webhooks" and then "Add webhook"
3. Set the Payload URL to `http://your-server:8000/webhook`
4. Set the Content type to `application/json`
5. Set the Secret to match your `GITHUB_WEBHOOK_SECRET`
6. Select the events you want to trigger the webhook (at least "Pull requests")
7. Click "Add webhook"

### Manual PR Review

You can manually trigger a PR review using the API:

```bash
curl -X POST "http://localhost:8000/api/reviews/manual?repo_name=owner/repo&pr_number=123"
```

### API Endpoints

- `POST /webhook`: GitHub webhook endpoint
- `GET /api/status`: Get agent status
- `GET /api/reviews`: Get list of reviews
- `GET /api/reviews/{id}`: Get specific review details
- `POST /api/reviews/manual`: Trigger manual review
- `GET /api/config`: Get current configuration
- `POST /api/config`: Update configuration
- `GET /api/docs/validate`: Validate documentation files
- `GET /api/health`: Health check endpoint

## Documentation Validation

The PR Review Agent validates PR changes against requirements specified in documentation files. It extracts requirements from Markdown files by looking for statements containing keywords like "must", "should", "shall", etc.

Example requirement in a Markdown file:
```markdown
## Requirements

- The system must support authentication via OAuth2.
- Users should be able to reset their passwords.
- The API shall provide detailed error messages.
```

The agent checks if the PR addresses these requirements by looking for relevant keywords in the PR title, body, and code changes.

## AI-Powered Code Review

The PR Review Agent uses LLMs (Claude or GPT-4) to analyze code changes and provide detailed feedback. The AI review includes:

- Overall assessment of the PR
- Code quality issues
- Potential bugs or issues
- Suggestions for improvement
- Recommendation for approval or changes

## Insights Storage

When a PR fails validation, the agent stores the validation results and insights for future reference. These insights can be used to improve the codebase and documentation.

The insights are stored in the directory specified in the `storage.path` configuration option.

## File Structure

```
pr_review_bot/
├── __init__.py                # Package initialization
├── main.py                    # Main entry point
├── config.yaml                # Default configuration
├── Dockerfile                 # Dockerfile for containerization
├── docker-compose.yml         # Docker Compose configuration
├── api/                       # API endpoints
│   ├── __init__.py
│   ├── app.py                 # FastAPI application
│   └── webhook_handler.py     # Webhook handler
├── core/                      # Core components
│   ├── __init__.py
│   ├── compatibility.py       # Compatibility layer
│   ├── config_manager.py      # Configuration manager
│   ├── github_client.py       # GitHub client
│   ├── pr_review_controller.py # PR review controller
│   └── pr_reviewer.py         # PR reviewer
├── validator/                 # Validation components
│   ├── __init__.py
│   ├── documentation_parser.py    # Documentation parser
│   ├── documentation_validator.py # Documentation validator
│   └── documentation_service.py   # Documentation validation service
├── utils/                     # Utility functions
│   ├── __init__.py
│   ├── ai_service.py          # AI service
│   ├── logger.py              # Logger
│   ├── slack_notifier.py      # Slack notifier
│   └── storage_manager.py     # Storage manager
├── monitors/                  # Monitoring components
│   ├── __init__.py
│   ├── branch_monitor.py      # Branch monitor
│   └── pr_monitor.py          # PR monitor
└── docs/                      # Documentation
    └── pr_review_management_workflow.md # PR review workflow
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [Codegen](https://github.com/Zeeeepa/codegen) for the inspiration and some code patterns
- [FastAPI](https://fastapi.tiangolo.com/) for the API framework
- [PyGithub](https://github.com/PyGithub/PyGithub) for GitHub API integration
- [Anthropic Claude](https://www.anthropic.com/claude) and [OpenAI GPT-4](https://openai.com/gpt-4) for AI-powered code reviews
