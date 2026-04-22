@echo off
setlocal enabledelayedexpansion

title UBNAD - Windows Network Monitor
color 0A

echo.
echo ================================================================
echo   UBNAD - Unauthorized Background Network Activity Detector
echo   Windows Edition  ^|  Full Demo Suite
echo ================================================================
echo.

REM ──────────────────────────────────────────────────────────────────
REM  1. PRE-FLIGHT CHECKS
REM ──────────────────────────────────────────────────────────────────

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.10+
    echo         https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Install dependencies
echo [*] Installing dependencies...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

REM Create logs directory
if not exist "logs" mkdir logs

REM Simulator duration in seconds (default 2 minutes)
set SIM_DURATION=120

REM ──────────────────────────────────────────────────────────────────
REM  2. START UBNAD BACKEND
REM ──────────────────────────────────────────────────────────────────

echo.
echo [*] Starting UBNAD backend (network collector + analyzer)...
start "UBNAD Backend" /min cmd /c "python main.py > logs\backend.log 2>&1"

REM Wait for backend to initialise
timeout /t 3 /nobreak >nul
echo [+] Backend started.

REM ──────────────────────────────────────────────────────────────────
REM  3. START TRAFFIC SIMULATORS  (each in its own console window)
REM ──────────────────────────────────────────────────────────────────

echo.
echo [*] Launching traffic simulators (%SIM_DURATION%s each)...
echo.

start "Sim-HTTPPoller"    cmd /c "title Sim - HTTP Poller    & color 0B & python simulators\sim_http_poller.py    --interval 2   --duration %SIM_DURATION% & pause"
echo     [+] HTTP Poller      started
timeout /t 1 /nobreak >nul

start "Sim-TCPConnector"  cmd /c "title Sim - TCP Connector  & color 0D & python simulators\sim_tcp_connector.py  --port 8080 --interval 1.5 --duration %SIM_DURATION% & pause"
echo     [+] TCP Connector    started  (port 8080 — unusual port detection)
timeout /t 1 /nobreak >nul

start "Sim-DNSResolver"   cmd /c "title Sim - DNS Resolver   & color 0E & python simulators\sim_dns_resolver.py   --interval 2.5 --duration %SIM_DURATION% & pause"
echo     [+] DNS Resolver     started
timeout /t 1 /nobreak >nul

start "Sim-BurstTraffic"  cmd /c "title Sim - Burst Traffic  & color 0C & python simulators\sim_burst_traffic.py  --burst-size 10 --burst-gap 0.2 --quiet-period 10 --duration %SIM_DURATION% & pause"
echo     [+] Burst Traffic    started

echo.
echo [+] All 4 simulators running in separate windows.
echo.

REM ──────────────────────────────────────────────────────────────────
REM  4. START STREAMLIT DASHBOARD  (foreground — blocks here)
REM ──────────────────────────────────────────────────────────────────

echo ================================================================
echo   Dashboard will open at:  http://localhost:8501
echo   Press Ctrl+C in THIS window to stop everything.
echo ================================================================
echo.

python -m streamlit run ui\dashboard.py --logger.level=info

REM ──────────────────────────────────────────────────────────────────
REM  5. CLEANUP  (runs when you Ctrl+C the dashboard)
REM ──────────────────────────────────────────────────────────────────

echo.
echo [*] Shutting down all services...

REM Kill backend
taskkill /FI "WINDOWTITLE eq UBNAD Backend"    /T /F >nul 2>&1

REM Kill simulators
taskkill /FI "WINDOWTITLE eq Sim-HTTPPoller"   /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Sim-TCPConnector" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Sim-DNSResolver"  /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Sim-BurstTraffic" /T /F >nul 2>&1

REM Also clean up via the stop script (catches any PID-tracked stragglers)
python simulators\stop_simulators.py >nul 2>&1

echo [+] All services stopped.
echo.
pause

endlocal
