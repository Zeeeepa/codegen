"""
WSL2 Deployment Utilities

This module provides utilities for deploying the WSL2 server,
with support for Docker and ctrlplane.
"""

import json
import logging
import os
import shutil
import subprocess
import tempfile
import time
from typing import Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


class WSLDeploymentError(Exception):
    """Exception raised for errors in the WSL deployment."""

    def __init__(self, message: str, command: Optional[str] = None, output: Optional[str] = None):
        """
        Initialize a new WSLDeploymentError.

        Args:
            message: Error message
            command: Optional command that failed
            output: Optional command output
        """
        self.message = message
        self.command = command
        self.output = output
        super().__init__(self.message)


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
        log_level: str = "info",
        server_dir: Optional[str] = None,
        timeout: int = 60,
    ):
        """
        Initialize a new WSLDeployment.

        Args:
            wsl_distro: WSL distribution to use
            port: Port to expose the server on
            api_key: Optional API key for authentication
            use_docker: Whether to use Docker for deployment
            use_ctrlplane: Whether to use ctrlplane for orchestration
            log_level: Log level for the server (debug, info, warning, error)
            server_dir: Optional directory containing the server code
            timeout: Command execution timeout in seconds
        """
        self.wsl_distro = wsl_distro
        self.port = port
        self.api_key = api_key
        self.use_docker = use_docker
        self.use_ctrlplane = use_ctrlplane
        self.log_level = log_level.lower()
        self.server_dir = server_dir
        self.timeout = timeout

        # Set environment variables
        self.env = os.environ.copy()
        if self.api_key:
            self.env["CODEGEN_API_KEY"] = self.api_key

    def _run_command(
        self,
        command: Union[str, List[str]],
        check: bool = True,
        capture_output: bool = True,
        timeout: Optional[int] = None,
        env: Optional[Dict[str, str]] = None,
        shell: bool = False,
    ) -> Tuple[int, str, str]:
        """
        Run a command and return the result.

        Args:
            command: Command to run
            check: Whether to raise an exception on non-zero exit code
            capture_output: Whether to capture stdout and stderr
            timeout: Command execution timeout in seconds
            env: Environment variables for the command
            shell: Whether to run the command in a shell

        Returns:
            Tuple of (return_code, stdout, stderr)

        Raises:
            WSLDeploymentError: If the command fails and check is True
        """
        timeout = timeout or self.timeout
        env = env or self.env

        try:
            logger.debug(f"Running command: {command}")

            if capture_output:
                result = subprocess.run(
                    command,
                    check=False,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=env,
                    timeout=timeout,
                    shell=shell,
                )
                stdout = result.stdout
                stderr = result.stderr
            else:
                result = subprocess.run(
                    command,
                    check=False,
                    env=env,
                    timeout=timeout,
                    shell=shell,
                )
                stdout = ""
                stderr = ""

            if check and result.returncode != 0:
                cmd_str = command if isinstance(command, str) else " ".join(command)
                raise WSLDeploymentError(
                    f"Command failed with exit code {result.returncode}",
                    command=cmd_str,
                    output=f"STDOUT:\n{stdout}\n\nSTDERR:\n{stderr}",
                )

            return result.returncode, stdout, stderr

        except subprocess.TimeoutExpired as e:
            cmd_str = command if isinstance(command, str) else " ".join(command)
            raise WSLDeploymentError(
                f"Command timed out after {timeout} seconds",
                command=cmd_str,
                output=str(e),
            )

        except Exception as e:
            cmd_str = command if isinstance(command, str) else " ".join(command)
            raise WSLDeploymentError(
                f"Error running command: {str(e)}",
                command=cmd_str,
            )

    def _run_wsl_command(
        self,
        command: Union[str, List[str]],
        check: bool = True,
        capture_output: bool = True,
        timeout: Optional[int] = None,
    ) -> Tuple[int, str, str]:
        """
        Run a command in the WSL distribution.

        Args:
            command: Command to run in WSL
            check: Whether to raise an exception on non-zero exit code
            capture_output: Whether to capture stdout and stderr
            timeout: Command execution timeout in seconds

        Returns:
            Tuple of (return_code, stdout, stderr)

        Raises:
            WSLDeploymentError: If the command fails and check is True
        """
        if isinstance(command, list):
            command = " ".join(command)

        wsl_command = ["wsl", "-d", self.wsl_distro, "--", "bash", "-c", command]
        return self._run_command(wsl_command, check, capture_output, timeout)

    def check_wsl_installed(self) -> bool:
        """
        Check if WSL is installed.

        Returns:
            True if WSL is installed, False otherwise
        """
        try:
            returncode, stdout, stderr = self._run_command(
                ["wsl", "--status"],
                check=False,
            )
            return returncode == 0
        except Exception:
            return False

    def check_distro_installed(self) -> bool:
        """
        Check if the specified WSL distribution is installed.

        Returns:
            True if the distribution is installed, False otherwise
        """
        try:
            returncode, stdout, stderr = self._run_command(
                ["wsl", "-l", "-v"],
                check=False,
            )
            return self.wsl_distro in stdout
        except Exception:
            return False

    def install_dependencies(self) -> bool:
        """
        Install dependencies in the WSL distribution.

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("Updating package lists...")
            self._run_wsl_command("sudo apt update")

            logger.info("Installing Python and dependencies...")
            self._run_wsl_command("sudo apt install -y python3 python3-pip python3-venv git")

            # Install Docker if needed
            if self.use_docker:
                logger.info("Installing Docker...")
                self._run_wsl_command("sudo apt install -y docker.io docker-compose")

                logger.info("Starting Docker service...")
                self._run_wsl_command("sudo systemctl start docker || true")

                logger.info("Enabling Docker service...")
                self._run_wsl_command("sudo systemctl enable docker || true")

                # Add current user to docker group
                logger.info("Adding current user to docker group...")
                self._run_wsl_command("sudo usermod -aG docker $USER || true")

            # Install ctrlplane if needed
            if self.use_ctrlplane:
                logger.info("Installing ctrlplane...")
                self._run_wsl_command("pip3 install ctrlplane")

            # Install additional Python packages
            logger.info("Installing Python packages...")
            self._run_wsl_command("pip3 install fastapi uvicorn requests pydantic")

            logger.info("Dependencies installed successfully")
            return True

        except WSLDeploymentError as e:
            logger.error(f"Error installing dependencies: {e.message}")
            if e.output:
                logger.error(f"Command output: {e.output}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error installing dependencies: {str(e)}")
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
            # If server_dir is not provided, use the one from initialization or the current directory
            server_dir = server_dir or self.server_dir or os.path.dirname(os.path.abspath(__file__))
            logger.info(f"Deploying server from {server_dir}")

            # Create a temporary directory for deployment
            with tempfile.TemporaryDirectory() as temp_dir:
                # Copy server files to temporary directory
                logger.info(f"Copying server files to temporary directory {temp_dir}")
                if os.path.isdir(server_dir):
                    shutil.copytree(
                        server_dir, os.path.join(temp_dir, "server"), dirs_exist_ok=True
                    )
                else:
                    raise WSLDeploymentError(f"Server directory not found: {server_dir}")

                # Create deployment directory in WSL
                logger.info("Creating deployment directory in WSL")
                self._run_wsl_command("mkdir -p /home/codegen-server")

                # Copy files to WSL
                logger.info("Copying files to WSL")
                self._run_command(
                    [
                        "wsl",
                        "-d",
                        self.wsl_distro,
                        "--",
                        "cp",
                        "-r",
                        f"{temp_dir}/server/.",
                        "/home/codegen-server/",
                    ]
                )

                # Deploy based on the selected method
                if self.use_docker:
                    logger.info("Deploying with Docker")
                    return self._deploy_with_docker()
                elif self.use_ctrlplane:
                    logger.info("Deploying with ctrlplane")
                    return self._deploy_with_ctrlplane()
                else:
                    logger.info("Deploying directly")
                    return self._deploy_direct()

        except WSLDeploymentError as e:
            logger.error(f"Error deploying server: {e.message}")
            if e.output:
                logger.error(f"Command output: {e.output}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deploying server: {str(e)}")
            return False

    def _create_dockerfile(self) -> bool:
        """
        Create a Dockerfile for the server.

        Returns:
            True if successful, False otherwise
        """
        try:
            dockerfile_content = """
