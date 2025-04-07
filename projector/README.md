# Projector

A tool for managing and automating software development projects using AI agents.

## Features

- Project management dashboard
- GitHub integration
- Slack integration
- AI-powered code generation and review
- Implementation planning and tracking

## Installation

### Prerequisites

- Python 3.8+ (Python 3.13 compatible)
- Node.js 14+ and npm
- Git

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/projector.git
cd projector
```

2. Update dependencies:
```bash
./scripts/update_dependencies.sh
```

3. Start the application:
```bash
# Start the backend
./scripts/start_backend.sh

# In a separate terminal, start the frontend
./scripts/start_frontend.sh
```

4. Open your browser and navigate to http://localhost:3000

## Python 3.13 Compatibility

If you're using Python 3.13, the application has been updated to ensure compatibility. The key changes include:

1. Updated Pydantic to version 2.4.0+ to fix ForwardRef._evaluate() errors
2. Added explicit installation of langgraph and plotly packages
3. Fixed PYTHONPATH settings to ensure proper module resolution

If you encounter any issues with Python 3.13:

```bash
# Run the update dependencies script
./scripts/update_dependencies.sh

# Verify the installations
pip show langgraph
pip show plotly
```

## Troubleshooting

### Connection Refused Errors

If you see "Failed to proxy http://localhost:8000/api/projects" errors:

1. Make sure the backend server is running on port 8000
2. Check if there are any Python import errors in the backend logs
3. Ensure PYTHONPATH is set correctly to include both the project root and the codegen src directory

### Module Not Found Errors

If you encounter "ModuleNotFoundError" for packages like langgraph or plotly:

```bash
# Activate your virtual environment
source venv/bin/activate

# Install the missing packages
pip install langgraph>=0.3.20 plotly>=5.24.0
```

## Configuration

Configuration is managed through environment variables. Create a `.env` file in the project root with the following variables:

```
GITHUB_TOKEN=your_github_token
GITHUB_USERNAME=your_github_username
SLACK_USER_TOKEN=your_slack_token
OPENAI_API_KEY=your_openai_api_key
```

## License

MIT
