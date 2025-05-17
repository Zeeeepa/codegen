# Modal Repository Analytics Example

This example demonstrates how to create a Modal application that provides analytics for GitHub repositories using the Codegen SDK. The application exposes an API that can analyze repositories for:

- Code complexity metrics
- Dependency graphs
- File statistics
- Contributor insights
- And more

## Prerequisites

- [Modal](https://modal.com/) account
- [GitHub](https://github.com/) repository access
- Python 3.10 or higher

## Setup

### 1. Install Dependencies

```bash
# Clone the repository
git clone https://github.com/Zeeeepa/codegen.git
cd codegen/codegen-examples/examples/modal_repo_analytics

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

This will deploy the application to Modal and provide you with a URL that you can use to access the API.

### Get Deployment Status

```bash
# Check the status of your Modal deployment
modal app status repo-analytics-api
```

### View Logs

```bash
# View logs from your Modal deployment
modal app logs repo-analytics-api
```

### Update Deployment

```bash
# Update your Modal deployment after making changes
./deploy.sh
```

### Stop Deployment

```bash
# Stop your Modal deployment
modal app stop repo-analytics-api
```

## API Usage

The API provides the following endpoints:

- `GET /analyze/{owner}/{repo}`: Analyze a repository and return metrics
- `GET /complexity/{owner}/{repo}`: Get code complexity metrics for a repository
- `GET /dependencies/{owner}/{repo}`: Get dependency graph for a repository

Example request:

```bash
curl https://your-modal-url.modal.run/analyze/Zeeeepa/codegen
```

## Customizing the Application

You can customize the application by modifying the API endpoints in `api.py`. The application uses the Codegen SDK to analyze repositories, so you can leverage all of its features to extract the metrics you need.

## Troubleshooting

- **Authentication errors**: Check that your GITHUB_TOKEN is correct and has the necessary permissions.
- **Modal deployment issues**: Run `modal app logs repo-analytics-api` to view logs and diagnose issues.
- **Rate limiting**: GitHub API has rate limits. If you're analyzing large repositories or making many requests, you might hit these limits.

## Additional Resources

- [Codegen Documentation](https://docs.codegen.sh/)
- [Modal Documentation](https://modal.com/docs)
- [GitHub API Documentation](https://docs.github.com/en/rest)

