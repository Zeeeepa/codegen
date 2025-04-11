"""
Storage Manager for PR Review Agent.
This module provides functionality for storing and retrieving review results and insights.
"""
import os
import json
import logging
import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class StorageManager:
    """
    Manager for storing and retrieving review results and insights.
    
    Provides functionality for saving review results, validation insights,
    and other data for future reference.
    """
    
    def __init__(self, storage_type: str = "local", storage_path: str = "data"):
        """
        Initialize the storage manager.
        
        Args:
            storage_type: Type of storage (local, s3, etc.)
            storage_path: Path to storage directory
        """
        self.storage_type = storage_type
        self.storage_path = storage_path
        
        # Create storage directories if they don't exist
        self._create_storage_directories()
    
    def _create_storage_directories(self) -> None:
        """Create storage directories if they don't exist."""
        if self.storage_type == "local":
            os.makedirs(os.path.join(self.storage_path, "reviews"), exist_ok=True)
            os.makedirs(os.path.join(self.storage_path, "insights"), exist_ok=True)
    
    def save_review_results(self, repo_name: str, pr_number: int, review_results: Dict[str, Any]) -> str:
        """
        Save review results.
        
        Args:
            repo_name: Repository name (owner/repo)
            pr_number: Pull request number
            review_results: Review results
            
        Returns:
            Path to saved review results
        """
        if self.storage_type == "local":
            # Create filename
            repo_slug = repo_name.replace("/", "-")
            timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            filename = f"{repo_slug}-pr-{pr_number}-{timestamp}.json"
            
            # Create file path
            file_path = os.path.join(self.storage_path, "reviews", filename)
            
            # Save review results
            with open(file_path, "w") as f:
                json.dump(review_results, f, indent=2)
            
            logger.info(f"Saved review results to {file_path}")
            
            return file_path
        else:
            logger.warning(f"Storage type {self.storage_type} not supported")
            return ""
    
    def get_review_results(self, repo_name: str, pr_number: int) -> Optional[Dict[str, Any]]:
        """
        Get review results.
        
        Args:
            repo_name: Repository name (owner/repo)
            pr_number: Pull request number
            
        Returns:
            Review results or None if not found
        """
        if self.storage_type == "local":
            # Create repo slug
            repo_slug = repo_name.replace("/", "-")
            
            # Get all review files
            reviews_dir = os.path.join(self.storage_path, "reviews")
            if not os.path.exists(reviews_dir):
                return None
            
            # Find the latest review for this PR
            review_files = [f for f in os.listdir(reviews_dir) if f.startswith(f"{repo_slug}-pr-{pr_number}-")]
            
            if not review_files:
                return None
            
            # Sort by timestamp (newest first)
            review_files.sort(reverse=True)
            
            # Load the latest review
            file_path = os.path.join(reviews_dir, review_files[0])
            
            with open(file_path, "r") as f:
                review_results = json.load(f)
            
            return review_results
        else:
            logger.warning(f"Storage type {self.storage_type} not supported")
            return None
    
    def save_insights(self, repo_name: str, pr_number: int, insights: Dict[str, Any], insight_type: str) -> str:
        """
        Save insights.
        
        Args:
            repo_name: Repository name (owner/repo)
            pr_number: Pull request number
            insights: Insights data
            insight_type: Type of insights (documentation, code, etc.)
            
        Returns:
            Path to saved insights
        """
        if self.storage_type == "local":
            # Create filename
            repo_slug = repo_name.replace("/", "-")
            timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            filename = f"{repo_slug}-pr-{pr_number}-{insight_type}-{timestamp}.json"
            
            # Create file path
            file_path = os.path.join(self.storage_path, "insights", filename)
            
            # Save insights
            with open(file_path, "w") as f:
                json.dump(insights, f, indent=2)
            
            logger.info(f"Saved {insight_type} insights to {file_path}")
            
            return file_path
        else:
            logger.warning(f"Storage type {self.storage_type} not supported")
            return ""
    
    def get_insights(self, repo_name: str, pr_number: int, insight_type: str) -> Optional[Dict[str, Any]]:
        """
        Get insights.
        
        Args:
            repo_name: Repository name (owner/repo)
            pr_number: Pull request number
            insight_type: Type of insights (documentation, code, etc.)
            
        Returns:
            Insights data or None if not found
        """
        if self.storage_type == "local":
            # Create repo slug
            repo_slug = repo_name.replace("/", "-")
            
            # Get all insight files
            insights_dir = os.path.join(self.storage_path, "insights")
            if not os.path.exists(insights_dir):
                return None
            
            # Find the latest insights for this PR and type
            insight_files = [f for f in os.listdir(insights_dir) if f.startswith(f"{repo_slug}-pr-{pr_number}-{insight_type}-")]
            
            if not insight_files:
                return None
            
            # Sort by timestamp (newest first)
            insight_files.sort(reverse=True)
            
            # Load the latest insights
            file_path = os.path.join(insights_dir, insight_files[0])
            
            with open(file_path, "r") as f:
                insights = json.load(f)
            
            return insights
        else:
            logger.warning(f"Storage type {self.storage_type} not supported")
            return None
