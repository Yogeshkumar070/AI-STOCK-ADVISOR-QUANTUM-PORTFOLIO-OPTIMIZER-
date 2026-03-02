@echo off
echo ==========================================
echo   Starting FinNet: AI Stock Advisor
echo ==========================================

:: Start the FastAPI Backend in a new window
echo [1/2] Starting Backend Server...
start "FinNet Backend" cmd /k "call backend\quantum_env\Scripts\activate.bat && uvicorn backend.main:app --reload"

:: Start the React Frontend in a new window
echo [2/2] Starting Frontend Server...
start "FinNet Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo Both servers are launching in separate windows!
echo Once they load, your app will be at: http://localhost:5173
pause