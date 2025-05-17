# Linear Ticket-to-PR Example

This example demonstrates how to create a Modal application that automatically creates GitHub pull requests from Linear tickets using the Codegen SDK. When a Linear ticket is moved to a specific state, this application will:

1. Create a new branch in the specified GitHub repository
2. Generate code changes based on the ticket description
3. Create a pull request with the changes
4. Link the pull request to the Linear ticket

## Prerequisites

- [Modal](https://modal.com/) account
- [Linear](https://linear.app/) workspace with admin access
- [GitHub](https://github.com/) repository access
- Python 3.10 or higher

## Setup

### 1. Install Dependencies

```bash
# Clone the repository
git clone https://github.com/Zeeeepa/codegen.git
cd codegen/codegen-examples/examples/ticket-to-pr

# Install dependencies
pip install -e .
```

### 2. Configure Environment Variables

Create a `.env` file with your credentials:

```
# Linear credentials
LINEAR_ACCESS_TOKEN=your_linear_api_token
LINEAR_SIGNING_SECRET=your_linear_webhook_signing_secret
LINEAR_TEAM_ID=your_linear_team_id

# GitHub credentials
GITHUB_TOKEN=your_github_token
GITHUB_REPO=your_github_repo_name
GITHUB_OWNER=your_github_username_or_org

# Modal configuration (optional)
MODAL_API_KEY=your_modal_api_key
```

To get these credentials:

- **LINEAR_ACCESS_TOKEN**: Create an API key in Linear (Settings → API → Create Key)
- **LINEAR_SIGNING_SECRET**: Create a webhook in Linear and copy the signing secret
- **LINEAR_TEAM_ID**: Your Linear team ID (can be found in team settings)
- **GITHUB_TOKEN**: Create a personal access token with repo permissions
- **GITHUB_REPO**: The name of your GitHub repository
- **GITHUB_OWNER**: Your GitHub username or organization name
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
modal app status linear-bot
```

### View Logs

```bash
# View logs from your Modal deployment
modal app logs linear-bot
```

### Update Deployment

```bash
# Update your Modal deployment after making changes
./deploy.sh
```

### Stop Deployment

```bash
# Stop your Modal deployment
modal app stop linear-bot
```

## Configuring Linear Webhooks

1. Go to your Linear workspace
2. Go to Settings → API → Webhooks
3. Click "New Webhook"
4. Enter the URL provided by Modal when you deployed the application
5. Select the "Issues" event
6. Copy the signing secret and add it to your `.env` file as `LINEAR_SIGNING_SECRET`
7. Click "Create Webhook"

## Usage

1. Create a ticket in Linear with a description of the changes you want to make
2. Move the ticket to the state that triggers the webhook (configured in `app.py`)
3. The application will automatically:
   - Create a new branch in your GitHub repository
   - Generate code changes based on the ticket description
   - Create a pull request with the changes
   - Link the pull request to the Linear ticket

## Customizing the Application

You can customize the application by modifying the following in `app.py`:

- `TARGET_STATE_NAME`: The Linear state that triggers the webhook
- `handle_issue_update`: The function that processes the Linear webhook
- `create_pr_from_ticket`: The function that creates the GitHub pull request

## Troubleshooting

- **Webhook not receiving events**: Verify that your Linear webhook is configured correctly and that the URL is accessible.
- **Authentication errors**: Check that your LINEAR_ACCESS_TOKEN, LINEAR_SIGNING_SECRET, and GITHUB_TOKEN are correct.
- **Modal deployment issues**: Run `modal app logs linear-bot` to view logs and diagnose issues.

## Additional Resources

- [Codegen Documentation](https://docs.codegen.sh/)
- [Modal Documentation](https://modal.com/docs)
- [Linear API Documentation](https://developers.linear.app/docs/)
- [GitHub API Documentation](https://docs.github.com/en/rest)

