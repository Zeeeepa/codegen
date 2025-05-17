# Linear Ticket to PR Example

This example demonstrates how to automatically create GitHub Pull Requests from Linear tickets using the Codegen SDK and Modal. When a Linear issue is labeled with "Codegen", this application will:

1. Process the Linear webhook event
2. Run a Codegen agent to analyze the issue
3. Create a GitHub Pull Request with changes addressing the issue
4. Comment on the Linear issue with a link to the PR

## Prerequisites

- [Modal](https://modal.com/) account
- [Linear](https://linear.app/) account with admin access
- [GitHub](https://github.com/) repository access
- Python 3.13 or higher

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
LINEAR_ACCESS_TOKEN="your_linear_api_token"
LINEAR_SIGNING_SECRET="your_linear_webhook_signing_secret"
LINEAR_TEAM_ID="your_linear_team_id"
GITHUB_TOKEN="your_github_personal_access_token"
MODAL_API_KEY="your_modal_api_key"  # Optional
```

To get these credentials:

- **LINEAR_ACCESS_TOKEN**: Go to Linear → Settings → API → Create Key
- **LINEAR_SIGNING_SECRET**: Created when you set up a webhook in Linear
- **LINEAR_TEAM_ID**: Found in Linear team settings or via the API
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
python app.py
```

This will deploy the application to Modal and provide you with a URL that you can use to configure the webhook in Linear.

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
python app.py
```

### Stop Deployment

```bash
# Stop your Modal deployment
modal app stop linear-bot
```

## Configuring Linear Webhooks

1. Go to Linear → Settings → API → Webhooks
2. Click "New Webhook"
3. Enter the URL provided by Modal when you deployed the application
4. Select the "Issue" event type
5. Copy the signing secret and add it to your `.env` file as `LINEAR_SIGNING_SECRET`
6. Click "Create Webhook"

## Creating a "Codegen" Label in Linear

1. Go to Linear → Settings → Labels
2. Click "New Label"
3. Name the label "Codegen"
4. Choose a color for the label
5. Click "Create Label"

## Usage

1. Create or update an issue in Linear
2. Add the "Codegen" label to the issue
3. The application will automatically:
   - Process the webhook event
   - Run a Codegen agent to analyze the issue
   - Create a GitHub Pull Request with changes
   - Comment on the Linear issue with a link to the PR

## Customizing the Application

You can customize the application by modifying the following files:

- `app.py`: Main application logic
- `helpers.py`: Utility functions for processing Linear events
- `data.py`: Data models for Linear events and labels

## Troubleshooting

- **Webhook not receiving events**: Verify that your Linear webhook is configured correctly and that the URL is accessible.
- **Authentication errors**: Check that your LINEAR_ACCESS_TOKEN and GITHUB_TOKEN are correct.
- **Modal deployment issues**: Run `modal app logs linear-bot` to view logs and diagnose issues.

## Additional Resources

- [Codegen Documentation](https://docs.codegen.sh/)
- [Modal Documentation](https://modal.com/docs)
- [Linear API Documentation](https://developers.linear.app/docs)
- [GitHub API Documentation](https://docs.github.com/en/rest)

