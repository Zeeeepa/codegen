"""
WSL Deployment Module

This module provides functionality for deploying and managing WSL servers.
"""

import logging
import os
import subprocess
from typing import Optional

logger = logging.getLogger(__name__)


class WSLDeployment:
    """
    Handles deployment of servers in WSL environments.
    
    This class provides methods for checking WSL installation,
    installing dependencies, and deploying/stopping servers.
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
            port: Port to run the server on
            api_key: API key for authentication
            use_docker: Whether to use Docker for deployment
            use_ctrlplane: Whether to use ctrlplane for deployment orchestration
        """
        self.wsl_distro = wsl_distro
        self.port = port
        self.api_key = api_key
        self.use_docker = use_docker
        self.use_ctrlplane = use_ctrlplane
    
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
                ["wsl", "-l", "-q"],
                capture_output=True,
                text=True,
                check=False,
            )
            return self.wsl_distro.lower() in result.stdout.lower()
        except Exception:
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
                    "wsl", "-d", self.wsl_distro, "--", "sudo", "apt", "install",
                    "-y", "python3", "python3-pip", "python3-venv",
                ],
                check=True,
            )
            
            # Install Docker if needed
            if self.use_docker:
                subprocess.run(
                    [
                        "wsl", "-d", self.wsl_distro, "--", "sudo", "apt", "install",
                        "-y", "docker.io", "docker-compose",
                    ],
                    check=True,
                )
            
            return True
        except subprocess.CalledProcessError:
            return False
    
    def deploy_server(self) -> bool:
        """
        Deploy the server in the WSL distribution.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create a deployment script
            script_content = self._generate_deployment_script()
            
            # Write the script to a temporary file
            script_path = os.path.join(os.getcwd(), "deploy_wsl_server.sh")
            with open(script_path, "w") as f:
                f.write(script_content)
            
            # Make the script executable
            os.chmod(script_path, 0o755)
            
            # Run the deployment script
            subprocess.run(
                ["wsl", "-d", self.wsl_distro, "--", script_path],
                check=True,
            )
            
            # Clean up
            os.remove(script_path)
            
            return True
        except Exception as e:
            logger.error(f"Error deploying server: {str(e)}")
            return False
    
    def stop_server(self) -> bool:
        """
        Stop the server in the WSL distribution.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create a stop script
            script_content = self._generate_stop_script()
            
            # Write the script to a temporary file
            script_path = os.path.join(os.getcwd(), "stop_wsl_server.sh")
            with open(script_path, "w") as f:
                f.write(script_content)
            
            # Make the script executable
            os.chmod(script_path, 0o755)
            
            # Run the stop script
            subprocess.run(
                ["wsl", "-d", self.wsl_distro, "--", script_path],
                check=True,
            )
            
            # Clean up
            os.remove(script_path)
            
            return True
        except Exception as e:
            logger.error(f"Error stopping server: {str(e)}")
            return False
    
    def _generate_deployment_script(self) -> str:
        """
        Generate a deployment script.
        
        Returns:
            The deployment script content
        """
        return f"""#!/bin/bash
set -e

echo "Deploying server..."

# Create a virtual environment
python3 -m venv ~/wsl_server_venv

# Activate the virtual environment
source ~/wsl_server_venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install uvicorn fastapi

# Set environment variables
export PORT={self.port}
{"export CODEGEN_API_KEY=" + self.api_key if self.api_key else ""}

# Start the server
{"docker-compose up -d" if self.use_docker else "uvicorn server:app --host 0.0.0.0 --port $PORT &"}

echo "Server deployed successfully!"
"""
    
    def _generate_stop_script(self) -> str:
        """
        Generate a stop script.
        
        Returns:
            The stop script content
        """
        return f"""#!/bin/bash
set -e

echo "Stopping server..."

# Find and kill the server process
{"docker-compose down" if self.use_docker else "pkill -f 'uvicorn server:app' || true"}

echo "Server stopped successfully!"
"""

