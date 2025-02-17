#!/bin/bash

# Verify if the virtual environment already exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
else
    echo "The virtual environment already exists."
fi

# activate the virtual environment
source venv/bin/activate

# Install the dependencies
pip install --upgrade pip
pip install -r requirements.txt

echo "Virtual environment created and dependencies installed."
