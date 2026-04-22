"""
Export utilities for suspicious events
CSV export for analysis and reporting
"""

import csv
import os
from pathlib import Path
from datetime import datetime
from database.activity_store import fetch_recent_events, get_events_by_severity

EXPORTS_DIR = Path(__file__).resolve().parent / "exports"

def ensure_exports_dir():
    """Ensure exports directory exists."""
    EXPORTS_DIR.mkdir(exist_ok=True)
    return EXPORTS_DIR

def export_suspicious_events_csv(severity_filter=None, limit=1000):
    """
    Export suspicious network events to CSV.
    
    Args:
        severity_filter: Filter by severity ('CRITICAL', 'HIGH', or None for all)
        limit: Maximum events to export
    
    Returns:
        str: Path to exported CSV file
    """
    try:
        ensure_exports_dir()
        
        # Fetch events
        if severity_filter:
            events = get_events_by_severity(severity_filter, limit=limit)
        else:
            events = fetch_recent_events(limit=limit)
        
        if not events:
            return None
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        severity_str = f"_{severity_filter}" if severity_filter else ""
        filename = f"ubnad_events_{timestamp}{severity_str}.csv"
        filepath = EXPORTS_DIR / filename
        
        # Write CSV
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            fieldnames = [
                'Timestamp', 'Process', 'PID', 'Destination IP', 'Port',
                'Suspicion Score', 'Risk Level', 'Severity', 'Reasons',
                'Intent Score', 'Protocol'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            # Write header
            writer.writeheader()
            
            # Write events
            for event in events:
                writer.writerow({
                    'Timestamp': event.get('timestamp', ''),
                    'Process': event.get('process_name', ''),
                    'PID': event.get('pid', ''),
                    'Destination IP': event.get('dest_ip', ''),
                    'Port': event.get('dest_port', ''),
                    'Suspicion Score': round(event.get('suspicion_score', 0), 2),
                    'Risk Level': event.get('risk_level', ''),
                    'Severity': event.get('severity', ''),
                    'Reasons': event.get('reason', ''),
                    'Intent Score': round(event.get('intent_score', 0), 2),
                    'Protocol': event.get('protocol', 'TCP'),
                })
        
        return str(filepath)
    
    except Exception as e:
        print(f"[Export] Error exporting to CSV: {e}")
        return None

def export_alert_summary():
    """Export summary of all alerts."""
    try:
        ensure_exports_dir()
        
        # Get critical and high severity events
        critical = get_events_by_severity('CRITICAL', limit=500)
        high = get_events_by_severity('HIGH', limit=500)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ubnad_alert_summary_{timestamp}.csv"
        filepath = EXPORTS_DIR / filename
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['Severity', 'Process', 'IP:Port', 'Score', 'Timestamp', 'Reason']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            writer.writeheader()
            
            # Write critical events first
            for event in critical:
                writer.writerow({
                    'Severity': 'CRITICAL',
                    'Process': event.get('process_name', ''),
                    'IP:Port': f"{event.get('dest_ip', '')}:{event.get('dest_port', '')}",
                    'Score': round(event.get('suspicion_score', 0), 1),
                    'Timestamp': event.get('timestamp', ''),
                    'Reason': event.get('reason', ''),
                })
            
            # Write high severity events
            for event in high:
                writer.writerow({
                    'Severity': 'HIGH',
                    'Process': event.get('process_name', ''),
                    'IP:Port': f"{event.get('dest_ip', '')}:{event.get('dest_port', '')}",
                    'Score': round(event.get('suspicion_score', 0), 1),
                    'Timestamp': event.get('timestamp', ''),
                    'Reason': event.get('reason', ''),
                })
        
        return str(filepath)
    
    except Exception as e:
        print(f"[Export] Error exporting alert summary: {e}")
        return None

def get_recent_exports(limit=10):
    """Get list of recent export files."""
    try:
        ensure_exports_dir()
        
        # Get all CSV files, sorted by modification time
        csv_files = sorted(
            EXPORTS_DIR.glob('*.csv'),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )[:limit]
        
        return [
            {
                'name': f.name,
                'size': f.stat().st_size,
                'modified': datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            }
            for f in csv_files
        ]
    
    except Exception as e:
        print(f"[Export] Error listing exports: {e}")
        return []
