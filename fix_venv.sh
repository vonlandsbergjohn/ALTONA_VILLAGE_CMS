#!/bin/bash
#
# Altona Village CMS - Virtual Environment Fix for Linux/macOS
#
# This script will:
# 1. Remove the old virtual environment
# 2. Create a new virtual environment
# 3. Install all required packages
#

echo "==============================================="
echo " Altona Village CMS - Virtual Environment Fix"
echo "==============================================="
echo ""
read -p "This script will delete and recreate the virtual environment. Press Enter to continue..."

echo ""
echo "Step 1: Removing old virtual environment..."
if [ -d "venv" ]; then
    rm -rf venv
    echo "✅ Old virtual environment removed"
else
    echo "ℹ️  No existing virtual environment found"
fi

echo ""
echo "Step 2: Creating new virtual environment..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "❌ Failed to create virtual environment"
    echo "💡 Make sure Python 3 is installed"
    exit 1
fi
echo "✅ New virtual environment created"

echo ""
echo "Step 3: Activating virtual environment and installing packages..."
source venv/bin/activate

echo "-> Upgrading pip..."
pip install --upgrade pip

echo "-> Installing required packages from altona_village_cms/requirements.txt..."
pip install -r altona_village_cms/requirements.txt

deactivate
echo "✅ Virtual Environment Setup Complete!"
echo ""
echo "To activate the environment, run: source venv/bin/activate"
echo "Then, to start the backend, run: python altona_village_cms/src/main.py"