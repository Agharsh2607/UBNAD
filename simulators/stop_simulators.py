"""
UBNAD Simulator Stopper
========================
Reads the PID file left by launch_simulators.py and gracefully terminates
every running simulator process.

Usage:
    python simulators/stop_simulators.py

This is a safe alternative to Ctrl+C if the launcher window is unavailable.
"""

import os
import signal
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PID_FILE = SCRIPT_DIR / ".simulator_pids"


def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


def _pid_is_alive(pid: int) -> bool:
    """Check whether a process with the given PID is still running (Windows + Unix)."""
    try:
        if sys.platform == "win32":
            import ctypes
            kernel32 = ctypes.windll.kernel32
            SYNCHRONIZE = 0x00100000
            handle = kernel32.OpenProcess(SYNCHRONIZE, False, pid)
            if handle:
                kernel32.CloseHandle(handle)
                return True
            return False
        else:
            os.kill(pid, 0)
            return True
    except (OSError, PermissionError):
        return False


def stop_all():
    print(f"\n[{_ts()}] ╔══════════════════════════════════════════════════╗")
    print(f"[{_ts()}] ║   UBNAD Simulator Suite — Stopper                ║")
    print(f"[{_ts()}] ╚══════════════════════════════════════════════════╝\n")

    if not PID_FILE.exists():
        print(f"[{_ts()}] No PID file found at {PID_FILE}")
        print(f"[{_ts()}] Simulators may have already stopped, or launcher was not used.")
        return

    pids: list[int] = []
    with open(PID_FILE) as f:
        for line in f:
            line = line.strip()
            if line.isdigit():
                pids.append(int(line))

    if not pids:
        print(f"[{_ts()}] PID file is empty — nothing to stop.")
        _cleanup_pid_file()
        return

    print(f"[{_ts()}] Found {len(pids)} simulator PID(s): {pids}\n")

    stopped = 0
    for pid in pids:
        if not _pid_is_alive(pid):
            print(f"[{_ts()}] PID {pid} — already exited ✓")
            continue

        try:
            if sys.platform == "win32":
                # Use taskkill on Windows for reliable termination
                os.system(f"taskkill /PID {pid} /T /F >nul 2>&1")
            else:
                os.kill(pid, signal.SIGTERM)
            stopped += 1
            print(f"[{_ts()}] PID {pid} — SIGTERM sent ✓")
        except (OSError, PermissionError) as exc:
            print(f"[{_ts()}] PID {pid} — could not stop ({exc})")

    _cleanup_pid_file()
    print(f"\n[{_ts()}] Done. Stopped {stopped}/{len(pids)} process(es).\n")


def _cleanup_pid_file():
    try:
        PID_FILE.unlink(missing_ok=True)
    except OSError:
        pass


if __name__ == "__main__":
    stop_all()
