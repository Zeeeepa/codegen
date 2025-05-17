# Snapshot Event Handler Example

This example demonstrates how to create a Modal application that handles GitHub events for repository snapshots using the Codegen SDK. The application can process various GitHub events such as pull request creation, updates, and more, and perform automated tasks like code reviews and issue creation.

## Prerequisites

- [Modal](https://modal.com/) account
- [GitHub](https://github.com/) repository access
- Python 3.10 or higher

## Setup

### 1. Install Dependencies

```bash
# Clone the repository
git clone https://github.com/Zeeeepa/codegen.git
cd codegen/codegen-examples/examples/snapshot_event_handler

# Install dependencies
pip install -e .
```

### 2. Configure Environment Variables

Create a `.env` file with your credentials:

```
# GitHub credentials
GITHUB_TOKEN=your_github_token

# Modal configuration (optional)
MODAL_API_KEY=your_modal_api_key
```

To get these credentials:

- **GITHUB_TOKEN**: Create a personal access token with repo permissions
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

This will deploy the application to Modal and provide you with a URL that you can use to configure the GitHub webhook.

### Get Deployment Status

```bash
# Check the status of your Modal deployment
modal app status snapshot-event-handler
```

### View Logs

```bash
# View logs from your Modal deployment
modal app logs snapshot-event-handler
```

### Update Deployment

```bash
# Update your Modal deployment after making changes
./deploy.sh
```

### Stop Deployment

```bash
# Stop your Modal deployment
modal app stop snapshot-event-handler
```

## Configuring GitHub Webhooks

1. Go to your GitHub repository
2. Go to Settings → Webhooks
3. Click "Add webhook"
4. Enter the URL provided by Modal when you deployed the application
5. Select "application/json" as the content type
6. Select "Let me select individual events"
7. Check the events you want to receive (e.g., "Pull requests", "Issues")
8. Click "Add webhook"

## Usage

The application handles the following GitHub events:

- **Pull Request**: Created, updated, or closed
- **Issue**: Created, updated, or closed
- **Push**: Code pushed to the repository

You can customize the handlers in `event_handlers.py` to process these events according to your needs.

## Customizing the Application

You can customize the application by modifying the event handlers in `event_handlers.py` and the PR tasks in `pr_tasks.py`. Each handler receives an event object that contains information about the event, including:

- `action`: The action that triggered the event (e.g., "opened", "closed")
- `repository`: Information about the repository
- `sender`: Information about the user who triggered the event
- Event-specific data (e.g., `pull_request`, `issue`)

## Troubleshooting

- **Webhook not receiving events**: Verify that your GitHub webhook is configured correctly and that the URL is accessible.
- **Authentication errors**: Check that your GITHUB_TOKEN is correct and has the necessary permissions.
- **Modal deployment issues**: Run `modal app logs snapshot-event-handler` to view logs and diagnose issues.

## Additional Resources

- [Codegen Documentation](https://docs.codegen.sh/)
- [Modal Documentation](https://modal.com/docs)
- [GitHub Webhooks Documentation](https://docs.github.com/en/developers/webhooks-and-events/webhooks/about-webhooks)

