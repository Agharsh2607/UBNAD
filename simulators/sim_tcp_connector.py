"""
UBNAD Simulator 2 — TCP Connector
===================================
Opens short-lived TCP connections to a configurable safe endpoint and port,
then immediately closes them.  This raw-socket pattern differs from normal
browser/HTTP traffic and should trigger UBNAD's "unusual port", "new destination",
and "frequent connections" detection rules.

Usage:
    python simulators/sim_tcp_connector.py [--host HOST] [--port PORT]
                                            [--interval SECS] [--duration SECS]

Defaults:
    host      = 93.184.216.34  (example.com — safe, public)
    port      = 80
    interval  = 2 seconds
    duration  = 120 seconds

Safety:
    • Connects only to a well-known public IP
    • No data is sent; connection is closed immediately
    • Stops automatically after --duration seconds
    • Clean Ctrl+C handling
"""

import argparse
import os
import signal
import socket
import sys
import time
from datetime import datetime

PROCESS_TAG = "TCPConnector"


class TCPConnectorSimulator:
    """Open-and-close rapid TCP connections."""

    def __init__(self, host: str, port: int, interval: float, duration: float):
        self.host = host
        self.port = port
        self.interval = interval
        self.duration = duration
        self.running = True
        self.connect_count = 0

        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)

    # ------------------------------------------------------------------
    def _shutdown(self, signum, frame):
        print(f"\n[{PROCESS_TAG}] ⏹  Shutdown signal received after {self.connect_count} connections.")
        self.running = False

    # ------------------------------------------------------------------
    def _log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] {PROCESS_TAG}: {msg}")

    # ------------------------------------------------------------------
    def run(self):
        self._log(f"Starting — target={self.host}:{self.port}  interval={self.interval}s  duration={self.duration}s")
        self._log(f"PID={os.getpid()} | Press Ctrl+C to stop early.\n")

        start = time.time()

        while self.running:
            elapsed = time.time() - start
            if elapsed >= self.duration:
                self._log(f"Duration limit reached ({self.duration}s). Stopping.")
                break

            sock = None
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                sock.connect((self.host, self.port))
                self.connect_count += 1
                remaining = max(0, self.duration - elapsed)
                self._log(
                    f"TCP connect {self.host}:{self.port} → OK  "
                    f"(#{self.connect_count}, {remaining:.0f}s remaining)"
                )
            except socket.timeout:
                self._log(f"TCP connect {self.host}:{self.port} → TIMEOUT")
            except OSError as exc:
                self._log(f"TCP connect {self.host}:{self.port} → FAILED ({exc})")
            finally:
                if sock:
                    try:
                        sock.close()
                    except OSError:
                        pass

            # Interruptible sleep
            sleep_end = time.time() + self.interval
            while self.running and time.time() < sleep_end:
                time.sleep(0.25)

        self._log(f"Finished. Total connections: {self.connect_count}")


# ---------------------------------------------------------------------------
# Entry-point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="UBNAD Simulator 2 — TCP Connector (safe, benign traffic generator)"
    )
    parser.add_argument("--host", default="93.184.216.34",
                        help="Target host IP (default: 93.184.216.34 = example.com)")
    parser.add_argument("--port", type=int, default=8080,
                        help="Target port (default: 8080 — triggers unusual-port detection)")
    parser.add_argument("--interval", type=float, default=1.5,
                        help="Seconds between connections (default: 1.5)")
    parser.add_argument("--duration", type=float, default=120.0,
                        help="Total run time in seconds (default: 120)")
    args = parser.parse_args()

    sim = TCPConnectorSimulator(
        host=args.host, port=args.port,
        interval=args.interval, duration=args.duration
    )
    sim.run()


if __name__ == "__main__":
    main()
