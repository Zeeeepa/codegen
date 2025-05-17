# Slack Chatbot Example

This example demonstrates how to create a Slack chatbot using the Codegen SDK and Modal. The chatbot can answer questions about codebases and provide code snippets and explanations.

## Prerequisites

- [Modal](https://modal.com/) account
- [Slack](https://slack.com/) workspace with admin access
- Python 3.13 or higher
- Codegen SDK (version 0.52.19 or higher)

## Setup

### 1. Install Dependencies

```bash
# Clone the repository
git clone https://github.com/Zeeeepa/codegen.git
cd codegen/codegen-examples/examples/slack_chatbot

# Install dependencies
pip install -e .
```

### 2. Configure Environment Variables

Create a `.env` file with your credentials:

```
# Slack credentials
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_SIGNING_SECRET=your-slack-signing-secret

# Modal configuration (optional)
MODAL_API_KEY=your_modal_api_key
```

To get these credentials:

- **SLACK_BOT_TOKEN**: Create a Slack app and get the Bot User OAuth Token
- **SLACK_SIGNING_SECRET**: Get the Signing Secret from your Slack app's Basic Information page
- **MODAL_API_KEY**: Your Modal API key (if not using Modal CLI authentication)

### 3. Authenticate with Modal

```bash
modal token new
```

## Deployment Commands

### Deploy to Modal

```bash
# Deploy the application to Modal
./deploy.sh
```

This will deploy the application to Modal and provide you with a URL that you can use to configure the Slack app.

### Get Deployment Status

```bash
# Check the status of your Modal deployment
modal app status slack-chatbot
```

### View Logs

```bash
# View logs from your Modal deployment
modal app logs slack-chatbot
```

### Update Deployment

```bash
# Update your Modal deployment after making changes
./deploy.sh
```

### Stop Deployment

```bash
# Stop your Modal deployment
modal app stop slack-chatbot
```

## Configuring Slack App

1. Go to [Slack API](https://api.slack.com/apps) and create a new app
2. Go to "OAuth & Permissions" and add the following scopes:
   - `app_mentions:read`
   - `chat:write`
   - `im:history`
   - `im:read`
   - `im:write`
3. Install the app to your workspace
4. Go to "Event Subscriptions" and enable events
5. Enter the URL provided by Modal when you deployed the application as the Request URL
6. Subscribe to the following bot events:
   - `app_mention`
   - `message.im`
7. Save changes

## Usage

Once the chatbot is deployed and configured, you can interact with it in two ways:

1. **Direct Messages**: Send a direct message to the bot
2. **Mentions**: Mention the bot in a channel using `@botname`

The bot will respond to your messages with information about the codebase you're asking about.

## Customizing the Application

You can customize the application by modifying the following files:

- `api.py`: The main application file that handles Slack events and responses

## Troubleshooting

- **Webhook not receiving events**: Verify that your Slack app is configured correctly and that the URL is accessible.
- **Authentication errors**: Check that your SLACK_BOT_TOKEN and SLACK_SIGNING_SECRET are correct.
- **Modal deployment issues**: Run `modal app logs slack-chatbot` to view logs and diagnose issues.

## Additional Resources

- [Codegen Documentation](https://docs.codegen.sh/)
- [Modal Documentation](https://modal.com/docs)
- [Slack API Documentation](https://api.slack.com/)

