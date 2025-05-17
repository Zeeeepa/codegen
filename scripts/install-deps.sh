#!/usr/bin/env bash
set -e

SUDO=""
if command -v sudo &> /dev/null; then
    SUDO="sudo"
fi

echo "Installing system dependencies..."

# Detect OS and install appropriate packages
if command -v apt &> /dev/null; then
    # Debian/Ubuntu
    echo "Detected Debian/Ubuntu system"

    # Check for compiler
    if ! (command -v clang &> /dev/null || command -v gcc &> /dev/null); then
        echo "Neither clang nor gcc found. Installing gcc..."
        $SUDO apt update && $SUDO apt install -y gcc build-essential python3-dev
    fi

    # Install required dependencies
    $SUDO apt update && $SUDO apt install -y \
        jq \
        build-essential \
        python3-dev \
        libpixman-1-dev \
        libcairo2-dev \
        libpango1.0-dev \
        libjpeg-dev \
        libgif-dev \
        librsvg2-dev \
        curl \
        git \
        ca-certificates

elif command -v brew &> /dev/null; then
    # macOS
    echo "Detected macOS system"
    brew install jq cairo pango jpeg giflib librsvg

elif command -v dnf &> /dev/null; then
    # Fedora/RHEL/CentOS
    echo "Detected Fedora/RHEL/CentOS system"
    $SUDO dnf install -y jq cairo-devel pango-devel libjpeg-devel giflib-devel librsvg2-devel

else
    echo "Error: Could not find a supported package manager (apt, brew, or dnf)"
    echo "Please install the required dependencies manually:"
    echo "- jq"
    echo "- cairo"
    echo "- pango"
    echo "- libjpeg"
    echo "- giflib"
    echo "- librsvg"
    exit 1
fi

echo "System dependencies installed successfully!"
