#!/bin/bash
echo "=========================================="
echo " DPSI LFR - Raspberry Pi Setup Installer"
echo "=========================================="

# Exit on any error
set -e

# Update and install system dependencies
echo "=> Installing system dependencies..."
sudo apt-get update -y
sudo apt-get install -y git python3-pip python3-venv python3-opencv libopenblas-dev

# Clone or Update Repo
REPO_DIR="$HOME/DPSI-LFR"
if [ -d "$REPO_DIR" ]; then
    echo "=> Repository found, pulling latest changes..."
    cd "$REPO_DIR"
    git pull
else
    echo "=> Cloning repository..."
    git clone https://github.com/Ojas-sta/DPSI-LFR.git "$REPO_DIR"
    cd "$REPO_DIR"
fi

# Enter the package directory
cd "$REPO_DIR/rbpi_package"

# Install package globally
echo "=> Installing Python package (lfr-cli)..."
# We use --break-system-packages if running on newer Debian/Ubuntu where pip is restricted
pip3 install -e . --break-system-packages || pip3 install -e .

echo "=========================================="
echo " Setup Complete!"
echo " You can now launch the dashboard by typing:"
echo "   lfr-cli"
echo "=========================================="

# Automatically launch it now with path fallback
if command -v lfr-cli &> /dev/null; then
    lfr-cli
else
    export PATH="$HOME/.local/bin:$PATH"
    if ! grep -q ".local/bin" "$HOME/.bashrc"; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
        echo "=> Added ~/.local/bin to ~/.bashrc"
    fi
    if command -v lfr-cli &> /dev/null; then
        lfr-cli
    else
        echo "Error: Could not find lfr-cli in PATH or ~/.local/bin/"
    fi
fi
