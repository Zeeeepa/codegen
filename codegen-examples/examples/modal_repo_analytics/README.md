# Modal Repository Analytics

This example demonstrates how to deploy a Modal application that uses Codegen to analyze GitHub repositories and extract code metrics.

## Features

- Analyze GitHub repositories using Codegen
- Extract code statistics and metrics (files, functions, classes)
- Web endpoint for API access
- Easily deployable to Modal cloud

## Prerequisites

Before you begin, ensure you have the following installed:
- Python 3.10+
- [Modal CLI](https://modal.com/docs/guide/cli-reference)
- [Codegen SDK](https://docs.codegen.com)

## Setup

1. Install the required dependencies:

```bash
pip install modal codegen==0.52.19
```

2. Authenticate with Modal:

```bash
modal token new
```

## Deployment

You can deploy this example to Modal using the provided deploy script:

```bash
./deploy.sh
```

This will deploy the application to Modal and provide you with a URL to access the API.

## Usage

Once deployed, you can use the API to analyze GitHub repositories:

```bash
curl "https://codegen-repo-analyzer--analyze-repo.modal.run?repo_name=owner/repo"
```

Replace `owner/repo` with the GitHub repository you want to analyze.

## API Response

The API returns a JSON response with the following structure:

```json
{
  "num_files": 123,
  "num_functions": 456,
  "num_classes": 78,
  "status": "success",
  "error": ""
}
```

If there's an error, the `status` field will be set to `"error"` and the `error` field will contain the error message.

## Customization

You can customize this example by:

1. Adding more metrics to the `RepoMetrics` model
2. Extending the `analyze_repo` function to extract additional information
3. Adding authentication to the API endpoint

## Troubleshooting

If you encounter issues:

1. Ensure you have the correct version of Modal and Codegen installed
2. Check that you're authenticated with Modal
3. Verify that the repository name is in the correct format (`owner/repo`)
4. Check the Modal logs for detailed error information

