"""
UBNAD Simulator 1 — HTTP Poller
================================
Generates repeated HTTP GET requests at a configurable interval to a safe
public endpoint.  This pattern mimics automated health-check / data-sync
behavior and should trigger UBNAD's "frequent connections" + "unknown process"
detection rules.

Usage:
    python simulators/sim_http_poller.py [--url URL] [--interval SECS] [--duration SECS]

Defaults:
    url       = http://httpbin.org/get
    interval  = 3 seconds
    duration  = 120 seconds (2 minutes)

Safety:
    • Targets a well-known public test endpoint (httpbin.org)
    • Read-only GET requests; no data is uploaded
    • Stops automatically after --duration seconds
    • Handles Ctrl+C for immediate clean exit
"""

import argparse
import os
import signal
import sys
import time
from datetime import datetime

# ---------------------------------------------------------------------------
# Optional: use requests if available, otherwise fall back to urllib
# ---------------------------------------------------------------------------
try:
    import requests as _requests

    def _http_get(url: str, timeout: int = 5):
        resp = _requests.get(url, timeout=timeout)
        return resp.status_code
except ImportError:
    import urllib.request

    def _http_get(url: str, timeout: int = 5):
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.status

# ---------------------------------------------------------------------------
# Simulator class
# ---------------------------------------------------------------------------

PROCESS_TAG = "HTTPPoller"

class HTTPPollerSimulator:
    """Send periodic HTTP GET requests and log results to the console."""

    def __init__(self, url: str, interval: float, duration: float):
        self.url = url
        self.interval = interval
        self.duration = duration
        self.running = True
        self.request_count = 0

        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)

    # ------------------------------------------------------------------
    def _shutdown(self, signum, frame):
        print(f"\n[{PROCESS_TAG}] ⏹  Shutdown signal received after {self.request_count} requests.")
        self.running = False

    # ------------------------------------------------------------------
    def _log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] {PROCESS_TAG}: {msg}")

    # ------------------------------------------------------------------
    def run(self):
        self._log(f"Starting — target={self.url}  interval={self.interval}s  duration={self.duration}s")
        self._log(f"PID={os.getpid()} | Press Ctrl+C to stop early.\n")

        start = time.time()

        while self.running:
            elapsed = time.time() - start
            if elapsed >= self.duration:
                self._log(f"Duration limit reached ({self.duration}s). Stopping.")
                break

            try:
                status = _http_get(self.url)
                self.request_count += 1
                remaining = max(0, self.duration - elapsed)
                self._log(f"GET {self.url} → {status}  (#{self.request_count}, {remaining:.0f}s remaining)")
            except Exception as exc:
                self._log(f"Request failed — {exc}")

            # Interruptible sleep
            sleep_end = time.time() + self.interval
            while self.running and time.time() < sleep_end:
                time.sleep(0.25)

        self._log(f"Finished. Total requests: {self.request_count}")

# ---------------------------------------------------------------------------
# Entry-point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="UBNAD Simulator 1 — HTTP Poller (safe, benign traffic generator)"
    )
    parser.add_argument("--url", default="http://httpbin.org/get",
                        help="Target URL for GET requests (default: httpbin.org)")
    parser.add_argument("--interval", type=float, default=2.0,
                        help="Seconds between requests (default: 2)")
    parser.add_argument("--duration", type=float, default=120.0,
                        help="Total run time in seconds (default: 120)")
    args = parser.parse_args()

    sim = HTTPPollerSimulator(url=args.url, interval=args.interval, duration=args.duration)
    sim.run()


if __name__ == "__main__":
    main()
