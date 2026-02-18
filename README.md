

# UBNAD

**Unauthorized Background Network Activity Detector**  
Real-time network monitoring and suspicion scoring for Windows 10/11

---

## Quick Start

### 1. Prerequisites

- **Windows 10/11** (64-bit)
- **Python 3.10+** - Download from https://www.python.org/downloads/
  - ☑️ Check "Add Python to PATH" during installation
- **Network connectivity** (obviously)

### 2. Verify Python Installation

Open Command Prompt and run:

```cmd
python --version
```

Should output: `Python 3.10.x` or higher

### 3. Run UBNAD

Navigate to project folder and run:

```cmd
run.bat
```

This will:
1. Install all required dependencies
2. Start the backend (network monitoring service)
3. Launch Streamlit dashboard at `http://localhost:8501`

### 4. Open Dashboard

Open your browser and go to:
```
http://localhost:8501
```

---

## How It Works

### Architecture

```
Windows Network Stack
    ↓ (Connection polling via psutil)
Windows Network Collector
    ↓ (Queue-based event push)
Event Analyzer
    ├─ Intent Monitor (user activity detection)
    ├─ Process Mapper (process metadata)
    ├─ Behavior Model (traffic baseline learning)
    ├─ Suspicion Engine (risk scoring)
    └─ Alert Manager (high-risk notifications)
    ↓
SQLite Database (ubnad_events.db)
    ↓
Streamlit Dashboard (live visualization)
```

### Network Collection

The Windows Network Collector:
- **Polls** active TCP connections every 1 second
- **Scans** using `psutil.net_connections()`
- **Filters** established outbound connections
- **Maps** connection → PID → process name
- **Detects** only new connections (avoids duplicates)
- **Runs** in background thread
- **No admin required** for basic monitoring

### Analysis Pipeline

Each network event is processed:

1. **Process Resolution** - Map connection to process name/metadata
2. **Intent Scoring** - Check user activity (mouse/keyboard listeners)
3. **Baseline Learning** - Compare against historical traffic patterns
4. **Suspicion Calculation** - Score based on:
   - Intent mismatch (idle user + traffic)
   - Abnormal traffic volume
   - Known suspicious applications
5. **Risk Classification** - SAFE / MEDIUM / HIGH / CRITICAL
6. **Database Storage** - Event logged with full context
7. **Alert Generation** - Console + dashboard alerts for HIGH/CRITICAL

### Risk Calculation

Suspicion score is increased by:
- **+10 points** - User idle while app sends traffic
- **+5 points** - Traffic > 5x baseline activity
- **+15 points** - Known silent app (calculator, notepad, etc.)

Events with score > 10 trigger alerts.

---

## Dashboard Features

### Live Metrics
- Total events processed
- High-risk event count
- Unique processes monitored
- Unique destination IPs

### Alerts Panel
- Real-time HIGH/CRITICAL alerts
- Process name, destination IP, risk score
- Timestamp and user idle duration

### Live Activity Table
- Last 50 network connections
- Timestamp, process, destination, risk level
- Color-coded by severity

### Charts
- **Traffic by Process** - Top applications by data transfer
- **Risk Distribution** - Pie chart of event severity breakdown

### Auto-Refresh
- Refreshes every 3 seconds by default
- Adjustable via sidebar slider
- Uses database (no fake data)

---

## Database

**Location:** `ubnad_events.db` (created automatically)

**Table: events**

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-increment ID |
| timestamp | REAL | Event Unix timestamp |
| pid | INTEGER | Process ID |
| process_name | TEXT | Executable name |
| dest_ip | TEXT | Destination IP address |
| dest_port | INTEGER | Destination port |
| src_ip | TEXT | Source IP (local) |
| src_port | INTEGER | Source port (local) |
| intent_score | REAL | User activity (0-1) |
| suspicion_score | REAL | Risk score (0-100) |
| traffic_kb | INTEGER | Data transfer estimate |
| idle_time | REAL | User idle seconds |
| risk_level | TEXT | SAFE/MEDIUM/HIGH/CRITICAL |

---

## Files & Structure

```
ubnad/
├── main.py                           # Main orchestration
├── requirements.txt                  # Python dependencies
├── run.bat                          # Windows startup script
├── ubnad_events.db                  # Database (created on first run)
├── logs/
│   └── backend.log                  # Service logs
├── collector/
│   ├── __init__.py
│   └── windows_net_collector.py     # Windows network monitor
├── core/
│   ├── __init__.py
│   ├── intent_monitor.py            # User activity detection
│   ├── process_mapper.py            # Process metadata lookup
│   ├── behavior_model.py            # Baseline learning
│   ├── suspicion_engine.py          # Risk scoring
│   └── alert_manager.py             # Alert generation
├── database/
│   ├── __init__.py
│   └── activity_store.py            # SQLite persistence
└── ui/
    ├── __init__.py
    └── dashboard.py                 # Streamlit web UI
```

---

## Troubleshooting

### "python command not found"
- Python not in PATH
- Solution: Reinstall Python and check "Add Python to PATH"

### Dependencies installation fails
- Ensure internet connection
- Try manual install:
  ```cmd
  pip install psutil streamlit pandas plotly pynput
  ```

### Dashboard won't open at localhost:8501
- Wait 10 seconds after running run.bat
- Check firewall isn't blocking localhost
- Try opening http://127.0.0.1:8501 instead

### No events appearing
- Check backend console for errors
- Ensure network connections are being made (open browser, etc.)
- Check `logs\backend.log` for details

### High CPU usage
- Normal during startup
- Polling interval adjustable in collector (default 1 sec)
- Reduce for less frequent scans

### Database locked error
- Close dashboard
- Delete `ubnad_events.db`
- Restart

---

## Performance

- **Memory:** ~100-200 MB (scales with event count)
- **CPU:** <1% idle, <5% during collection/analysis
- **Network:** No external connections (local only)
- **Latency:** Event to dashboard ~500ms

---

## Security Notes

- **No admin required** for basic monitoring
- All events stored **locally** in SQLite
- **No telemetry** sent to external servers
- Input monitoring via **keyboard/mouse listeners** (Windows compatible)
- Graceful handling of privilege limitations

---

## Advanced Usage

### Manually Run Components

**Backend only:**
```cmd
python main.py
```

**Dashboard only:**
```cmd
streamlit run ui\dashboard.py
```

### Adjust Collection Frequency

Edit `collector/windows_net_collector.py`:
```python
self.poll_interval = 2.0  # Change from 1.0 to 2.0 seconds
```

### Change Risk Thresholds

Edit `main.py` `determine_risk_level()`:
```python
if score > 25:      # Increase from 20
    return "CRITICAL"
```

---

## Known Limitations

- Requires Windows 10/11
- pynput may not work in all terminal environments
- Intent scoring relies on GUI input detection (fails in headless mode)
- Memory grows with event history (database cleanup available)

---

## Support

For issues, check:
1. Python version: `python --version`
2. Dependencies: `pip list | findstr /I "psutil streamlit"`
3. Logs: `type logs\backend.log`
4. Firewall: Check Windows Defender Firewall

---

**UBNAD v2.0 - Windows Edition**  
Unauthorized Background Network Activity Detector
