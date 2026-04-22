import sys
import os
import time
from config import (
    TRUSTED_PROCESSES,
    get_process_score_reduction,
    is_safe_port,
    SUSPICION_SCORING,
    RISK_LEVELS,
)

# Track seen destination IPs and port combinations
_seen_destinations = {}  # {process_name: set of (ip, port)}
_connection_history = {}  # {process_name: [(timestamp, ip, port)]}

def track_connection(process_name, dest_ip, dest_port, timestamp):
    """Track network connection for pattern detection."""
    if process_name not in _seen_destinations:
        _seen_destinations[process_name] = set()
    
    _seen_destinations[process_name].add((dest_ip, dest_port))
    
    if process_name not in _connection_history:
        _connection_history[process_name] = []
    
    _connection_history[process_name].append((timestamp, dest_ip, dest_port))
    
    # Keep only last 1000 connections per process
    if len(_connection_history[process_name]) > 1000:
        _connection_history[process_name].pop(0)

def get_recent_connection_count(process_name, time_window=60):
    """Get connection count in recent time window (seconds)."""
    if process_name not in _connection_history:
        return 0
    
    now = time.time()
    return sum(1 for ts, _, _ in _connection_history[process_name] 
              if now - ts < time_window)

def is_new_destination(process_name, dest_ip, dest_port):
    """Check if this is a new destination for the process."""
    if process_name not in _seen_destinations:
        return True
    return (dest_ip, dest_port) not in _seen_destinations[process_name]

# ── NEW: Beaconing pattern helpers ──────────────────────────────────

def _get_same_dest_count(process_name, dest_ip, dest_port, time_window=60):
    """Count connections to the *exact same* destination in the time window."""
    if process_name not in _connection_history:
        return 0
    now = time.time()
    return sum(
        1 for ts, ip, port in _connection_history[process_name]
        if now - ts < time_window and ip == dest_ip and port == dest_port
    )

# ── NEW: Burst detection helper ─────────────────────────────────────

def _get_burst_count(process_name, time_window=10):
    """Count connections in a very short window (burst detector)."""
    if process_name not in _connection_history:
        return 0
    now = time.time()
    return sum(1 for ts, _, _ in _connection_history[process_name]
              if now - ts < time_window)

# ── NEW: Multi-destination helper ───────────────────────────────────

def _get_unique_dest_count(process_name, time_window=60):
    """Count unique (ip, port) pairs contacted in the time window."""
    if process_name not in _connection_history:
        return 0
    now = time.time()
    recent = {
        (ip, port)
        for ts, ip, port in _connection_history[process_name]
        if now - ts < time_window
    }
    return len(recent)

# ════════════════════════════════════════════════════════════════════

