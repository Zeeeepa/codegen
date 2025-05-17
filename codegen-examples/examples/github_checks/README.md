# GitHub Checks Example

This example demonstrates how to create a GitHub check that analyzes import cycles in a repository using the Codegen SDK and Modal. When a pull request is labeled, this application will:

1. Analyze the codebase for import cycles
2. Identify potentially problematic cycles with mixed static and dynamic imports
3. Post a comment on the pull request with the analysis results

## Prerequisites

- [Modal](https://modal.com/) account
- [GitHub](https://github.com/) repository access
- Python 3.13 or higher

## Setup

### 1. Install Dependencies

```bash
# Clone the repository
git clone https://github.com/Zeeeepa/codegen.git
cd codegen/codegen-examples/examples/github_checks

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
modal app status codegen-import-cycles-github-check
```

### View Logs

```bash
# View logs from your Modal deployment
modal app logs codegen-import-cycles-github-check
```

### Update Deployment

```bash
# Update your Modal deployment after making changes
./deploy.sh
```

### Stop Deployment

```bash
# Stop your Modal deployment
modal app stop codegen-import-cycles-github-check
```

## Configuring GitHub Webhooks

1. Go to your GitHub repository
2. Go to Settings → Webhooks
3. Click "Add webhook"
4. Enter the URL provided by Modal when you deployed the application
5. Select "application/json" as the content type
6. Select "Let me select individual events"
7. Check "Pull requests"
8. Click "Add webhook"

## Usage

1. Create a pull request in your repository
2. Add a label to the pull request
3. The application will automatically:
   - Analyze the codebase for import cycles
   - Identify potentially problematic cycles
   - Post a comment on the pull request with the analysis results

## Customizing the Application

You can customize the application by modifying the following functions in `app.py`:

- `create_graph_from_codebase`: Creates a directed graph representing import relationships
- `find_import_cycles`: Identifies strongly connected components (cycles) in the import graph
- `find_problematic_import_loops`: Identifies cycles with both static and dynamic imports

## Troubleshooting

- **Webhook not receiving events**: Verify that your GitHub webhook is configured correctly and that the URL is accessible.
- **Authentication errors**: Check that your GITHUB_TOKEN is correct and has the necessary permissions.
- **Modal deployment issues**: Run `modal app logs codegen-import-cycles-github-check` to view logs and diagnose issues.

## Additional Resources

- [Codegen Documentation](https://docs.codegen.sh/)
- [Modal Documentation](https://modal.com/docs)
- [GitHub Webhooks Documentation](https://docs.github.com/en/developers/webhooks-and-events/webhooks/about-webhooks)

