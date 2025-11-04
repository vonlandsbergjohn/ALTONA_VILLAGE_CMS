#!/bin/bash
# This script starts the Flask back-end server.

echo "🚀 Starting Back-end Server..."

# Activate the Python virtual environment
source venv/bin/activate

# Run the main Flask application
python altona_village_cms/src/main.py
