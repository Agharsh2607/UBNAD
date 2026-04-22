# UBNAD 2.0 - Quick Start Guide

## 🚀 Installation & Setup

### Prerequisites
- Windows 10/11
- Python 3.8+
- Administrator access (for network monitoring)

### Step 1: Install Python Dependencies

```bash
pip install -r requirements.txt
```

**Required packages:**
- streamlit (dashboard UI)
- pandas (data manipulation)
- psutil (network monitoring)
- plotly (charts & visualization)
- pynput (user activity detection)
- pywin32 (Windows integration)

### Step 2: Run the Application

**Via batch file (recommended):**
```bash
run.bat
```

**Or directly with Python:**
```bash
python main.py
```

### Step 3: Access the Dashboard

1. The collector will start logging network events to console
2. In a separate terminal, run the dashboard:
```bash
streamlit run ui/dashboard.py
```
3. Open browser: `http://localhost:8501`

---

## 🎯 Quick Configuration

### Add a Trusted Process

Edit `config.py`:

```python
TRUSTED_PROCESSES = {
    'myapp.exe': {'category': 'application', 'score_reduction': 15},
}
```

### Add a Trusted Destination IP

Edit `config.py`:

```python
TRUSTED_DESTINATIONS = {
    '192.168.1.100': 'Internal Server',
}
```

### Adjust Alert Sensitivity

**Sensitivity levels (edit config.py):**

```python
RISK_LEVELS = {
    'SAFE': {'min': 0, 'max': 25},
    'MEDIUM': {'min': 26, 'max': 50},
    'HIGH': {'min': 51, 'max': 75},      # Alerts triggered here
    'CRITICAL': {'min': 76, 'max': 100},  # And here
}
```

---

## 📊 Dashboard Overview

### Available Tabs

**1. 📊 Dashboard** (Main view)
- Real-time statistics (Safe/Medium/High/Critical counts)
- Risk distribution pie chart
- Top processes bar chart
- Live activity table

**2. 🚨 Alerts** (Alert history)
- All HIGH and CRITICAL events
- Detailed reasoning for each alert
- Expandable alert details

**3. 📈 Analysis** (Deep dive)
- Score distribution histogram
- Activity timeline
- Per-process statistics
- Process activity trends

**4. 💾 Export** (Data export)
- Export all events as CSV
- Export alerts only
- View recent exports

---

## 🎮 Basic Usage

### Monitor Network Connections

```bash
# Start the collector and analyzer
python main.py

# (In another terminal) View the dashboard
streamlit run ui/dashboard.py
```

### Export Suspicious Events

**Via dashboard:**
1. Click "💾 Export" tab
2. Click "📥 Export Alerts Only (CSV)"
3. Check `exports/` folder

**Via Python:**
```python
from utils import export_suspicious_events_csv

# Export all events
path = export_suspicious_events_csv()

# Export only critical
path = export_suspicious_events_csv(severity_filter='CRITICAL')
```

### Query Database Directly

```python
from database.activity_store import get_alerts, get_process_events

# Get all alerts
alerts = get_alerts(limit=50)

# Get events for specific process
events = get_process_events('chrome.exe', limit=20)
```

---

## 🔴 Understanding Alerts

### Alert Format

```
🔴 CRITICAL | Process: svchost.exe | IP: 1.2.3.4:4444 | Score: 85.0/100 | Idle: 120s
Reasons: Unknown process not in whitelist; New destination: 1.2.3.4:4444; Unusual port: 4444
```

### What Triggers an Alert?

- **Score ≥ 51** = Potential threat
- **Score ≥ 76** = High confidence threat
- **Only 1 alert per process per 60 seconds** (rate limited)

### Scoring Factors (+points = more suspicious)

- Unknown process: **+20 points**
- 10+ connections/minute: **+25 points**
- User idle but process active: **+20 points**
- First time seeing this IP:port: **+15 points**
- Unusual port (not 80/443/53): **+10 points**

---

## 📈 Example Scenarios

### Scenario 1: Detection - Malware Attempt

```
Process: suspicious.exe
Target: 192.168.1.100:4444
Score: 92/100 (CRITICAL)

Why?
✓ Unknown process (not whitelisted) +20
✓ Unusual port 4444 +10
✓ New destination +15
✓ 15 connections in 60 seconds +25
✓ User idle for 5 minutes +20
✓ Traffic spike 5MB +5
= 95/100 → CRITICAL ALERT
```

### Scenario 2: False Positive - Whitelisted Browser

```
Process: chrome.exe
Target: 172.217.14.206:443
Score: 5/100 (SAFE)

Why?
✓ Trusted browser in whitelist -10
✓ Safe port 443 (HTTPS) 0
✓ Known destination (Google) 0
✓ Normal connection pattern 0
✓ User active (typing) 0
= 5/100 → SAFE (no alert)
```

