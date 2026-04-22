"""
Alert Manager - Generate and manage security alerts with reasoning
"""

import threading
import time
from datetime import datetime
from collections import defaultdict

# Track recent alerts to prevent spam
_alert_history = defaultdict(list)  # {process_name: [timestamps]}
_last_alert_time = {}  # {process_name: last_alert_timestamp}

def should_rate_limit(process_name, rate_limit_secs=60):
    """Check if alert should be rate-limited for this process."""
    last_alert = _last_alert_time.get(process_name, 0)
    now = time.time()
    
    if now - last_alert < rate_limit_secs:
        return True
    
    return False

def record_alert(process_name):
    """Record alert timestamp for a process."""
    now = time.time()
    _last_alert_time[process_name] = now
    _alert_history[process_name].append(now)
    
    # Keep only last 100 alerts per process
    if len(_alert_history[process_name]) > 100:
        _alert_history[process_name].pop(0)

def get_alert_count_in_window(process_name, window_secs=3600):
    """Get alert count for process in recent time window."""
    now = time.time()
    return sum(1 for ts in _alert_history[process_name] 
              if now - ts < window_secs)

def generate_alert(process_name, dest_ip, dest_port, suspicion_score, 
                   idle_time, reasons, intent_score):
    """
    Generate alert for suspicious network activity with detailed reasoning.
    
    Returns:
        tuple: (should_alert: bool, alert_message: str, severity: str)
    """
    try:
        # Determine severity level
        if suspicion_score >= 76:
            severity = "CRITICAL"
        elif suspicion_score >= 51:
            severity = "HIGH"
        else:
            severity = "MEDIUM"
        
        # Only create alerts for HIGH and CRITICAL
        if severity not in ['HIGH', 'CRITICAL']:
            return False, "", severity
        
        # Rate limiting to prevent spam
        if should_rate_limit(process_name, rate_limit_secs=60):
            return False, "", severity
        
        # Build detailed alert message
        alert_parts = [
            f"{severity}",
            f"Process: {process_name}",
            f"IP: {dest_ip}:{dest_port}",
            f"Score: {suspicion_score:.1f}/100",
            f"Idle: {idle_time:.0f}s"
        ]
        
        if reasons:
            alert_parts.append(f"Reasons: {'; '.join(reasons)}")
        
        alert_msg = " | ".join(alert_parts)
        
        # Record this alert
        record_alert(process_name)
        
        return True, alert_msg, severity
        
    except Exception as e:
        print(f"[AlertMgr] Error generating alert: {e}")
        return False, "", "UNKNOWN"

def format_alert_for_display(alert_dict):
    """Format alert for dashboard display."""
    try:
        return {
            'time': alert_dict.get('timestamp', 'Unknown'),
            'process': alert_dict.get('process_name', 'Unknown'),
            'ip': alert_dict.get('dest_ip', '?'),
            'port': alert_dict.get('dest_port', '?'),
            'severity': alert_dict.get('severity', 'UNKNOWN'),
            'score': round(alert_dict.get('suspicion_score', 0), 1),
            'reason': alert_dict.get('reason', 'No details'),
        }
    except Exception as e:
        print(f"[AlertMgr] Format error: {e}")
        return {}

def get_alert_summary():
    """Get summary of current alerts."""
    critical_count = len([k for k, v in _alert_history.items() 
                         if len(v) > 0])
    
    return {
        'total_alerts': sum(len(v) for v in _alert_history.values()),
        'unique_processes': len(_alert_history),
        'recent_alerts': critical_count
    }

