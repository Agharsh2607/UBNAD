"""
Configuration and Whitelist Manager
Centralized settings and trusted process definitions
"""

# Trusted/Whitelisted Processes - Known safe applications
TRUSTED_PROCESSES = {
    # System processes
    'svchost.exe': {'category': 'system', 'score_reduction': 20},
    'services.exe': {'category': 'system', 'score_reduction': 20},
    'lsass.exe': {'category': 'system', 'score_reduction': 20},
    'ntoskrnl.exe': {'category': 'system', 'score_reduction': 20},
    'explorer.exe': {'category': 'system', 'score_reduction': 15},
    'dwm.exe': {'category': 'system', 'score_reduction': 15},
    'csrss.exe': {'category': 'system', 'score_reduction': 20},
    'taskhostw.exe': {'category': 'system', 'score_reduction': 15},
    
    # Browsers
    'chrome.exe': {'category': 'browser', 'score_reduction': 10},
    'firefox.exe': {'category': 'browser', 'score_reduction': 10},
    'msedge.exe': {'category': 'browser', 'score_reduction': 10},
    'opera.exe': {'category': 'browser', 'score_reduction': 10},
    
    # Communications
    'thunderbird.exe': {'category': 'communication', 'score_reduction': 10},
    'telegram.exe': {'category': 'communication', 'score_reduction': 10},
    'slack.exe': {'category': 'communication', 'score_reduction': 10},
    'discord.exe': {'category': 'communication', 'score_reduction': 10},
    
    # Utilities & Tools
    'python.exe': {'category': 'utility', 'score_reduction': 5},
    'node.exe': {'category': 'utility', 'score_reduction': 5},
    'docker.exe': {'category': 'utility', 'score_reduction': 5},
    'git.exe': {'category': 'utility', 'score_reduction': 5},
    'wget.exe': {'category': 'utility', 'score_reduction': 5},
    'curl.exe': {'category': 'utility', 'score_reduction': 5},
    'vmware-host-d.exe': {'category': 'virtualization', 'score_reduction': 10},
}

# Trusted Destination IPs/Ranges - Known safe destinations
TRUSTED_DESTINATIONS = {
    # Content Delivery Networks & CDNs
    '1.1.1.1': 'Cloudflare DNS',
    '8.8.8.8': 'Google DNS',
    '8.8.4.4': 'Google DNS',
    '208.67.222.222': 'OpenDNS',
}

# Ports considered normal and low-risk
SAFE_PORTS = {
    80: 'HTTP',
    443: 'HTTPS',
    53: 'DNS',
    123: 'NTP',
    25: 'SMTP',
    587: 'SMTP',
    110: 'POP3',
    143: 'IMAP',
    465: 'SMTPS',
    993: 'IMAPS',
}

# Unusual ports that raise suspicion
SUSPICIOUS_PORTS = {
    4444: 'Metasploit C2',
    5555: 'Android Debug Bridge',
    6666: 'IRC',
    6667: 'IRC',
    8080: 'Proxy/Web',
    9090: 'Proxy/Web',
    31337: 'Back Orifice',
}

# Scoring Configuration
SUSPICION_SCORING = {
    'unknown_process': 20,              # Process not in whitelist
    'frequent_connections': 25,         # Many rapid connections
    'user_idle_active': 20,             # User idle but process active
    'new_destination': 15,              # Never seen before IP/port combo
    'unusual_port': 10,                 # Non-standard port
    'low_traffic': 3,                   # Light traffic activity
    'beaconing_pattern': 15,            # Repetitive connections to same dest
    'connection_burst': 12,             # Many connections in very short window
    'multi_destination': 10,            # Connecting to many different IPs rapidly
}

# Risk Level Thresholds
RISK_LEVELS = {
    'SAFE': {'min': 0, 'max': 25, 'alert': False},
    'MEDIUM': {'min': 26, 'max': 50, 'alert': False},
    'HIGH': {'min': 51, 'max': 75, 'alert': True},
    'CRITICAL': {'min': 76, 'max': 100, 'alert': True},
}

# Alert Configuration
ALERT_CONFIG = {
    'min_severity': 'HIGH',             # Only alert on HIGH and CRITICAL
    'rate_limit_secs': 60,              # Don't alert same process more than every 60 seconds
    'max_alerts_per_process': 5,        # Max alerts per process per hour
}

# Monitoring Configuration
MONITORING_CONFIG = {
    'poll_interval': 0.5,               # Network scan interval in seconds
    'event_queue_max': 1000,            # Max events in queue
    'cleanup_hours': 24,                # Clean old events after N hours
    'max_known_connections': 10000,     # Track up to N known connections
}

def is_trusted_process(process_name):
    """Check if process is in whitelist."""
    return process_name.lower() in TRUSTED_PROCESSES

def get_process_score_reduction(process_name):
    """Get score reduction for whitelisted process."""
    process_lower = process_name.lower()
    if process_lower in TRUSTED_PROCESSES:
        return TRUSTED_PROCESSES[process_lower]['score_reduction']
    return 0

def is_trusted_destination(ip_address):
    """Check if destination IP is trusted."""
    return ip_address in TRUSTED_DESTINATIONS

def get_destination_name(ip_address):
    """Get friendly name for trusted IP."""
    return TRUSTED_DESTINATIONS.get(ip_address, 'Unknown')

def is_safe_port(port):
    """Check if port is in safe/common ports list."""
    return port in SAFE_PORTS

def get_port_name(port):
    """Get service name for port."""
    if port in SAFE_PORTS:
        return SAFE_PORTS[port]
    elif port in SUSPICIOUS_PORTS:
        return SUSPICIOUS_PORTS[port]
    return 'Unknown'

def get_risk_level_from_score(score):
    """Determine risk level from numerical score."""
    for level, config in RISK_LEVELS.items():
        if config['min'] <= score <= config['max']:
            return level
    return 'SAFE'

def should_alert(risk_level):
    """Check if risk level should trigger alert."""
    return RISK_LEVELS.get(risk_level, {}).get('alert', False)
