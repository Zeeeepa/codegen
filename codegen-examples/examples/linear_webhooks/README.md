# Linear Webhooks Example

This example demonstrates how to handle Linear webhook events using the Codegen SDK and Modal. It provides a simple webhook handler that processes different types of Linear events, such as Issue and Comment events.

## Features

- Receive and process Linear webhook events
- Handle specific event types (Issues, Comments)
- Deploy as a serverless application using Modal
- Secure webhook verification using Linear's signing secret

## Prerequisites

- Python 3.13 or higher
- A Linear account with admin access
- A Modal account (for deployment)
- Codegen SDK (version 0.26.3 or higher)

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/your-repo.git
cd your-repo/examples/linear_webhooks
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -e ".[dev]"
```

### 4. Set Up Environment Variables

Create a `.env` file in the project root with the following variables:

```
LINEAR_API_KEY=your_linear_api_key
LINEAR_SIGNING_SECRET=your_linear_webhook_signing_secret
MODAL_API_KEY=your_modal_api_key
```

You can get your Linear API key from the Linear dashboard under Settings > API > Personal API Keys.

## Local Development

For local development and testing, you can run the webhook handler locally:

```bash
python webhooks.py
```

This will start a local server that you can use for testing. However, for Linear to send webhooks to your local machine, you'll need to use a tool like ngrok to expose your local server to the internet.

## Deployment

### Deploy to Modal

To deploy the webhook handler to Modal, run:

```bash
modal deploy webhooks.py
```

This will deploy the webhook handler to Modal and provide you with a URL that you can use to configure the Linear webhook.

### Update the Deployment

To update an existing deployment:

```bash
modal deploy webhooks.py
```

### Stop the Deployment

To stop the deployment:

```bash
modal app stop linear-webhooks
```

## Configuring Linear Webhooks

1. Go to Linear → Settings → API → Webhooks
1. Click "New Webhook"
1. Enter the URL provided by Modal when you deployed the webhook handler
1. Select the events you want to receive (e.g., Issues, Comments)
1. Copy the signing secret and add it to your `.env` file as `LINEAR_SIGNING_SECRET`
1. Click "Create Webhook"

## Customizing Event Handlers

You can customize the event handlers in `webhooks.py` to handle different types of Linear events. The example includes handlers for Issue and Comment events, but you can add handlers for other event types as well.

To add a new event handler, add a new method to the `LinearEventHandlers` class and decorate it with `@app.linear.event("EventType")`:

```python
@app.linear.event("Project")
def handle_project(self, event: LinearEvent):
    """Handle Linear Project events"""
    logger.info(f"Received Linear Project event: {event.action}")
    # Process the event
    return {"status": "success", "message": f"Processed Linear Project event: {event.action}"}
```

## Event Types

Linear supports various event types, including:

- Issue
- Comment
- Project
- Cycle
- Team
- User
- Attachment
- Reaction
- Label
- State

Refer to the [Linear API documentation](https://developers.linear.app/docs/graphql/webhooks) for a complete list of event types and their payloads.

## Resources

- [Codegen Documentation](https://docs.codegen.sh/)
- [Modal Documentation](https://modal.com/docs)
- [Linear API Documentation](https://developers.linear.app/docs)

