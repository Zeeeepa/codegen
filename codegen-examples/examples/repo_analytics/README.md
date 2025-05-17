# Repository Analytics Example

This example demonstrates how to use the Codegen SDK with Modal to analyze GitHub repositories and generate insights about code complexity, dependencies, and more.

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
cd codegen/codegen-examples/examples/repo_analytics

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

This will deploy the application to Modal and provide you with a URL that you can use to access the analytics dashboard.

### Get Deployment Status

```bash
# Check the status of your Modal deployment
modal app status repo-analytics
```

### View Logs

```bash
# View logs from your Modal deployment
modal app logs repo-analytics
```

### Update Deployment

```bash
# Update your Modal deployment after making changes
./deploy.sh
```

### Stop Deployment

```bash
# Stop your Modal deployment
modal app stop repo-analytics
```

## Usage

Once deployed, you can use the repository analytics tool to:

1. Analyze code complexity metrics
1. Identify dependencies between modules
1. Generate visualizations of code structure
1. Track changes over time

To run an analysis, use the following command:

```bash
modal run run.py --repo owner/repo
```

## Customizing the Application

You can customize the application by modifying the `run.py` file to add new analytics features or change the visualization options.

## Troubleshooting

- **Authentication errors**: Check that your GITHUB_TOKEN is correct and has the necessary permissions.
- **Modal deployment issues**: Run `modal app logs repo-analytics` to view logs and diagnose issues.
- **Repository access issues**: Ensure that your GitHub token has access to the repositories you're trying to analyze.

## Additional Resources

- [Codegen Documentation](https://docs.codegen.sh/)
- [Modal Documentation](https://modal.com/docs)
- [GitHub API Documentation](https://docs.github.com/en/rest)
