"""
UBNAD Simulator 4 — Burst Traffic Generator
=============================================
Alternates between quiet periods and short bursts of rapid network activity.
During a burst, it fires multiple HTTP GET requests in quick succession, then
goes silent.  This bursty pattern is different from steady traffic and should
trigger UBNAD's "frequent connections" spike detection.

Usage:
    python simulators/sim_burst_traffic.py [--url URL]
                                            [--burst-size N] [--burst-gap SECS]
                                            [--quiet-period SECS] [--duration SECS]

Defaults:
    url           = http://httpbin.org/get
    burst_size    = 8   (requests per burst)
    burst_gap     = 0.3 (seconds between requests inside a burst)
    quiet_period  = 15  (seconds between bursts)
    duration      = 120 seconds

Safety:
    • Targets only a safe public test endpoint
    • Read-only GET requests
    • Automatic stop after --duration seconds
"""

import argparse
import os
import signal
import sys
import time
from datetime import datetime

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

PROCESS_TAG = "BurstTraffic"


class BurstTrafficSimulator:
    """Alternate quiet + burst phases."""

    def __init__(self, url: str, burst_size: int, burst_gap: float,
                 quiet_period: float, duration: float):
        self.url = url
        self.burst_size = burst_size
        self.burst_gap = burst_gap
        self.quiet_period = quiet_period
        self.duration = duration
        self.running = True
        self.total_requests = 0
        self.burst_count = 0

        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)

    # ------------------------------------------------------------------
    def _shutdown(self, signum, frame):
        print(
            f"\n[{PROCESS_TAG}] ⏹  Shutdown after {self.burst_count} bursts, "
            f"{self.total_requests} requests."
        )
        self.running = False

    # ------------------------------------------------------------------
    def _log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] {PROCESS_TAG}: {msg}")

    # ------------------------------------------------------------------
    def _fire_burst(self):
        """Send a rapid burst of requests."""
        self.burst_count += 1
        self._log(f"━━ BURST #{self.burst_count} ({self.burst_size} requests @ {self.burst_gap}s gap) ━━")

        for i in range(1, self.burst_size + 1):
            if not self.running:
                break
            try:
                status = _http_get(self.url)
                self.total_requests += 1
                self._log(f"  [{i}/{self.burst_size}] GET {self.url} → {status}")
            except Exception as exc:
                self._log(f"  [{i}/{self.burst_size}] FAILED — {exc}")

            if i < self.burst_size:
                time.sleep(self.burst_gap)

        self._log(f"━━ BURST #{self.burst_count} complete ━━\n")

    # ------------------------------------------------------------------
    def run(self):
        self._log(
            f"Starting — url={self.url}  burst={self.burst_size}×{self.burst_gap}s  "
            f"quiet={self.quiet_period}s  duration={self.duration}s"
        )
        self._log(f"PID={os.getpid()} | Press Ctrl+C to stop early.\n")

        start = time.time()

        while self.running:
            elapsed = time.time() - start
            if elapsed >= self.duration:
                self._log(f"Duration limit reached ({self.duration}s). Stopping.")
                break

            # Fire burst
            self._fire_burst()

            if not self.running:
                break

            # Quiet period (interruptible)
            remaining = max(0, self.duration - (time.time() - start))
            quiet = min(self.quiet_period, remaining)
            self._log(f"💤 Quiet period — sleeping {quiet:.0f}s …")
            sleep_end = time.time() + quiet
            while self.running and time.time() < sleep_end:
                time.sleep(0.25)

        self._log(f"Finished. Total bursts: {self.burst_count}, Total requests: {self.total_requests}")


# ---------------------------------------------------------------------------
# Entry-point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="UBNAD Simulator 4 — Burst Traffic Generator (safe, benign traffic)"
    )
    parser.add_argument("--url", default="http://httpbin.org/get",
                        help="Target URL (default: httpbin.org)")
    parser.add_argument("--burst-size", type=int, default=10,
                        help="Requests per burst (default: 10)")
    parser.add_argument("--burst-gap", type=float, default=0.2,
                        help="Seconds between requests in a burst (default: 0.2)")
    parser.add_argument("--quiet-period", type=float, default=10.0,
                        help="Quiet seconds between bursts (default: 10)")
    parser.add_argument("--duration", type=float, default=120.0,
                        help="Total run time in seconds (default: 120)")
    args = parser.parse_args()

    sim = BurstTrafficSimulator(
        url=args.url,
        burst_size=args.burst_size,
        burst_gap=args.burst_gap,
        quiet_period=args.quiet_period,
        duration=args.duration,
    )
    sim.run()


if __name__ == "__main__":
    main()
