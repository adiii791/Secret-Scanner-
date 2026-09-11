#!/bin/bash
echo "============================================"
echo "  Secret Scanner - One-Click Setup (Mac/Linux)"
echo "============================================"
echo ""

# Check Python is installed
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed."
    echo "Install it from https://www.python.org/downloads/"
    exit 1
fi

echo "[1/4] Creating virtual environment..."
python3 -m venv .venv
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to create virtual environment."
    exit 1
fi

echo "[2/4] Installing dependencies..."
source .venv/bin/activate
pip install -r requirements.txt --quiet
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to install dependencies."
    exit 1
fi

echo "[3/4] Setting up environment file..."
if [ ! -f backend/.env ]; then
    cp backend/.env.example backend/.env
    echo "     Created backend/.env with local dev defaults."
else
    echo "     backend/.env already exists, skipping."
fi

echo "[4/4] Starting the app..."
echo ""
echo "============================================"
echo "  App is running at http://localhost:5000"
echo "  Press Ctrl+C to stop."
echo "============================================"
echo ""
cd backend
python app.py
