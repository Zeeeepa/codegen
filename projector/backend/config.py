"""
Configuration settings for the MultiThread Slack GitHub Tool.
Store your API tokens and configuration in a secure way.
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

# Get configuration from environment variables
def get_config(key, default=None):
    # Get from environment variables
    value = os.getenv(key)
    if value is not None:
        return value
    
    # Return default if not found
    return default

# Slack configuration
SLACK_USER_TOKEN = get_config("SLACK_USER_TOKEN")
SLACK_DEFAULT_CHANNEL = get_config("SLACK_DEFAULT_CHANNEL", "general")

# GitHub configuration
GITHUB_TOKEN = get_config("GITHUB_TOKEN")
GITHUB_USERNAME = get_config("GITHUB_USERNAME")
GITHUB_DEFAULT_REPO = get_config("GITHUB_DEFAULT_REPO")
GITHUB_DEFAULT_BRANCH = get_config("GITHUB_DEFAULT_BRANCH", "main")

# AI assistant configuration
OPENAI_API_KEY = get_config("OPENAI_API_KEY")
AI_MODEL = get_config("AI_MODEL", "gpt-4")
ENABLE_AI_FEATURES = get_config("ENABLE_AI_FEATURES", "True").lower() == "true"

# Application settings
MD_DOCS_FOLDER = get_config("MD_DOCS_FOLDER", "./docs")
DEBUG_MODE = get_config("DEBUG_MODE", "False").lower() == "true"
MAX_THREADS = int(get_config("MAX_THREADS", "10"))
MONITOR_THREADS = get_config("MONITOR_THREADS", "True").lower() == "true"

# Runtime configuration that can be updated via UI
runtime_config = {
    "slack_connected": False,
    "github_connected": False,
    "ai_enabled": ENABLE_AI_FEATURES,
    "active_channel": SLACK_DEFAULT_CHANNEL,
    "active_repo": GITHUB_DEFAULT_REPO,
    "max_threads": MAX_THREADS
}
