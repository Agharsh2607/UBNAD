#!/usr/bin/env python3
"""Test psutil network enumeration on Windows."""

import psutil
import time
from collections import defaultdict

def test_psutil():
    """Test psutil.net_connections() capability."""
    print("=" * 70)
    print("PSUTIL Network Enumeration Test")
    print("=" * 70)
    
    # Test 1: Can we enumerate connections?
    print("\n[TEST 1] Enumerating TCP connections...")
    try:
        conns = psutil.net_connections(kind='inet')
        print(f"✓ Successfully enumerated {len(conns)} TCP connections")
        
        # Categorize by state
        by_state = defaultdict(int)
        by_conn_type = {'outbound': 0, 'inbound': 0, 'listening': 0}
        
        for conn in conns:
            by_state[conn.status] += 1
            
            if conn.status == 'LISTEN':
                by_conn_type['listening'] += 1
            elif conn.raddr:
                by_conn_type['outbound'] += 1
            else:
                by_conn_type['inbound'] += 1
        
        print("\nConnection States:")
        for state, count in sorted(by_state.items()):
            print(f"  {state:20} {count:4d}")
        
        print("\nConnection Types:")
        for ctype, count in by_conn_type.items():
            print(f"  {ctype:20} {count:4d}")
        
        # Test 2: Can we get process info?
        print("\n[TEST 2] Retrieving process information...")
        sample_conns = [c for c in conns if c.raddr and c.status not in ('LISTEN', 'NONE')]
        
        if sample_conns:
            print(f"✓ Found {len(sample_conns)} outbound connections")
            print("\nSample connections:")
            for conn in sample_conns[:5]:
                try:
                    proc = psutil.Process(conn.pid)
                    name = proc.name()
                except:
                    name = f"PID_{conn.pid}"
                
                print(f"  {name:20} {conn.laddr.ip}:{conn.laddr.port} -> {conn.raddr.ip}:{conn.raddr.port}")
        else:
            print("✗ No outbound connections found (this is unusual)")
            print("  The collector would have trouble finding connections")
        
        # Test 3: Repeated polling
        print("\n[TEST 3] Polling for new connections (5 second scan)...")
        known = set()
        new_count = 0
        
        start = time.time()
        while time.time() - start < 5:
            try:
                conns = psutil.net_connections(kind='inet')
                for conn in conns:
                    if not conn.raddr or conn.status in ('LISTEN', 'NONE', 'CLOSING', 'CLOSE_WAIT'):
                        continue
                    
                    key = (conn.pid, conn.laddr.ip, conn.laddr.port, conn.raddr.ip, conn.raddr.port)
                    if key not in known:
                        known.add(key)
                        new_count += 1
                
                time.sleep(0.1)
            except Exception as e:
                print(f"✗ Error during polling: {e}")
                break
        
        print(f"✓ Found {new_count} new unique connections during 5-second scan")
        print(f"  (Total unique tracked: {len(known)})")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        print("\nPossible reasons:")
        print("  1. psutil not installed: pip install psutil")
        print("  2. Admin privileges required: run PowerShell as Administrator")
        print("  3. Windows Defender blocking access")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    test_psutil()
