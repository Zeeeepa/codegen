"""
Notification Service

Handles desktop notifications, in-app alerts, and notification management
for agent runs, project updates, and system events.
"""

import logging
import platform
import subprocess
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import uuid
import threading
import time

from .state_manager import NotificationState


class NotificationService:
    """
    Service for managing notifications across multiple channels.
    
    Supports:
    - Desktop notifications (cross-platform)
    - In-app notifications
    - Sound alerts
    - Notification history and management
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the notification service."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Notification settings
        self.desktop_notifications_enabled = config.get('desktop_notifications', True)
        self.sound_notifications_enabled = config.get('sound_notifications', True)
        self.notification_sound = config.get('notification_sound', 'default')
        
        # Callbacks for in-app notifications
        self.notification_callbacks: List[Callable] = []
        
        # Detect platform for desktop notifications
        self.platform = platform.system().lower()
        self._check_notification_support()
        
    def _check_notification_support(self):
        """Check if desktop notifications are supported on this platform."""
        try:
            if self.platform == 'windows':
                # Windows 10+ has built-in toast notifications
                self.notification_method = 'windows_toast'
            elif self.platform == 'darwin':  # macOS
                # Use osascript for macOS notifications
                self.notification_method = 'macos_osascript'
            elif self.platform == 'linux':
                # Use notify-send for Linux
                result = subprocess.run(['which', 'notify-send'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    self.notification_method = 'linux_notify_send'
                else:
                    self.notification_method = None
                    self.logger.warning("notify-send not found. Desktop notifications disabled.")
            else:
                self.notification_method = None
                self.logger.warning(f"Unsupported platform: {self.platform}. Desktop notifications disabled.")
                
        except Exception as e:
            self.logger.error(f"Error checking notification support: {e}")
            self.notification_method = None
    
    def notify_agent_run_completed(self, agent_run_id: int, status: str, result: Optional[str] = None):
        """Send notification when an agent run completes."""
        title = f"Agent Run {agent_run_id} Completed"
        
        if status == 'success':
            message = f"Agent run completed successfully"
            icon = "✅"
        elif status == 'failed':
            message = f"Agent run failed"
            icon = "❌"
        else:
            message = f"Agent run finished with status: {status}"
            icon = "ℹ️"
        
        if result:
            message += f"\nResult: {result[:100]}..."
        
        self._send_notification(
            title=title,
            message=message,
            notification_type='agent_completion',
            related_agent_run_id=agent_run_id,
            icon=icon
        )
    
    def notify_pr_update(self, project_id: int, project_name: str, pr_title: str, pr_action: str):
        """Send notification for PR updates on starred projects."""
        title = f"PR Update: {project_name}"
        message = f"{pr_action}: {pr_title}"
        icon = "🔄"
        
        self._send_notification(
            title=title,
            message=message,
            notification_type='pr_update',
            related_project_id=project_id,
            icon=icon
        )
    
    def notify_validation_gate_result(self, project_id: int, project_name: str, gate_name: str, passed: bool):
        """Send notification for validation gate results."""
        title = f"Validation Gate: {project_name}"
        
        if passed:
            message = f"✅ {gate_name} passed"
            icon = "✅"
        else:
            message = f"❌ {gate_name} failed"
            icon = "❌"
        
        self._send_notification(
            title=title,
            message=message,
            notification_type='validation_gate',
            related_project_id=project_id,
            icon=icon
        )
    
    def notify_workflow_completed(self, workflow_name: str, status: str, agent_count: int):
        """Send notification when a workflow completes."""
        title = f"Workflow Completed: {workflow_name}"
        
        if status == 'success':
            message = f"✅ Workflow completed successfully with {agent_count} agents"
            icon = "✅"
        else:
            message = f"❌ Workflow failed with status: {status}"
            icon = "❌"
        
        self._send_notification(
            title=title,
            message=message,
            notification_type='workflow_completion',
            icon=icon
        )
    
    def notify_system_alert(self, title: str, message: str, alert_type: str = 'info'):
        """Send a system alert notification."""
        icons = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'error': '❌',
            'success': '✅'
        }
        
        self._send_notification(
            title=title,
            message=message,
            notification_type='system_alert',
            icon=icons.get(alert_type, 'ℹ️')
        )
    
    def _send_notification(self, title: str, message: str, notification_type: str, 
                          related_agent_run_id: Optional[int] = None,
                          related_project_id: Optional[int] = None,
                          icon: str = "ℹ️"):
        """Send a notification through all enabled channels."""
        notification_id = str(uuid.uuid4())
        
        # Create notification state
        notification = NotificationState(
            id=notification_id,
            type=notification_type,
            title=title,
            message=message,
            created_at=datetime.now(),
            related_agent_run_id=related_agent_run_id,
            related_project_id=related_project_id
        )
        
        # Send desktop notification
        if self.desktop_notifications_enabled:
            self._send_desktop_notification(title, message, icon)
        
        # Play sound notification
        if self.sound_notifications_enabled:
            self._play_notification_sound()
        
        # Send in-app notification
        self._send_in_app_notification(notification)
        
        self.logger.info(f"Notification sent: {title}")
    
    def _send_desktop_notification(self, title: str, message: str, icon: str = "ℹ️"):
        """Send a desktop notification based on the platform."""
        try:
            if not self.notification_method:
                return
            
            # Format the message with icon
            formatted_message = f"{icon} {message}"
            
            if self.notification_method == 'windows_toast':
                self._send_windows_notification(title, formatted_message)
            elif self.notification_method == 'macos_osascript':
                self._send_macos_notification(title, formatted_message)
            elif self.notification_method == 'linux_notify_send':
                self._send_linux_notification(title, formatted_message)
                
        except Exception as e:
            self.logger.error(f"Failed to send desktop notification: {e}")
    
    def _send_windows_notification(self, title: str, message: str):
        """Send Windows toast notification."""
        try:
            # Use PowerShell to send Windows 10+ toast notification
            ps_script = f'''
            [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
            [Windows.UI.Notifications.ToastNotification, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
            [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
            
            $template = @"
            <toast>
                <visual>
                    <binding template="ToastGeneric">
                        <text>{title}</text>
                        <text>{message}</text>
                    </binding>
                </visual>
            </toast>
            "@
            
            $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
            $xml.LoadXml($template)
            $toast = New-Object Windows.UI.Notifications.ToastNotification $xml
            [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Codegen Dashboard").Show($toast)
            '''
            
            subprocess.run(['powershell', '-Command', ps_script], 
                         capture_output=True, text=True, timeout=5)
            
        except Exception as e:
            self.logger.error(f"Failed to send Windows notification: {e}")
    
    def _send_macos_notification(self, title: str, message: str):
        """Send macOS notification using osascript."""
        try:
            script = f'display notification "{message}" with title "{title}"'
            subprocess.run(['osascript', '-e', script], 
                         capture_output=True, text=True, timeout=5)
            
        except Exception as e:
            self.logger.error(f"Failed to send macOS notification: {e}")
    
    def _send_linux_notification(self, title: str, message: str):
        """Send Linux notification using notify-send."""
        try:
            subprocess.run(['notify-send', title, message], 
                         capture_output=True, text=True, timeout=5)
            
        except Exception as e:
            self.logger.error(f"Failed to send Linux notification: {e}")
    
    def _play_notification_sound(self):
        """Play notification sound."""
        try:
            if self.notification_sound == 'none':
                return
            
            # Play system notification sound in a separate thread
            def play_sound():
                try:
                    if self.platform == 'windows':
                        import winsound
                        winsound.MessageBeep(winsound.MB_ICONINFORMATION)
                    elif self.platform == 'darwin':
                        subprocess.run(['afplay', '/System/Library/Sounds/Glass.aiff'], 
                                     capture_output=True, timeout=2)
                    elif self.platform == 'linux':
                        subprocess.run(['paplay', '/usr/share/sounds/alsa/Front_Left.wav'], 
                                     capture_output=True, timeout=2)
                except Exception as e:
                    self.logger.debug(f"Could not play notification sound: {e}")
            
            threading.Thread(target=play_sound, daemon=True).start()
            
        except Exception as e:
            self.logger.error(f"Failed to play notification sound: {e}")
    
    def _send_in_app_notification(self, notification: NotificationState):
        """Send in-app notification to registered callbacks."""
        for callback in self.notification_callbacks:
            try:
                callback(notification)
            except Exception as e:
                self.logger.error(f"Error in notification callback: {e}")
    
    def register_notification_callback(self, callback: Callable):
        """Register a callback for in-app notifications."""
        self.notification_callbacks.append(callback)
    
    def unregister_notification_callback(self, callback: Callable):
        """Unregister a notification callback."""
        if callback in self.notification_callbacks:
            self.notification_callbacks.remove(callback)
    
    def set_desktop_notifications_enabled(self, enabled: bool):
        """Enable or disable desktop notifications."""
        self.desktop_notifications_enabled = enabled
        self.logger.info(f"Desktop notifications {'enabled' if enabled else 'disabled'}")
    
    def set_sound_notifications_enabled(self, enabled: bool):
        """Enable or disable sound notifications."""
        self.sound_notifications_enabled = enabled
        self.logger.info(f"Sound notifications {'enabled' if enabled else 'disabled'}")
    
    def test_notification(self):
        """Send a test notification to verify the system is working."""
        self._send_notification(
            title="Codegen Dashboard Test",
            message="Notification system is working correctly!",
            notification_type="test",
            icon="🧪"
        )
