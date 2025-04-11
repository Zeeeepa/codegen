# Automated Code Improvement System

This application integrates multiple Codegen components to create a comprehensive automated code improvement system that can detect and fix issues, review pull requests, and track AI contributions to your codebase.

## Features

- **Automatic Issue Solving**: Detects issues with specific labels and automatically creates PRs with fixes
- **PR Review Bot**: Reviews pull requests and provides detailed feedback
- **Slack Integration**: Interact with the system through Slack commands
- **Snapshot Management**: Maintains codebase snapshots for fast analysis
- **AI Impact Analysis**: Tracks and visualizes AI contributions to the codebase

## Components

The system integrates several key Codegen components:

1. **IssueSolverAgent**: Automatically solves coding issues
2. **PR Review Bot**: Reviews pull requests and provides feedback
3. **Slack Chatbot**: Provides a chat interface for interacting with the system
4. **Snapshot Event Handler**: Maintains codebase snapshots for fast analysis
5. **AI Impact Analysis**: Tracks the impact of AI-generated code on the codebase

## Usage

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Zeeeepa/codegen.git
   cd codegen
   ```

2. Install dependencies:
   ```bash
   pip install -e .
   ```

3. Create a `.env` file with your credentials:
   ```
   GITHUB_TOKEN=your_github_token
   SLACK_BOT_TOKEN=your_slack_bot_token
   SLACK_APP_TOKEN=your_slack_app_token
   ```

### Running the System

Run the system with:

```bash
python codegen-examples/apps/automated_code_improvement_system.py your-org/your-repo
```

Or with a custom base branch:

```bash
python codegen-examples/apps/automated_code_improvement_system.py your-org/your-repo develop
```

### Slack Commands

Once the system is running, you can interact with it through Slack:

- `@bot solve issue #123` - Solve a GitHub issue and create a PR
- `@bot review pr #123` - Review a pull request and provide feedback
- `@bot analyze impact` - Analyze the impact of AI-generated code on the codebase
- `@bot help` - Show help message

## Configuration

You can customize the system's behavior by modifying the configuration:

```python
config = {
    "notification_channel": "dev-notifications",  # Slack channel for notifications
    "auto_fix_label": "auto-fix",                # Label that triggers auto-fixing
    # Add more configuration options as needed
}

system = AutomatedCodeImprovementSystem(
    repo="your-org/your-repo",
    base_branch="main",
    auto_fix_label="auto-fix",
    config=config
)
```

## Deployment

The system is designed to be deployed as a Modal application:

```bash
modal deploy codegen-examples/apps/automated_code_improvement_system.py
```

## Architecture

The system follows an event-driven architecture:

1. **Event Handlers**: Register handlers for GitHub, Slack, and Linear events
2. **Issue Solving**: Automatically solves issues with specific labels
3. **PR Review**: Reviews pull requests and provides feedback
4. **Impact Analysis**: Tracks AI contributions to the codebase

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