### Scenario 3: Monitored - Suspicious System Process

```
Process: dwm.exe
Target: 10.20.30.40:31337
Score: 45/100 (MEDIUM)

Why?
✓ System process in whitelist -20
✓ Unusual port 31337 +10
✓ New destination +15
✓ Light activity +10
✓ User idle +20
= 45/100 → MEDIUM (monitored, no alert)
```

---

## ⚙️ Advanced Configuration

### Change Network Poll Interval

Faster = more CPU usage, slower = might miss events

```python
# In config.py
MONITORING_CONFIG = {
    'poll_interval': 0.5,  # Scan every 500ms (default)
}

# Change to: 1.0 for 1 second (lighter load)
```

### Adjust Score Calculations

Edit `core/suspicion_engine.py` to modify individual factors.

### Add Custom Alert Triggers

Edit `core/alert_manager.py` to customize alert generation.

---

## 🐛 Troubleshooting

### Q: No events are being recorded

**A:** Check collector is running in main.py:
```bash
python main.py 2>&1 | grep "\[Collector\]"
```

Expected output:
```
[Collector] Started - will scan every 0.5s
[Collector] Status: 15 scans, 23 events created
```

### Q: Getting too many alerts

**A:** Increase rate limit in `config.py`:
```python
ALERT_CONFIG = {
    'rate_limit_secs': 60,  # Increase to 120 or 300
}
```

Or add process to whitelist to reduce score.

### Q: Dashboard not loading

**A:** Make sure Streamlit is installed:
```bash
pip install streamlit>=1.28.0
```

Then run:
```bash
streamlit run ui/dashboard.py
```

### Q: High CPU usage

**A:** Reduce polling frequency in `config.py`:
```python
'poll_interval': 1.0,  # Changed from 0.5
```

---

## 📊 Reading the Dashboard

### Risk Metrics
- **🟢 Safe**: 0-25 (no action needed)
- **🟡 Medium**: 26-50 (monitor)
- **🔴 High**: 51-75 (investigate)
- **🔴 Critical**: 76-100 (urgent action)

### Color Coding
- Green background = SAFE
- Orange background = MEDIUM
- Red background = HIGH/CRITICAL

### Top Processes
Shows which processes are generating the most network events.

---

## 📝 Common Tasks

### Export suspicious activity for analysis

```bash
# Via dashboard: Open Export tab, click "Export Alerts Only"

# Via code:
python -c "from utils import export_suspicious_events_csv; \
           print(export_suspicious_events_csv(severity_filter='CRITICAL'))"
```

### Find all events from a specific process

```python
from database.activity_store import get_process_events
import pandas as pd

events = get_process_events('svchost.exe', limit=100)
df = pd.DataFrame(events)
print(f"High severity: {len(df[df['severity'] == 'CRITICAL'])}")
print(f"Average score: {df['suspicion_score'].mean():.1f}")
```

### Check alert history

```python
from database.activity_store import get_alerts

alerts = get_alerts(limit=50)
for alert in alerts:
    print(f"{alert['timestamp']} - {alert['process_name']} ({alert['severity']})")
```

---

## 🔐 Security Best Practices

1. **Review alerts regularly** - Daily alert check recommended
2. **Maintain whitelist** - Remove unused entries quarterly
3. **Monitor unusual processes** - Check top processes chart
4. **Export suspicious events** - Keep forensic records
5. **Update configurations** - Adjust as new apps installed

---

## 🚀 Performance Tips

| Adjustment | Impact | CPU | Memory |
|-----------|--------|-----|--------|
| Increase poll_interval | Slower detection | ↓ | ↓ |
| Reduce whitelist | More alerts | ↑ | ↔ |
| Increase rate_limit | Fewer alerts | ↓ | ↓ |
| Reduce dashboard refresh | Less responsive | ↓ | ↓ |

---

## 📞 Quick Help

**See application logs:**
```bash
python main.py 2>&1 | tee ubnad.log
```

**Clear old events (>24 hours):**
```python
from database.activity_store import clear_old_events
clear_old_events(hours=24)
```

**Get database statistics:**
```python
from database.activity_store import get_event_count, get_risk_distribution

print(f"Total events: {get_event_count()}")
print(f"Risk dist: {get_risk_distribution()}")
```

---

## 🎓 Learn More

- **Full Documentation**: See `ENHANCEMENTS.md`
- **Configuration Help**: See `config.py` comments
- **API Reference**: Check docstrings in `database/activity_store.py`
- **Troubleshooting**: See `TROUBLESHOOTING.md`

---

**🎯 You're ready to start! Run `python main.py` now.**
