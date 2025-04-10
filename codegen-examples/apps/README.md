# Codegen Apps

This directory contains production-ready applications that demonstrate how to integrate Codegen with various platforms and services.

## Available Apps

### Slack Codegen Integration (`slack_codegen.py`)

A comprehensive Slack integration for Codegen that allows users to interact with Codegen's capabilities through Slack. This integration combines functionality from various Codegen components including event handling, codebase operations, and agent interactions.

#### Features

- **Slack Event Handling**: Responds to mentions in Slack channels
- **Codebase Interaction**: Analyzes and answers questions about codebases
- **GitHub Integration**: Handles PR events and provides automated analysis
- **Linear Integration**: Processes Linear issue events
- **Memory Snapshots**: Uses Modal's memory snapshots for efficient codebase caching

#### Setup Instructions

1. **Prerequisites**:
   - A Slack workspace with admin permissions
   - A Slack app with the following permissions:
     - `app_mentions:read`
     - `chat:write`
     - `reactions:write`
   - Modal.com account for deployment
   - GitHub access token (for repository access)

2. **Environment Variables**:
   Create a `.env` file with the following variables:
   ```
   SLACK_BOT_TOKEN=xoxb-your-bot-token
   SLACK_SIGNING_SECRET=your-signing-secret
   GITHUB_ACCESS_TOKEN=your-github-token
   OPENAI_API_KEY=your-openai-key
   ```

3. **Deployment**:
   ```bash
   # Install dependencies
   pip install modal-client codegen slack_bolt

   # Deploy to Modal
   modal deploy slack_codegen.py
   ```

4. **Slack App Configuration**:
   - Set up your Slack app's Event Subscriptions to point to your Modal endpoint:
     - Request URL: `https://{your-modal-app}.modal.run/slack/events`
     - Subscribe to bot events: `app_mention`

#### Usage

Once deployed, you can interact with the bot in your Slack workspace:

- **Ask questions about a codebase**:
  ```
  @codegen-bot What does the CodeAgent class do?
  ```

- **Get help with code analysis**:
  ```
  @codegen-bot Can you explain how the event handling system works?
  ```

### PR Review Bot (`pr_review_agent.py`)

An AI-powered GitHub PR review bot that automatically reviews pull requests when triggered by labels. The bot uses Codegen's GitHub integration and AI capabilities to provide comprehensive code reviews with actionable feedback.

#### Features

- **Automated PR Reviews**: Triggered by adding a "Codegen" label to PRs
- **Deep Code Analysis**: Examines code changes and their impact
- **Contextual Feedback**: Provides specific, actionable comments
- **GitHub Integration**: Seamlessly works with GitHub's PR system
- **Customizable Review Criteria**: Adaptable to different project requirements

#### Setup Instructions

1. **Prerequisites**:
   - GitHub repository with admin access
   - Modal.com account for deployment
   - API keys for your preferred LLM provider (OpenAI, Anthropic, etc.)

2. **Environment Variables**:
   Create a `.env` file with the following variables:
   ```
   GITHUB_TOKEN=your-github-token
   ANTHROPIC_API_KEY=your-anthropic-key
   OPENAI_API_KEY=your-openai-key
   ```

3. **Deployment**:
   ```bash
   # Install dependencies
   pip install modal-client codegen

   # Deploy to Modal
   modal deploy pr_review_agent.py
   ```

4. **GitHub Webhook Configuration**:
   - Go to your repository settings
   - Add a webhook pointing to your Modal endpoint
   - Select "Pull request" events
   - Add a webhook secret (optional but recommended)

#### Usage

1. Create or update a pull request in your repository
2. Add the "Codegen" label to trigger a review
3. The bot will:
   - Post a temporary "starting review" comment
   - Analyze the PR changes
   - Post detailed review comments
   - Remove the temporary comment when done

To remove the bot's comments:
1. Remove the "Codegen" label
2. The bot will automatically clean up its comments

## Contributing

To add a new app to this directory:

1. Create a new Python file with your app implementation
2. Add documentation in the README.md explaining how to use your app
3. Include any necessary configuration files (e.g., `.env.template`)
