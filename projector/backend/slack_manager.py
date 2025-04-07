import os
import logging
import time
import json
import re
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from projector.backend.thread_pool import ThreadPool

class SlackManager:
    """Manager for Slack integration with multithreading capabilities."""
    
    def __init__(self, slack_token, default_channel):
        """Initialize the Slack manager."""
        self.client = WebClient(token=slack_token)
        self.default_channel = default_channel
        self.logger = logging.getLogger(__name__)
        self.threads = {}  # Store thread details: {topic: {"channel": channel, "ts": timestamp}}
        self.thread_pool = ThreadPool(max_workers=10)  # Allow up to 10 concurrent threads
        
        # Load threads from disk if available
        self._load_threads()
    
    def get_channel_id(self, channel_name):
        """Get the ID of a channel by name."""
        try:
            result = self.client.conversations_list()
            for channel in result["channels"]:
                if channel["name"] == channel_name:
                    return channel["id"]
            
            self.logger.warning(f"Channel '{channel_name}' not found.")
            return None
        except SlackApiError as e:
            self.logger.error(f"Error getting channel ID: {e}")
            return None
    
    def create_thread(self, topic, message, channel=None):
        """Create a new thread in Slack."""
        if not channel:
            channel = self.default_channel
        
        try:
            # Get channel ID
            channel_id = self.get_channel_id(channel)
            if not channel_id:
                return None
            
            # Create thread
            result = self.client.chat_postMessage(
                channel=channel_id,
                text=f"*Topic: {topic}*\n\n{message}"
            )
            
            # Store thread details
            thread_ts = result["ts"]
            self.threads[topic] = {
                "channel": channel,
                "ts": thread_ts,
                "created_at": time.time(),
                "last_updated": time.time()
            }
            
            # Save threads to disk
            self._save_threads()
            
            return thread_ts
        except SlackApiError as e:
            self.logger.error(f"Error creating thread: {e}")
            return None
    
    def reply_to_thread(self, topic, message):
        """Reply to an existing thread."""
        if topic not in self.threads:
            self.logger.error(f"Thread for topic '{topic}' not found.")
            return None
        
        thread_info = self.threads[topic]
        channel_id = self.get_channel_id(thread_info["channel"])
        
        if not channel_id:
            return None
        
        try:
            result = self.client.chat_postMessage(
                channel=channel_id,
                text=message,
                thread_ts=thread_info["ts"]
            )
            
            # Update last_updated timestamp
            self.threads[topic]["last_updated"] = time.time()
            self._save_threads()
            
            return result["ts"]
        except SlackApiError as e:
            self.logger.error(f"Error replying to thread: {e}")
            return None
    
    def get_thread_history(self, topic):
        """Get the history of a thread."""
        if topic not in self.threads:
            self.logger.error(f"Thread for topic '{topic}' not found.")
            return []
        
        thread_info = self.threads[topic]
        channel_id = self.get_channel_id(thread_info["channel"])
        
        if not channel_id:
            return []
        
        try:
            result = self.client.conversations_replies(
                channel=channel_id,
                ts=thread_info["ts"]
            )
            
            return result["messages"]
        except SlackApiError as e:
            self.logger.error(f"Error getting thread history: {e}")
            return []
    
    def create_multiple_threads(self, topics, message_template, channel=None):
        """Create multiple threads concurrently."""
        results = {}
        for topic in topics:
            task_id = self.thread_pool.submit_task(
                self.create_thread,
                priority=3,
                topic=topic,
                message=message_template.format(topic=topic),
                channel=channel
            )
            results[topic] = task_id
            
        # Wait for all tasks to complete or timeout
        completed_results = {}
        for topic, task_id in results.items():
            result = self.thread_pool.get_result(task_id, timeout=30)
            if result and result.get("status") == "completed":
                completed_results[topic] = {"success": True, "ts": result.get("result")}
            else:
                completed_results[topic] = {"success": False, "error": result.get("error") if result else "Timeout"}
            
        return completed_results
    
    def reply_to_multiple_threads(self, topics_messages, channel=None):
        """Reply to multiple threads concurrently."""
        results = {}
        for topic, message in topics_messages.items():
            task_id = self.thread_pool.submit_task(
                self.reply_to_thread,
                priority=5,
                topic=topic,
                message=message
            )
            results[topic] = task_id
            
        # Wait for all tasks to complete or timeout
        completed_results = {}
        for topic, task_id in results.items():
            result = self.thread_pool.get_result(task_id, timeout=30)
            if result and result.get("status") == "completed":
                completed_results[topic] = {"success": True, "ts": result.get("result")}
            else:
                completed_results[topic] = {"success": False, "error": result.get("error") if result else "Timeout"}
            
        return completed_results
    
    def post_status_update(self, topic, status, details=None):
        """Post a status update to a thread."""
        status_emoji = {
            "completed": "✅",
            "in_progress": "🚧",
            "blocked": "🚫",
            "testing": "🧪",
            "review": "👀",
            "not_started": "⏳"
        }
        
        emoji = status_emoji.get(status, "ℹ️")
        message = f"{emoji} *Status Update: {status.upper()}*\n"
        
        if details:
            message += f"{details}"
        
        return self.reply_to_thread(topic, message)
    
    def search_threads(self, keyword):
        """Search for threads containing a keyword."""
        matching_threads = {}
        
        for topic, thread_info in self.threads.items():
            if keyword.lower() in topic.lower():
                matching_threads[topic] = thread_info
                continue
            
            # Search in thread history
            messages = self.get_thread_history(topic)
            for message in messages:
                if keyword.lower() in message.get("text", "").lower():
                    matching_threads[topic] = thread_info
                    break
        
        return matching_threads
    
    def get_thread_activity_metrics(self):
        """Get activity metrics for all threads."""
        metrics = {
            "total_threads": len(self.threads),
            "active_today": 0,
            "active_this_week": 0,
            "inactive_threads": 0,
            "most_active_threads": []
        }
        
        now = time.time()
        day_seconds = 86400  # 24 hours in seconds
        week_seconds = 604800  # 7 days in seconds
        
        thread_activity = []
        for topic, thread_info in self.threads.items():
            last_updated = thread_info["last_updated"]
            time_since_update = now - last_updated
            
            if time_since_update < day_seconds:
                metrics["active_today"] += 1
            
            if time_since_update < week_seconds:
                metrics["active_this_week"] += 1
            else:
                metrics["inactive_threads"] += 1
            
            # Get activity level (message count)
            messages = self.get_thread_history(topic)
            activity_level = len(messages)
            
            thread_activity.append({
                "topic": topic,
                "last_updated": last_updated,
                "activity_level": activity_level
            })
        
        # Sort threads by activity level
        thread_activity.sort(key=lambda x: x["activity_level"], reverse=True)
        metrics["most_active_threads"] = thread_activity[:5]  # Top 5 most active threads
        
        return metrics
    
    def archive_old_threads(self, days_threshold=30):
        """Archive threads that haven't been updated in a while."""
        now = time.time()
        threshold = now - (days_threshold * 86400)  # Convert days to seconds
        
        archived_threads = []
        for topic, thread_info in list(self.threads.items()):
            if thread_info["last_updated"] < threshold:
                # Archive this thread
                archived_threads.append({
                    "topic": topic,
                    "thread_info": thread_info
                })
                
                # Remove from active threads
                del self.threads[topic]
        
        # Save changes
        self._save_threads()
        
        # Save archived threads
        self._save_archived_threads(archived_threads)
        
        return archived_threads
    
    def _save_threads(self):
        """Save threads to disk."""
        try:
            with open("threads.json", "w") as f:
                json.dump(self.threads, f)
        except Exception as e:
            self.logger.error(f"Error saving threads: {e}")
    
    def _load_threads(self):
        """Load threads from disk."""
        try:
            if os.path.exists("threads.json"):
                with open("threads.json", "r") as f:
                    self.threads = json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading threads: {e}")
    
    def _save_archived_threads(self, archived_threads):
        """Save archived threads to disk."""
        try:
            archived = []
            if os.path.exists("archived_threads.json"):
                with open("archived_threads.json", "r") as f:
                    archived = json.load(f)
            
            archived.extend(archived_threads)
            
            with open("archived_threads.json", "w") as f:
                json.dump(archived, f)
        except Exception as e:
            self.logger.error(f"Error saving archived threads: {e}")
