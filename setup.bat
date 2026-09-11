@echo off
echo ============================================
echo   Secret Scanner - One-Click Setup (Windows)
echo ============================================
echo.

:: Check Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Download it from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/4] Creating virtual environment...
python -m venv .venv
if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment.
    pause
    exit /b 1
)

echo [2/4] Installing dependencies...
call .venv\Scripts\activate.bat
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

echo [3/4] Setting up environment file...
if not exist backend\.env (
    copy backend\.env.example backend\.env >nul
    echo      Created backend\.env with local dev defaults.
) else (
    echo      backend\.env already exists, skipping.
)

echo [4/4] Starting the app...
echo.
echo ============================================
echo   App is running at http://localhost:5000
echo   Press Ctrl+C to stop.
echo ============================================
echo.
cd backend
python app.py
