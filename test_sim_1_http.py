"""
UBNAD Test Simulator 1 - HTTP Request Generator
Generates repeated HTTP GET requests at configurable intervals
Safe test pattern: simulates legitimate periodic health checks or data sync
"""

import requests
import time
import sys
import signal
from datetime import datetime

class HTTPSimulator:
    def __init__(self, target_url="http://httpbin.org/get", interval=2, duration=None):
        self.target_url = target_url
        self.interval = interval
        self.duration = duration
        self.running = True
        self.request_count = 0
        
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle graceful shutdown"""
        print(f"\n[HTTPSim] Shutdown signal received. Processed {self.request_count} requests.")
        self.running = False
        sys.exit(0)
    
    def run(self):
        """Main loop - send HTTP requests"""
        print("[HTTPSim] Starting HTTP request simulator")
        print(f"[HTTPSim] Target: {self.target_url}")
        print(f"[HTTPSim] Interval: {self.interval}s")
        if self.duration:
            print(f"[HTTPSim] Duration: {self.duration}s")
        print("[HTTPSim] Ready. Press Ctrl+C to stop.\n")
        
        start_time = time.time()
        
        while self.running:
            try:
                elapsed = time.time() - start_time
                
                # Check duration limit
                if self.duration and elapsed > self.duration:
                    print(f"[HTTPSim] Duration limit reached ({self.duration}s)")
                    break
                
                # Send HTTP request
                try:
                    response = requests.get(self.target_url, timeout=5)
                    self.request_count += 1
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"[{timestamp}] HTTPSim: GET {self.target_url} -> {response.status_code}")
                except requests.exceptions.RequestException as e:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"[{timestamp}] HTTPSim: Request failed - {str(e)[:50]}")
                
                # Wait for next interval
                time.sleep(self.interval)
                
            except KeyboardInterrupt:
                self.running = False
                break
            except Exception as e:
                print(f"[HTTPSim] Error: {e}")
                time.sleep(1)
        
        print(f"\n[HTTPSim] Stopped. Total requests sent: {self.request_count}")

if __name__ == "__main__":
    # Command-line arguments
    target = sys.argv[1] if len(sys.argv) > 1 else "http://httpbin.org/get"
    interval = float(sys.argv[2]) if len(sys.argv) > 2 else 2
    duration = float(sys.argv[3]) if len(sys.argv) > 3 else None
    
    simulator = HTTPSimulator(target_url=target, interval=interval, duration=duration)
    simulator.run()
