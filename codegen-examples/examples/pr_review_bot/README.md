# PR Review Bot Example

This example demonstrates how to create a GitHub Pull Request review bot using the Codegen SDK and Modal. The bot automatically reviews pull requests and provides feedback on code quality, potential issues, and suggestions for improvement.

## Prerequisites

- [Modal](https://modal.com/) account
- [GitHub](https://github.com/) repository access
- Python 3.13 or higher
- Codegen SDK (version 0.52.19 or higher)

## Setup

### 1. Install Dependencies

```bash
# Clone the repository
git clone https://github.com/Zeeeepa/codegen.git
cd codegen/codegen-examples/examples/pr_review_bot

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
modal app status pr-review-bot
```

### View Logs

```bash
# View logs from your Modal deployment
modal app logs pr-review-bot
```

### Update Deployment

```bash
# Update your Modal deployment after making changes
./deploy.sh
```

### Stop Deployment

```bash
# Stop your Modal deployment
modal app stop pr-review-bot
```

## Configuring GitHub Webhooks

1. Go to your GitHub repository
1. Go to Settings → Webhooks
1. Click "Add webhook"
1. Enter the URL provided by Modal when you deployed the application
1. Select "application/json" as the content type
1. Select "Let me select individual events"
1. Check "Pull requests"
1. Click "Add webhook"

## Usage

The PR review bot automatically reviews pull requests when they are opened or updated. It provides feedback on:

- Code quality
- Potential bugs
- Security issues
- Performance concerns
- Documentation
- Testing

The bot posts its review as a comment on the pull request.

## Customizing the Application

You can customize the application by modifying the following files:

- `app.py`: The main application file that handles GitHub webhook events
- `helpers.py`: Helper functions for analyzing code and generating reviews

## Troubleshooting

- **Webhook not receiving events**: Verify that your GitHub webhook is configured correctly and that the URL is accessible.
- **Authentication errors**: Check that your GITHUB_TOKEN is correct and has the necessary permissions.
- **Modal deployment issues**: Run `modal app logs pr-review-bot` to view logs and diagnose issues.

## Additional Resources

- [Codegen Documentation](https://docs.codegen.sh/)
- [Modal Documentation](https://modal.com/docs)
- [GitHub Webhooks Documentation](https://docs.github.com/en/developers/webhooks-and-events/webhooks/about-webhooks)
