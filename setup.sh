#!/bin/bash

echo "========================================"
echo "Gmail Order Processor - Mac/Linux Setup"
echo "========================================"
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo
    echo "Please install Python 3 first:"
    echo "- Mac: Install from https://www.python.org/downloads/ or use 'brew install python3'"
    echo "- Linux: Run 'sudo apt install python3 python3-pip python3-venv' (Ubuntu/Debian)"
    echo
    exit 1
fi

echo "Python 3 found! Starting setup..."
echo

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to create virtual environment"
    exit 1
fi

# Activate virtual environment and install requirements
echo "Installing packages..."
source venv/bin/activate
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install packages"
    exit 1
fi

# Copy environment template
if [ ! -f .env ]; then
    echo "Creating configuration file..."
    cp .env.example .env
fi

echo
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo
echo "NEXT STEPS:"
echo "1. Edit .env file with your inFlow API credentials"
echo "2. Run OAuth setup: source venv/bin/activate && python setup_oauth_flow.py"
echo "3. Start the processor: source venv/bin/activate && python main.py"
echo
echo "For detailed help, see INSTALL.md"
echo