# Codegen Apps

This directory contains example applications that demonstrate how to integrate Codegen with various platforms and services.

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

#### Architecture

The integration consists of several components:

1. **SlackCodegenAPI**: A Modal class that handles Slack events and integrates with Codegen
2. **FastAPI Integration**: Provides HTTP endpoints for Slack events
3. **Cron Job**: Periodically refreshes repository snapshots for better performance

#### Customization

You can customize the integration by:

- Modifying the `process_codebase_query` function to use different agent capabilities
- Adding additional event handlers for other Slack events
- Integrating with other Codegen extensions and tools

## Contributing

To add a new app to this directory:

1. Create a new Python file with your app implementation
2. Add documentation in the README.md explaining how to use your app
3. Include any necessary configuration files (e.g., `.env.template`)
