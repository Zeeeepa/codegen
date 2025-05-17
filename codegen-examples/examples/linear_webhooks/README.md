# Linear Webhooks Example

This example demonstrates how to set up a webhook handler for Linear events using the Codegen SDK and Modal. The webhook handler can process events from Linear such as issue creation, updates, comments, and more.

## Prerequisites

- [Modal](https://modal.com/) account
- [Linear](https://linear.app/) account with admin access
- Python 3.13 or higher

## Setup

### 1. Install Dependencies

```bash
# Clone the repository
git clone https://github.com/Zeeeepa/codegen.git
cd codegen/codegen-examples/examples/linear_webhooks

# Install dependencies
pip install -e .
```

### 2. Configure Environment Variables

Copy the `.env.template` file to `.env` and fill in your credentials:

```bash
cp .env.template .env
```

Edit the `.env` file with your Linear API credentials:

```
LINEAR_ACCESS_TOKEN="your_linear_api_token"
LINEAR_SIGNING_SECRET="your_linear_webhook_signing_secret"
LINEAR_TEAM_ID="your_linear_team_id"
MODAL_API_KEY="your_modal_api_key"  # Optional
```

To get these credentials:

- **LINEAR_ACCESS_TOKEN**: Go to Linear → Settings → API → Create Key
- **LINEAR_SIGNING_SECRET**: Created when you set up a webhook in Linear
- **LINEAR_TEAM_ID**: Found in Linear team settings or via the API
- **MODAL_API_KEY**: Your Modal API key (if not using Modal CLI authentication)

### 3. Authenticate with Modal

```bash
modal token new
```

## Deployment Commands

### Deploy to Modal

```bash
# Deploy the webhook handler to Modal
python webhooks.py
```

This will deploy the webhook handler to Modal and provide you with a URL that you can use to configure the webhook in Linear.

### Get Deployment Status

```bash
# Check the status of your Modal deployment
modal app status linear-webhooks
```

### View Logs

```bash
# View logs from your Modal deployment
modal app logs linear-webhooks
```

### Update Deployment

```bash
# Update your Modal deployment after making changes
python webhooks.py
```

### Stop Deployment

```bash
# Stop your Modal deployment
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

The example includes handlers for Issue and Comment events. You can customize these handlers or add new ones by modifying the `webhooks.py` file:

```python
@modal.web_endpoint(method="POST")
@app.linear.event("YourEventType")
def handle_your_event(self, event: LinearEvent):
    # Process the event
    return {"status": "success"}
```

## Available Event Types

Linear supports the following event types:

- `Issue`
- `Comment`
- `Project`
- `Cycle`
- `Reaction`
- And more...

Refer to the [Linear API documentation](https://developers.linear.app/docs/graphql/webhooks) for a complete list of event types.

## Troubleshooting

- **Webhook not receiving events**: Verify that your Linear webhook is configured correctly and that the URL is accessible.
- **Authentication errors**: Check that your LINEAR_ACCESS_TOKEN and LINEAR_SIGNING_SECRET are correct.
- **Modal deployment issues**: Run `modal app logs linear-webhooks` to view logs and diagnose issues.

## Additional Resources

- [Codegen Documentation](https://docs.codegen.sh/)
- [Modal Documentation](https://modal.com/docs)
- [Linear API Documentation](https://developers.linear.app/docs)
