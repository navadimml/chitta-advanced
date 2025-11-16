#!/bin/bash
# Backend Setup Script for Chitta
# This script creates a Python virtual environment and installs dependencies

set -e  # Exit on error

echo "🚀 Setting up Chitta Backend..."

# Check if Python3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✓ Found Python $PYTHON_VERSION"

# Navigate to backend directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip --quiet

# Install requirements
echo "📦 Installing dependencies..."
pip install -r requirements.txt --quiet

echo ""
echo "✅ Backend setup complete!"
echo ""
echo "To activate the virtual environment, run:"
echo "  cd backend"
echo "  source venv/bin/activate"
echo ""
echo "To start the backend server:"
echo "  python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
echo ""
echo "To deactivate the virtual environment:"
echo "  deactivate"
echo ""
