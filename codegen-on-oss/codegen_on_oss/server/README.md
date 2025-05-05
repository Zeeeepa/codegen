# Server Module

This module contains all server-related functionality for the codegen-on-oss project.

## Structure

- `analysis/`: Analysis server implementation
  - `server.py`: Main analysis server
  - `project_manager.py`: Project management for analysis server
  - `webhook_handler.py`: Webhook handling for analysis server

- `api/`: API server implementations
  - `websocket_manager.py`: WebSocket management

- `scripts/`: Server scripts
  - `run_wsl_server.py`: Script to run the WSL server

- `wsl/`: WSL server implementation
  - `server.py`: WSL server for code validation
  - `client.py`: Client for interacting with WSL server
  - `deployment.py`: Deployment utilities for WSL server
  - `cli.py`: Command-line interface for WSL server
  - `integration.py`: Integration with external tools

## Usage

Each server component can be used independently or together depending on your needs.
Refer to the individual module documentation for specific usage instructions.

