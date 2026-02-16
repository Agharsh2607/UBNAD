#!/usr/bin/env python3
"""Test database setup and verify schema."""

import sqlite3
from pathlib import Path
import sys

# Add database module to path
sys.path.insert(0, str(Path(__file__).parent))

from database.activity_store import get_connection, init_db, insert_event, fetch_recent_events

def test_database():
    """Test database setup and operations."""
    print("=" * 70)
    print("UBNAD Database Test")
    print("=" * 70)
    
    # Test 1: Database path
    print("\n[TEST 1] Database path...")
    db_path = Path(__file__).parent / "database" / "ubnad.db"
    print(f"Database file: {db_path}")
    if db_path.exists():
        size_mb = db_path.stat().st_size / 1024 / 1024
        print(f"✓ File exists ({size_mb:.2f} MB)")
    else:
        print("✗ File does not exist (will be created)")
    
    # Test 2: Initialize database
    print("\n[TEST 2] Database initialization...")
    if init_db():
        print("✓ Database initialized successfully")
    else:
        print("✗ Database initialization failed")
        return
    
    # Test 3: Check schema
    print("\n[TEST 3] Checking table schema...")
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(events)")
        columns = cursor.fetchall()
        
        print("Table 'events' columns:")
        for col in columns:
            col_id, name, type_, notnull, default, pk = col
            print(f"  {name:20} {type_:10} {'PK' if pk else ''}")
        
        conn.close()
        print("✓ Table schema verified")
    except Exception as e:
        print(f"✗ Schema check failed: {e}")
        return
    
    # Test 4: Insert test event
    print("\n[TEST 4] Test event insertion...")
    test_event = {
        "timestamp": "2025-01-15 14:30:00",
        "pid": 1234,
        "process_name": "test.exe",
        "dest_ip": "192.0.2.1",
        "dest_port": 443,
        "intent_score": 0.5,
        "suspicion_score": 2.3,
        "risk_level": "LOW"
    }
    
    try:
        insert_event(test_event)
        print("✓ Test event inserted successfully")
    except Exception as e:
        print(f"✗ Insert failed: {e}")
        return
    
    # Test 5: Read back events
    print("\n[TEST 5] Retrieving recent events...")
    try:
        events = fetch_recent_events(5)
        print(f"✓ Retrieved {len(events)} recent events")
        
        if events:
            print("\nMost recent events:")
            for event in events[-3:]:
                timestamp = event[1]  # second column
                process = event[3]    # fourth column
                dest_ip = event[4]    # fifth column
                dest_port = event[5]  # sixth column
                print(f"  {timestamp} | {process:15} | {dest_ip}:{dest_port}")
    except Exception as e:
        print(f"✗ Retrieval failed: {e}")
        return
    
    # Test 6: Row count
    print("\n[TEST 6] Database statistics...")
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM events")
        count = cursor.fetchone()[0]
        
        cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM events")
        date_range = cursor.fetchone()
        
        conn.close()
        
        print(f"✓ Total events in database: {count}")
        if date_range[0]:
            print(f"  Date range: {date_range[0]} to {date_range[1]}")
    except Exception as e:
        print(f"✗ Statistics failed: {e}")
    
    print("\n" + "=" * 70)
    print("Database test complete!")

if __name__ == "__main__":
    test_database()
