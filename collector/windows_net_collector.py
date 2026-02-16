"""
Windows Network Activity Collector
Detects outbound TCP connections via socket polling and process mapping
"""

import psutil
import threading
import time
from datetime import datetime

class WindowsNetCollector:
    def __init__(self, event_queue):
        """Initialize Windows network collector."""
        self.event_queue = event_queue
        self.running = False
        self.known_connections = set()
        self.poll_interval = 0.5  # Poll every 500ms
        self.scan_count = 0
        self.event_count = 0
        self.last_status = None
        
    def start(self):
        """Start the collector in background thread."""
        self.running = True
        self.last_status = time.time()
        thread = threading.Thread(target=self._poll_loop, daemon=True)
        thread.start()
        print("[Collector] Started - will scan every 0.5s")
        return True
    
    def _poll_loop(self):
        """Main polling loop - continuously detect new connections."""
        while self.running:
            try:
                self._scan_connections()
                time.sleep(self.poll_interval)
            except Exception as e:
                if self.running:
                    print(f"[Collector] Poll error: {e}")
                time.sleep(0.5)
    
    def _scan_connections(self):
        """Scan for all TCP connections and detect new outbound ones."""
        try:
            self.scan_count += 1
            connections = psutil.net_connections(kind='inet')
            total_connections = len(connections)
            new_events = 0
            
            # Periodic status every 10 seconds (20 scans at 0.5s interval)
            now = time.time()
            if now - self.last_status >= 10:
                print(f"[Collector] Status: {self.scan_count} scans, {self.event_count} events created, "
                      f"tracking {len(self.known_connections)} known connections")
                self.last_status = now
            
            for conn in connections:
                # Skip if no remote address (not outbound)
                if not conn.raddr:
                    continue
                
                # Skip unwanted states
                if conn.status in ('LISTEN', 'NONE', 'CLOSING', 'CLOSE_WAIT'):
                    continue
                
                # Skip local/private destinations
                if self._is_local_ip(conn.raddr.ip):
                    continue
                
                # Create unique connection key
                conn_key = (conn.pid, conn.laddr.ip, conn.laddr.port, conn.raddr.ip, conn.raddr.port)
                
                # Only process if new
                if conn_key in self.known_connections:
                    continue
                
                # Mark as known
                self.known_connections.add(conn_key)
                
                # Resolve process name
                process_name = self._get_process_name(conn.pid)
                
                # Create event with string timestamp
                timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                event = {
                    "timestamp": timestamp_str,
                    "pid": conn.pid,
                    "process": process_name,
                    "dest_ip": conn.raddr.ip,
                    "dest_port": conn.raddr.port
                }
                
                # Push to queue
                try:
                    self.event_queue.put(event, timeout=1.0)
                    new_events += 1
                    self.event_count += 1
                    print(f"[Collector] NEW: {process_name} ({conn.pid}) -> {conn.raddr.ip}:{conn.raddr.port}")
                except Exception as e:
                    print(f"[Collector] Queue error: {e}")
                    
        except Exception as e:
            if self.running:
                print(f"[Collector] Scan error: {e}")
    
    def _get_process_name(self, pid):
        """Get process name from PID, handle errors gracefully."""
        try:
            proc = psutil.Process(pid)
            return proc.name()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.Error):
            return f"PID_{pid}"
    
    def _is_local_ip(self, ip):
        """Check if IP is loopback or private."""
        try:
            # Loopback
            if ip.startswith('127.') or ip == '::1':
                return True
            
            # RFC 1918 private ranges
            if ip.startswith('192.168.') or ip.startswith('10.') or ip.startswith('172.'):
                return True
            
            # Link-local
            if ip.startswith('169.254.'):
                return True
            
            # Localhost variants
            if ip.lower() in ('localhost', '::'):
                return True
            
            return False
        except:
            return True
    
    def stop(self):
        """Stop the collector."""
        self.running = False
