"""
WSL2 Integration Module

This module provides integration with external tools:
- ctrlplane for deployment orchestration
- weave for visualization
- probot for GitHub automation
- pkg.pr.new for continuous preview releases
- tldr for PR summarization
"""

import json
import logging
import os
import subprocess
import tempfile
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class CtrlplaneIntegration:
    """
    Integration with ctrlplane for deployment orchestration.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize a new CtrlplaneIntegration.

        Args:
            api_key: Optional API key for authentication
        """
        self.api_key = api_key or os.getenv("CTRLPLANE_API_KEY", "")

    def deploy_service(
        self,
        name: str,
        command: str,
        environment: Optional[Dict[str, str]] = None,
        ports: Optional[List[Dict[str, int]]] = None,
    ) -> bool:
        """
        Deploy a service using ctrlplane.

        Args:
            name: Name of the service
            command: Command to run
            environment: Environment variables
            ports: Ports to expose

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create ctrlplane configuration
            config = {
                "name": name,
                "description": "Deployed by Codegen WSL2 Integration",
                "version": "1.0.0",
                "services": [
                    {
                        "name": name,
                        "command": command,
                        "environment": environment or {},
                        "ports": ports or [],
                    }
                ],
            }

            # Write configuration to file
            with tempfile.NamedTemporaryFile(
                suffix=".json", mode="w", delete=False
            ) as f:
                json.dump(config, f, indent=2)
                config_path = f.name

            # Deploy using ctrlplane
            env = os.environ.copy()
            if self.api_key:
                env["CTRLPLANE_API_KEY"] = self.api_key

            subprocess.run(
                ["ctrlplane", "deploy", "-f", config_path],
                check=True,
                env=env,
            )

            # Clean up
            os.unlink(config_path)

            logger.info(f"Service '{name}' deployed successfully")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Error deploying service: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error deploying service: {str(e)}")
            return False

    def stop_service(self, name: str) -> bool:
        """
        Stop a service using ctrlplane.

        Args:
            name: Name of the service

        Returns:
            True if successful, False otherwise
        """
        try:
            # Stop using ctrlplane
            env = os.environ.copy()
            if self.api_key:
                env["CTRLPLANE_API_KEY"] = self.api_key

            subprocess.run(
                ["ctrlplane", "stop", name],
                check=True,
                env=env,
            )

            logger.info(f"Service '{name}' stopped successfully")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Error stopping service: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error stopping service: {str(e)}")
            return False


class WeaveIntegration:
    """
    Integration with weave for visualization.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize a new WeaveIntegration.

        Args:
            api_key: Optional API key for authentication
        """
        self.api_key = api_key or os.getenv("WEAVE_API_KEY", "")

    def create_visualization(
        self,
        data: Dict[str, Any],
        title: str,
        description: Optional[str] = None,
    ) -> Optional[str]:
        """
        Create a visualization using weave.

        Args:
            data: Data to visualize
            title: Title of the visualization
            description: Optional description

        Returns:
            URL of the visualization if successful, None otherwise
        """
        try:
            # Check if weave is installed
            subprocess.run(
                ["weave", "--version"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # Create temporary file for data
            with tempfile.NamedTemporaryFile(
                suffix=".json", mode="w", delete=False
            ) as f:
                json.dump(data, f, indent=2)
                data_path = f.name

            # Create visualization
            env = os.environ.copy()
            if self.api_key:
                env["WEAVE_API_KEY"] = self.api_key

            result = subprocess.run(
                [
                    "weave",
                    "publish",
                    "--title",
                    title,
                    "--description",
                    description or "",
                    data_path,
                ],
                check=True,
                env=env,
                stdout=subprocess.PIPE,
                text=True,
            )

            # Clean up
            os.unlink(data_path)

            # Extract URL from output
            for line in result.stdout.splitlines():
                if "https://" in line:
                    url = line.strip()
                    logger.info(f"Visualization created: {url}")
                    return url

            logger.warning("Visualization created, but URL not found in output")
            return None

        except subprocess.CalledProcessError as e:
            logger.error(f"Error creating visualization: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error creating visualization: {str(e)}")
            return None


class ProbotIntegration:
    """
    Integration with probot for GitHub automation.
    """

    def __init__(self, github_token: Optional[str] = None):
        """
        Initialize a new ProbotIntegration.

        Args:
            github_token: Optional GitHub token for authentication
        """
        self.github_token = github_token or os.getenv("GITHUB_TOKEN", "")

    def register_webhook(
        self,
        repo: str,
        events: List[str],
        webhook_url: str,
        secret: Optional[str] = None,
    ) -> bool:
        """
        Register a webhook for a repository.

        Args:
            repo: Repository in the format "owner/repo"
            events: List of events to listen for
            webhook_url: URL to send webhook events to
            secret: Optional secret for webhook verification

        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if probot is installed
            subprocess.run(
                ["probot", "--version"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # Create webhook configuration
            config = {
                "repo": repo,
                "events": events,
                "url": webhook_url,
            }

            if secret:
                config["secret"] = secret

            # Write configuration to file
            with tempfile.NamedTemporaryFile(
                suffix=".json", mode="w", delete=False
            ) as f:
                json.dump(config, f, indent=2)
                config_path = f.name

            # Register webhook
            env = os.environ.copy()
            if self.github_token:
                env["GITHUB_TOKEN"] = self.github_token

            subprocess.run(
                ["probot", "webhook", "create", "-f", config_path],
                check=True,
                env=env,
            )

            # Clean up
            os.unlink(config_path)

            logger.info(f"Webhook registered for {repo}")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Error registering webhook: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error registering webhook: {str(e)}")
            return False


class PkgPrNewIntegration:
    """
    Integration with pkg.pr.new for continuous preview releases.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize a new PkgPrNewIntegration.

        Args:
            api_key: Optional API key for authentication
        """
        self.api_key = api_key or os.getenv("PKG_PR_NEW_API_KEY", "")

    def create_preview_release(
        self,
        repo: str,
        branch: str,
        version: str,
        package_name: Optional[str] = None,
    ) -> Optional[str]:
        """
        Create a preview release.

        Args:
            repo: Repository in the format "owner/repo"
            branch: Branch to create preview release from
            version: Version of the preview release
            package_name: Optional package name

        Returns:
            URL of the preview release if successful, None otherwise
        """
        try:
            # Check if pkg.pr.new is installed
            subprocess.run(
                ["pkg-pr-new", "--version"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # Create preview release
            env = os.environ.copy()
            if self.api_key:
                env["PKG_PR_NEW_API_KEY"] = self.api_key

            cmd = [
                "pkg-pr-new",
                "create",
                "--repo",
                repo,
                "--branch",
                branch,
                "--version",
                version,
            ]

            if package_name:
                cmd.extend(["--package", package_name])

            result = subprocess.run(
                cmd,
                check=True,
                env=env,
                stdout=subprocess.PIPE,
                text=True,
            )

            # Extract URL from output
            for line in result.stdout.splitlines():
                if "https://" in line:
                    url = line.strip()
                    logger.info(f"Preview release created: {url}")
                    return url

            logger.warning("Preview release created, but URL not found in output")
            return None

        except subprocess.CalledProcessError as e:
            logger.error(f"Error creating preview release: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error creating preview release: {str(e)}")
            return None


class TldrIntegration:
    """
    Integration with tldr for PR summarization.
    """

    def __init__(self, github_token: Optional[str] = None):
        """
        Initialize a new TldrIntegration.

        Args:
            github_token: Optional GitHub token for authentication
        """
        self.github_token = github_token or os.getenv("GITHUB_TOKEN", "")

    def summarize_pr(
        self,
        repo: str,
        pr_number: int,
        post_comment: bool = False,
    ) -> Optional[str]:
        """
        Summarize a pull request.

        Args:
            repo: Repository in the format "owner/repo"
            pr_number: PR number to summarize
            post_comment: Whether to post the summary as a comment

        Returns:
            Summary if successful, None otherwise
        """
        try:
            # Check if tldr is installed
            subprocess.run(
                ["tldr", "--version"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # Summarize PR
            env = os.environ.copy()
            if self.github_token:
                env["GITHUB_TOKEN"] = self.github_token

            cmd = [
                "tldr",
                "summarize",
                "--repo",
                repo,
                "--pr",
                str(pr_number),
            ]

            if post_comment:
                cmd.append("--post-comment")

            result = subprocess.run(
                cmd,
                check=True,
                env=env,
                stdout=subprocess.PIPE,
                text=True,
            )

            summary = result.stdout.strip()
            logger.info(f"PR summarized: {repo}#{pr_number}")
            return summary

        except subprocess.CalledProcessError as e:
            logger.error(f"Error summarizing PR: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error summarizing PR: {str(e)}")
            return None
