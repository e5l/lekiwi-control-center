#!/bin/bash
# Start the LeKiwi Control Center server

set -e

# Check if uv is installed
if command -v uv &> /dev/null; then
    echo "Starting LeKiwi Control Center with uv..."
    uv run lekiwi-server
else
    # Fallback: activate venv and run directly
    echo "uv not found, using virtual environment..."
    if [ -d ".venv" ]; then
        source .venv/bin/activate
        lekiwi-server
    else
        echo "Error: No virtual environment found. Run 'uv sync' first."
        exit 1
    fi
fi
