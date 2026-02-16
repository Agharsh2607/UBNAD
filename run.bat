@echo off
setlocal enabledelayedexpansion

title UBNAD - Windows Network Monitor
color 0A

echo.
echo ============================================================
echo UBNAD - Unauthorized Background Network Activity Detector
echo Windows Edition
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.10+
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Install dependencies
echo Installing dependencies...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

REM Create logs directory
if not exist "logs" mkdir logs

REM Start backend in background
echo.
echo Starting UBNAD backend...
start "UBNAD Backend" python main.py > logs\backend.log 2>&1

REM Wait for backend to initialize
timeout /t 2 /nobreak

REM Start Streamlit dashboard
echo Starting Streamlit dashboard...
echo.
echo Dashboard will open at: http://localhost:8501
echo.
echo Press Ctrl+C to stop both services
echo.

python -m streamlit run ui\dashboard.py --logger.level=info

REM Cleanup
taskkill /FI "WINDOWTITLE eq UBNAD Backend" /T /F >nul 2>&1

endlocal
