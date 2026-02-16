import streamlit as st
import pandas as pd
import sys
import os
import time
from datetime import datetime

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.activity_store import fetch_recent_events, get_alerts, get_event_count, init_db

# Ensure database exists before querying
init_db()

st.set_page_config(page_title="UBNAD Monitor", layout="wide", page_icon="🛡️")

st.title("🛡️ UBNAD Privacy Monitor")
st.caption("Unauthorized Background Network Activity Detector - Windows Edition")

# Sidebar controls
st.sidebar.header("⚙️ Controls")
refresh_rate = st.sidebar.slider("Auto-Refresh Rate (sec)", 1, 10, 2, step=1)
st.sidebar.info("Status: ✅ Live Monitoring Active")

# Auto-refresh trigger using streamlit-autorefresh approach
if "page_load_time" not in st.session_state:
    st.session_state.page_load_time = time.time()

# Display current refresh settings
st.sidebar.success(f"📡 Refreshing every {refresh_rate} seconds")

# Fetch data from database (directly, no cache issues)
try:
    events = fetch_recent_events(limit=50)
    alerts = get_alerts(limit=20)
    total_count = get_event_count()
    df = pd.DataFrame(events) if events else pd.DataFrame()
except Exception as e:
    st.error(f"Database error: {e}")
    df = pd.DataFrame()
    alerts = []
    total_count = 0

# Live metrics - Real-time statistics
st.subheader("📊 Live Statistics")
col1, col2, col3, col4, col5 = st.columns(5)

if len(df) > 0:
    high_risk = len(df[df["suspicion_score"] > 10])
    critical = len(df[df["suspicion_score"] > 20])
    unique_processes = df["process_name"].nunique()
    
    col1.metric("📈 Total Events", total_count)
    col2.metric("⚠️ High Risk", high_risk, delta=f"{high_risk} recent")
    col3.metric("🔴 Critical", critical, delta=f"{critical} recent")
    col4.metric("🔧 Processes", unique_processes)
    col5.metric("📡 Live", "✅ Recording", delta="0s ago")
else:
    col1.metric("📈 Total Events", 0)
    col2.metric("⚠️ High Risk", 0)
    col3.metric("🔴 Critical", 0)
    col4.metric("🔧 Processes", 0)
    col5.metric("📡 Live", "⏳ Waiting")

st.divider()

# Live table
st.subheader("📡 Live Network Activity")

if len(df) == 0:
    st.info("⏳ Waiting for network activity...")
else:
    # Format for display
    df_display = df.copy()
    df_display["suspicion_score"] = df_display["suspicion_score"].round(2)
    
    # Select columns
    cols_to_show = ["timestamp", "process_name", "dest_ip", "dest_port", "suspicion_score", "risk_level"]
    df_display = df_display[cols_to_show]
    
    # Color styling
    def highlight(row):
        if row["risk_level"] == "CRITICAL":
            return ["background-color: #450a0a; color: white"] * len(row)
        elif row["risk_level"] == "HIGH":
            return ["background-color: #7f1d1d"] * len(row)
        elif row["risk_level"] == "MEDIUM":
            return ["background-color: #78350f"] * len(row)
        else:
            return ["background-color: #064e3b"] * len(row)
    
    st.dataframe(df_display.style.apply(highlight, axis=1), use_container_width=True, height=400)

st.divider()

# Alerts
st.subheader("🚨 Recent Alerts")

if len(alerts) == 0:
    st.success("✅ No suspicious behavior detected")
else:
    for alert in alerts[:5]:
        risk = alert.get("risk_level", "UNKNOWN")
        score = alert.get("suspicion_score", 0)
        process = alert.get("process_name", "Unknown")
        ip = alert.get("dest_ip", "Unknown")
        port = alert.get("dest_port", 0)
        timestamp = alert.get("timestamp", "")
        
        if risk in ["HIGH", "CRITICAL"]:
            emoji = "🔴" if risk == "CRITICAL" else "🟠"
            st.warning(f"{emoji} **{risk}** | {process} → {ip}:{port} | Score: {score:.1f} | {timestamp}")

st.divider()

# Live status footer with timestamp
col_time, col_refresh = st.columns([3, 1])
with col_time:
    st.markdown(f"**🕐 Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | **Auto-Refresh:** Every {refresh_rate}s")
with col_refresh:
    st.caption("UBNAD v2.0 Windows Edition")

# Auto-refresh mechanism
time.sleep(refresh_rate)
st.rerun()

