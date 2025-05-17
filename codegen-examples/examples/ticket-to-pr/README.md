# Linear Ticket to GitHub PR Example

This example demonstrates how to automatically create GitHub Pull Requests from Linear tickets using the Codegen SDK and Modal. When a Linear issue is labeled with "Codegen", this application will:

1. Process the Linear webhook event
1. Run a Codegen agent to analyze the issue
1. Create a GitHub Pull Request with changes addressing the issue
1. Comment on the Linear issue with a link to the PR

## Prerequisites

- Python 3.13 or higher
- A Linear account with admin access
- A GitHub account with access to the repository you want to create PRs in
- A Modal account (for deployment)
- Codegen SDK (version 0.26.3 or higher)

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/your-repo.git
cd your-repo/examples/ticket-to-pr
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
# Linear configuration
LINEAR_API_KEY=your_linear_api_key
LINEAR_SIGNING_SECRET=your_linear_webhook_signing_secret

# GitHub configuration
GITHUB_OWNER=your_github_username_or_organization
GITHUB_REPO=your_repository_name
GITHUB_TOKEN=your_github_personal_access_token

# Modal configuration (optional)
MODAL_API_KEY=your_modal_api_key
```

You can get your Linear API key from the Linear dashboard under Settings > API > Personal API Keys.

For GitHub, you'll need to create a personal access token with the following permissions:
- `repo` (Full control of private repositories)
- `workflow` (Update GitHub Action workflows)

## Local Development

For local development and testing, you can run the application locally:

```bash
python app.py
```

This will start a local server that you can use for testing. However, for Linear to send webhooks to your local machine, you'll need to use a tool like ngrok to expose your local server to the internet.

## Deployment

### Deploy to Modal

To deploy the application to Modal, run:

```bash
modal deploy app.py
```

This will deploy the application to Modal and provide you with a URL that you can use to configure the Linear webhook.

### Update the Deployment

To update an existing deployment:

```bash
modal deploy app.py
```

### Stop the Deployment

To stop the deployment:

```bash
modal app stop linear-bot
```

## Configuring Linear Webhooks

1. Go to Linear → Settings → API → Webhooks
1. Click "New Webhook"
1. Enter the URL provided by Modal when you deployed the application
1. Select the "Issue" event type
1. Copy the signing secret and add it to your `.env` file as `LINEAR_SIGNING_SECRET`
1. Click "Create Webhook"

## Creating a "Codegen" Label in Linear

1. Go to Linear → Settings → Labels
1. Click "New Label"
1. Name the label "Codegen"
1. Choose a color for the label
1. Click "Create Label"

## Usage

1. Create or update an issue in Linear
1. Add the "Codegen" label to the issue
1. The application will automatically:
   - Process the webhook event
   - Run a Codegen agent to analyze the issue
   - Create a GitHub Pull Request with changes
   - Comment on the Linear issue with a link to the PR

## Customization

You can customize the application by modifying the following files:

- `app.py`: The main application file that handles Linear webhook events
- `helpers.py`: Helper functions for processing Linear events and creating PRs
- `data.py`: Data structures and constants used by the application

## Troubleshooting

### Webhook Not Triggering

- Check that the webhook URL is correctly configured in Linear
- Verify that the Linear signing secret is correctly set in your `.env` file
- Check the Modal logs for any errors

### PR Creation Failing

- Verify that the GitHub token has the necessary permissions
- Check that the repository exists and you have access to it
- Ensure the Codegen agent has the necessary context to create meaningful changes

## Resources

- [Codegen Documentation](https://docs.codegen.sh/)
- [Modal Documentation](https://modal.com/docs)
- [Linear API Documentation](https://developers.linear.app/docs)
- [GitHub API Documentation](https://docs.github.com/en/rest)

