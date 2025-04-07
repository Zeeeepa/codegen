"""
Utility functions for the MultiThread Slack GitHub Tool.
"""
import os
import re
import logging
from projector.backend.config import (
    SLACK_USER_TOKEN, GITHUB_TOKEN, GITHUB_USERNAME,
    SLACK_DEFAULT_CHANNEL, GITHUB_DEFAULT_REPO,
    OPENAI_API_KEY, ENABLE_AI_FEATURES
)

logger = logging.getLogger(__name__)

def validate_config():
    """Validate configuration settings."""
    # Check Slack configuration
    if not SLACK_USER_TOKEN:
        logger.error("SLACK_USER_TOKEN is missing.")
        return False
    
    # Check GitHub configuration
    if not GITHUB_TOKEN:
        logger.error("GITHUB_TOKEN is missing.")
        return False
    
    if not GITHUB_USERNAME:
        logger.error("GITHUB_USERNAME is missing.")
        return False
    
    if not GITHUB_DEFAULT_REPO:
        logger.error("GITHUB_DEFAULT_REPO is missing.")
        return False
    
    # Check AI configuration if enabled
    if ENABLE_AI_FEATURES and not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY is missing but AI features are enabled.")
        return False
    
    return True

def sanitize_branch_name(name):
    """Sanitize a name for use as a branch name."""
    # Convert to lowercase
    name = name.lower()
    
    # Replace spaces and special characters with hyphens
    name = re.sub(r'[^a-z0-9]+', '-', name)
    
    # Remove leading and trailing hyphens
    name = name.strip('-')
    
    return name

def format_markdown_link(text, url):
    """Format a Markdown link."""
    return f"[{text}]({url})"

def parse_feature_from_branch(branch_name):
    """Parse feature name from branch name."""
    if branch_name.startswith("feature/"):
        feature_name = branch_name[8:]  # Remove "feature/" prefix
        feature_name = feature_name.replace("-", " ")  # Replace hyphens with spaces
        return feature_name.title()  # Convert to title case
    return None

def generate_file_path(feature_name, file_type):
    """Generate file path based on feature name and type."""
    sanitized_name = sanitize_branch_name(feature_name)
    
    if file_type == "model":
        return f"src/models/{sanitized_name}_model.py"
    elif file_type == "controller":
        return f"src/controllers/{sanitized_name}_controller.py"
    elif file_type == "service":
        return f"src/services/{sanitized_name}_service.py"
    elif file_type == "route":
        return f"src/routes/{sanitized_name}_routes.py"
    elif file_type == "test":
        return f"tests/{sanitized_name}_test.py"
    else:
        return f"src/{sanitized_name}.py"

def calculate_completion_percentage(feature):
    """Calculate completion percentage for a feature."""
    if not feature or "plan" not in feature:
        return 0
    
    steps = feature.get("plan", {}).get("steps", [])
    if not steps:
        return 0
    
    status = feature.get("status", "not_started")
    if status == "completed":
        return 100
    elif status == "not_started":
        return 0
    
    # For in_progress features, estimate based on GitHub activity
    if "github_branch" in feature and "generated_code" in feature:
        return 50  # Code has been generated, approximately halfway done
    
    # Default for in_progress without code generation
    return 25

def estimate_project_completion(features):
    """Estimate overall project completion percentage."""
    if not features:
        return 0
    
    total_features = len(features)
    completed_features = sum(1 for f in features.values() if f.get("status") == "completed")
    in_progress_features = sum(1 for f in features.values() if f.get("status") == "in_progress")
    
    # Weight completed features fully, in-progress features partially
    completion = (completed_features + (in_progress_features * 0.5)) / total_features
    
    return round(completion * 100, 1)

def get_priority_emoji(priority):
    """Get emoji for a priority level."""
    if priority.lower() == "high":
        return "🔴"
    elif priority.lower() == "medium":
        return "🟡"
    elif priority.lower() == "low":
        return "🟢"
    else:
        return "⚪"

def get_status_emoji(status):
    """Get emoji for a status."""
    if status == "completed":
        return "✅"
    elif status == "in_progress":
        return "🚧"
    elif status == "blocked":
        return "🚫"
    elif status == "testing":
        return "🧪"
    elif status == "review":
        return "👀"
    elif status == "not_started":
        return "⏳"
    else:
        return "ℹ️"
