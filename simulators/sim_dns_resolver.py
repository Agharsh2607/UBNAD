"""
UBNAD Simulator 3 — DNS Resolver
==================================
Performs periodic DNS lookups for a rotating list of public domain names.
Between lookups it also makes a lightweight HTTP HEAD request to show
mixed network activity.  This pattern should trigger UBNAD's "frequent
connections" and "user-idle-but-active" rules.

Usage:
    python simulators/sim_dns_resolver.py [--interval SECS] [--duration SECS]
                                           [--domains d1,d2,d3]

Defaults:
    interval  = 4 seconds
    duration  = 120 seconds
    domains   = example.com, httpbin.org, google.com, github.com, python.org

Safety:
    • Standard DNS lookups — identical to what every browser does
    • Targets only well-known, safe public domains
    • No data is uploaded; HEAD requests transfer minimal data
    • Automatic stop after --duration seconds
"""

import argparse
import os
import signal
import socket
import sys
import time
from datetime import datetime

# Optional lightweight HTTP for HEAD requests
try:
    import urllib.request

    def _http_head(url: str, timeout: int = 5):
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status
except Exception:
    def _http_head(url: str, timeout: int = 5):
        return None

PROCESS_TAG = "DNSResolver"

DEFAULT_DOMAINS = [
    "example.com",
    "httpbin.org",
    "google.com",
    "github.com",
    "python.org",
    "wikipedia.org",
    "cloudflare.com",
    "mozilla.org",
]


class DNSResolverSimulator:
    """Cycle through domains doing DNS resolution + optional HEAD request."""

    def __init__(self, domains: list[str], interval: float, duration: float):
        self.domains = domains
        self.interval = interval
        self.duration = duration
        self.running = True
        self.lookup_count = 0

        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)

    # ------------------------------------------------------------------
    def _shutdown(self, signum, frame):
        print(f"\n[{PROCESS_TAG}] ⏹  Shutdown after {self.lookup_count} lookups.")
        self.running = False

    # ------------------------------------------------------------------
    def _log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] {PROCESS_TAG}: {msg}")

    # ------------------------------------------------------------------
    def run(self):
        self._log(f"Starting — {len(self.domains)} domains  interval={self.interval}s  duration={self.duration}s")
        self._log(f"PID={os.getpid()} | Press Ctrl+C to stop early.\n")

        start = time.time()
        idx = 0

        while self.running:
            elapsed = time.time() - start
            if elapsed >= self.duration:
                self._log(f"Duration limit reached ({self.duration}s). Stopping.")
                break

            domain = self.domains[idx % len(self.domains)]
            idx += 1

            # --- DNS lookup ---
            try:
                ip = socket.gethostbyname(domain)
                self.lookup_count += 1
                remaining = max(0, self.duration - elapsed)
                self._log(f"DNS  {domain} → {ip}  (#{self.lookup_count}, {remaining:.0f}s remaining)")
            except socket.gaierror as exc:
                self._log(f"DNS  {domain} → FAILED ({exc})")

            # --- Optional HEAD request (every other lookup) ---
            if idx % 2 == 0:
                url = f"http://{domain}"
                try:
                    status = _http_head(url)
                    if status:
                        self._log(f"HEAD {url} → {status}")
                except Exception as exc:
                    self._log(f"HEAD {url} → FAILED ({exc})")

            # Interruptible sleep
            sleep_end = time.time() + self.interval
            while self.running and time.time() < sleep_end:
                time.sleep(0.25)

        self._log(f"Finished. Total lookups: {self.lookup_count}")


# ---------------------------------------------------------------------------
# Entry-point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="UBNAD Simulator 3 — DNS Resolver (safe, benign traffic generator)"
    )
    parser.add_argument("--interval", type=float, default=2.5,
                        help="Seconds between lookups (default: 2.5)")
    parser.add_argument("--duration", type=float, default=120.0,
                        help="Total run time in seconds (default: 120)")
    parser.add_argument("--domains", type=str, default=None,
                        help="Comma-separated domain list (default: built-in safe list)")
    args = parser.parse_args()

    domains = args.domains.split(",") if args.domains else DEFAULT_DOMAINS

    sim = DNSResolverSimulator(domains=domains, interval=args.interval, duration=args.duration)
    sim.run()


if __name__ == "__main__":
    main()
