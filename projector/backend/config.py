"""
Configuration settings for the MultiThread Slack GitHub Tool.
Store your API tokens and configuration in a secure way.
"""
import os
from dotenv import load_dotenv
import streamlit as st

# Load environment variables from .env file if present
load_dotenv()

# Attempt to load from Streamlit secrets if available
def get_config(key, default=None):
    # Try to get from st.secrets first (for deployed apps)
    if hasattr(st, 'secrets') and key in st.secrets:
        return st.secrets[key]
    # Then from environment variables
    value = os.getenv(key)
    if value is not None:
        return value
    # Finally return default
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
