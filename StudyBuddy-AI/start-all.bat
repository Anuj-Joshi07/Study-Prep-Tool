@echo off
echo ============================================================
echo  Study Prep Tool — Starting All Services
echo ============================================================
echo.

REM ── StudyBuddy Backend (Engineering) → port 8000
echo [1/3] Starting Engineering Backend (port 8000)...
start "StudyBuddy Backend :8000" cmd /k ^
  "cd /d "c:\Users\ACER\Downloads\final project\StudyBuddy-AI\backend" ^&^& venv\Scripts\activate ^&^& python main.py"

timeout /t 3 /nobreak > nul

REM ── JEE GenAI Backend (School) → port 8001
echo [2/3] Starting School/JEE Backend (port 8001)...
start "JEE GenAI Backend :8001" cmd /k ^
  "cd /d "c:\Users\ACER\Downloads\final project\gen ai" ^&^& python -m uvicorn main_groq:app --host 0.0.0.0 --port 8001 --reload"

timeout /t 3 /nobreak > nul

REM ── React Frontend → port 5173
echo [3/3] Starting React Frontend (port 5173)...
start "EduVerse Frontend :5173" cmd /k ^
  "cd /d "c:\Users\ACER\Downloads\final project\StudyBuddy-AI\frontend" ^&^& npm run dev"

echo.
echo ============================================================
echo  All services starting in separate windows:
echo.
echo   Engineering Backend  → http://localhost:8000
echo   School/JEE Backend   → http://localhost:8001
echo   Frontend (React)     → http://localhost:5173
echo.
echo   Open http://localhost:5173 in your browser
echo ============================================================
echo.
pause
