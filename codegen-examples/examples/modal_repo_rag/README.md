# Modal Repository RAG Q&A

This example demonstrates how to deploy a Modal application that uses Codegen's VectorIndex for RAG-based code question answering.

## Features

- Answer questions about code using Retrieval-Augmented Generation (RAG)
- Automatically index GitHub repositories
- Persistent vector indices using Modal volumes
- Web endpoint for API access
- Easily deployable to Modal cloud

## Prerequisites

Before you begin, ensure you have the following installed:
- Python 3.10+
- [Modal CLI](https://modal.com/docs/guide/cli-reference)
- [Codegen SDK](https://docs.codegen.com)
- OpenAI API key (for the LLM)

## Setup

1. Install the required dependencies:

```bash
pip install modal codegen==0.52.19 openai
```

2. Authenticate with Modal:

```bash
modal token new
```

3. Set up your OpenAI API key:

```bash
export OPENAI_API_KEY=your_api_key_here
```

## Deployment

You can deploy this example to Modal using the provided deploy script:

```bash
./deploy.sh
```

This will:
1. Create a Modal volume for storing vector indices (if it doesn't exist)
2. Deploy the application to Modal
3. Provide you with a URL to access the API

## Usage

Once deployed, you can use the API to ask questions about GitHub repositories:

```bash
curl -X POST "https://codegen-rag-qa--answer-code-question.modal.run" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_name": "owner/repo",
    "query": "How does the authentication system work?"
  }'
```

Replace `owner/repo` with the GitHub repository you want to query and adjust the question as needed.

## API Response

The API returns a JSON response with the following structure:

```json
{
  "answer": "The authentication system works by...",
  "context": [
    {
      "filepath": "src/auth/login.py",
      "snippet": "def authenticate_user(username, password):..."
    },
    {
      "filepath": "src/auth/session.py",
      "snippet": "class Session:..."
    }
  ],
  "status": "success",
  "error": ""
}
```

If there's an error, the `status` field will be set to `"error"` and the `error` field will contain the error message.

## How It Works

1. The application creates or loads a vector index for the specified repository
2. When a question is asked, it finds the most relevant code snippets using semantic search
3. It then uses OpenAI's API to generate an answer based on the retrieved code context
4. The vector indices are stored in a Modal volume for persistence between runs

## Customization

You can customize this example by:

1. Changing the LLM model (currently uses GPT-4 Turbo)
2. Adjusting the number of context snippets retrieved
3. Modifying the prompt template for better answers
4. Adding authentication to the API endpoint

## Troubleshooting

If you encounter issues:

1. Ensure you have the correct version of Modal and Codegen installed
2. Check that you're authenticated with Modal
3. Verify that your OpenAI API key is set correctly
4. Check the Modal logs for detailed error information