def calculate_suspicion(process_name, traffic_bytes, intent_score, baseline, 
                       dest_ip=None, dest_port=None, timestamp=None):
    """
    Calculate comprehensive suspicion/risk score (0-100) for network activity.
    
    Scoring factors:
    - Unknown process: +20
    - Frequent connections: +25
    - User idle but active: +20
    - New destination: +15
    - Unusual port: +10
    - Beaconing pattern: +15  (repeated connections to same dest)
    - Connection burst: +12   (many connections in < 10 s)
    - Multi-destination: +10  (contacting many different IPs)
    """
    score = 0.0
    reasons = []
    
    # 1. UNKNOWN PROCESS CHECK (+20)
    is_whitelisted = process_name.lower() in TRUSTED_PROCESSES
    if is_whitelisted:
        score_reduction = get_process_score_reduction(process_name)
        # Reduce base score for trusted processes
        score -= score_reduction
    else:
        score += SUSPICION_SCORING['unknown_process']
        reasons.append("Unknown process not in whitelist")
    
    # 2. FREQUENT CONNECTIONS CHECK (+25)
    if dest_port and timestamp:
        track_connection(process_name, dest_ip or 'unknown', dest_port, timestamp)
    
    recent_connections = get_recent_connection_count(process_name, time_window=60)
    if recent_connections > 10:
        score += SUSPICION_SCORING['frequent_connections']
        reasons.append(f"Frequent connections: {recent_connections} in 60 seconds")
    elif recent_connections > 5:
        score += 15  # Increased partial score (was 10)
        reasons.append(f"Multiple connections: {recent_connections} in 60 seconds")
    elif recent_connections > 3:
        score += 8   # New: even 3-5 connections is mildly suspicious
        reasons.append(f"Elevated connection rate: {recent_connections} in 60 seconds")
    
    # 3. USER IDLE BUT ACTIVE CHECK (+20)
    if intent_score < 0.2:  # User is idle
        score += SUSPICION_SCORING['user_idle_active']
        reasons.append("User is idle but process is active")
    elif intent_score < 0.5:  # User is somewhat active
        score += 8
        reasons.append("Low user activity while process sends data")
    elif intent_score < 0.8:  # User is active but process is still suspicious
        score += 3
    
    # 4. NEW DESTINATION CHECK (+15)
    if dest_ip and dest_port:
        if is_new_destination(process_name, dest_ip, dest_port):
            score += SUSPICION_SCORING['new_destination']
            reasons.append(f"New destination: {dest_ip}:{dest_port}")
    
    # 5. UNUSUAL PORT CHECK (+10)
    if dest_port:
        if not is_safe_port(dest_port):
            score += SUSPICION_SCORING['unusual_port']
            reasons.append(f"Unusual port: {dest_port}")
    
    # 6. TRAFFIC VOLUME ANALYSIS
    baseline_traffic = baseline.get('traffic_total', 500)
    if traffic_bytes > baseline_traffic * 3:
        score += 5
        reasons.append(f"Abnormal traffic volume: {traffic_bytes} bytes")
    elif traffic_bytes > baseline_traffic * 2:
        score += 2
    
    # 7. CONNECTION FREQUENCY BASELINE
    baseline_conn_count = baseline.get('connection_count', 0)
    if baseline_conn_count > 20:
        score += 5
        reasons.append(f"High connection frequency baseline: {baseline_conn_count}")
    
    # ── 8. BEACONING PATTERN CHECK (+15) ────────────────────────────
    #   Detects repetitive connections to the *same* destination,
    #   which is a hallmark of C2 beacons and automated scrapers.
    if dest_ip and dest_port:
        same_dest = _get_same_dest_count(process_name, dest_ip, dest_port, 60)
        if same_dest > 8:
            score += SUSPICION_SCORING.get('beaconing_pattern', 15)
            reasons.append(f"Beaconing pattern: {same_dest} hits to {dest_ip}:{dest_port}")
        elif same_dest > 4:
            score += 8
            reasons.append(f"Repeated destination: {same_dest} hits to {dest_ip}:{dest_port}")
    
    # ── 9. CONNECTION BURST CHECK (+12) ─────────────────────────────
    #   Fires when many connections happen in a very short window.
    burst = _get_burst_count(process_name, time_window=10)
    if burst > 5:
        score += SUSPICION_SCORING.get('connection_burst', 12)
        reasons.append(f"Connection burst: {burst} connections in 10 seconds")
    elif burst > 3:
        score += 6
        reasons.append(f"Rapid connection rate: {burst} in 10 seconds")
    
    # ── 10. MULTI-DESTINATION CHECK (+10) ───────────────────────────
    #   Flags processes that contact many *different* IPs quickly,
    #   resembling port scanning or domain enumeration.
    unique_dests = _get_unique_dest_count(process_name, time_window=60)
    if unique_dests > 6:
        score += SUSPICION_SCORING.get('multi_destination', 10)
        reasons.append(f"Multi-destination activity: {unique_dests} unique endpoints")
    elif unique_dests > 3:
        score += 5
        reasons.append(f"Multiple destinations: {unique_dests} unique endpoints")
    
    # Ensure score is within bounds (0-100)
    score = max(0, min(100, score))
    
    return score, reasons

def determine_risk_level(score):
    """Determine risk level from suspicion score (0-100)."""
    if score >= 76:
        return "CRITICAL"
    elif score >= 51:
        return "HIGH"
    elif score >= 26:
        return "MEDIUM"
    else:
        return "SAFE"

def get_severity_indicator(risk_level):
    """Get emoji/visual indicator for severity."""
    indicators = {
        'SAFE': '✅',
        'MEDIUM': '⚠️',
        'HIGH': '🔴',
        'CRITICAL': '🚨',
    }
    return indicators.get(risk_level, '?')
