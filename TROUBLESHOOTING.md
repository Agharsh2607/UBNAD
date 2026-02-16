# UBNAD Windows Edition - Troubleshooting Guide

## Quick Start

1. **Start the backend:**
   ```powershell
   .\run.bat
   ```

2. **Open the dashboard** in your browser:
   ```
   http://localhost:8501
   ```

3. **Generate network activity** to test:
   ```powershell
   curl https://google.com
   nslookup google.com
   ```

---

## Testing Network Collection

### 1. Test psutil capability (no admin required)

```powershell
python test_psutil.py
```

This will show:
- ✓ If psutil can enumerate TCP connections
- ✓ How many outbound vs listening connections exist
- ✓ If process information is accessible
- ✓ If repeated polling detects new connections

**Expected output**: Should show dozens of existing connections (ESTABLISHED, SYN_SENT, etc.)

**If it fails**: You may need admin privileges:
```powershell
# Right-click PowerShell → "Run as Administrator"
# Then try again
python test_psutil.py
```

### 2. Test database

```powershell
python test_database.py
```

This will:
- ✓ Verify database file location
- ✓ Check table schema matches expected format
- ✓ Insert a test event
- ✓ Retrieve events
- ✓ Show total event count

**Expected output**: Should show table columns and ability to insert/read events

---

## Running with Full Diagnostics

The collector and analyzer now print detailed status messages:

### Collector Diagnostics
Every 10 seconds, the backend will print:
```
[Collector] Status: 20 scans, 5 events created, tracking 5 known connections
[Collector] NEW: chrome.exe (1234) -> 142.250.183.14:443
```

### Analyzer Diagnostics
Every 15 seconds, the analyzer will print queue depth and event count.

### Dashboard
Opens at `http://localhost:8501` and shows:
- Last 50 network events
- Process responsible for each connection
- Destination IP and port
- Risk scores and intent detection

---

## Common Issues

### "No events appearing in dashboard"

**Step 1: Check if network events are being detected**
```powershell
# Start backend
.\run.bat

# Look for "[Collector] NEW:" messages in output
# These indicate actual connections being detected

# If you don't see them after 10+ seconds, continue below
```

**Step 2: Verify psutil can see connections**
```powershell
python test_psutil.py

# Check:
# - How many connections are shown?
# - Can it retrieve process information?
# - Does repeated polling find "new" connections?
```

**Step 3: Check database connectivity**
```powershell
python test_database.py

# Verify:
# - Database file location
# - Schema is correct
# - Can insert events
# - Can retrieve events
```

**Step 4: Generate test traffic**
```powershell
# While backend is running, open another PowerShell and run:
curl https://google.com
nslookup google.com
ipconfig /flushdns
```

Then check:
- Console output for "[Collector] NEW:" messages
- Dashboard for new events appearing

### "Access Denied" errors

Some network information on Windows requires **administrator privileges**:

```powershell
# Right-click PowerShell → "Run as Administrator"
.\run.bat
```

If you still get errors, try disabling Windows Defender temporarily:
1. Settings → Privacy & Security → Windows Security
2. Virus & threat protection → Manage settings
3. Toggle "Real-time protection" OFF

### "psutil not found" errors

Install required package:
```powershell
pip install psutil streamlit
```

Or use the included installer:
```powershell
python install_requirements.py
```

### Dashboard not updating

1. **Close and restart Streamlit:**
   - Stop backend (Ctrl+C)
   - Kill any Streamlit processes:
     ```powershell
     Get-Process streamlit -ErrorAction SilentlyContinue | Stop-Process -Force
     ```
   - Restart: `.\run.bat`

2. **Clear cache:**
   - In dashboard, click hamburger menu (top right)
   - Select "Settings"
   - Click "Clear cache"
   - Refresh page

3. **Check database path:**
   ```powershell
   # Database should be at:
   # C:\Users\USER\OneDrive\Desktop\Ubnad\database\ubnad.db
   
   # Verify it exists:
   ls database/ubnad.db
   ```

---

## Diagnostic Output Reference

