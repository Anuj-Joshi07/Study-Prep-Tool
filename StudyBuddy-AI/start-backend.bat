@echo off
echo ============================================
echo  Study Prep Tool - Backend Setup ^& Start
echo ============================================

cd /d "%~dp0backend"

:: Create venv if not present
if not exist "venv" (
    echo [1/4] Creating Python virtual environment...
    python -m venv venv
)

:: Activate
echo [2/4] Activating virtual environment...
call venv\Scripts\activate.bat

:: Install dependencies
echo [3/4] Installing dependencies...
pip install -r requirements.txt --quiet

:: Start server
echo [4/4] Starting FastAPI server on http://localhost:8000
echo       API Docs: http://localhost:8000/docs
echo.
python main.py

pause
