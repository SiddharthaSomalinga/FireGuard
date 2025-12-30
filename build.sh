#!/bin/bash
# Build script for Render deployment
# Installs SWI-Prolog and Python dependencies

set -e  # Exit on error

echo "Installing SWI-Prolog..."
apt-get update
apt-get install -y swi-prolog

echo "Verifying SWI-Prolog installation..."
swipl --version

echo "Installing Python dependencies..."
pip install -r requirements_prolog_api.txt

echo "Build complete!"

