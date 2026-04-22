"""
Activity Store - SQLite Database for network events
"""

import sqlite3
import threading
import time
from pathlib import Path
import json

# Absolute database path
DB_PATH = Path(__file__).resolve().parent / "ubnad.db"
DB_LOCK = threading.Lock()

def get_connection():
    """Get a SQLite connection to the database."""
    conn = sqlite3.connect(str(DB_PATH), timeout=10.0)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize SQLite database with events table."""
    with DB_LOCK:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Check if new columns exist
            cursor.execute("PRAGMA table_info(events)")
            columns = [col[1] for col in cursor.fetchall()]
            
            # Create table if it doesn't exist
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                pid INTEGER,
                process_name TEXT,
                dest_ip TEXT,
                dest_port INTEGER,
                intent_score REAL,
                suspicion_score REAL,
                risk_level TEXT,
                reason TEXT,
                severity TEXT,
                protocol TEXT
            )
            """)
            
            # Add missing columns if they don't exist
            if 'reason' not in columns:
                cursor.execute("ALTER TABLE events ADD COLUMN reason TEXT")
            if 'severity' not in columns:
                cursor.execute("ALTER TABLE events ADD COLUMN severity TEXT")
            if 'protocol' not in columns:
                cursor.execute("ALTER TABLE events ADD COLUMN protocol TEXT DEFAULT 'TCP'")
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"[DB] Init error: {e}")
            return False

def insert_event(event_dict):
    """Insert event into database from dictionary."""
    with DB_LOCK:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Handle reasons - if list, join with semicolon
            reasons = event_dict.get("reasons", [])
            reason_str = "; ".join(reasons) if isinstance(reasons, list) else str(reasons)
            
            cursor.execute("""
            INSERT INTO events 
            (timestamp, pid, process_name, dest_ip, dest_port, intent_score, 
             suspicion_score, risk_level, reason, severity, protocol)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event_dict.get("timestamp"),
                event_dict.get("pid"),
                event_dict.get("process_name"),
                event_dict.get("dest_ip"),
                event_dict.get("dest_port"),
                event_dict.get("intent_score"),
                event_dict.get("suspicion_score"),
                event_dict.get("risk_level"),
                reason_str,
                event_dict.get("severity"),
                event_dict.get("protocol", "TCP")
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"[DB] Insert error: {e}")
            return False

def fetch_recent_events(limit=50):
    """Fetch recent events from database."""
    with DB_LOCK:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
            SELECT * FROM events 
            ORDER BY timestamp DESC 
            LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"[DB] Fetch error: {e}")
            return []

def get_last_events(limit=50):
    """Get last N events from database."""
    return fetch_recent_events(limit)

def get_alerts(limit=10):
    """Get high/critical risk events."""
    with DB_LOCK:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
            SELECT * FROM events 
            WHERE risk_level IN ('HIGH', 'CRITICAL')
            ORDER BY timestamp DESC 
            LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"[DB] Alert fetch error: {e}")
            return []

def get_events_by_severity(severity, limit=50):
    """Get events filtered by severity level."""
    with DB_LOCK:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
            SELECT * FROM events 
            WHERE severity = ?
            ORDER BY timestamp DESC 
            LIMIT ?
            """, (severity, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"[DB] Fetch error: {e}")
            return []

def get_process_events(process_name, limit=50):
    """Get events for a specific process."""
    with DB_LOCK:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
            SELECT * FROM events 
            WHERE process_name = ?
            ORDER BY timestamp DESC 
            LIMIT ?
            """, (process_name, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"[DB] Fetch error: {e}")
            return []

def get_event_count():
    """Get total event count."""
    with DB_LOCK:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM events")
            count = cursor.fetchone()[0]
            conn.close()
            
            return count
        except Exception as e:
            print(f"[DB] Count error: {e}")
            return 0

def get_risk_distribution():
    """Get distribution of risk levels."""
    with DB_LOCK:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
            SELECT risk_level, COUNT(*) as count 
            FROM events 
            GROUP BY risk_level
            """)
            
            rows = cursor.fetchall()
            conn.close()
            
            return {dict(row)['risk_level']: dict(row)['count'] for row in rows}
        except Exception as e:
            print(f"[DB] Distribution error: {e}")
            return {}

def get_top_processes(limit=10):
    """Get top processes by event count."""
    with DB_LOCK:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
            SELECT process_name, COUNT(*) as count 
            FROM events 
            GROUP BY process_name 
            ORDER BY count DESC 
            LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [{'process': dict(row)['process_name'], 'count': dict(row)['count']} for row in rows]
        except Exception as e:
            print(f"[DB] Top processes error: {e}")
            return []

def export_to_csv(filepath, filter_severity=None):
    """Export events to CSV file."""
    with DB_LOCK:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            if filter_severity:
                cursor.execute("""
                SELECT * FROM events 
                WHERE severity = ?
                ORDER BY timestamp DESC
                """, (filter_severity,))
            else:
                cursor.execute("SELECT * FROM events ORDER BY timestamp DESC")
            
            rows = cursor.fetchall()
            conn.close()
            
            if not rows:
                return False
            
            import csv
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # Write header
                writer.writerow(['Timestamp', 'Process', 'PID', 'Dest IP', 'Port', 
                               'Suspicion Score', 'Risk Level', 'Severity', 'Reason'])
                
                # Write rows
                for row in rows:
                    r = dict(row)
                    writer.writerow([
                        r['timestamp'],
                        r['process_name'],
                        r['pid'],
                        r['dest_ip'],
                        r['dest_port'],
                        round(r['suspicion_score'], 2),
                        r['risk_level'],
                        r['severity'],
                        r['reason']
                    ])
            
            return True
        except Exception as e:
            print(f"[DB] Export error: {e}")
            return False

def clear_old_events(hours=24):
    """Remove events older than N hours."""
    with DB_LOCK:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[DB] Clear error: {e}")
