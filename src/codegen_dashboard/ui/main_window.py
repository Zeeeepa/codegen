"""
Main Window for the Codegen Dashboard.

Provides the primary GUI interface with navigation, running instances counter,
and content areas for different dashboard views.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import asyncio
from typing import Dict, Any, Optional, Callable
import logging
from datetime import datetime

from ..services.state_manager import StateManager, NotificationState
from ..services.codegen_client import CodegenClient
from ..services.notification_service import NotificationService


class MainWindow:
    """
    Main window for the Codegen Dashboard.
    
    Features:
    - Navigation sidebar with different views
    - Running instances counter (prominent display)
    - Content area for different dashboard views
    - Status bar with connection and notification status
    - Real-time updates and notifications
    """
    
    def __init__(self, root: tk.Tk, state_manager: StateManager, 
                 codegen_client: CodegenClient, notification_service: NotificationService):
        """Initialize the main window."""
        self.root = root
        self.state_manager = state_manager
        self.codegen_client = codegen_client
        self.notification_service = notification_service
        self.logger = logging.getLogger(__name__)
        
        # Window configuration
        self.root.title("Codegen CI/CD Dashboard")
        self.root.geometry("1400x900")
        self.root.minsize(1000, 600)
        
        # Configure styles
        self._configure_styles()
        
        # Create main layout
        self._create_layout()
        
        # Initialize state
        self.current_view = "dashboard"
        self.running_count = 0
        
        # Register for state changes
        self.state_manager.register_state_change_callback(self._on_state_change)
        self.notification_service.register_notification_callback(self._on_notification)
        
        # Start background tasks
        self._start_background_tasks()
        
        # Initial update
        self._update_running_counter()
    
    def _configure_styles(self):
        """Configure ttk styles for consistent theming."""
        style = ttk.Style()
        
        # Configure colors (inspired by Codegen TUI theme)
        colors = {
            'bg': '#1a1a1a',
            'fg': '#ffffff',
            'select_bg': '#3d5afe',
            'select_fg': '#ffffff',
            'accent': '#00bcd4',
            'success': '#4caf50',
            'warning': '#ff9800',
            'error': '#f44336'
        }
        
        # Configure main window
        self.root.configure(bg=colors['bg'])
        
        # Configure ttk styles
        style.theme_use('clam')
        style.configure('Dashboard.TFrame', background=colors['bg'])
        style.configure('Sidebar.TFrame', background='#2d2d2d')
        style.configure('Content.TFrame', background=colors['bg'])
        
        # Button styles
        style.configure('RunningCounter.TButton', 
                       font=('Arial', 16, 'bold'),
                       foreground=colors['accent'],
                       background='#2d2d2d')
        
        style.configure('Nav.TButton',
                       font=('Arial', 10),
                       foreground=colors['fg'],
                       background='#2d2d2d')
        
        # Label styles
        style.configure('Title.TLabel',
                       font=('Arial', 18, 'bold'),
                       foreground=colors['fg'],
                       background=colors['bg'])
        
        style.configure('Status.TLabel',
                       font=('Arial', 9),
                       foreground='#888888',
                       background=colors['bg'])
    
    def _create_layout(self):
        """Create the main window layout."""
        # Main container
        main_frame = ttk.Frame(self.root, style='Dashboard.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create sidebar
        self._create_sidebar(main_frame)
        
        # Create content area
        self._create_content_area(main_frame)
        
        # Create status bar
        self._create_status_bar(main_frame)
    
    def _create_sidebar(self, parent):
        """Create the navigation sidebar."""
        sidebar_frame = ttk.Frame(parent, style='Sidebar.TFrame', width=250)
        sidebar_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        sidebar_frame.pack_propagate(False)
        
        # Dashboard title
        title_label = ttk.Label(sidebar_frame, text="Codegen Dashboard", 
                               style='Title.TLabel')
        title_label.pack(pady=(20, 30))
        
        # Running instances counter (prominent)
        self._create_running_counter(sidebar_frame)
        
        # Navigation buttons
        nav_frame = ttk.Frame(sidebar_frame, style='Sidebar.TFrame')
        nav_frame.pack(fill=tk.X, padx=20, pady=20)
        
        nav_buttons = [
            ("🏠 Dashboard", "dashboard"),
            ("🤖 Agent Runs", "agent_runs"),
            ("⭐ Starred", "starred"),
            ("📊 Projects", "projects"),
            ("🔔 Notifications", "notifications"),
            ("⚙️ Workflows", "workflows"),
            ("🛠️ Settings", "settings")
        ]
        
        self.nav_buttons = {}
        for text, view_id in nav_buttons:
            btn = ttk.Button(nav_frame, text=text, style='Nav.TButton',
                           command=lambda v=view_id: self._switch_view(v))
            btn.pack(fill=tk.X, pady=2)
            self.nav_buttons[view_id] = btn
        
        # Quick actions
        actions_frame = ttk.Frame(sidebar_frame, style='Sidebar.TFrame')
        actions_frame.pack(fill=tk.X, padx=20, pady=20)
        
        ttk.Label(actions_frame, text="Quick Actions", 
                 font=('Arial', 12, 'bold')).pack(anchor=tk.W)
        
        quick_actions = [
            ("➕ New Agent Run", self._create_agent_run),
            ("📝 New PRD", self._create_prd),
            ("🔧 Test Notification", self._test_notification)
        ]
        
        for text, command in quick_actions:
            btn = ttk.Button(actions_frame, text=text, style='Nav.TButton',
                           command=command)
            btn.pack(fill=tk.X, pady=2)
    
    def _create_running_counter(self, parent):
        """Create the prominent running instances counter."""
        counter_frame = ttk.Frame(parent, style='Sidebar.TFrame')
        counter_frame.pack(fill=tk.X, padx=20, pady=20)
        
        # Counter button (clickable)
        self.running_counter_btn = ttk.Button(
            counter_frame, 
            text="🔄 0 Running", 
            style='RunningCounter.TButton',
            command=self._show_running_instances
        )
        self.running_counter_btn.pack(fill=tk.X, pady=5)
        
        # Status text
        self.counter_status_label = ttk.Label(
            counter_frame, 
            text="No active agent runs",
            style='Status.TLabel'
        )
        self.counter_status_label.pack()
    
    def _create_content_area(self, parent):
        """Create the main content area."""
        self.content_frame = ttk.Frame(parent, style='Content.TFrame')
        self.content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Content will be dynamically loaded based on selected view
        self._load_dashboard_view()
    
    def _create_status_bar(self, parent):
        """Create the status bar."""
        status_frame = ttk.Frame(parent, style='Dashboard.TFrame')
        status_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 0))
        
        # Connection status
        self.connection_status = ttk.Label(
            status_frame, 
            text="🟢 Connected to Codegen API",
            style='Status.TLabel'
        )
        self.connection_status.pack(side=tk.LEFT)
        
        # Notification count
        self.notification_count = ttk.Label(
            status_frame,
            text="📬 0 unread notifications",
            style='Status.TLabel'
        )
        self.notification_count.pack(side=tk.RIGHT)
        
        # Last update time
        self.last_update = ttk.Label(
            status_frame,
            text=f"Last update: {datetime.now().strftime('%H:%M:%S')}",
            style='Status.TLabel'
        )
        self.last_update.pack(side=tk.RIGHT, padx=(0, 20))
    
    def _load_dashboard_view(self):
        """Load the main dashboard view."""
        # Clear content
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Dashboard overview
        overview_frame = ttk.Frame(self.content_frame, style='Content.TFrame')
        overview_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Welcome message
        welcome_label = ttk.Label(
            overview_frame,
            text="Welcome to Codegen CI/CD Dashboard",
            style='Title.TLabel'
        )
        welcome_label.pack(pady=(0, 20))
        
        # Stats cards
        stats_frame = ttk.Frame(overview_frame, style='Content.TFrame')
        stats_frame.pack(fill=tk.X, pady=20)
        
        # Create stats cards (placeholder for now)
        stats = [
            ("Total Agent Runs", "0", "🤖"),
            ("Starred Items", "0", "⭐"),
            ("Active Projects", "0", "📊"),
            ("Unread Notifications", "0", "🔔")
        ]
        
        for i, (title, value, icon) in enumerate(stats):
            card_frame = ttk.Frame(stats_frame, style='Content.TFrame')
            card_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
            
            ttk.Label(card_frame, text=icon, font=('Arial', 24)).pack()
            ttk.Label(card_frame, text=value, font=('Arial', 18, 'bold')).pack()
            ttk.Label(card_frame, text=title, font=('Arial', 10)).pack()
        
        # Recent activity
        activity_frame = ttk.Frame(overview_frame, style='Content.TFrame')
        activity_frame.pack(fill=tk.BOTH, expand=True, pady=20)
        
        ttk.Label(activity_frame, text="Recent Activity", 
                 font=('Arial', 14, 'bold')).pack(anchor=tk.W)
        
        # Activity list (placeholder)
        activity_text = tk.Text(activity_frame, height=10, width=80)
        activity_text.pack(fill=tk.BOTH, expand=True, pady=10)
        activity_text.insert(tk.END, "No recent activity to display.\n")
        activity_text.insert(tk.END, "Create your first agent run to get started!")
        activity_text.config(state=tk.DISABLED)
    
    def _switch_view(self, view_id: str):
        """Switch to a different view."""
        self.current_view = view_id
        self.logger.info(f"Switching to view: {view_id}")
        
        # Update navigation button states
        for btn_id, btn in self.nav_buttons.items():
            if btn_id == view_id:
                btn.configure(style='Nav.TButton')  # Selected style
            else:
                btn.configure(style='Nav.TButton')  # Normal style
        
        # Load the appropriate view
        if view_id == "dashboard":
            self._load_dashboard_view()
        elif view_id == "agent_runs":
            self._load_agent_runs_view()
        elif view_id == "starred":
            self._load_starred_view()
        elif view_id == "projects":
            self._load_projects_view()
        elif view_id == "notifications":
            self._load_notifications_view()
        elif view_id == "workflows":
            self._load_workflows_view()
        elif view_id == "settings":
            self._load_settings_view()
    
    def _load_agent_runs_view(self):
        """Load the agent runs view."""
        # Clear content
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Agent runs view
        runs_frame = ttk.Frame(self.content_frame, style='Content.TFrame')
        runs_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        ttk.Label(runs_frame, text="Agent Runs", style='Title.TLabel').pack(anchor=tk.W)
        
        # Placeholder content
        ttk.Label(runs_frame, text="Agent runs view - Coming soon!").pack(pady=20)
    
    def _load_starred_view(self):
        """Load the starred items view."""
        # Clear content
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        starred_frame = ttk.Frame(self.content_frame, style='Content.TFrame')
        starred_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        ttk.Label(starred_frame, text="Starred Items", style='Title.TLabel').pack(anchor=tk.W)
        
        # Placeholder content
        ttk.Label(starred_frame, text="Starred items view - Coming soon!").pack(pady=20)
    
    def _load_projects_view(self):
        """Load the projects view."""
        # Clear content
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        projects_frame = ttk.Frame(self.content_frame, style='Content.TFrame')
        projects_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        ttk.Label(projects_frame, text="Projects", style='Title.TLabel').pack(anchor=tk.W)
        
        # Placeholder content
        ttk.Label(projects_frame, text="Projects view - Coming soon!").pack(pady=20)
    
    def _load_notifications_view(self):
        """Load the notifications view."""
        # Clear content
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        notifications_frame = ttk.Frame(self.content_frame, style='Content.TFrame')
        notifications_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        ttk.Label(notifications_frame, text="Notifications", style='Title.TLabel').pack(anchor=tk.W)
        
        # Placeholder content
        ttk.Label(notifications_frame, text="Notifications view - Coming soon!").pack(pady=20)
    
    def _load_workflows_view(self):
        """Load the workflows view."""
        # Clear content
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        workflows_frame = ttk.Frame(self.content_frame, style='Content.TFrame')
        workflows_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        ttk.Label(workflows_frame, text="Workflows", style='Title.TLabel').pack(anchor=tk.W)
        
        # Placeholder content
        ttk.Label(workflows_frame, text="Workflows view - Coming soon!").pack(pady=20)
    
    def _load_settings_view(self):
        """Load the settings view."""
        # Clear content
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        settings_frame = ttk.Frame(self.content_frame, style='Content.TFrame')
        settings_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        ttk.Label(settings_frame, text="Settings", style='Title.TLabel').pack(anchor=tk.W)
        
        # Placeholder content
        ttk.Label(settings_frame, text="Settings view - Coming soon!").pack(pady=20)
    
    def _show_running_instances(self):
        """Show detailed view of running instances."""
        running_runs = self.state_manager.get_running_agent_runs()
        
        if not running_runs:
            messagebox.showinfo("Running Instances", "No agent runs are currently running.")
            return
        
        # Create a popup window with running instances
        popup = tk.Toplevel(self.root)
        popup.title("Running Agent Instances")
        popup.geometry("600x400")
        popup.transient(self.root)
        popup.grab_set()
        
        # List of running instances
        frame = ttk.Frame(popup)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        ttk.Label(frame, text="Currently Running Agent Runs", 
                 font=('Arial', 14, 'bold')).pack(anchor=tk.W, pady=(0, 10))
        
        for run in running_runs:
            run_frame = ttk.Frame(frame)
            run_frame.pack(fill=tk.X, pady=5)
            
            ttk.Label(run_frame, text=f"Agent Run {run.id}").pack(side=tk.LEFT)
            ttk.Label(run_frame, text=f"Status: {run.status}").pack(side=tk.LEFT, padx=(20, 0))
            
            if run.web_url:
                ttk.Button(run_frame, text="View", 
                          command=lambda url=run.web_url: self._open_url(url)).pack(side=tk.RIGHT)
    
    def _create_agent_run(self):
        """Show dialog to create a new agent run."""
        # Placeholder for agent run creation dialog
        messagebox.showinfo("Create Agent Run", "Agent run creation dialog - Coming soon!")
    
    def _create_prd(self):
        """Show dialog to create a new PRD."""
        # Placeholder for PRD creation dialog
        messagebox.showinfo("Create PRD", "PRD creation dialog - Coming soon!")
    
    def _test_notification(self):
        """Send a test notification."""
        self.notification_service.test_notification()
    
    def _open_url(self, url: str):
        """Open URL in default browser."""
        import webbrowser
        webbrowser.open(url)
    
    def _update_running_counter(self):
        """Update the running instances counter."""
        count = self.state_manager.get_running_count()
        self.running_count = count
        
        # Update counter button
        if count == 0:
            self.running_counter_btn.configure(text="🔄 0 Running")
            self.counter_status_label.configure(text="No active agent runs")
        else:
            self.running_counter_btn.configure(text=f"🔄 {count} Running")
            status_text = f"{count} agent run{'s' if count != 1 else ''} active"
            self.counter_status_label.configure(text=status_text)
    
    def _update_status_bar(self):
        """Update the status bar information."""
        # Update last update time
        self.last_update.configure(text=f"Last update: {datetime.now().strftime('%H:%M:%S')}")
        
        # Update notification count
        unread_count = len(self.state_manager.get_unread_notifications())
        self.notification_count.configure(text=f"📬 {unread_count} unread notifications")
        
        # Update connection status (check if client is authenticated)
        if self.codegen_client.is_authenticated():
            self.connection_status.configure(text="🟢 Connected to Codegen API")
        else:
            self.connection_status.configure(text="🔴 Not connected to Codegen API")
    
    def _on_state_change(self, event_type: str, data: Dict[str, Any]):
        """Handle state changes."""
        self.logger.debug(f"State change: {event_type}")
        
        # Update UI on main thread
        self.root.after(0, self._update_running_counter)
        self.root.after(0, self._update_status_bar)
    
    def _on_notification(self, notification: NotificationState):
        """Handle new notifications."""
        self.logger.info(f"New notification: {notification.title}")
        
        # Update UI on main thread
        self.root.after(0, self._update_status_bar)
    
    def _start_background_tasks(self):
        """Start background tasks for real-time updates."""
        def update_loop():
            """Background update loop."""
            while True:
                try:
                    # Update running counter every 30 seconds
                    self.root.after(0, self._update_running_counter)
                    self.root.after(0, self._update_status_bar)
                    
                    # Sleep for 30 seconds
                    threading.Event().wait(30)
                    
                except Exception as e:
                    self.logger.error(f"Error in background update: {e}")
        
        # Start background thread
        update_thread = threading.Thread(target=update_loop, daemon=True)
        update_thread.start()
    
    def cleanup(self):
        """Cleanup resources when closing."""
        self.logger.info("Cleaning up main window")
        self.state_manager.cleanup()
