# Projector

A tool for managing projects across Slack and GitHub.

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/Zeeeepa/codegen.git
   cd codegen
   ```

2. Install the package in development mode:
   ```
   pip install -e .
   ```

3. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Run the application:
   ```
   python projector/main.py
   ```

## Configuration

Create a `.env` file in the root directory with the following variables:

```
SLACK_USER_TOKEN=your-slack-token
GITHUB_TOKEN=your-github-token
GITHUB_USERNAME=your-github-username
SLACK_DEFAULT_CHANNEL=general
GITHUB_DEFAULT_REPO=your-default-repo
```

## Usage

Run the application with various options:

```
python projector/main.py --help
```

- `--ui` or `-u`: Launch only the Streamlit UI
- `--backend` or `-b`: Run only the backend service
- `--docs` or `-d`: Path to markdown documents folder
- `--debug`: Enable debug logging
- `--threads`: Maximum number of concurrent threads (1-10)
- `--monitor`: Enable automatic Slack thread monitoring
- `--max_concurrent_projects`: Maximum number of concurrent projects to implement (1-5)
