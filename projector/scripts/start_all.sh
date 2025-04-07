#!/bin/bash

# Set up environment
echo "Setting up environment..."
cd "$(dirname "$0")/.."
ROOT_DIR=$(pwd)

# Function to check if a command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Check Python version
python_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "Using Python $python_version"

# Check if we need to update dependencies for Python 3.13+
if [[ "$python_version" == "3.13" || "$python_version" > "3.13" ]]; then
    echo "Python 3.13+ detected. Updating dependencies..."
    ./scripts/update_dependencies.sh
fi

# Check if tmux is installed
if ! command_exists tmux; then
    echo "tmux is not installed. Would you like to install it? (y/n)"
    read -r install_tmux
    if [[ "$install_tmux" =~ ^[Yy]$ ]]; then
        if command_exists apt-get; then
            sudo apt-get update && sudo apt-get install -y tmux
        elif command_exists brew; then
            brew install tmux
        else
            echo "Could not install tmux automatically. Please install it manually."
            exit 1
        fi
    else
        echo "Running without tmux (backend and frontend will run in separate terminals)..."
        # Start backend in a new terminal
        gnome-terminal -- bash -c "cd '$ROOT_DIR' && ./scripts/start_backend.sh; exec bash" || \
        xterm -e "cd '$ROOT_DIR' && ./scripts/start_backend.sh; exec bash" || \
        open -a Terminal.app "cd '$ROOT_DIR' && ./scripts/start_backend.sh" || \
        echo "Could not open a new terminal. Please run the backend script manually."
        
        # Start frontend in the current terminal
        cd "$ROOT_DIR"
        ./scripts/start_frontend.sh
        exit 0
    fi
fi

# Create a new tmux session
tmux new-session -d -s projector

# Split the window horizontally
tmux split-window -h -t projector

# Run backend in the left pane
tmux send-keys -t projector:0.0 "cd '$ROOT_DIR' && ./scripts/start_backend.sh" C-m

# Run frontend in the right pane
tmux send-keys -t projector:0.1 "cd '$ROOT_DIR' && ./scripts/start_frontend.sh" C-m

# Attach to the tmux session
tmux attach-session -t projector

# Clean up on exit
tmux kill-session -t projector