#!/bin/bash

# EDI CODECO Generator API - Startup Script for macOS/Linux

echo "==============================================="
echo "EDI CODECO Generator API"
echo "==============================================="
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "Failed to create virtual environment."
        exit 1
    fi
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "Failed to activate virtual environment."
    exit 1
fi

# Install/update dependencies
echo "Installing dependencies..."
pip install -r requirements.txt -q
if [ $? -ne 0 ]; then
    echo "Failed to install dependencies."
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo ""
    echo "NOTE: .env file not found. Creating from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo ".env created. Edit it with your SFTP settings if needed."
    else
        echo "WARNING: .env.example not found. Using defaults."
    fi
fi

# Display startup info
echo ""
echo "==============================================="
echo "Starting API Server..."
echo "==============================================="
echo ""
echo "API will be available at:"
echo "  http://localhost:5000"
echo ""
echo "Interactive API Documentation:"
echo "  http://localhost:5000/api/docs"
echo ""
echo "Press CTRL+C to stop the server."
echo "==============================================="
echo ""

# Start the API
python app.py
