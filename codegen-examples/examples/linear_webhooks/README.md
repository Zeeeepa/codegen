# Linear Webhooks Handler

This example demonstrates how to deploy a Modal application that handles Linear webhooks and processes events using Codegen.

## Features

- Handle Linear webhooks securely
- Process Linear issue events
- Easily deployable to Modal cloud
- Extensible event handling framework

## Prerequisites

Before you begin, ensure you have the following installed:

- Python 3.10+
- [Modal CLI](https://modal.com/docs/guide/cli-reference)
- [Codegen SDK](https://docs.codegen.com)
- A Linear account with admin access to create webhooks

## Setup

1. Install the required dependencies:

```bash
pip install modal codegen==0.52.19
```

2. Authenticate with Modal:

```bash
modal token new
```

3. Configure your environment variables:

```bash
cp .env.template .env
```

Edit the `.env` file and add your Linear API key and webhook secret:

```
LINEAR_API_KEY=your_linear_api_key
LINEAR_WEBHOOK_SECRET=your_linear_webhook_secret
```

## Deployment

You can deploy this example to Modal using the provided deploy script:

```bash
./deploy.sh
```

This will deploy the application to Modal and provide you with a URL to configure in Linear.

## Linear Webhook Configuration

1. Go to your Linear workspace settings
1. Navigate to "API" > "Webhooks"
1. Click "New Webhook"
1. Enter the URL provided by the deployment script
1. Select the events you want to receive (e.g., "Issues")
1. Copy the webhook secret and add it to your `.env` file
1. Click "Create webhook"

## Customizing Event Handlers

You can customize the event handlers by modifying the `webhooks.py` file. The example includes a basic handler for Issue events, but you can add handlers for other event types:

```python
@app.linear.event("Comment")
def handle_comment(self, data: dict):
    # Process comment events
    print(f"New comment: {data['data']['body']}")
```

## Available Event Types

Linear supports the following event types:

- Issue
- Comment
- Project
- Cycle
- Reaction
- IssueLabel
- Team
- Milestone
- User
- Attachment

## Troubleshooting

If you encounter issues:

1. Ensure you have the correct version of Modal and Codegen installed
1. Check that you're authenticated with Modal
1. Verify that your Linear API key and webhook secret are correct
1. Check the Modal logs for detailed error information
1. Verify that the webhook URL is correctly configured in Linear

## Security Considerations

- Keep your Linear API key and webhook secret secure
- Use environment variables for sensitive information
- Consider adding authentication to your webhook endpoint
- Validate webhook signatures to ensure requests are coming from Linear
