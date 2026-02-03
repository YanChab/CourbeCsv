#!/bin/bash
# Script to run the application with Docker on macOS
# Requires XQuartz to be installed: brew install --cask xquartz

# Allow connections from localhost
xhost +localhost 2>/dev/null || echo "Note: xhost not found, install XQuartz"

# Set DISPLAY for macOS
export DISPLAY=host.docker.internal:0

# Run docker-compose
docker-compose up --build
