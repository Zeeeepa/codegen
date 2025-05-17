# Linear Webhooks Example

This example demonstrates how to create a webhook handler for Linear events using the Codegen SDK and Modal. The application can process various Linear events such as issue creation, updates, comments, and more.

## Prerequisites

- [Modal](https://modal.com/) account
- [Linear](https://linear.app/) workspace with admin access
- Python 3.13 or higher
- Codegen SDK (version 0.52.19 or higher)

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

Create a `.env` file with your credentials:

```
# Linear API credentials
LINEAR_ACCESS_TOKEN=your_linear_api_token
LINEAR_SIGNING_SECRET=your_linear_webhook_signing_secret
LINEAR_TEAM_ID=your_linear_team_id

# Modal configuration (optional)
MODAL_API_KEY=your_modal_api_key
```

To get these credentials:

- **LINEAR_ACCESS_TOKEN**: Create an API key in Linear (Settings → API → Create Key)
- **LINEAR_SIGNING_SECRET**: Create a webhook in Linear and copy the signing secret
- **LINEAR_TEAM_ID**: Your Linear team ID (can be found in team settings)
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

This will deploy the application to Modal and provide you with a URL that you can use to configure the Linear webhook.

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
./deploy.sh
```

### Stop Deployment

```bash
# Stop your Modal deployment
modal app stop linear-webhooks
```

## Configuring Linear Webhooks

1. Go to your Linear workspace
2. Go to Settings → API → Webhooks
3. Click "New Webhook"
4. Enter the URL provided by Modal when you deployed the application
5. Select the events you want to receive (e.g., Issues, Comments)
6. Copy the signing secret and add it to your `.env` file as `LINEAR_SIGNING_SECRET`
7. Click "Create Webhook"

## Usage

The application handles the following Linear events:

- **Issue**: Created, updated, or removed
- **Comment**: Created, updated, or removed

You can customize the handlers in `webhooks.py` to process these events according to your needs.

## Customizing the Application

You can customize the application by modifying the event handlers in `webhooks.py`. Each handler receives a `LinearEvent` object that contains information about the event, including:

- `action`: The action that triggered the event (e.g., "create", "update")
- `data`: The data associated with the event (e.g., issue details, comment details)
- `type`: The type of event (e.g., "Issue", "Comment")

## Troubleshooting

- **Webhook not receiving events**: Verify that your Linear webhook is configured correctly and that the URL is accessible.
- **Authentication errors**: Check that your LINEAR_ACCESS_TOKEN and LINEAR_SIGNING_SECRET are correct.
- **Modal deployment issues**: Run `modal app logs linear-webhooks` to view logs and diagnose issues.

## Additional Resources

- [Codegen Documentation](https://docs.codegen.sh/)
- [Modal Documentation](https://modal.com/docs)
- [Linear API Documentation](https://developers.linear.app/docs/)
