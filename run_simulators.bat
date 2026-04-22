@echo off
setlocal enabledelayedexpansion

title UBNAD Simulator Suite — Launcher
color 0E

echo.
echo ============================================================
echo   UBNAD Simulator Suite — Quick Launcher
echo   Starts all 4 benign traffic simulators for testing
echo ============================================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.10+
    pause
    exit /b 1
)

REM Default duration (seconds)
set DURATION=120
if not "%~1"=="" set DURATION=%~1

echo Duration: %DURATION% seconds per simulator
echo.

python simulators\launch_simulators.py --duration %DURATION%

echo.
echo Simulators finished.
pause

endlocal
