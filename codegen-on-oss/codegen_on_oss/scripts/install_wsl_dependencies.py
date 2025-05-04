#!/usr/bin/env python3
"""
Script to install dependencies for the WSL2 server.

This script installs the required dependencies for the WSL2 server,
including Python packages and system dependencies.
"""

import argparse
import logging
import subprocess
import sys
from typing import List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def run_command(command: List[str], check: bool = True) -> subprocess.CompletedProcess:
    """
    Run a command and return the result.

    Args:
        command: Command to run
        check: Whether to check the return code

    Returns:
        Completed process
    """
    logger.debug(f"Running command: {' '.join(command)}")
    return subprocess.run(
        command,
        check=check,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def check_wsl_installed() -> bool:
    """
    Check if WSL is installed.

    Returns:
        True if WSL is installed, False otherwise
    """
    try:
        result = run_command(["wsl", "--status"], check=False)
        return result.returncode == 0
    except FileNotFoundError:
        return False


def check_distro_installed(distro: str) -> bool:
    """
    Check if the specified WSL distribution is installed.

    Args:
        distro: WSL distribution to check

    Returns:
        True if the distribution is installed, False otherwise
    """
    try:
        result = run_command(["wsl", "-l", "-v"], check=False)
        return distro in result.stdout
    except FileNotFoundError:
        return False


def install_system_dependencies(distro: str) -> bool:
    """
    Install system dependencies in the WSL distribution.

    Args:
        distro: WSL distribution to install dependencies in

    Returns:
        True if successful, False otherwise
    """
    try:
        # Update package lists
        logger.info("Updating package lists...")
        run_command(
            ["wsl", "-d", distro, "--", "sudo", "apt", "update"],
            check=True,
        )

        # Install Python and pip
        logger.info("Installing Python and pip...")
        run_command(
            [
                "wsl",
                "-d",
                distro,
                "--",
                "sudo",
                "apt",
                "install",
                "-y",
                "python3",
                "python3-pip",
                "python3-venv",
                "git",
                "build-essential",
                "python3-dev",
                "libpq-dev",
            ],
            check=True,
        )

        # Install Docker if needed
        logger.info("Installing Docker...")
        run_command(
            [
                "wsl",
                "-d",
                distro,
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
        logger.info("Starting Docker service...")
        run_command(
            [
                "wsl",
                "-d",
                distro,
                "--",
                "sudo",
                "systemctl",
                "start",
                "docker",
            ],
            check=True,
        )

        # Enable Docker service
        logger.info("Enabling Docker service...")
        run_command(
            [
                "wsl",
                "-d",
                distro,
                "--",
                "sudo",
                "systemctl",
                "enable",
                "docker",
            ],
            check=True,
        )

        # Install psutil
        logger.info("Installing psutil...")
        run_command(
            [
                "wsl",
                "-d",
                distro,
                "--",
                "pip3",
                "install",
                "psutil",
            ],
            check=True,
        )

        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Error installing system dependencies: {str(e)}")
        logger.error(f"Command output: {e.stdout}")
        logger.error(f"Command error: {e.stderr}")
        return False


def install_python_dependencies(distro: str, requirements_file: Optional[str] = None) -> bool:
    """
    Install Python dependencies in the WSL distribution.

    Args:
        distro: WSL distribution to install dependencies in
        requirements_file: Optional path to requirements file

    Returns:
        True if successful, False otherwise
    """
    try:
        # Create virtual environment
        logger.info("Creating virtual environment...")
        run_command(
            [
                "wsl",
                "-d",
                distro,
                "--",
                "python3",
                "-m",
                "venv",
                "/home/codegen-venv",
            ],
            check=True,
        )

        # Install dependencies
        if requirements_file:
            # Copy requirements file to WSL
            logger.info(f"Copying requirements file to WSL: {requirements_file}")
            run_command(
                [
                    "wsl",
                    "-d",
                    distro,
                    "--",
                    "mkdir",
                    "-p",
                    "/home/codegen-temp",
                ],
                check=True,
            )
            with open(requirements_file, "r") as f:
                requirements = f.read()
            run_command(
                [
                    "wsl",
                    "-d",
                    distro,
                    "--",
                    "bash",
                    "-c",
                    f"echo '{requirements}' > /home/codegen-temp/requirements.txt",
                ],
                check=True,
            )

            # Install requirements
            logger.info("Installing requirements...")
            run_command(
                [
                    "wsl",
                    "-d",
                    distro,
                    "--",
                    "bash",
                    "-c",
                    "source /home/codegen-venv/bin/activate && "
                    "pip install -r /home/codegen-temp/requirements.txt",
                ],
                check=True,
            )
        else:
            # Install basic dependencies
            logger.info("Installing basic dependencies...")
            run_command(
                [
                    "wsl",
                    "-d",
                    distro,
                    "--",
                    "bash",
                    "-c",
                    ("source /home/codegen-venv/bin/activate && "
                     "pip install fastapi uvicorn psutil"),
                ],
                check=True,
            )

        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Error installing Python dependencies: {str(e)}")
        logger.error(f"Command output: {e.stdout}")
        logger.error(f"Command error: {e.stderr}")
        return False


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Install dependencies for the WSL2 server")
    parser.add_argument(
        "--distro",
        default="Ubuntu",
        help="WSL distribution to install dependencies in",
    )
    parser.add_argument(
        "--requirements",
        help="Path to requirements file",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Check if WSL is installed
    if not check_wsl_installed():
        logger.error("WSL is not installed. Please install WSL first.")
        sys.exit(1)

    # Check if the specified distribution is installed
    if not check_distro_installed(args.distro):
        logger.error(f"WSL distribution '{args.distro}' is not installed.")
        logger.info("Please install it using: wsl --install -d Ubuntu")
        sys.exit(1)

    # Install system dependencies
    logger.info(f"Installing system dependencies in {args.distro}...")
    if not install_system_dependencies(args.distro):
        logger.error("Failed to install system dependencies.")
        sys.exit(1)

    # Install Python dependencies
    logger.info(f"Installing Python dependencies in {args.distro}...")
    if not install_python_dependencies(args.distro, args.requirements):
        logger.error("Failed to install Python dependencies.")
        sys.exit(1)

    logger.info("Dependencies installed successfully.")


if __name__ == "__main__":
    main()
