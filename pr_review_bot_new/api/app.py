"""
FastAPI application for the PR Review Bot.
Provides endpoints for handling GitHub webhook events.
"""

import os
import logging
import json
from typing import Dict, Any, Optional
from fastapi import FastAPI, Request, Response, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import pkg_resources

from ..core.github_client import GitHubClient
from ..core.pr_reviewer import PRReviewer
from .webhook_handler import WebhookHandler

# Configure logging
logger = logging.getLogger(__name__)

class PRReviewBotApp:
    """
    FastAPI application for the PR Review Bot.
    """
    
    def __init__(self):
        """
        Initialize the FastAPI application.
        """
        self.app = FastAPI(title="PR Review Bot")
        self.setup_dependencies()
        self.setup_routes()
        
        # Initialize templates
        try:
            templates_path = pkg_resources.resource_filename("pr_review_bot", "templates")
            self.templates = Jinja2Templates(directory=templates_path)
        except (pkg_resources.DistributionNotFound, FileNotFoundError):
            # Fallback to local templates
            self.templates = None
    
    def setup_dependencies(self):
        """
        Set up dependencies for the application.
        """
        # Get GitHub token
        github_token = os.environ.get("GITHUB_TOKEN")
        if not github_token:
            logger.error("GITHUB_TOKEN environment variable is required")
            raise ValueError("GITHUB_TOKEN environment variable is required")
        
        # Get webhook secret
        webhook_secret = os.environ.get("WEBHOOK_SECRET", "")
        
        # Create GitHub client
        self.github_client = GitHubClient(github_token)
        
        # Create PR reviewer
        self.pr_reviewer = PRReviewer(github_token)
        
        # Create webhook handler
        self.webhook_handler = WebhookHandler(
            github_client=self.github_client,
            pr_reviewer=self.pr_reviewer,
            webhook_secret=webhook_secret
        )
    
    def setup_routes(self):
        """
        Set up routes for the application.
        """
        @self.app.get("/", response_class=HTMLResponse)
        async def root(request: Request):
            """
            Root endpoint for the PR Review Bot.
            """
            if self.templates:
                return self.templates.TemplateResponse("index.html", {"request": request})
            else:
                # Fallback to simple HTML
                html_content = """
                <!DOCTYPE html>
                <html>
                <head>
                    <title>PR Review Bot</title>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; line-height: 1.6; }
                        .container { max-width: 800px; margin: 0 auto; }
                        h1 { color: #333; }
                        .card { background: #f9f9f9; border-radius: 5px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                        .footer { margin-top: 30px; font-size: 0.8em; color: #666; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>PR Review Bot</h1>
                        <div class="card">
                            <h2>Status: Running</h2>
                            <p>The PR Review Bot is currently running and monitoring repositories for new branches and pull requests.</p>
                            <p>Check the <a href="/status">status page</a> for more information.</p>
                        </div>
                        <div class="card">
                            <h2>API Endpoints</h2>
                            <ul>
                                <li><a href="/health">Health Check</a></li>
                                <li><a href="/api/status">Status Report</a></li>
                                <li><a href="/api/merges">Recent Merges</a></li>
                                <li><a href="/api/projects">Project Stats</a></li>
                            </ul>
                        </div>
                        <div class="footer">
                            <p>PR Review Bot - Powered by GitHub</p>
                        </div>
                    </div>
                </body>
                </html>
                """
                return HTMLResponse(content=html_content)
        
        @self.app.get("/status", response_class=HTMLResponse)
        async def status_page(request: Request):
            """
            Status page for the PR Review Bot.
            """
            if self.templates:
                return self.templates.TemplateResponse("status.html", {"request": request})
            else:
                # Fallback to simple HTML with JavaScript to fetch status
                html_content = """
                <!DOCTYPE html>
                <html>
                <head>
                    <title>PR Review Bot - Status</title>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; line-height: 1.6; }
                        .container { max-width: 800px; margin: 0 auto; }
                        h1, h2, h3 { color: #333; }
                        .card { background: #f9f9f9; border-radius: 5px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                        .footer { margin-top: 30px; font-size: 0.8em; color: #666; }
                        #status-report { white-space: pre-wrap; }
                        .loading { color: #666; font-style: italic; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>PR Review Bot - Status</h1>
                        <div class="card">
                            <h2>Status Report</h2>
                            <div id="status-report" class="loading">Loading status report...</div>
                        </div>
                        <div class="card">
                            <h2>Recent Merges</h2>
                            <div id="recent-merges" class="loading">Loading recent merges...</div>
                        </div>
                        <div class="card">
                            <h2>Project Implementation Stats</h2>
                            <div id="project-stats" class="loading">Loading project stats...</div>
                        </div>
                        <div class="footer">
                            <p>PR Review Bot - Powered by GitHub</p>
                        </div>
                    </div>
                    
                    <script>
                        // Fetch status report
                        fetch('/api/status')
                            .then(response => response.json())
                            .then(data => {
                                if (data.error) {
                                    document.getElementById('status-report').innerHTML = `<p>Error: ${data.error}</p>`;
                                } else {
                                    document.getElementById('status-report').innerHTML = data.report;
                                }
                            })
                            .catch(error => {
                                document.getElementById('status-report').innerHTML = `<p>Error fetching status: ${error}</p>`;
                            });
                        
                        // Fetch recent merges
                        fetch('/api/merges')
                            .then(response => response.json())
                            .then(data => {
                                if (data.error) {
                                    document.getElementById('recent-merges').innerHTML = `<p>Error: ${data.error}</p>`;
                                } else if (data.merges && data.merges.length > 0) {
                                    let html = '<ul>';
                                    data.merges.slice(0, 10).forEach((merge, index) => {
                                        html += `<li><a href="${merge.pr_url}" target="_blank">${merge.pr_title}</a> - ${merge.repo_name}</li>`;
                                    });
                                    html += '</ul>';
                                    document.getElementById('recent-merges').innerHTML = html;
                                } else {
                                    document.getElementById('recent-merges').innerHTML = '<p>No recent merges found.</p>';
                                }
                            })
                            .catch(error => {
                                document.getElementById('recent-merges').innerHTML = `<p>Error fetching merges: ${error}</p>`;
                            });
                        
                        // Fetch project stats
                        fetch('/api/projects')
                            .then(response => response.json())
                            .then(data => {
                                if (data.error) {
                                    document.getElementById('project-stats').innerHTML = `<p>Error: ${data.error}</p>`;
                                } else if (data.projects && Object.keys(data.projects).length > 0) {
                                    let html = '<ul>';
                                    Object.entries(data.projects).slice(0, 10).forEach(([project, count]) => {
                                        html += `<li>${project}: ${count} implementations</li>`;
                                    });
                                    html += '</ul>';
                                    document.getElementById('project-stats').innerHTML = html;
                                } else {
                                    document.getElementById('project-stats').innerHTML = '<p>No project stats available.</p>';
                                }
                            })
                            .catch(error => {
                                document.getElementById('project-stats').innerHTML = `<p>Error fetching project stats: ${error}</p>`;
                            });
                    </script>
                </body>
                </html>
                """
                return HTMLResponse(content=html_content)
        
        @self.app.post("/webhook")
        async def webhook(request: Request):
            """
            GitHub webhook endpoint.
            """
            return await self.webhook_handler.handle_webhook(request)
        
        @self.app.get("/health")
        async def health():
            """
            Health check endpoint.
            """
            return {"status": "healthy"}

# Create the application
app_instance = PRReviewBotApp()
app = app_instance.app
