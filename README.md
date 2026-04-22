# UBNAD - Unauthorized Background Network Activity Detector

**Windows Edition** | Real-time network monitoring with AI-powered threat detection

## 🎯 Overview

UBNAD is a sophisticated Windows-based security tool that monitors unauthorized background network activity. It combines real-time network packet analysis with behavioral profiling and machine learning to detect suspicious processes attempting unauthorized network communications.

## ✨ Features

- **Real-Time Network Monitoring**: Captures and analyzes all network connections in real-time
- **Process Behavior Profiling**: Builds baseline behavior models for each process
- **AI-Powered Suspicion Scoring**: Advanced suspicion engine calculates risk scores (0-100)
- **Intent Analysis**: Monitors user activity to correlate with network events
- **Alert Management**: Generates actionable alerts for high-risk activities
- **SQLite Logging**: Persistent database storage for forensic analysis
- **Graceful Shutdown**: Ensures all data is saved on exit

## 📋 Requirements

- **Windows 10/11** (x64)
- **Python 3.8+**
- **Administrator privileges** (for network packet capture)
- **Dependencies**:
  ```bash
  pip install -r requirements.txt
  ```

## 🚀 Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/UBNAD.git
   cd UBNAD
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run with administrator privileges**:
   ```bash
   python main.py
   ```

## 📁 Project Structure

```
UBNAD/
├── main.py                          # Main orchestration & event loop
├── config.py                        # Configuration & trusted processes
├── requirements.txt                 # Python dependencies
├── database/
│   └── activity_store.py           # SQLite database operations
├── collector/
│   └── windows_net_collector.py    # Windows network packet capture
├── core/
│   ├── intent_monitor.py           # User activity analysis
│   ├── process_mapper.py           # Process metadata resolution
│   ├── behavior_model.py           # Baseline profiling
│   ├── suspicion_engine.py         # Risk scoring algorithm
│   └── alert_manager.py            # Alert generation
└── database/
    └── ubnad.db                    # SQLite database (auto-created)
```

## 🔧 Usage

### Basic Start
```bash
python main.py
```

### What It Does
1. Initializes SQLite database (`database/ubnad.db`)
2. Starts Windows network collector (requires admin)
3. Processes network events in real-time
4. Calculates suspicion scores for each connection
5. Logs events and generates alerts for suspicious activity
6. Saves all data persistently on shutdown (Ctrl+C)

### Example Output
```
2026-04-22 14:30:45,123 - INFO - UBNAD - Unauthorized Background Network Activity Detector
2026-04-22 14:30:45,456 - INFO - Database initialized: database/ubnad.db
2026-04-22 14:30:46,789 - INFO - Windows network collector started
2026-04-22 14:30:47,012 - INFO - Analyzer loop started - waiting for network events
2026-04-22 14:31:05,345 - WARNING - 🚨 ALERT: Suspicious network activity detected from chrome.exe
2026-04-22 14:31:05,567 - INFO - ⚠️  HIGH: chrome.exe (4892) -> 192.168.1.100:443 (Score: 72.5)
```

## 📊 Suspicion Scoring

The suspicion engine calculates scores on a **0-100 scale**:

- **0-25**: SAFE - Normal activity
- **26-50**: MEDIUM - Requires monitoring
- **51-75**: HIGH - Suspicious behavior
- **76-100**: CRITICAL - Immediate action required

Factors considered:
- Process behavior baseline deviation
- Port reputation (known malware ports)
- Timing patterns (idle vs. active user)
- Connection frequency and volume
- Destination IP reputation

## 🛡️ Configuration

Edit `config.py` to customize:
- Trusted processes (whitelist)
- Safe ports (allowlist)
- Alert thresholds
- Behavior baselines

## 💾 Database

Events are stored in `database/ubnad.db` with fields:
- `timestamp` - Event time
- `pid` - Process ID
- `process_name` - Executable name
- `dest_ip` - Destination IP
- `dest_port` - Destination port
- `suspicion_score` - Calculated risk (0-100)
- `risk_level` - SAFE/MEDIUM/HIGH/CRITICAL
- `severity` - Display severity
- `reasons` - List of risk factors
- `intent_score` - User activity metric

### Query Examples
```sql
-- Find all HIGH and CRITICAL alerts
SELECT * FROM events WHERE suspicion_score >= 50 ORDER BY timestamp DESC;

-- Top suspicious processes
SELECT process_name, COUNT(*) as connections, AVG(suspicion_score) as avg_risk 
FROM events GROUP BY process_name ORDER BY avg_risk DESC LIMIT 10;

-- Recent alerts
SELECT timestamp, process_name, dest_ip, dest_port, suspicion_score 
FROM events WHERE risk_level IN ('HIGH', 'CRITICAL') 
ORDER BY timestamp DESC LIMIT 20;
```

## ⚙️ Advanced Features

### Behavior Profiling
- Maintains per-process behavior baselines
- Detects anomalies based on historical patterns
- Adapts to legitimate process behavior over time

### Intent Analysis
- Correlates network activity with user activity
- Detects background activity during idle periods
- Flags suspicious timing patterns

### Alert Management
- Configurable alert rules
- Severity-based filtering
- Detailed reasoning for each alert

## 🔐 Security Considerations

- **Admin Required**: Network packet capture needs administrator privileges
- **Minimal Overhead**: Efficient real-time processing
- **Local Storage**: All data stored locally in SQLite
- **Graceful Shutdown**: Ensures data persistence on exit

## 🐛 Troubleshooting

### "Permission Denied" Error
Run terminal as Administrator:
```bash
python main.py
```

### Database Locked Error
Ensure no other instances are running. Close and restart:
```bash
# Kill any running instances
taskkill /f /im python.exe
python main.py
```

### No Network Events Captured
- Verify Windows Defender/Firewall isn't blocking
- Check network adapter is not disabled
- Ensure WinPcap/Npcap is properly installed

## 📝 Logging

Logs are displayed in console with timestamps. For persistent logs, redirect output:
```bash
python main.py > ubnad.log 2>&1
```

## 🤝 Contributing

Contributions welcome! Areas for enhancement:
- ML-based anomaly detection
- Network visualization dashboard
- Integration with SIEM systems
- Performance optimization

## 📄 License

MIT License - See LICENSE file for details

## 👤 Author

Created for advanced network security monitoring

## 🔗 Links

- [GitHub Repository](https://github.com/YOUR_USERNAME/UBNAD)
- [Issues & Feature Requests](https://github.com/YOUR_USERNAME/UBNAD/issues)
- [Discussions](https://github.com/YOUR_USERNAME/UBNAD/discussions)

---

**Last Updated**: April 22, 2026 | Version 1.0.0