FROM python:3.9-slim

WORKDIR /app

COPY . /app/

RUN pip install --no-cache-dir -e .

EXPOSE 8000

CMD ["python", "-m", "codegen_on_oss.analysis.wsl_server"]
"""
            logger.info("Creating Dockerfile")
            self._run_wsl_command(f'echo "{dockerfile_content}" > /home/codegen-server/Dockerfile')

            return True
        except Exception as e:
            logger.error(f"Error creating Dockerfile: {str(e)}")
            return False

    def _create_docker_compose(self) -> bool:
        """
        Create a docker-compose.yml file for the server.

        Returns:
            True if successful, False otherwise
        """
        try:
            compose_content = f"""
version: '3'

services:
  wsl-server:
    build: .
    ports:
      - "{self.port}:8000"
    environment:
      - CODEGEN_API_KEY={self.api_key or ""}
    volumes:
      - .:/app
    restart: unless-stopped
"""
            logger.info("Creating docker-compose.yml")
            self._run_wsl_command(
                f'echo "{compose_content}" > /home/codegen-server/docker-compose.yml'
            )

            return True
        except Exception as e:
            logger.error(f"Error creating docker-compose.yml: {str(e)}")
            return False

    def _deploy_with_docker(self) -> bool:
        """
        Deploy the server using Docker.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create Dockerfile and docker-compose.yml
            if not self._create_dockerfile() or not self._create_docker_compose():
                return False

            # Build Docker image
            logger.info("Building Docker image")
            self._run_wsl_command(
                "cd /home/codegen-server && docker-compose build",
                timeout=300,  # Allow more time for building
            )

            # Start Docker container
            logger.info("Starting Docker container")
            self._run_wsl_command(
                "cd /home/codegen-server && docker-compose up -d",
            )

            # Verify the container is running
            logger.info("Verifying container is running")
            returncode, stdout, stderr = self._run_wsl_command(
                "docker ps | grep wsl-server",
                check=False,
            )

            if returncode != 0:
                logger.warning("Container not found in docker ps output, checking logs")
                returncode, stdout, stderr = self._run_wsl_command(
                    "cd /home/codegen-server && docker-compose logs",
                    check=False,
                )
                logger.info(f"Docker logs: {stdout}")

                if "Error" in stdout or "error" in stdout:
                    raise WSLDeploymentError(
                        "Docker container failed to start",
                        output=stdout,
                    )

            logger.info(f"Server deployed using Docker on port {self.port}")
            return True

        except WSLDeploymentError as e:
            logger.error(f"Error deploying with Docker: {e.message}")
            if e.output:
                logger.error(f"Command output: {e.output}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deploying with Docker: {str(e)}")
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
                        "command": (
                            "cd /home/codegen-server && "
                            f"python3 -m codegen_on_oss.analysis.wsl_server "
                            f"--log-level {self.log_level}"
                        ),
                        "environment": {
                            "CODEGEN_API_KEY": self.api_key or "",
                        },
                        "ports": [
                            {
                                "internal": 8000,
                                "external": self.port,
                            }
                        ],
                    }
                ],
            }

            # Write configuration to file
            config_path = "/home/codegen-server/ctrlplane.json"
            logger.info(f"Creating ctrlplane configuration at {config_path}")
            self._run_wsl_command(f"echo '{json.dumps(config, indent=2)}' > {config_path}")

            # Deploy using ctrlplane
            logger.info("Deploying with ctrlplane")
            self._run_wsl_command(f"cd /home/codegen-server && ctrlplane deploy -f {config_path}")

            # Verify the service is running
            logger.info("Verifying service is running")
            time.sleep(2)  # Give it a moment to start
            returncode, stdout, stderr = self._run_wsl_command(
                "ctrlplane list | grep codegen-wsl-server",
                check=False,
            )

            if returncode != 0:
                logger.warning("Service not found in ctrlplane list output")
                raise WSLDeploymentError(
                    "ctrlplane service failed to start",
                    output=stdout,
                )

            logger.info(f"Server deployed using ctrlplane on port {self.port}")
            return True

        except WSLDeploymentError as e:
            logger.error(f"Error deploying with ctrlplane: {e.message}")
            if e.output:
                logger.error(f"Command output: {e.output}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deploying with ctrlplane: {str(e)}")
            return False

    def _deploy_direct(self) -> bool:
        """
        Deploy the server directly.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create virtual environment
            logger.info("Creating virtual environment")
            self._run_wsl_command("cd /home/codegen-server && python3 -m venv venv")

            # Install dependencies
            logger.info("Installing dependencies")
            self._run_wsl_command(
                "cd /home/codegen-server && source venv/bin/activate && pip install -e .",
                timeout=300,  # Allow more time for installation
            )

            # Create a systemd service file
            service_content = f"""
