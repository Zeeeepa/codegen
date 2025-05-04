"""
WSL2 Deployment Utilities

This module provides utilities for deploying the WSL2 server
for code validation, with integration for ctrlplane and other tools.
"""

import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

logger = logging.getLogger(__name__)


class WSLDeployment:
    """
    Utilities for deploying the WSL2 server.
    """

    def __init__(
        self,
        wsl_distro: str = "Ubuntu",
        port: int = 8000,
        api_key: Optional[str] = None,
        use_docker: bool = False,
        use_ctrlplane: bool = False,
    ):
        """
        Initialize a new WSLDeployment.

        Args:
            wsl_distro: WSL distribution to use
            port: Port to expose the server on
            api_key: Optional API key for authentication
            use_docker: Whether to use Docker for deployment
            use_ctrlplane: Whether to use ctrlplane for orchestration
        """
        self.wsl_distro = wsl_distro
        self.port = port
        self.api_key = api_key
        self.use_docker = use_docker
        self.use_ctrlplane = use_ctrlplane
        
        # Set environment variables
        self.env = os.environ.copy()
        if self.api_key:
            self.env["CODEGEN_API_KEY"] = self.api_key

    def check_wsl_installed(self) -> bool:
        """
        Check if WSL is installed.

        Returns:
            True if WSL is installed, False otherwise
        """
        try:
            result = subprocess.run(
                ["wsl", "--status"],
                capture_output=True,
                text=True,
                check=False,
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def check_distro_installed(self) -> bool:
        """
        Check if the specified WSL distribution is installed.

        Returns:
            True if the distribution is installed, False otherwise
        """
        try:
            result = subprocess.run(
                ["wsl", "-l", "-v"],
                capture_output=True,
                text=True,
                check=False,
            )
            return self.wsl_distro in result.stdout
        except FileNotFoundError:
            return False

    def install_dependencies(self) -> bool:
        """
        Install dependencies in the WSL distribution.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Update package lists
            subprocess.run(
                ["wsl", "-d", self.wsl_distro, "--", "sudo", "apt", "update"],
                check=True,
            )
            
            # Install Python and pip
            subprocess.run(
                [
                    "wsl",
                    "-d",
                    self.wsl_distro,
                    "--",
                    "sudo",
                    "apt",
                    "install",
                    "-y",
                    "python3",
                    "python3-pip",
                    "python3-venv",
                    "git",
                ],
                check=True,
            )
            
            # Install Docker if needed
            if self.use_docker:
                subprocess.run(
                    [
                        "wsl",
                        "-d",
                        self.wsl_distro,
                        "--",
                        "sudo",
                        "apt",
                        "install",
                        "-y",
                        "docker.io",
                        "docker-compose",
                    ],
                    check=True,
                )
                
                # Start Docker service
                subprocess.run(
                    [
                        "wsl",
                        "-d",
                        self.wsl_distro,
                        "--",
                        "sudo",
                        "systemctl",
                        "start",
                        "docker",
                    ],
                    check=True,
                )
                
                # Enable Docker service
                subprocess.run(
                    [
                        "wsl",
                        "-d",
                        self.wsl_distro,
                        "--",
                        "sudo",
                        "systemctl",
                        "enable",
                        "docker",
                    ],
                    check=True,
                )
            
            # Install ctrlplane if needed
            if self.use_ctrlplane:
                subprocess.run(
                    [
                        "wsl",
                        "-d",
                        self.wsl_distro,
                        "--",
                        "pip3",
                        "install",
                        "ctrlplane",
                    ],
                    check=True,
                )
            
            return True
        
        except subprocess.CalledProcessError as e:
            logger.error(f"Error installing dependencies: {str(e)}")
            return False

    def deploy_server(self, server_dir: Optional[str] = None) -> bool:
        """
        Deploy the WSL2 server.

        Args:
            server_dir: Optional directory containing the server code

        Returns:
            True if successful, False otherwise
        """
        try:
            # If server_dir is not provided, use the current directory
            if not server_dir:
                server_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Create a temporary directory for deployment
            with tempfile.TemporaryDirectory() as temp_dir:
                # Copy server files to temporary directory
                subprocess.run(
                    ["cp", "-r", server_dir, temp_dir],
                    check=True,
                )
                
                # Create deployment directory in WSL
                subprocess.run(
                    [
                        "wsl",
                        "-d",
                        self.wsl_distro,
                        "--",
                        "mkdir",
                        "-p",
                        "/home/codegen-server",
                    ],
                    check=True,
                )
                
                # Copy files to WSL
                subprocess.run(
                    [
                        "wsl",
                        "-d",
                        self.wsl_distro,
                        "--",
                        "cp",
                        "-r",
                        f"{temp_dir}/*",
                        "/home/codegen-server/",
                    ],
                    check=True,
                )
                
                if self.use_docker:
                    # Deploy using Docker
                    return self._deploy_with_docker()
                elif self.use_ctrlplane:
                    # Deploy using ctrlplane
                    return self._deploy_with_ctrlplane()
                else:
                    # Deploy directly
                    return self._deploy_direct()
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error deploying server: {str(e)}")
            return False

    def _deploy_with_docker(self) -> bool:
        """
        Deploy the server using Docker.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Build Docker image
            subprocess.run(
                [
                    "wsl",
                    "-d",
                    self.wsl_distro,
                    "--",
                    "cd",
                    "/home/codegen-server",
                    "&&",
                    "docker-compose",
                    "build",
                ],
                check=True,
                env=self.env,
            )
            
            # Start Docker container
            subprocess.run(
                [
                    "wsl",
                    "-d",
                    self.wsl_distro,
                    "--",
                    "cd",
                    "/home/codegen-server",
                    "&&",
                    "docker-compose",
                    "up",
                    "-d",
                ],
                check=True,
                env=self.env,
            )
            
            logger.info(f"Server deployed using Docker on port {self.port}")
            return True
        
        except subprocess.CalledProcessError as e:
            logger.error(f"Error deploying with Docker: {str(e)}")
            return False

    def _deploy_with_ctrlplane(self) -> bool:
        """
        Deploy the server using ctrlplane.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create ctrlplane configuration
            config = {
                "name": "codegen-wsl-server",
                "description": "Codegen WSL2 Server for Code Validation",
                "version": "1.0.0",
                "services": [
                    {
                        "name": "wsl-server",
                        "command": f"cd /home/codegen-server && python3 -m codegen_on_oss.analysis.wsl_server",
                        "environment": {
                            "CODEGEN_API_KEY": self.api_key or "",
                        },
                        "ports": [
                            {
                                "internal": self.port,
                                "external": self.port,
                            }
                        ],
                    }
                ],
            }
            
            # Write configuration to file
            config_path = "/home/codegen-server/ctrlplane.json"
            subprocess.run(
                [
                    "wsl",
                    "-d",
                    self.wsl_distro,
                    "--",
                    "bash",
                    "-c",
                    f"echo '{json.dumps(config)}' > {config_path}",
                ],
                check=True,
            )
            
            # Deploy using ctrlplane
            subprocess.run(
                [
                    "wsl",
                    "-d",
                    self.wsl_distro,
                    "--",
                    "ctrlplane",
                    "deploy",
                    "-f",
                    config_path,
                ],
                check=True,
                env=self.env,
            )
            
            logger.info(f"Server deployed using ctrlplane on port {self.port}")
            return True
        
        except subprocess.CalledProcessError as e:
            logger.error(f"Error deploying with ctrlplane: {str(e)}")
            return False

    def _deploy_direct(self) -> bool:
        """
        Deploy the server directly.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create virtual environment
            subprocess.run(
                [
                    "wsl",
                    "-d",
                    self.wsl_distro,
                    "--",
                    "cd",
                    "/home/codegen-server",
                    "&&",
                    "python3",
                    "-m",
                    "venv",
                    "venv",
                ],
                check=True,
            )
            
            # Install dependencies
            subprocess.run(
                [
                    "wsl",
                    "-d",
                    self.wsl_distro,
                    "--",
                    "cd",
                    "/home/codegen-server",
                    "&&",
                    "source",
                    "venv/bin/activate",
                    "&&",
                    "pip",
                    "install",
                    "-e",
                    ".",
                ],
                check=True,
            )
            
            # Start server in background
            subprocess.Popen(
                [
                    "wsl",
                    "-d",
                    self.wsl_distro,
                    "--",
                    "cd",
                    "/home/codegen-server",
                    "&&",
                    "source",
                    "venv/bin/activate",
                    "&&",
                    "python",
                    "-m",
                    "codegen_on_oss.analysis.wsl_server",
                ],
                env=self.env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            
            logger.info(f"Server deployed directly on port {self.port}")
            return True
        
        except subprocess.CalledProcessError as e:
            logger.error(f"Error deploying directly: {str(e)}")
            return False

    def stop_server(self) -> bool:
        """
        Stop the WSL2 server.

        Returns:
            True if successful, False otherwise
        """
        try:
            if self.use_docker:
                # Stop Docker container
                subprocess.run(
                    [
                        "wsl",
                        "-d",
                        self.wsl_distro,
                        "--",
                        "cd",
                        "/home/codegen-server",
                        "&&",
                        "docker-compose",
                        "down",
                    ],
                    check=True,
                )
            elif self.use_ctrlplane:
                # Stop ctrlplane service
                subprocess.run(
                    [
                        "wsl",
                        "-d",
                        self.wsl_distro,
                        "--",
                        "ctrlplane",
                        "stop",
                        "codegen-wsl-server",
                    ],
                    check=True,
                )
            else:
                # Stop direct process
                subprocess.run(
                    [
                        "wsl",
                        "-d",
                        self.wsl_distro,
                        "--",
                        "pkill",
                        "-f",
                        "codegen_on_oss.analysis.wsl_server",
                    ],
                    check=True,
                )
            
            logger.info("Server stopped")
            return True
        
        except subprocess.CalledProcessError as e:
            logger.error(f"Error stopping server: {str(e)}")
            return False

