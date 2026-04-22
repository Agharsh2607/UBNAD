"""
UBNAD Simulator Launcher
=========================
Starts all four simulator scripts as separate sub-processes and manages them
as a group.  Each simulator runs in its own console window (Windows) so you
can watch the output side-by-side.

Usage:
    python simulators/launch_simulators.py [--duration SECS]

Defaults:
    duration = 120 seconds  (applies to every simulator)

Shutdown:
    • Press Ctrl+C in THIS window — all child processes are terminated
    • Or run  python simulators/stop_simulators.py  from another terminal
    • Or wait for --duration to expire naturally
"""

import argparse
import os
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Resolve paths relative to this file
SCRIPT_DIR = Path(__file__).resolve().parent
PID_FILE = SCRIPT_DIR / ".simulator_pids"

SIMULATORS = [
    {
        "name": "HTTPPoller",
        "script": "sim_http_poller.py",
        "extra_args": ["--url", "http://httpbin.org/get", "--interval", "3"],
    },
    {
        "name": "TCPConnector",
        "script": "sim_tcp_connector.py",
        "extra_args": ["--host", "93.184.216.34", "--port", "80", "--interval", "2"],
    },
    {
        "name": "DNSResolver",
        "script": "sim_dns_resolver.py",
        "extra_args": ["--interval", "4"],
    },
    {
        "name": "BurstTraffic",
        "script": "sim_burst_traffic.py",
        "extra_args": ["--burst-size", "8", "--quiet-period", "15"],
    },
]


def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


def launch_all(duration: float):
    """Start every simulator in a new console window, track PIDs."""
    procs: list[subprocess.Popen] = []
    pids: list[int] = []

    print(f"\n[{_ts()}] ╔══════════════════════════════════════════════════╗")
    print(f"[{_ts()}] ║   UBNAD Simulator Suite — Launcher               ║")
    print(f"[{_ts()}] ╚══════════════════════════════════════════════════╝\n")

    for sim in SIMULATORS:
        script_path = str(SCRIPT_DIR / sim["script"])
        cmd = [
            sys.executable, script_path,
            "--duration", str(duration),
            *sim["extra_args"],
        ]

        # On Windows, launch each simulator in its own visible console window
        if sys.platform == "win32":
            proc = subprocess.Popen(
                cmd,
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )
        else:
            proc = subprocess.Popen(cmd)

        procs.append(proc)
        pids.append(proc.pid)
        print(f"[{_ts()}] ✅  Started {sim['name']:<16}  PID={proc.pid}  ({sim['script']})")

    # Persist PIDs so stop_simulators.py can find them
    _write_pids(pids)

    print(f"\n[{_ts()}] All {len(procs)} simulators running.  Duration: {duration}s")
    print(f"[{_ts()}] PID file: {PID_FILE}")
    print(f"[{_ts()}] Press Ctrl+C to stop all simulators.\n")

    # ---------- Wait / handle Ctrl+C ----------
    def _cleanup(signum=None, frame=None):
        print(f"\n[{_ts()}] Stopping all simulators …")
        for p in procs:
            try:
                p.terminate()
            except OSError:
                pass
        # Give them a moment to exit
        for p in procs:
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill()
        _remove_pid_file()
        print(f"[{_ts()}] All simulators stopped.\n")

    signal.signal(signal.SIGINT, _cleanup)
    signal.signal(signal.SIGTERM, _cleanup)

    try:
        # Wait for all children to exit naturally (they will after --duration)
        for p in procs:
            p.wait()
        print(f"\n[{_ts()}] All simulators completed their duration ({duration}s).")
    except KeyboardInterrupt:
        _cleanup()
    finally:
        _remove_pid_file()


# ---------------------------------------------------------------------------
# PID-file helpers (used by stop_simulators.py)
# ---------------------------------------------------------------------------

def _write_pids(pids: list[int]):
    with open(PID_FILE, "w") as f:
        for pid in pids:
            f.write(f"{pid}\n")


def _remove_pid_file():
    try:
        PID_FILE.unlink(missing_ok=True)
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Entry-point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Launch all UBNAD simulators")
    parser.add_argument("--duration", type=float, default=120.0,
                        help="Run time for each simulator in seconds (default: 120)")
    args = parser.parse_args()

    launch_all(duration=args.duration)


if __name__ == "__main__":
    main()