[Unit]
Description=Codegen WSL2 Server
After=network.target

[Service]
User=$USER
WorkingDirectory=/home/codegen-server
Environment="CODEGEN_API_KEY={self.api_key or ""}"
ExecStart=/home/codegen-server/venv/bin/python -m codegen_on_oss.analysis.wsl_server \
--log-level {self.log_level}
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
"""
            logger.info("Creating systemd service file")
            self._run_wsl_command(f'echo "{service_content}" > /tmp/codegen-wsl-server.service')

            # Install the service file
            logger.info("Installing systemd service")
            self._run_wsl_command("sudo mv /tmp/codegen-wsl-server.service /etc/systemd/system/")

            # Reload systemd
            logger.info("Reloading systemd")
            self._run_wsl_command("sudo systemctl daemon-reload")

            # Enable and start the service
            logger.info("Enabling and starting service")
            self._run_wsl_command("sudo systemctl enable codegen-wsl-server")
            self._run_wsl_command("sudo systemctl start codegen-wsl-server")

            # Check service status
            logger.info("Checking service status")
            returncode, stdout, stderr = self._run_wsl_command(
                "systemctl is-active codegen-wsl-server",
                check=False,
            )

            if returncode != 0:
                logger.warning("Service is not active, checking logs")
                returncode, stdout, stderr = self._run_wsl_command(
                    "journalctl -u codegen-wsl-server -n 50",
                    check=False,
                )
                logger.info(f"Service logs: {stdout}")

                # Try starting the server directly as a fallback
                logger.info("Attempting to start server directly as fallback")
                self._run_wsl_command(
                    "cd /home/codegen-server && source venv/bin/activate && "
                    f"nohup python -m codegen_on_oss.analysis.wsl_server "
                    f"--log-level {self.log_level} "
                    f"> /home/codegen-server/server.log 2>&1 &",
                    check=False,
                )

            logger.info(f"Server deployed directly on port {self.port}")
            return True

        except WSLDeploymentError as e:
            logger.error(f"Error deploying directly: {e.message}")
            if e.output:
                logger.error(f"Command output: {e.output}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deploying directly: {str(e)}")
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
                logger.info("Stopping Docker container")
                self._run_wsl_command(
                    "cd /home/codegen-server && docker-compose down",
                    check=False,
                )
            elif self.use_ctrlplane:
                # Stop ctrlplane service
                logger.info("Stopping ctrlplane service")
                self._run_wsl_command(
                    "ctrlplane stop codegen-wsl-server",
                    check=False,
                )
            else:
                # Stop systemd service
                logger.info("Stopping systemd service")
                self._run_wsl_command(
                    "sudo systemctl stop codegen-wsl-server",
                    check=False,
                )

                # Also kill any direct processes
                logger.info("Killing any direct processes")
                self._run_wsl_command(
                    "pkill -f codegen_on_oss.analysis.wsl_server",
                    check=False,
                )

            logger.info("Server stopped")
            return True

        except WSLDeploymentError as e:
            logger.error(f"Error stopping server: {e.message}")
            if e.output:
                logger.error(f"Command output: {e.output}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error stopping server: {str(e)}")
            return False

    def get_server_status(self) -> Dict[str, str]:
        """
        Get the status of the WSL2 server.

        Returns:
            Dictionary with status information
        """
        status = {
            "deployment_type": "docker"
            if self.use_docker
            else "ctrlplane"
            if self.use_ctrlplane
            else "direct",
            "port": str(self.port),
            "wsl_distro": self.wsl_distro,
            "status": "unknown",
            "uptime": "unknown",
            "logs": "",
        }

        try:
            if self.use_docker:
                # Check Docker container status
                returncode, stdout, stderr = self._run_wsl_command(
                    "docker ps --filter name=wsl-server --format '{{.Status}}'",
                    check=False,
                )

                if stdout.strip():
                    status["status"] = "running"
                    status["uptime"] = stdout.strip()
                else:
                    status["status"] = "stopped"

                # Get logs
                returncode, stdout, stderr = self._run_wsl_command(
                    "cd /home/codegen-server && docker-compose logs --tail=20",
                    check=False,
                )
                status["logs"] = stdout

            elif self.use_ctrlplane:
                # Check ctrlplane service status
                returncode, stdout, stderr = self._run_wsl_command(
                    "ctrlplane list | grep codegen-wsl-server",
                    check=False,
                )

                if returncode == 0:
                    status["status"] = "running"
                    status["uptime"] = "N/A"
                else:
                    status["status"] = "stopped"

                # Get logs
                returncode, stdout, stderr = self._run_wsl_command(
                    "ctrlplane logs codegen-wsl-server --tail=20",
                    check=False,
                )
                status["logs"] = stdout

            else:
                # Check systemd service status
                returncode, stdout, stderr = self._run_wsl_command(
                    "systemctl is-active codegen-wsl-server",
                    check=False,
                )

                if returncode == 0:
                    status["status"] = "running"

                    # Get uptime
                    returncode, stdout, stderr = self._run_wsl_command(
                        "systemctl show codegen-wsl-server "
                        "--property=ActiveState,ActiveEnterTimestamp",
                        check=False,
                    )
                    status["uptime"] = stdout.strip()
                else:
                    status["status"] = "stopped"

                # Get logs
                returncode, stdout, stderr = self._run_wsl_command(
                    "journalctl -u codegen-wsl-server -n 20",
                    check=False,
                )
                status["logs"] = stdout

            return status

        except Exception as e:
            logger.error(f"Error getting server status: {str(e)}")
            status["status"] = "error"
            status["logs"] = str(e)
            return status