### What to look for when running `.\run.bat`:

#### Good signs:
```
[Collector] Started - will scan every 0.5s
Database initialized: database/ubnad.db
Analyzer loop started - waiting for network events
[Collector] Status: 20 scans, 5 events created, tracking 5 known connections
[Collector] NEW: firefox.exe (2156) -> 104.21.24.13:443
Event stored: Event(timestamp='2025-01-15 14:30:45', process='firefox.exe', dest_ip='104.21.24.13', ...)
```

#### Bad signs:
```
[Collector] Scan error: AccessDenied (need admin)
[Collector] Status: 20 scans, 0 events created (no network activity)
Database initialization failed (permissions issue)
```

---

## Manual Connection Testing

### Detailed psutil inspection:

```python
import psutil

# See all TCP connections with details
conns = psutil.net_connections(kind='inet')
for conn in conns[:10]:  # First 10
    if conn.raddr:  # Outbound
        try:
            proc = psutil.Process(conn.pid)
            print(f"{proc.name():20} {conn.laddr.ip}:{conn.laddr.port:5} -> {conn.raddr.ip}:{conn.raddr.port:5}")
        except:
            print(f"PID_{conn.pid:5} {conn.laddr.ip}:{conn.laddr.port:5} -> {conn.raddr.ip}:{conn.raddr.port:5}")
```

### Direct database inspection:

```python
import sqlite3

conn = sqlite3.connect('database/ubnad.db')
cursor = conn.cursor()

# See all events
cursor.execute("SELECT timestamp, process_name, dest_ip, dest_port FROM events ORDER BY timestamp DESC LIMIT 10")
for row in cursor.fetchall():
    print(row)

# Count events
cursor.execute("SELECT COUNT(*) FROM events")
print(f"Total events: {cursor.fetchone()[0]}")

conn.close()
```

---

## Architecture Overview

```
Windows Network Activity Flow:
│
├─ windows_net_collector.py (every 0.5 sec)
│  └─ psutil.net_connections()
│     └─ Filts outbound TCP connections
│        └─ Detects NEW connections
│           └─ Creates event dict
│
│
├─ Queue (thread-safe event buffer)
│  
│
├─ main.py analyzer_loop()
│  ├─ Gets event from queue
│  │
│  ├─ process_event()
│  │  ├─ Get process metadata
│  │  ├─ Calculate intent score (user activity)
│  │  ├─ Calculate suspicion score (risk algorithm)
│  │  ├─ Determine risk level
│  │  │
│  │  └─ insert_event() → database
│  │
│  └─ Repeats
│
│
├─ SQLite Database
│  └─ database/ubnad.db
│     └─ Table: events (timestamp, pid, process, dest_ip, dest_port, scores)
│
│
└─ ui/dashboard.py (Streamlit)
   ├─ Refreshes every 1 second
   ├─ Queries: SELECT * FROM events ORDER BY timestamp DESC LIMIT 50
   └─ Displays: table, charts, alerts
```

---

## Performance Notes

- **Collector poll interval**: 0.5 seconds (2 scans per second)
- **Analyzer timeout**: 1 second (processes events as they arrive)
- **Dashboard refresh**: Auto-refresh every second
- **Known connections tracking**: In-memory set (can grow over time)

If collector is creating too many events:
- Increase `poll_interval` in `collector/windows_net_collector.py`
- Reduce `poll_interval` if you're missing connections

---

## Contact / Next Steps

If diagnostics show:

1. **"✓ Successfully enumerated X TCP connections"** in `test_psutil.py`:
   - Network collection is working
   - Check `test_database.py` for database issues

2. **"✗ No outbound connections found"** in `test_psutil.py`:
   - This is unusual - may need admin privileges
   - Try: `Run PowerShell as Administrator`

3. **Database test passes but dashboard empty**:
   - Collector may not be detecting connections on your network
   - Check firewall settings
   - Try generating explicit traffic: `curl https://google.com`

4. **Everything passes but still no events**:
   - May have discovered a platform-specific limitation
   - Provide output of all three test scripts for debugging
