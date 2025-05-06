#!/usr/bin/env python3
"""
Script to run the WSL2 server with improved error handling.

This script provides a command-line interface for running the WSL2 server
with various configuration options and improved error handling.
"""

import argparse
import logging
import os
import sys
import traceback
from typing import Any, Dict, Optional

from codegen_on_oss.analysis.wsl_deployment import WSLDeployment
from codegen_on_oss.analysis.wsl_server import run_server

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("wsl_server.log"),
    ],
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Run the WSL2 server")
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind the server to (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to run the server on (default: 8000)",
    )
    parser.add_argument(
        "--api-key",
        help="API key for authentication",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode",
    )
    parser.add_argument(
        "--deploy",
        action="store_true",
        help="Deploy the server using WSLDeployment",
    )
    parser.add_argument(
        "--distro",
        default="Ubuntu",
        help="WSL distribution to use for deployment (default: Ubuntu)",
    )
    parser.add_argument(
        "--docker",
        action="store_true",
        help="Use Docker for deployment",
    )
    parser.add_argument(
        "--ctrlplane",
        action="store_true",
        help="Use ctrlplane for deployment orchestration",
    )
    parser.add_argument(
        "--stop",
        action="store_true",
        help="Stop the server if it's running",
    )
    return parser.parse_args()


from typing import Protocol


class Deployer(Protocol):
    def check_wsl_installed(self) -> bool: ...
    def check_distro_installed(self) -> bool: ...
    def install_dependencies(self) -> bool: ...
    def deploy_server(self) -> bool: ...


def deploy_server(args: argparse.Namespace, deployer_class: Type[Deployer] = WSLDeployment) -> bool:
    try:
        logger.info("Deploying WSL2 server...")
        deployment = deployer_class(
            wsl_distro=args.distro,
            port=args.port,
            api_key=args.api_key,
            use_docker=args.docker,
            use_ctrlplane=args.ctrlplane,
        )

        if not deployment.check_wsl_installed():
            logger.error("WSL is not installed. Please install WSL first.")
            return False

        if not deployment.check_distro_installed():
            logger.error(f"WSL distribution '{args.distro}' is not installed.")
            logger.info(f"Please install it using: wsl --install -d {args.distro}")
            return False

        logger.info("Installing dependencies...")
        if not deployment.install_dependencies():
            logger.error("Failed to install dependencies.")
            return False

        logger.info("Deploying server...")
        if not deployment.deploy_server():
            logger.error("Failed to deploy server.")
            return False

        logger.info(f"Server deployed successfully on port {args.port}.")
        logger.info(f"You can access the server at: http://localhost:{args.port}")
        return True

    except Exception as e:
        logger.error(f"Error deploying server: {str(e)}")
        logger.error(traceback.format_exc())
        return False
        logger.error(f"Error deploying server: {str(e)}")
        logger.error(traceback.format_exc())
        return False


def stop_server(args: argparse.Namespace) -> bool:
    """
    Stop the WSL2 server.

    Args:
        args: Command-line arguments

    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info("Stopping WSL2 server...")
        deployment = WSLDeployment(
            wsl_distro=args.distro,
            port=args.port,
            api_key=args.api_key,
            use_docker=args.docker,
            use_ctrlplane=args.ctrlplane,
        )

        # Stop server
        if not deployment.stop_server():
            logger.error("Failed to stop server.")
            return False

        logger.info("Server stopped successfully.")
        return True

    except Exception as e:
        logger.error(f"Error stopping server: {str(e)}")
        logger.error(traceback.format_exc())
        return False


def run_server_with_error_handling(args: argparse.Namespace) -> None:
    """
    Run the WSL2 server with error handling.

    Args:
        args: Command-line arguments
    """
    try:
        # Set environment variables
        if args.api_key:
            os.environ["CODEGEN_API_KEY"] = args.api_key

        if args.debug:
            os.environ["DEBUG"] = "true"
            logging.getLogger().setLevel(logging.DEBUG)
            logger.debug("Debug mode enabled")

        # Run the server
        logger.info(f"Starting WSL2 server on {args.host}:{args.port}...")
        run_server(host=args.host, port=args.port)

    except KeyboardInterrupt:
        logger.info("Server stopped by user.")
    except Exception as e:
        logger.error(f"Error running server: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)


def main() -> None:
    """Main entry point for the script."""
    args = parse_args()

    if args.stop:
        # Stop the server
        if not stop_server(args):
            sys.exit(1)
    elif args.deploy:
        # Deploy the server
        if not deploy_server(args):
            sys.exit(1)
    else:
        # Run the server
        run_server_with_error_handling(args)


if __name__ == "__main__":
    main()
