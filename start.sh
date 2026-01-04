#!/bin/bash

# Go to script's directory
cd "$(dirname "$0")"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
fi

# Activate venv
source .venv/bin/activate

# Install missing dependencies
echo "Checking dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Launch the app
echo "Launching Bouzouki Lesson Player..."
python3 main.py
