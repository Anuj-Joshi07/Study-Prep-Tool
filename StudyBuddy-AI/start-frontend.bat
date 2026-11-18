@echo off
echo ============================================
echo  Study Prep Tool - Frontend Setup ^& Start
echo ============================================

cd /d "%~dp0frontend"

:: Install if node_modules missing
if not exist "node_modules" (
    echo [1/2] Installing npm dependencies...
    npm install
)

echo [2/2] Starting React dev server on http://localhost:5173
echo.
npm run dev

pause
